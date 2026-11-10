import json
import unittest
from unittest import mock

import anthropic
import httpx2

from agentic import LLM, Tool, ToolBox, ToolError, run_agent, schema
from agentic.llm import as_assistant_message

from .fakes import ScriptedLLM, message, text, tool


def echo_tool():
    return Tool("echo", "Echo the text.", schema({"text": {"type": "string"}}), lambda text: {"echo": text})


class ToolBoxTests(unittest.TestCase):
    def test_success_is_json(self):
        out, err = ToolBox([echo_tool()]).run("echo", {"text": "hi"})
        self.assertFalse(err)
        self.assertEqual(json.loads(out), {"echo": "hi"})

    def test_tool_error_message_reaches_model(self):
        def boom():
            raise ToolError("Use ORD-1234 format.")

        out, err = ToolBox([Tool("boom", "", schema({}), boom)]).run("boom", {})
        self.assertTrue(err)
        self.assertEqual(out, "Use ORD-1234 format.")

    def test_unknown_tool_and_bad_args_do_not_raise(self):
        box = ToolBox([echo_tool()])
        out, err = box.run("nope", {})
        self.assertTrue(err)
        self.assertIn("echo", out)
        out, err = box.run("echo", {"wrong": 1})
        self.assertTrue(err)
        self.assertIn("Bad arguments", out)

    def test_unexpected_exception_is_reported(self):
        box = ToolBox([Tool("div", "", schema({}), lambda: 1 / 0)])
        out, err = box.run("div", {})
        self.assertTrue(err)
        self.assertIn("ZeroDivisionError", out)

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            ToolBox([echo_tool(), echo_tool()])


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


class LLMWrapperTests(unittest.TestCase):
    def _client(self, *effects):
        client = mock.Mock()
        client.messages.create.side_effect = list(effects)
        return client

    @mock.patch("agentic.llm.time.sleep")
    def test_retries_connection_errors_then_succeeds(self, sleep):
        error = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))
        llm = LLM("m", client=self._client(error, message(text("ok"))))
        response = llm(messages=[{"role": "user", "content": "x"}])
        self.assertEqual(response.content[0].text, "ok")
        self.assertEqual(llm.usage.calls, 1)
        sleep.assert_called_once_with(1)

    @mock.patch("agentic.llm.time.sleep")
    def test_gives_up_after_max_retries(self, sleep):
        error = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))
        llm = LLM("m", client=self._client(error, error, error), max_retries=2)
        with self.assertRaises(anthropic.APIConnectionError):
            llm(messages=[{"role": "user", "content": "x"}])

    def test_request_shape(self):
        client = self._client(message(text("ok")))
        LLM("my-model", client=client)(messages=[], system="s", max_tokens=5)
        self.assertEqual(
            client.messages.create.call_args.kwargs,
            {"model": "my-model", "max_tokens": 5, "messages": [], "system": "s"},
        )


if __name__ == "__main__":
    unittest.main()
