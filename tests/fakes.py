"""A scripted stand-in for the model, so every test runs offline and free.

`ScriptedLLM` has the same call signature as agentic.LLM. It returns real SDK
`Message` objects from a script, and records every request it received.
"""

from __future__ import annotations

import copy
import itertools

from anthropic.types import Message

from agentic.llm import Usage

_ids = itertools.count(1)


def text(t: str) -> dict:
    return {"type": "text", "text": t}


def tool(name: str, **args) -> dict:
    return {"type": "tool_use", "id": f"toolu_{next(_ids):04d}", "name": name, "input": args}


def message(*blocks: dict, stop: str | None = None) -> Message:
    if stop is None:
        stop = "tool_use" if any(b["type"] == "tool_use" for b in blocks) else "end_turn"
    return Message.model_validate(
        {
            "id": f"msg_{next(_ids):04d}",
            "type": "message",
            "role": "assistant",
            "model": "scripted",
            "content": list(blocks),
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


class ScriptedLLM:
    def __init__(self, *responses: Message):
        self.responses = list(responses)
        self.requests: list[dict] = []
        self.usage = Usage()
        self.model = "scripted"

    def __call__(self, **request):
        self.requests.append(copy.deepcopy(request))
        if not self.responses:
            raise AssertionError("ScriptedLLM ran out of responses")
        self.usage.calls += 1
        return self.responses.pop(0)
