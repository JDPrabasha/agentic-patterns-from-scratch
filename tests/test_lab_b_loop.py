"""Lab B checks: does your run_agent (agentic/loop.py) handle tool calls correctly?

    uv run python -m unittest tests.test_lab_b_loop -v
"""

import json
import unittest

from agentic import Tool, ToolBox, run_agent, schema
from agentic.llm import as_assistant_message

from .fakes import ScriptedLLM, message, text, tool


def echo_tool():
    return Tool("echo", "Echo the text.", schema({"text": {"type": "string"}}), lambda text: {"echo": text})


class LoopTests(unittest.TestCase):
    def test_tool_call_then_answer(self):
        call = tool("echo", text="hello")
        llm = ScriptedLLM(message(text("Let me check."), call), message(text("It says hello.")))
        messages = [{"role": "user", "content": "go"}]
        result = run_agent(llm, messages=messages, toolbox=ToolBox([echo_tool()]))

        self.assertEqual(result.text, "It says hello.")
        self.assertEqual(result.steps, 2)
        self.assertTrue(result.finished)
        # user, assistant(tool_use), user(tool_result), assistant(text)
        self.assertEqual([m["role"] for m in messages], ["user", "assistant", "user", "assistant"])
        tool_result = messages[2]["content"][0]
        self.assertEqual(tool_result["tool_use_id"], call["id"])
        self.assertFalse(tool_result["is_error"])
        # the second request carried the whole history and the tool specs
        self.assertEqual(len(llm.requests[1]["messages"]), 3)
        self.assertEqual(llm.requests[1]["tools"][0]["name"], "echo")

    def test_parallel_calls_answered_in_one_message(self):
        a, b = tool("echo", text="a"), tool("echo", text="b")
        llm = ScriptedLLM(message(a, b), message(text("done")))
        messages = [{"role": "user", "content": "go"}]
        run_agent(llm, messages=messages, toolbox=ToolBox([echo_tool()]))
        results = messages[2]["content"]
        self.assertEqual([r["tool_use_id"] for r in results], [a["id"], b["id"]])

    def test_max_steps_stops_the_loop(self):
        llm = ScriptedLLM(*[message(tool("echo", text="again")) for _ in range(3)])
        result = run_agent(llm, messages=[{"role": "user", "content": "go"}], toolbox=ToolBox([echo_tool()]),
                           max_steps=3)
        self.assertEqual(result.stop, "max_steps")
        self.assertFalse(result.finished)
        self.assertEqual(len(llm.requests), 3)

    def test_no_tools_sends_no_tools_field(self):
        llm = ScriptedLLM(message(text("hi")))
        run_agent(llm, messages=[{"role": "user", "content": "go"}])
        self.assertIsNone(llm.requests[0]["tools"])

    def test_truncated_reply_is_not_finished(self):
        llm = ScriptedLLM(message(text("half a sent"), stop="max_tokens"))
        result = run_agent(llm, messages=[{"role": "user", "content": "go"}])
        self.assertEqual(result.stop, "max_tokens")
        self.assertFalse(result.finished)

    def test_assistant_message_is_plain_dicts(self):
        m = as_assistant_message(message(text("a"), tool("echo", text="x")))
        json.dumps(m)  # must be serialisable
        self.assertEqual(m["content"][1]["name"], "echo")


if __name__ == "__main__":
    unittest.main()
