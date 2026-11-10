"""Checks for agentic/planning.py (ready-made). Execution tests need your Lab 1 loop."""

import unittest

from agentic import Tool, ToolBox, schema
from agentic.planning import Step, execute_plan, make_plan, order_steps, validate_plan

from .fakes import ScriptedLLM, message, text, tool


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
