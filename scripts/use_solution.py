"""Stuck? Swap in the reference implementation for one lab, keeping your attempt.

    uv run scripts/use_solution.py loop          # Lab B: agentic/loop.py
    uv run scripts/use_solution.py reflection    # Lab C: agentic/reflection.py
    uv run scripts/use_solution.py loop --undo   # put your own version back

Your version is saved next to it as agentic/<name>.mine.py.
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = {"loop": "Lab B", "reflection": "Lab C"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", choices=list(NAMES))
    parser.add_argument("--undo", action="store_true", help="restore your own version")
    args = parser.parse_args()

    target = ROOT / "agentic" / f"{args.name}.py"
    mine = ROOT / "agentic" / f"{args.name}.mine.py"
    if args.undo:
        if not mine.exists():
            raise SystemExit(f"No saved version at {mine.relative_to(ROOT)}.")
        shutil.copyfile(mine, target)
        print(f"Restored your version of {target.relative_to(ROOT)}.")
        return
    if not mine.exists():
        shutil.copyfile(target, mine)
    shutil.copyfile(ROOT / "solutions" / f"{args.name}.py", target)
    print(f"{NAMES[args.name]}: {target.relative_to(ROOT)} now holds the reference solution.")
    print(f"Your attempt is in {mine.relative_to(ROOT)}. Compare them: they are short.")


if __name__ == "__main__":
    main()
