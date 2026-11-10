"""The book-club task and three strategies for it, shared by labs/03_planning.py and labs/04_tournament.py.

    react         one agent loop with every tool and the whole goal
    plan          plan -> validate -> execute step by step (replan on failure)
    plan-reflect  plan -> critique plan -> revise -> execute -> verify & fix
"""

from __future__ import annotations

import json
from pathlib import Path

from agentic import run_agent, trace
from agentic.planning import Step, execute_plan, make_plan, plan_to_text, validate_plan
from agentic.reflection import critique
from shop import Shop, grade_book_club, shop_toolbox

# The task. Do NOT change it during the tournament: every team must solve the same problem.
GOAL = """The Inkwell Books club (every current book-club member) will read one science-fiction \
book together next month. Choose a single science-fiction title with a retail price under $20. \
Make sure there are enough copies in stock for every member, buying from the supplier if needed \
without going over the $60 supplier budget. Place one order of exactly one copy for each member, \
then email each member their own order id."""

# =============================================================================
# TOURNAMENT KNOBS. Your team changes ONE of these (or --model), then runs
#   uv run labs/04_tournament.py --runs 2 --quiet --team <your-team>
# Allowed: anything in this block. Not allowed: GOAL, shop/, the grader, agentic/planning.py.
# =============================================================================

SYSTEM = """You operate Inkwell Books' systems through tools. Orders, restocks and emails are real \
and cannot be undone, so check before you act and never place duplicate orders. Never invent ids, \
prices or email addresses: get them from the tools."""

PLAN_RUBRIC = """1. Finds the members (and so how many copies are needed) before choosing quantities.
2. Compares candidate books on genre, price under $20, current stock AND the supplier cost of the \
shortfall against the $60 budget (e.g. with get_supplier_quote) before committing to one.
3. Restocks only the shortfall, and only after the book is chosen; restocks before placing orders.
4. Places exactly one single-copy order per member and keeps every order id.
5. Emails each member their own order id after their order exists.
6. Contains no unnecessary, duplicate or irreversible extra actions."""

VERIFY = f"""Verification pass. This goal was supposedly completed:

{GOAL}

Do not trust that it was. Use the read-only tools (list_book_club_members, list_orders, \
list_sent_emails, get_book) to check every requirement against the shop's actual state. \
If something is missing, fix only that, and never give a member a second order. \
Finish with a checklist of each requirement and whether it is now met."""

PLAN_REVIEW_ROUNDS = 2  # how many times the plan is critiqued and revised before acting
MAX_STEPS_PER_STEP = 12  # model calls allowed for each plan step
MAX_REPLANS = 2  # how many times a failed step may trigger a new plan
VERIFY_AFTER = True  # run the verify-and-fix pass at the end

# =============================================================================

SAVED_PLAN = Path(__file__).resolve().parent / "plan.json"


def react(llm, shop: Shop) -> None:
    trace.system(SYSTEM)
    trace.user(GOAL)
    run_agent(llm, system=SYSTEM, messages=[{"role": "user", "content": GOAL}],
              toolbox=shop_toolbox(shop), max_steps=30, max_tokens=2048)


def new_plan(llm, toolbox):
    steps = make_plan(llm, goal=GOAL, toolbox=toolbox)
    errors = validate_plan(steps)
    if errors:  # one structural retry: feed the validator's complaints back to the planner
        trace.warn("Plan rejected: " + " ".join(errors))
        steps = make_plan(llm, goal=GOAL, toolbox=toolbox, previous=steps, feedback=errors)
        errors = validate_plan(steps)
        if errors:
            raise RuntimeError("Planner could not produce a valid plan: " + " ".join(errors))
    return steps


def save_plan(steps: list[Step]) -> None:
    data = [{"id": s.id, "action": s.action, "depends_on": s.depends_on} for s in steps]
    SAVED_PLAN.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_plan() -> list[Step] | None:
    if not SAVED_PLAN.exists():
        return None
    data = json.loads(SAVED_PLAN.read_text(encoding="utf-8"))
    steps = [Step(int(d["id"]), str(d["action"]), [int(x) for x in d.get("depends_on", [])]) for d in data]
    errors = validate_plan(steps)
    if errors:
        raise SystemExit(f"labs/plan.json is not a valid plan: {' '.join(errors)}")
    trace.block("Using the saved plan from labs/plan.json", plan_to_text(steps))
    return steps


def plan(llm, shop: Shop, steps: list[Step] | None = None) -> None:
    toolbox = shop_toolbox(shop)
    steps = steps or new_plan(llm, toolbox)
    run = execute_plan(llm, goal=GOAL, steps=steps, toolbox=toolbox, system=SYSTEM,
                       max_steps_per_step=MAX_STEPS_PER_STEP, max_replans=MAX_REPLANS)
    trace.note(f"Plan finished: completed={run.completed}, replans={run.replans}")


def plan_reflect(llm, shop: Shop) -> None:
    toolbox = shop_toolbox(shop)
    steps = new_plan(llm, toolbox)

    # Reflection on the PLAN: cheap, because nothing has happened yet.
    for n in range(1, PLAN_REVIEW_ROUNDS + 1):
        review = critique(llm, task=GOAL, rubric=PLAN_RUBRIC, artifact=plan_to_text(steps))
        trace.block(f"Plan review {n}: {'PASS' if review.passed else 'FAIL'}",
                    "\n".join(f"- {i}" for i in review.issues))
        if review.passed:
            break
        revised = make_plan(llm, goal=GOAL, toolbox=toolbox, previous=steps, feedback=review.issues)
        if validate_plan(revised):
            trace.warn("Revised plan was malformed; keeping the previous one")
            break
        steps = revised

    run = execute_plan(llm, goal=GOAL, steps=steps, toolbox=toolbox, system=SYSTEM,
                       max_steps_per_step=MAX_STEPS_PER_STEP, max_replans=MAX_REPLANS)
    trace.note(f"Plan finished: completed={run.completed}, replans={run.replans}")

    # Reflection on the OUTCOME: inspect the real state and repair gaps.
    if VERIFY_AFTER:
        trace.heading("Verify")
        run_agent(llm, system=SYSTEM, messages=[{"role": "user", "content": VERIFY}],
                  toolbox=shop_toolbox(shop), max_steps=20, max_tokens=2048)


STRATEGIES = {"react": react, "plan": plan, "plan-reflect": plan_reflect}


def chosen_books(shop: Shop) -> str:
    ids = {o.book_id for o in shop.orders.values()
           if o.id not in shop.initial_order_ids and o.status != "cancelled"}
    return ", ".join(sorted(shop.books[i].title for i in ids)) or "no book"


def grade(shop: Shop) -> tuple[int, int]:
    trace.heading("Grade (shop state, not the agent's words)")
    checks = grade_book_club(shop)
    for c in checks:
        trace.check(c.name, c.passed, c.detail)
    passed = sum(c.passed for c in checks)
    trace.note(f"{'PASS' if passed == len(checks) else 'FAIL'}: {passed}/{len(checks)} checks")
    return passed, len(checks)
