"""Offline checks for framework_lab/parity.py: metering, judging and fidelity.

The real API is replaced underneath the harness by a scripted Messages.create,
so these run with no key and no cost. The baseline needs your Lab 1 loop.
"""

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import anthropic.resources.messages as sdk_messages

from .fakes import message, text, tool

ROOT = Path(__file__).resolve().parent.parent


def load_parity():
    spec = importlib.util.spec_from_file_location("parity", ROOT / "framework_lab" / "parity.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["parity"] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


class FakeAPI:
    """Stands in for Messages.create at the class level, like a real HTTP call would."""

    def __init__(self, *responses):
        self.responses = list(responses)

    def __call__(self, client_self, **kwargs):
        return self.responses.pop(0)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.parity = load_parity()
        os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

    def run_with(self, fake, impl, scenario):
        with mock.patch.object(sdk_messages.Messages, "create", fake):
            return self.parity.run_one("x", impl, scenario, "scripted")

    def test_baseline_bad_description_is_judged_from_state(self):
        fake = FakeAPI(message(tool("cancel_order", order_id="ORD-1042")), message(text("All set!")))
        row = self.run_with(fake, self.parity.baseline_run, "bad-description")
        self.assertEqual(row.outcome, "ORDER CANCELLED")
        self.assertEqual(row.api_calls, 2)
        self.assertEqual(row.tool_calls, 1)
        self.assertEqual(row.tokens, 30)
        self.assertEqual(row.notes, ["exact"])

    def test_recovery_judged_from_tool_log(self):
        fake = FakeAPI(message(tool("get_order", order_id="1042")), message(tool("get_order", order_id="ORD-1042")),
                       message(text("It's processing.")))
        row = self.run_with(fake, self.parity.baseline_run, "good-error")
        self.assertEqual(row.outcome, "recovered")

    def test_fidelity_catches_a_framework_that_rewrites_the_prompt(self):
        def sneaky(question, *, system, tools, model, max_steps):
            import anthropic

            spec = [{"name": t.name, "description": t.description + " Always be thorough.",
                     "input_schema": t.input_schema} for t in tools]
            anthropic.Anthropic().messages.create(model=model, max_tokens=100, system="You are helpful.\n" + system,
                                                  tools=spec, messages=[{"role": "user", "content": question}])
            return "done"

        row = self.run_with(FakeAPI(message(text("done"))), sneaky, "tools")
        self.assertTrue(any("system prompt changed" in n for n in row.notes), row.notes)
        self.assertIn("get_order: description changed", row.notes)

    def test_crash_is_a_result_not_an_exception(self):
        def broken(question, **kwargs):
            raise RuntimeError("framework exploded")

        row = self.run_with(FakeAPI(), broken, "tools")
        self.assertEqual(row.outcome, "CRASHED")
        self.assertIn("framework exploded", row.error)
        self.assertEqual(row.api_calls, "unmeasured")

    def test_async_run_is_supported(self):
        async def async_impl(question, **kwargs):
            return "async reply"

        row = self.run_with(FakeAPI(), async_impl, "tools")
        self.assertEqual(row.reply, "async reply")

    def test_stub_reports_not_implemented(self):
        row = self.run_with(FakeAPI(), self.parity.load_mine().run, "tools")
        self.assertIn("not implemented", row.error)


if __name__ == "__main__":
    unittest.main()
