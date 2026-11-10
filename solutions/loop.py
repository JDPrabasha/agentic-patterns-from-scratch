"""The agent loop: the whole of "tool use" in about forty lines.

    while True:
        response = model(messages, tools)
        if the model did not ask for a tool: we are done
        run every tool it asked for
        append the results and go round again

There is no orchestration library hiding anything. If you can read this
function you know exactly what an "agent" is in this repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import trace
from .llm import as_assistant_message, text_of
from .tools import ToolBox


@dataclass
class AgentResult:
    text: str  # the final reply ("" if we stopped early)
    messages: list[dict]  # the full conversation, including tool calls and results
    steps: int  # how many model calls the loop made
    stop: str  # "end_turn", "max_steps", "max_tokens", "refusal", ...

    @property
    def finished(self) -> bool:
        return self.stop in ("end_turn", "stop_sequence")


def run_agent(
    llm: Any,
    *,
    messages: list[dict],
    system: str | None = None,
    toolbox: ToolBox | None = None,
    max_steps: int = 10,
    max_tokens: int = 1024,
) -> AgentResult:
    toolbox = toolbox or ToolBox()
    for step in range(1, max_steps + 1):
        # STEP 1: ask the model, offering the tools.
        response = llm(messages=messages, system=system, tools=toolbox.specs() or None, max_tokens=max_tokens)

        # STEP 2: remember what it said (the API is stateless; this list is the memory).
        messages.append(as_assistant_message(response))
        for block in response.content:
            if block.type == "text" and block.text.strip():
                trace.assistant(block.text.strip())

        # STEP 3: no tool requested -> the model is done (or was cut off / refused).
        if response.stop_reason != "tool_use":
            return AgentResult(text_of(response), messages, step, response.stop_reason or "unknown")

        # STEP 4: run *every* tool_use block. Models may ask for several at once.
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            trace.tool_call(block.name, block.input)
            output, is_error = toolbox.run(block.name, block.input)
            trace.tool_result(block.name, output, is_error)
            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": is_error}
            )

        # STEP 5: results go back as a *user* message, each paired by tool_use_id.
        messages.append({"role": "user", "content": results})

    # STEP 6: a hard cap. Without it a confused agent loops (and bills) forever.
    trace.warn(f"Stopped after {max_steps} model calls without a final answer")
    return AgentResult("", messages, max_steps, "max_steps")
