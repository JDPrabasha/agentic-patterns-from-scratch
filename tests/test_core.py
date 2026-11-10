"""Checks for the parts that come ready-made: ToolBox and the LLM wrapper."""

import json
import unittest
from unittest import mock

import anthropic
import httpx2

from agentic import LLM, Tool, ToolBox, ToolError, schema

from .fakes import message, text


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
