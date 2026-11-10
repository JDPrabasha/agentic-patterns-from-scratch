"""Lab 03 — Planning: plan first, execute step by step, replan on failure.

Task: set up next month's book-club read (see labs/_bookclub.py). The catalogue
has traps: one sci-fi book is fully stocked but over $20; another is cheap at
retail but too expensive to restock within the budget.

Run:  uv run labs/03_planning.py [--scenario react|plan]
Read: agentic/planning.py, labs/_bookclub.py, shop/grading.py
"""

import _common  # noqa: F401
from _bookclub import STRATEGIES, grade

from shop import Shop


def _scenario(name):
    def scenario(llm):
        shop = Shop()
        STRATEGIES[name](llm, shop)
        grade(shop)

    return scenario


SCENARIOS = {
    "react": ("no plan: one loop with the whole goal and every tool", _scenario("react")),
    "plan": ("plan -> validate -> execute each step in a fresh context", _scenario("plan")),
}

if __name__ == "__main__":
    _common.run("lab03", "Lab 03: planning from scratch.", SCENARIOS)
