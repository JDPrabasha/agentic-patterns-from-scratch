"""Lab D — Planning: plan first, review the plan, execute step by step.

Task: set up next month's book-club read (see GOAL in labs/_bookclub.py). The
catalogue has traps: one sci-fi book is fully stocked but over $20; another is
cheap at retail but too expensive to restock within the budget.

Run:  uv run labs/d_planning.py --scenario plan-only   # 1 model call: write labs/plan.json
      (swap plans with another team and review; you may edit labs/plan.json by hand)
      uv run labs/d_planning.py --scenario plan        # execute labs/plan.json (or a new plan)
      uv run labs/d_planning.py --scenario react       # stretch: no plan at all
Read: agentic/planning.py, labs/_bookclub.py, shop/grading.py
"""

import _common  # noqa: F401
from _bookclub import SAVED_PLAN, chosen_books, grade, load_plan, new_plan, plan, react, save_plan

from agentic import trace
from agentic.planning import plan_to_text
from shop import Shop, shop_toolbox


def plan_only(llm):
    steps = new_plan(llm, shop_toolbox(Shop()))
    save_plan(steps)
    trace.note(f"Saved to {SAVED_PLAN.relative_to(_common.ROOT)}. Nothing has been executed yet.")
    trace.note("Swap with another team: would this plan fall into the Hyperion or Neuromancer trap?")
    return f"{len(steps)} steps", plan_to_text(steps).replace("\n", " | ")[:200]


def _graded(strategy):
    def scenario(llm):
        shop = Shop()
        strategy(llm, shop)
        passed, total = grade(shop)
        return f"{passed}/{total} checks", chosen_books(shop)

    return scenario


def execute(llm):
    steps = load_plan()
    if steps is None:
        trace.note("No labs/plan.json; making a fresh plan.")
    shop = Shop()
    plan(llm, shop, steps)
    passed, total = grade(shop)
    source = "saved plan" if steps else "fresh plan"
    return f"{passed}/{total} checks", f"{chosen_books(shop)} ({source})"


SCENARIOS = {
    "plan-only": ("make a plan and save it to labs/plan.json (no actions)", plan_only),
    "plan": ("execute labs/plan.json step by step, then grade", execute),
    "react": ("no plan: one loop with the whole goal and every tool", _graded(react)),
}

if __name__ == "__main__":
    _common.run("labD", "Lab D: planning from scratch.", SCENARIOS)
