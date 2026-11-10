"""YOUR framework agent for the framework lab.

Rebuild Lab 1 (a tool-using support agent) on the framework your team chose.
The harness (framework_lab/parity.py) calls `run` once per scenario with fresh
tools and a fresh shop, then judges the shop's state. Do not import from
agentic/loop.py: the point is to let the framework do the looping.

What you get in `tools`: a list of agentic.tools.Tool objects. Each has
    tool.name          str
    tool.description   str   (pass it through unchanged: Lab 1 scenarios depend on it)
    tool.input_schema  dict  (JSON Schema for the arguments)
    tool.fn            callable(**arguments) -> result; may raise agentic.tools.ToolError

Requirements your adapter must meet (each is a question for your justification):
  1. Use the description and schema exactly as given. How does your framework
     declare a tool from a function plus an existing JSON Schema?
  2. A ToolError's message must reach the MODEL as a tool error, not crash the run.
     What does your framework do with an exception raised inside a tool?
  3. Respect `max_steps`: at most that many model calls. What is your framework's
     equivalent, and what happens when it is hit?
  4. Use `model` (an Anthropic model id) and `system`.
  5. Return the final reply text. `run` may be `async def` if your framework is async.

Record every surprise, workaround and doc page you needed in JUSTIFICATION.md as you go.
"""

from __future__ import annotations

FRAMEWORK = "name and version of your framework here"


def run(question: str, *, system: str, tools: list, model: str, max_steps: int) -> str:
    raise NotImplementedError("Framework lab: implement run() in framework_lab/my_agent.py")
