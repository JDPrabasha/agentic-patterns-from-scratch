"""Shared plumbing for the lab scripts: paths, .env, argument parsing, setup checks.

Nothing agentic lives here. Labs run as plain scripts (`uv run labs/01_tool_use.py`),
so we put the repository root on sys.path ourselves instead of packaging anything.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import anthropic  # noqa: E402

from agentic import LLM, trace  # noqa: E402

Scenario = Callable[[LLM], None]


def parse_args(description: str, scenarios: dict[str, tuple[str, Scenario]], extra=None) -> argparse.Namespace:
    epilog = "scenarios:\n" + "\n".join(f"  {name:<20} {desc}" for name, (desc, _) in scenarios.items())
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--scenario", choices=list(scenarios), help="run only this scenario (default: all)")
    parser.add_argument("--model", help="model id (default: $ANTHROPIC_MODEL, then claude-haiku-5-5)")
    parser.add_argument("--team", default=os.getenv("TEAM", "solo"),
                        help="team name for the scoreboard (default: $TEAM in .env)")
    if extra:
        extra(parser)
    return parser.parse_args()


def make_llm(model: str | None) -> LLM:
    """Create the LLM after checking the key and model id (the model lookup is free)."""
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your-key-here":
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")
    llm = LLM(model)
    try:
        llm.client.models.retrieve(llm.model)
    except anthropic.AuthenticationError:
        sys.exit("The API key was rejected. Check ANTHROPIC_API_KEY in .env.")
    except anthropic.NotFoundError:
        sys.exit(f"Unknown model id '{llm.model}'. Try claude-haiku-5-5 or claude-sonnet-5-5.")
    return llm


def run(lab: str, description: str, scenarios: dict[str, tuple[str, Scenario]]) -> None:
    """Run the chosen scenarios. A scenario may return (result, detail) for the scoreboard."""
    args = parse_args(description, scenarios)
    llm = make_llm(args.model)
    trace.start(f"{lab}-{args.team}", ROOT / "runs")
    trace.note(f"Team: {args.team} · Model: {llm.model}")
    chosen = [args.scenario] if args.scenario else list(scenarios)
    lines = []
    for name in chosen:
        desc, fn = scenarios[name]
        trace.heading(f"{lab} / {name}: {desc}")
        calls, tokens = llm.usage.calls, llm.usage.input_tokens + llm.usage.output_tokens
        outcome = fn(llm)
        if outcome:
            result, detail = outcome
            used = llm.usage.input_tokens + llm.usage.output_tokens - tokens
            lines.append((name, result, llm.usage.calls - calls, used, detail))
    trace.note(f"Total usage: {llm.usage}")
    if lines:
        print("\nPaste these lines into the class scoreboard (select, copy, paste into column A):")
        for name, result, calls, used, detail in lines:
            trace.scoreboard(args.team, lab, name, result, calls, used, detail)
