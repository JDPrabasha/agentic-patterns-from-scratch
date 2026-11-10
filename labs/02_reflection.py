"""Lab 02 — Reflection: generate, critique, revise.

Task: reply to a customer whose book arrived damaged and who asks for more
than the policy allows. Compare four ways of producing the reply.

Run:  uv run labs/02_reflection.py [--scenario NAME]
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


CHECKS = [mentions_order, short_enough, no_placeholders, no_gift_card_promise, refund_amount_ok, signed_off]


def _run(llm, *, rubric, checks, rounds):
    before = llm.usage.calls
    trace.system(SYSTEM)
    trace.user(TASK)
    result = reflect(llm, task=TASK, system=SYSTEM, rubric=rubric, checks=checks, max_rounds=rounds)
    final_problems = run_checks(result.final, CHECKS)
    trace.block("Final reply", result.final)
    for check in CHECKS:
        problem = check(result.final)
        trace.check(check.__name__, problem is None, problem or "")
    trace.note(f"{len(result.rounds)} review round(s), {llm.usage.calls - before} model calls, "
               f"{len(CHECKS) - len(final_problems)}/{len(CHECKS)} deterministic checks pass")


def one_shot(llm):
    """One draft. It is still reviewed once (by checks only) so we can score it."""
    _run(llm, rubric=None, checks=CHECKS, rounds=1)


def self_critique(llm):
    """The model reviews its own draft against the rubric. No code checks."""
    _run(llm, rubric=RUBRIC, checks=[], rounds=3)


def checks_only(llm):
    """Only the Python checks give feedback. Exact, but blind to tone."""
    _run(llm, rubric=None, checks=CHECKS, rounds=3)


def grounded(llm):
    """Both: code checks feed the model critic, which adds what code cannot see."""
    _run(llm, rubric=RUBRIC, checks=CHECKS, rounds=3)


SCENARIOS = {
    "one-shot": ("single draft, no revision", one_shot),
    "self-critique": ("model critic with a rubric", self_critique),
    "checks-only": ("deterministic checks as the only feedback", checks_only),
    "grounded": ("checks + model critic", grounded),
}

if __name__ == "__main__":
    _common.run("lab02", "Lab 02: reflection from scratch.", SCENARIOS)
