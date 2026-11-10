"""Tracing: print what the agent does, and keep a JSONL record of it.

No logging framework. Every event is one `_emit` call that
  1. prints a coloured line to the terminal, and
  2. appends one JSON object to runs/<timestamp>-<name>.jsonl (after `start`).

Reading the trace is half of the workshop, so keep it boring and predictable.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_COLOURS = {
    "heading": "1;36",  # bold cyan
    "system": "2",  # dim
    "user": "1;34",  # bold blue
    "assistant": "1;32",  # bold green
    "tool_call": "33",  # yellow
    "tool_result": "2;33",  # dim yellow
    "tool_error": "31",  # red
    "llm_call": "2;35",  # dim magenta
    "note": "36",  # cyan
    "warn": "1;31",  # bold red
    "pass": "32",
    "fail": "31",
}

_state: dict[str, Any] = {
    "file": None,
    "quiet": os.getenv("AGENTIC_QUIET") == "1",
    "colour": sys.stdout.isatty() and not os.getenv("NO_COLOR"),
    "max_chars": 1200,
}


def start(name: str, directory: str | Path = "runs") -> Path:
    """Begin a new JSONL trace file and return its path."""
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{stamp}-{name}.jsonl"
    _state["file"] = path
    note(f"Trace: {path}")
    return path


def set_quiet(quiet: bool = True) -> None:
    """Silence terminal output (tests use this). The JSONL file is unaffected."""
    _state["quiet"] = quiet


def _paint(kind: str, text: str) -> str:
    if not _state["colour"]:
        return text
    return f"\033[{_COLOURS.get(kind, '0')}m{text}\033[0m"


def _clip(text: str) -> str:
    limit = _state["max_chars"]
    return text if len(text) <= limit else text[:limit] + f" … (+{len(text) - limit} chars)"


def _emit(kind: str, label: str, text: str = "", **data: Any) -> None:
    if _state["file"] is not None:
        record = {"t": time.time(), "kind": kind, "label": label, "text": text, **data}
        with open(_state["file"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    if _state["quiet"]:
        return
    head = _paint(kind, label)
    if not text:
        print(head)
        return
    body = textwrap.indent(_clip(text), "    ")
    print(f"{head}\n{body}")


# --- Event helpers ---------------------------------------------------------


def heading(text: str) -> None:
    _emit("heading", f"\n=== {text} ===")


def note(text: str) -> None:
    _emit("note", f"• {text}")


def warn(text: str) -> None:
    _emit("warn", f"! {text}")


def system(text: str) -> None:
    _emit("system", "[system]", text)


def user(text: str) -> None:
    _emit("user", "[user]", text)


def assistant(text: str) -> None:
    _emit("assistant", "[assistant]", text)


def tool_call(name: str, args: dict) -> None:
    _emit("tool_call", f"→ {name}({json.dumps(args, ensure_ascii=False)})", name=name, args=args)


def tool_result(name: str, output: str, is_error: bool) -> None:
    kind = "tool_error" if is_error else "tool_result"
    label = f"← {name} {'ERROR' if is_error else 'ok'}"
    _emit(kind, label, output, name=name, is_error=is_error)


def llm_call(
    model: str, seconds: float, input_tokens: int, output_tokens: int, stop_reason: str | None
) -> None:
    _emit(
        "llm_call",
        f"  (llm {model} · {seconds:.1f}s · in {input_tokens} / out {output_tokens} tok · stop={stop_reason})",
        model=model,
        seconds=seconds,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        stop_reason=stop_reason,
    )


def block(label: str, text: str) -> None:
    """A labelled chunk of text (a draft, a plan, a report)."""
    _emit("note", label, text)


def check(name: str, passed: bool, detail: str = "") -> None:
    mark = "PASS" if passed else "FAIL"
    suffix = f" — {detail}" if detail else ""
    _emit("pass" if passed else "fail", f"  [{mark}] {name}{suffix}", name=name, passed=passed)
