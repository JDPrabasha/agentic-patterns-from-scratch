import unittest

from agentic import Tool, ToolBox, schema
from agentic.planning import Step, execute_plan, make_plan, order_steps, validate_plan
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


class PlanValidationTests(unittest.TestCase):
    def test_valid_plan(self):
        steps = [Step(1, "a"), Step(2, "b", [1]), Step(3, "c", [1, 2])]
        self.assertEqual(validate_plan(steps), [])

    def test_problems_are_reported(self):
        self.assertTrue(validate_plan([]))
        self.assertIn("Duplicate", " ".join(validate_plan([Step(1, "a"), Step(1, "b")])))
        self.assertIn("unknown", " ".join(validate_plan([Step(1, "a", [9])])))
        self.assertIn("itself", " ".join(validate_plan([Step(1, "a", [1])])))
        self.assertIn("cycle", " ".join(validate_plan([Step(1, "a", [2]), Step(2, "b", [1])])))
        self.assertIn("limit", " ".join(validate_plan([Step(i, "x") for i in range(1, 5)], max_steps=3)))

    def test_completed_steps_satisfy_dependencies(self):
        self.assertEqual(validate_plan([Step(5, "x", [2])], completed={1, 2}), [])
        self.assertTrue(validate_plan([Step(2, "x")], completed={2}))

    def test_order_respects_dependencies(self):
        steps = [Step(3, "c", [2]), Step(1, "a"), Step(2, "b", [1])]
        self.assertEqual([s.id for s in order_steps(steps)], [1, 2, 3])


class PlanExecutionTests(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.box = ToolBox([Tool("act", "Do a thing.", schema({"what": {"type": "string"}}),
                                 lambda what: self.log.append(what) or "done")])

    def test_make_plan_parses_forced_tool(self):
        llm = ScriptedLLM(message(tool("submit_plan", steps=[
            {"id": 1, "action": "first", "depends_on": []},
            {"id": 2, "action": "second", "depends_on": [1]},
        ])))
        steps = make_plan(llm, goal="g", toolbox=self.box)
        self.assertEqual([(s.id, s.depends_on) for s in steps], [(1, []), (2, [1])])
        self.assertIn("act: Do a thing.", llm.requests[0]["system"])

    def test_steps_run_in_fresh_contexts_with_earlier_results(self):
        llm = ScriptedLLM(
            message(tool("act", what="one")), message(text("made X-1")),
            message(text("used X-1")),
        )
        run = execute_plan(llm, goal="g", steps=[Step(1, "first"), Step(2, "second", [1])], toolbox=self.box)
        self.assertTrue(run.completed)
        self.assertEqual(self.log, ["one"])
        second_step_prompt = llm.requests[2]["messages"]
        self.assertEqual(len(second_step_prompt), 1)  # fresh conversation
        self.assertIn("made X-1", second_step_prompt[0]["content"])

    def test_failed_step_triggers_replan(self):
        llm = ScriptedLLM(
            message(text("FAILED: out of stock")),
            message(tool("submit_plan", steps=[{"id": 3, "action": "alternative", "depends_on": [1]}])),
            message(text("alternative worked")),
        )
        run = execute_plan(llm, goal="g", steps=[Step(1, "first"), Step(2, "second", [1])], toolbox=self.box)
        self.assertTrue(run.completed)
        self.assertEqual(run.replans, 1)
        self.assertEqual([(r.step.id, r.ok) for r in run.results], [(1, False), (3, True)])

    def test_replan_budget(self):
        llm = ScriptedLLM(message(text("FAILED: no")))
        run = execute_plan(llm, goal="g", steps=[Step(1, "first")], toolbox=self.box, max_replans=0)
        self.assertFalse(run.completed)


if __name__ == "__main__":
    unittest.main()
