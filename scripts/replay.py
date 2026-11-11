"""Replay a saved trace without calling the model (no key, no cost).

    uv run scripts/replay.py                         # the newest file in runs/
    uv run scripts/replay.py examples/labB-bad-description.jsonl --delay 0.5

Every lab run saves its trace to runs/<timestamp>-<lab>.jsonl. If your key or the
network fails during the lab, replay a recording from examples/ and keep going.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic import trace  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", help="trace file (default: newest in runs/)")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to pause between events")
    parser.add_argument("--no-llm", action="store_true", help="hide the per-call model/token lines")
    args = parser.parse_args()

    if args.path:
        path = Path(args.path)
    else:
        traces = sorted((ROOT / "runs").glob("*.jsonl"))
        if not traces:
            raise SystemExit("No traces in runs/ yet. Pass a file, e.g. one from examples/.")
        path = traces[-1]

    print(f"Replaying {path}\n")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if args.no_llm and record.get("kind") == "llm_call":
            continue
        trace.replay(record)
        if args.delay:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
