"""Lab C — Reflection: generate, critique, revise.

Task: reply to a customer whose book arrived damaged and who asks for more
than the policy allows. Compare ways of producing the reply.

First write STEPS 2-3 in agentic/reflection.py, then:

Run:  uv run labs/c_reflection.py --scenario NAME
Read: agentic/reflection.py
"""

import re

import _common  # noqa: F401

from agentic import trace
from agentic.reflection import reflect, run_checks

ORDER = "ORD-1037"
ITEM_PRICE = 18.00

SYSTEM = """You write customer emails for Inkwell Books. Policy:
- Damaged on arrival: offer EITHER a free replacement OR a refund of the item price. \
The customer keeps the damaged copy; no return needed.
- Refunds reach the original payment method within 5 business days.
- No gift cards, vouchers or other compensation.
- Sign off as "Inkwell Books Support". Never use placeholders like [Name]."""

TASK = f"""Write the email reply to this customer message.

Order {ORDER}: 1 x The Left Hand of Darkness, ${ITEM_PRICE:.2f}, delivered 2026-11-06.

Customer (Maya Fernando): "My book arrived with the cover torn half off. I want a full refund,
I'm keeping the book, and I think a $25 gift card is the least you can do after this."
"""

RUBRIC = f"""1. Apologises sincerely, once, without grovelling.
2. Grants what policy allows (refund of ${ITEM_PRICE:.2f}, keep the book) clearly and early.
3. Declines the gift card politely and briefly, without blaming the customer.
4. Says exactly what happens next and when.
5. Mentions the order id {ORDER}.
6. At most 120 words, plain and warm; signed "Inkwell Books Support"."""


# --- Deterministic checks: each returns a problem string or None ------------

def mentions_order(text):
    return None if ORDER in text else f"Mention the order id {ORDER}."


def short_enough(text):
    words = len(text.split())
    return None if words <= 120 else f"Cut the reply to at most 120 words (it has {words})."


def no_placeholders(text):
    found = re.findall(r"\[[^\]]+\]", text)
    return None if not found else f"Remove placeholders: {', '.join(found)}."


def no_gift_card_promise(text):
    negations = ("not", "unable", "can't", "cannot", "don't", "isn't", "aren't", "no ", "won't")
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if re.search(r"gift card|voucher", sentence, re.I) and not any(n in sentence.lower() for n in negations):
            return f"Do not offer a gift card or voucher (found: \"{sentence.strip()}\")."
    return None


def refund_amount_ok(text):
    amounts = [float(a) for a in re.findall(r"\$(\d+(?:\.\d{1,2})?)", text)]
    too_big = [a for a in amounts if a > ITEM_PRICE and a != 25.0]  # $25 may be quoted when declining
    return None if not too_big else f"No amount above ${ITEM_PRICE:.2f} may be offered (found {too_big})."


def signed_off(text):
    return None if "Inkwell Books Support" in text else 'Sign off as "Inkwell Books Support".'


def team_check(text):
    """YOUR TEAM'S CHECK. Return a short instruction to fix the problem, or None if the text is fine.

    Ideas: doesn't blame the courier; offers the refund in the first two sentences;
    no exclamation marks; uses the customer's name.
    """
    return None


CHECKS = [mentions_order, short_enough, no_placeholders, no_gift_card_promise, refund_amount_ok, signed_off,
          team_check]


def _run(llm, *, rubric, checks, rounds):
    before = llm.usage.calls
    trace.system(SYSTEM)
    trace.user(TASK)
    result = reflect(llm, task=TASK, system=SYSTEM, rubric=rubric, checks=checks, max_rounds=rounds)
    final_problems = run_checks(result.final, CHECKS)
    trace.block("Final reply", result.final)
    (_common.ROOT / "runs").mkdir(exist_ok=True)
    (_common.ROOT / "runs" / "last-draft.txt").write_text(result.final, encoding="utf-8")
    trace.note("Saved to runs/last-draft.txt (share it with another team for check-draft).")
    for check in CHECKS:
        problem = check(result.final)
        trace.check(check.__name__, problem is None, problem or "")
    passed = len(CHECKS) - len(final_problems)
    trace.note(f"{len(result.rounds)} review round(s), {llm.usage.calls - before} model calls, "
               f"{passed}/{len(CHECKS)} deterministic checks pass")
    return f"{passed}/{len(CHECKS)} checks", f"{len(result.rounds)} review round(s)"


def one_shot(llm):
    """One draft. It is still reviewed once (by checks only) so we can score it."""
    return _run(llm, rubric=None, checks=CHECKS, rounds=1)


def self_critique(llm):
    """The model reviews its own draft against the rubric. No code checks."""
    return _run(llm, rubric=RUBRIC, checks=[], rounds=3)


def checks_only(llm):
    """Only the Python checks give feedback. Exact, but blind to tone."""
    return _run(llm, rubric=None, checks=CHECKS, rounds=3)


def grounded(llm):
    """Both: code checks feed the model critic, which adds what code cannot see."""
    return _run(llm, rubric=RUBRIC, checks=CHECKS, rounds=3)


def check_draft(llm):
    """No model calls: run every check on another team's draft pasted into labs/draft.txt."""
    path = _common.ROOT / "labs" / "draft.txt"
    if not path.exists():
        trace.warn("Paste a draft into labs/draft.txt first.")
        return None
    text = path.read_text(encoding="utf-8").strip()
    trace.block("Draft under review", text)
    problems = 0
    for check in CHECKS:
        problem = check(text)
        problems += problem is not None
        trace.check(check.__name__, problem is None, problem or "")
    return f"{len(CHECKS) - problems}/{len(CHECKS)} checks", "on a pasted draft"


SCENARIOS = {
    "one-shot": ("single draft, no revision", one_shot),
    "self-critique": ("model critic with a rubric", self_critique),
    "checks-only": ("deterministic checks as the only feedback", checks_only),
    "grounded": ("checks + model critic", grounded),
    "check-draft": ("no model: run the checks on labs/draft.txt", check_draft),
}

if __name__ == "__main__":
    _common.run("labC", "Lab C: reflection from scratch.", SCENARIOS)
