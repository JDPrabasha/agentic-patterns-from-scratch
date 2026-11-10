"""For facilitators and maintainers: run the whole test suite against the reference solutions.

    uv run scripts/check_solutions.py

Copies the repository to a temporary folder, puts solutions/*.py over the
starter files in agentic/, and runs every test there. Your checkout is untouched.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = shutil.ignore_patterns(".venv", ".git", "runs", "__pycache__", "*.mine.py")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(ROOT, copy, ignore=SKIP)
        for solution in (ROOT / "solutions").glob("*.py"):
            shutil.copyfile(solution, copy / "agentic" / solution.name)
        result = subprocess.run([sys.executable, "-m", "unittest"], cwd=copy, check=False)
    print("\nSolutions pass every test." if result.returncode == 0 else "\nSolutions FAIL.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
