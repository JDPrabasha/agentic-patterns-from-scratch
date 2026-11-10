"""Planning: think first, then act one step at a time, and replan when a step fails.

    plan  = planner(goal, tool catalogue)          # structured: steps + dependencies
    check the plan is well-formed (ids, deps, no cycles)
    for step in dependency order:
        result = run_agent(step, results of earlier steps)   # fresh, small context
        if the step failed: plan = replanner(goal, done, failure, rest)

The planner sees what the tools *do* but cannot call them. The executor sees
one step at a time, so its context stays short no matter how long the plan is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import trace
from .loop import run_agent
from .tools import ToolBox

PLAN_TOOL = {
    "name": "submit_plan",
    "description": "Submit the plan as an ordered list of steps.",
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "action": {
                            "type": "string",
                            "description": "What to do and what the step must produce, in one or two sentences.",
                        },
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Ids of steps whose results this step needs.",
                        },
                    },
                    "required": ["id", "action", "depends_on"],
                },
            }
        },
        "required": ["steps"],
    },
}

PLANNER_SYSTEM = """You are a planner. You never act yourself: an executor will carry out \
each step of your plan, one at a time, using only these tools:

{catalogue}

Write the shortest plan that fully achieves the goal (at most {max_steps} steps).
- Each step must be doable with the tools above and must say what it should produce.
- A step may cover a batch of similar actions (for example "for every member, ...").
- Put checks of constraints (prices, budgets, stock) before the actions that depend on them.
- Use depends_on to list the earlier steps whose results a step needs."""

EXECUTOR_RULES = """You are executing ONE step of a larger plan. Do only this step, using the tools.
When the step is done, reply with a short summary of the result, including every id,
number or name that later steps will need. If the step cannot be done, reply starting
with "FAILED:" and explain why."""


@dataclass
class Step:
    id: int
    action: str
    depends_on: list[int] = field(default_factory=list)


@dataclass
class StepResult:
    step: Step
    summary: str
    ok: bool


@dataclass
class PlanRun:
    results: list[StepResult]
    replans: int
    completed: bool


def plan_to_text(steps: list[Step]) -> str:
    lines = []
    for s in steps:
        deps = f"  (after {', '.join(map(str, s.depends_on))})" if s.depends_on else ""
        lines.append(f"{s.id}. {s.action}{deps}")
    return "\n".join(lines)


def _catalogue(toolbox: ToolBox) -> str:
    return "\n".join(f"- {t.name}: {t.description}" for t in toolbox.tools.values())


def _ask_for_plan(llm: Any, *, prompt: str, toolbox: ToolBox, max_steps: int) -> list[Step]:
    response = llm(
        system=PLANNER_SYSTEM.format(catalogue=_catalogue(toolbox), max_steps=max_steps),
        messages=[{"role": "user", "content": prompt}],
        tools=[PLAN_TOOL],
        tool_choice={"type": "tool", "name": "submit_plan"},
        max_tokens=1500,
    )
    raw = next((b.input for b in response.content if b.type == "tool_use"), {"steps": []})
    steps = []
    for item in raw.get("steps", []):
        try:
            steps.append(
                Step(int(item["id"]), str(item["action"]), [int(d) for d in item.get("depends_on", [])])
            )
        except (KeyError, TypeError, ValueError):
            continue  # validate_plan will notice anything missing
    return steps


def make_plan(
    llm: Any,
    *,
    goal: str,
    toolbox: ToolBox,
    context: str = "",
    previous: list[Step] | None = None,
    feedback: list[str] | None = None,
    max_steps: int = 10,
) -> list[Step]:
    prompt = f"<goal>\n{goal}\n</goal>"
    if context:
        prompt += f"\n\n<context>\n{context}\n</context>"
    if previous and feedback:
        prompt += f"\n\nYour previous plan was:\n{plan_to_text(previous)}\n\nA reviewer found these problems:\n"
        prompt += "\n".join(f"- {f}" for f in feedback)
        prompt += "\n\nWrite a corrected plan."
    steps = _ask_for_plan(llm, prompt=prompt, toolbox=toolbox, max_steps=max_steps)
    trace.block("Plan", plan_to_text(steps))
    return steps


def replan(
    llm: Any,
    *,
    goal: str,
    toolbox: ToolBox,
    context: str,
    done: list[StepResult],
    remaining: list[Step],
    max_steps: int = 10,
) -> list[Step]:
    next_id = max([r.step.id for r in done] + [s.id for s in remaining] + [0]) + 1
    history = "\n".join(
        f"- step {r.step.id} [{'ok' if r.ok else 'FAILED'}] {r.step.action}\n  result: {r.summary}" for r in done
    )
    prompt = (
        f"<goal>\n{goal}\n</goal>\n\n<context>\n{context}\n</context>\n\n"
        f"Steps carried out so far (their effects are real and cannot be undone):\n{history}\n\n"
        f"Steps not yet started:\n{plan_to_text(remaining) or '(none)'}\n\n"
        f"The last step failed. Write a new plan for the REST of the work only. "
        f"Number the new steps from {next_id}. depends_on may refer to completed steps."
    )
    steps = _ask_for_plan(llm, prompt=prompt, toolbox=toolbox, max_steps=max_steps)
    trace.block("Revised plan", plan_to_text(steps))
    return steps


def validate_plan(steps: list[Step], *, completed: set[int] = frozenset(), max_steps: int = 15) -> list[str]:
    """Return a list of problems; empty means the plan can be executed."""
    errors: list[str] = []
    if not steps:
        return ["The plan has no steps."]
    if len(steps) > max_steps:
        errors.append(f"The plan has {len(steps)} steps; the limit is {max_steps}.")
    ids = [s.id for s in steps]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        errors.append(f"Duplicate step ids: {sorted(duplicates)}.")
    clashes = set(ids) & set(completed)
    if clashes:
        errors.append(f"Step ids already used by completed steps: {sorted(clashes)}.")
    known = set(ids) | set(completed)
    for s in steps:
        missing = [d for d in s.depends_on if d not in known]
        if missing:
            errors.append(f"Step {s.id} depends on unknown steps {missing}.")
        if s.id in s.depends_on:
            errors.append(f"Step {s.id} depends on itself.")
    if not errors and len(order_steps(steps, completed=completed)) != len(steps):
        errors.append("The dependencies contain a cycle.")
    return errors


def order_steps(steps: list[Step], *, completed: set[int] = frozenset()) -> list[Step]:
    """Topological order (Kahn's algorithm), stable with respect to the given order.

    Steps caught in a cycle are left out, which is how validate_plan detects cycles.
    """
    satisfied = set(completed)
    remaining = list(steps)
    ordered: list[Step] = []
    progress = True
    while remaining and progress:
        progress = False
        for s in list(remaining):
            if all(d in satisfied for d in s.depends_on):
                ordered.append(s)
                satisfied.add(s.id)
                remaining.remove(s)
                progress = True
    return ordered


def _step_prompt(goal: str, context: str, done: list[StepResult], step: Step) -> str:
    earlier = "\n".join(f"- step {r.step.id}: {r.summary}" for r in done if r.ok) or "(none yet)"
    return (
        f"Overall goal (for context only):\n{goal}\n\n"
        + (f"Context:\n{context}\n\n" if context else "")
        + f"Results of earlier steps:\n{earlier}\n\n"
        f"YOUR STEP ({step.id}): {step.action}"
    )


def execute_plan(
    llm: Any,
    *,
    goal: str,
    steps: list[Step],
    toolbox: ToolBox,
    system: str = "",
    context: str = "",
    max_steps_per_step: int = 12,
    max_replans: int = 2,
) -> PlanRun:
    executor_system = f"{system}\n\n{EXECUTOR_RULES}".strip()
    pending = order_steps(steps)
    done: list[StepResult] = []
    replans = 0

    while pending:
        step = pending.pop(0)
        trace.heading(f"Step {step.id}: {step.action}")

        # STEP 1: each step gets a fresh conversation containing only what it needs.
        result = run_agent(
            llm,
            system=executor_system,
            messages=[{"role": "user", "content": _step_prompt(goal, context, done, step)}],
            toolbox=toolbox,
            max_steps=max_steps_per_step,
        )
        failed = not result.finished or result.text.lstrip().upper().startswith("FAILED")
        done.append(StepResult(step, result.text or f"(stopped: {result.stop})", ok=not failed))
        if not failed:
            continue

        # STEP 2: a step failed. Replan the remaining work, keeping what already happened.
        if replans >= max_replans:
            trace.warn(f"Step {step.id} failed and the replan budget ({max_replans}) is used up")
            return PlanRun(done, replans, completed=False)
        replans += 1
        trace.warn(f"Step {step.id} failed; replanning ({replans}/{max_replans})")
        new_steps = replan(llm, goal=goal, toolbox=toolbox, context=context, done=done, remaining=pending)
        completed_ids = {r.step.id for r in done}
        problems = validate_plan(new_steps, completed=completed_ids)
        if problems:
            trace.warn("Revised plan rejected: " + " ".join(problems))
            return PlanRun(done, replans, completed=False)
        pending = order_steps(new_steps, completed=completed_ids)

    # Failed steps either triggered a successful replan or returned above,
    # so reaching here means every remaining step ran and the last one succeeded.
    return PlanRun(done, replans, completed=True)
