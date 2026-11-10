"""Agentic patterns from primitives: one SDK call, a loop, and plain Python.

    llm.py         the single place that calls the Anthropic API
    tools.py       Tool / ToolBox / ToolError
    loop.py        run_agent: the tool-use loop
    reflection.py  reflect: generate -> critique -> revise
    planning.py    make_plan / validate_plan / execute_plan / replan
    trace.py       terminal + JSONL tracing
"""

from .llm import LLM, as_assistant_message, text_of
from .loop import AgentResult, run_agent
from .tools import Tool, ToolBox, ToolError, schema

__all__ = [
    "LLM",
    "AgentResult",
    "Tool",
    "ToolBox",
    "ToolError",
    "as_assistant_message",
    "run_agent",
    "schema",
    "text_of",
]
