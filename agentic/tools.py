"""Tools from scratch.

To the model, a tool is three things: a name, a description and a JSON Schema
for its input. That is all it ever sees. To us, a tool is also a Python
function. `Tool` keeps the two together; `ToolBox` looks tools up by name and
turns every outcome, including failures, into text the model can read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


class ToolError(Exception):
    """Raise this inside a tool to send a message back to the model as an error.

    The message is the model's only clue for recovering, so write it for the
    model: say what was wrong and what a correct call looks like.
    """


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., Any]

    def spec(self) -> dict:
        """The part the model sees."""
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


def schema(properties: dict[str, dict], required: list[str] | None = None) -> dict:
    """Small helper for writing JSON Schemas by hand."""
    return {"type": "object", "properties": properties, "required": required or list(properties)}


class ToolBox:
    def __init__(self, tools: list[Tool] | None = None):
        self.tools: dict[str, Tool] = {}
        for tool in tools or []:
            self.add(tool)

    def add(self, tool: Tool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"duplicate tool name: {tool.name}")
        self.tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [tool.spec() for tool in self.tools.values()]

    def names(self) -> list[str]:
        return list(self.tools)

    def run(self, name: str, args: dict) -> tuple[str, bool]:
        """Execute a tool call. Returns (output_text, is_error). Never raises."""
        tool = self.tools.get(name)
        if tool is None:
            return f"Unknown tool '{name}'. Available tools: {', '.join(self.tools) or 'none'}.", True
        try:
            result = tool.fn(**args)
        except ToolError as exc:
            return str(exc), True
        except TypeError as exc:  # wrong / missing arguments
            return f"Bad arguments for {name}: {exc}", True
        except Exception as exc:  # a bug in the tool: report it, don't crash the agent
            return f"{name} failed unexpectedly: {type(exc).__name__}: {exc}", True
        if isinstance(result, str):
            return result, False
        return json.dumps(result, ensure_ascii=False, default=str), False
