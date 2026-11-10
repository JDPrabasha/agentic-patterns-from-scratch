import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from shop import Shop, grade_book_club, shop_toolbox
from agentic import ToolError

from .fakes import ScriptedLLM, message, text, tool

ROOT = Path(__file__).resolve().parent.parent
LABS = ROOT / "labs"
sys.path.insert(0, str(LABS))


def load_lab(filename):
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), LABS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def solve_by_hand(shop):
    """A correct solution: Left Hand of Darkness, restock 3, six orders, six emails."""
    shop.restock("BK-104", 3)
    for m in shop.list_book_club_members():
        order = shop.place_order(m["customer_id"], "BK-104", 1)
        shop.send_email(m["email"], "Book club", f"Your order id is {order['order_id']}.")


class ShopTests(unittest.TestCase):
    def test_place_order_needs_stock(self):
        shop = Shop()
        with self.assertRaises(ToolError) as ctx:
            shop.place_order("C-310", "BK-103", 1)  # Foundation: 0 in stock
        self.assertIn("restock", str(ctx.exception))

    def test_restock_budget_is_enforced(self):
        shop = Shop()
        with self.assertRaises(ToolError) as ctx:
            shop.restock("BK-102", 5)  # Neuromancer: 5 x $16 = $80
        self.assertIn("$60.00", str(ctx.exception))
        self.assertEqual(shop.supplier_spend, 0)

    def test_order_id_errors_explain_the_format(self):
        with self.assertRaises(ToolError) as ctx:
            Shop().get_order("1042")
        self.assertIn("ORD-1042", str(ctx.exception))

    def test_cancel_only_processing(self):
        shop = Shop()
        with self.assertRaises(ToolError):
            shop.cancel_order("ORD-1037")
        self.assertEqual(shop.cancel_order("ORD-1042")["status"], "cancelled")

    def test_grader_passes_a_correct_solution(self):
        shop = Shop()
        solve_by_hand(shop)
        checks = grade_book_club(shop)
        self.assertTrue(all(c.passed for c in checks), [c for c in checks if not c.passed])

    def test_grader_fails_untouched_shop_and_traps(self):
        untouched = [c.name for c in grade_book_club(Shop()) if c.passed]
        # doing nothing trivially respects the "don'ts"; every "do" fails
        self.assertEqual(untouched, ["No orders placed for non-members", "Supplier spend within $60"])
        shop = Shop()  # Hyperion is in stock but costs $22
        for m in shop.list_book_club_members():
            o = shop.place_order(m["customer_id"], "BK-105", 1)
            shop.send_email(m["email"], "Book club", o["order_id"])
        failed = [c.name for c in grade_book_club(shop) if not c.passed]
        self.assertEqual(failed, ["Book is science fiction under $20"])

    def test_at_least_one_valid_choice_exists_within_budget(self):
        members = len(Shop().list_book_club_members())
        ok = [b for b in Shop().books.values()
              if "science fiction" in b.genre and b.price < 20 and max(0, members - b.stock) * b.wholesale <= 60]
        self.assertGreaterEqual(len(ok), 1)
        self.assertNotIn("BK-102", [b.id for b in ok])  # the budget trap


class LabTests(unittest.TestCase):
    def test_every_lab_prints_help(self):
        for lab in sorted(LABS.glob("0*.py")):
            out = subprocess.run([sys.executable, str(lab), "--help"], capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(out.returncode, 0, f"{lab.name}: {out.stderr}")
            self.assertIn("scenarios", out.stdout)

    def test_reflection_checks(self):
        lab = load_lab("02_reflection.py")
        good = ("Hi Maya, I'm so sorry your copy of order ORD-1037 arrived damaged. We'll refund the "
                "$18.00 to your original payment method within 5 business days, and please keep the book. "
                "We're unable to offer a gift card, but we hope you enjoy reading it.\n\nInkwell Books Support")
        self.assertEqual([c(good) for c in lab.CHECKS if c(good)], [])
        bad = "Sorry! Here is a $25 gift card for you. [Your Name]"
        problems = [p for c in lab.CHECKS if (p := c(bad))]
        self.assertTrue(any("gift card" in p for p in problems))
        self.assertTrue(any("placeholder" in p.lower() for p in problems))
        self.assertTrue(any("ORD-1037" in p for p in problems))

    def test_react_strategy_end_to_end_with_scripted_model(self):
        import _bookclub

        shop = Shop()
        members = shop.list_book_club_members()
        script = [message(tool("list_book_club_members")),
                  message(tool("restock", book_id="BK-104", quantity=3))]
        script.append(message(*[tool("place_order", customer_id=m["customer_id"], book_id="BK-104", quantity=1)
                                for m in members]))
        script.append(message(*[tool("send_email", to=m["email"], subject="Book club",
                                     body=f"Your order id is ORD-{2001 + i}.") for i, m in enumerate(members)]))
        script.append(message(text("All done.")))
        _bookclub.react(ScriptedLLM(*script), shop)
        passed, total = _bookclub.grade(shop)
        self.assertEqual((passed, total), (6, 6))

    def test_plan_reflect_pipeline_with_scripted_model(self):
        import _bookclub

        shop = Shop()
        members = shop.list_book_club_members()
        plan = [{"id": 1, "action": "Find members", "depends_on": []},
                {"id": 2, "action": "Restock, order and email", "depends_on": [1]}]
        script = [
            message(tool("submit_plan", steps=plan[:1])),                       # first plan: too thin
            message(tool("submit_review", passed=False, issues=["No ordering step."])),
            message(tool("submit_plan", steps=plan)),                           # revised plan
            message(tool("submit_review", passed=True, issues=[])),
            message(tool("list_book_club_members")), message(text("6 members.")),  # step 1
            message(tool("restock", book_id="BK-104", quantity=3)),               # step 2
            message(*[tool("place_order", customer_id=m["customer_id"], book_id="BK-104", quantity=1)
                      for m in members[:5]]),
            message(text("Ordered for five members.")),                          # forgot one
            message(tool("list_orders")),                                        # verify pass finds the gap
            message(tool("place_order", customer_id=members[5]["customer_id"], book_id="BK-104", quantity=1)),
            message(*[tool("send_email", to=m["email"], subject="Book club",
                           body=f"Your order id is ORD-{2001 + i}.") for i, m in enumerate(members)]),
            message(text("Checklist: all met.")),
        ]
        llm = ScriptedLLM(*script)
        _bookclub.plan_reflect(llm, shop)
        self.assertEqual(llm.responses, [])
        self.assertEqual(_bookclub.grade(shop), (6, 6))

    def test_toolbox_subset(self):
        self.assertEqual(shop_toolbox(Shop(), ["get_order"]).names(), ["get_order"])


if __name__ == "__main__":
    unittest.main()
