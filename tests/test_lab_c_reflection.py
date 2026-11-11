"""Lab C checks: does your reflect (agentic/reflection.py) stop and revise correctly?

    uv run python -m unittest tests.test_lab_c_reflection -v
"""

import unittest

from agentic.reflection import critique, reflect

from .fakes import ScriptedLLM, message, text, tool


def review(passed, *issues):
    return message(tool("submit_review", passed=passed, issues=list(issues)))


class ReflectionTests(unittest.TestCase):
    def test_stops_when_review_passes(self):
        llm = ScriptedLLM(message(text("draft 1")), review(True))
        result = reflect(llm, task="t", rubric="r")
        self.assertTrue(result.passed)
        self.assertEqual(result.final, "draft 1")
        self.assertEqual(len(llm.requests), 2)
        self.assertEqual(llm.requests[1]["tool_choice"], {"type": "tool", "name": "submit_review"})

    def test_check_failure_drives_revision(self):
        def must_say_ok(t):
            return None if "OK" in t else "Say OK."

        llm = ScriptedLLM(message(text("nope")), message(text("OK now")))
        result = reflect(llm, task="t", checks=[must_say_ok], max_rounds=3)
        self.assertTrue(result.passed)
        self.assertEqual(result.final, "OK now")
        self.assertEqual([r.passed for r in result.rounds], [False, True])
        # the revision request continues the same conversation and carries the feedback
        revision = llm.requests[1]["messages"]
        self.assertEqual([m["role"] for m in revision], ["user", "assistant", "user"])
        self.assertIn("Say OK.", revision[2]["content"])

    def test_critic_cannot_overrule_failing_checks(self):
        llm = ScriptedLLM(message(text("draft")), review(True))
        result = reflect(llm, task="t", rubric="r", checks=[lambda t: "too long"], max_rounds=1)
        self.assertFalse(result.passed)
        self.assertIn("too long", result.rounds[0].issues)

    def test_max_rounds(self):
        llm = ScriptedLLM(message(text("a")), review(False, "x"), message(text("b")), review(False, "y"))
        result = reflect(llm, task="t", rubric="r", max_rounds=2)
        self.assertFalse(result.passed)
        self.assertEqual(result.final, "b")
        self.assertEqual(len(result.rounds), 2)

    def test_pass_with_issues_counts_as_fail(self):
        llm = ScriptedLLM(review(True, "still a problem"))
        self.assertFalse(critique(llm, task="t", rubric="r", artifact="a").passed)


if __name__ == "__main__":
    unittest.main()
