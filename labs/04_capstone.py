"""Lab 04 — Capstone: tools + planning + reflection, measured.

Runs each strategy on a fresh shop, grades the resulting state, and prints a
comparison table. One run proves little; use --runs to see the spread.

Run:  uv run labs/04_capstone.py [--scenario react|plan|plan-reflect] [--runs 3] [--quiet]
Read: labs/_bookclub.py (plan_reflect)
"""

import _common
from _bookclub import STRATEGIES, grade

from agentic import trace
from shop import Shop


def main():
    scenarios = {name: (name, None) for name in STRATEGIES}

    def extra(parser):
        parser.add_argument("--runs", type=int, default=1, help="runs per strategy (default 1)")
        parser.add_argument("--quiet", action="store_true", help="hide traces; print only the table")

    args = _common.parse_args("Lab 04: compare strategies on the book-club task.", scenarios, extra)
    llm = _common.make_llm(args.model)
    trace.start("lab04", _common.ROOT / "runs")
    trace.note(f"Model: {llm.model}")
    if args.quiet:
        trace.set_quiet(True)

    rows = []
    for name in [args.scenario] if args.scenario else list(STRATEGIES):
        for i in range(1, args.runs + 1):
            trace.heading(f"lab04 / {name} / run {i}")
            shop = Shop()
            calls, tok_in, tok_out = llm.usage.calls, llm.usage.input_tokens, llm.usage.output_tokens
            try:
                STRATEGIES[name](llm, shop)
                passed, total = grade(shop)
                outcome = "PASS" if passed == total else "FAIL"
            except Exception as exc:  # an API failure should not lose the other runs
                trace.warn(f"{type(exc).__name__}: {exc}")
                passed, total = grade(shop)
                outcome = "ERROR"
            rows.append((name, i, outcome, f"{passed}/{total}", llm.usage.calls - calls,
                         llm.usage.input_tokens - tok_in + llm.usage.output_tokens - tok_out))

    print(f"\n{'strategy':<14}{'run':>4}  {'result':<7}{'checks':>7}{'calls':>7}{'tokens':>9}")
    for name, i, outcome, checks, calls, tokens in rows:
        print(f"{name:<14}{i:>4}  {outcome:<7}{checks:>7}{calls:>7}{tokens:>9}")
    print(f"\nTotal: {llm.usage}")


if __name__ == "__main__":
    main()
