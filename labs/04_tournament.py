"""Lab 3 (part 2) — Tournament: tools + planning + reflection, measured.

Change ONE tournament knob in labs/_bookclub.py (or pass --model), then run
plan-reflect on fresh shops and post your results to the scoreboard.

Run:  uv run labs/04_tournament.py --runs 2 --quiet --team <your-team>
      uv run labs/04_tournament.py --scenario react --runs 2 --quiet   # compare strategies
Read: labs/_bookclub.py (plan_reflect and the knobs)
"""

import _common
from _bookclub import STRATEGIES, chosen_books, grade

from agentic import trace
from shop import Shop


def main():
    scenarios = {name: (name, None) for name in STRATEGIES}

    def extra(parser):
        parser.add_argument("--runs", type=int, default=1, help="runs per strategy (default 1)")
        parser.add_argument("--quiet", action="store_true", help="hide traces; print only results")

    args = _common.parse_args("Tournament: run a strategy on fresh shops and grade it.", scenarios, extra)
    llm = _common.make_llm(args.model)
    trace.start(f"lab3-tournament-{args.team}", _common.ROOT / "runs")
    trace.note(f"Team: {args.team} · Model: {llm.model}")
    if args.quiet:
        trace.set_quiet(True)

    rows = []
    for name in [args.scenario] if args.scenario else ["plan-reflect"]:
        for i in range(1, args.runs + 1):
            trace.heading(f"tournament / {name} / run {i}")
            if args.quiet:
                print(f"Running {name}, run {i} of {args.runs}...", flush=True)
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
            tokens = llm.usage.input_tokens - tok_in + llm.usage.output_tokens - tok_out
            rows.append((name, i, outcome, passed, total, llm.usage.calls - calls, tokens, chosen_books(shop)))

    print(f"\n{'strategy':<14}{'run':>4}  {'result':<7}{'checks':>7}{'calls':>7}{'tokens':>9}  book")
    for name, i, outcome, passed, total, calls, tokens, book in rows:
        print(f"{name:<14}{i:>4}  {outcome:<7}{f'{passed}/{total}':>7}{calls:>7}{tokens:>9}  {book}")
    print(f"\nTotal: {llm.usage}")
    print("\nPaste these lines into the class scoreboard (select, copy, paste into column A):")
    for name, i, _outcome, passed, total, calls, tokens, book in rows:
        trace.scoreboard(args.team, "tournament", f"{name} run {i}", f"{passed}/{total} checks",
                         calls, tokens, f"{book}; model={llm.model}")


if __name__ == "__main__":
    main()
