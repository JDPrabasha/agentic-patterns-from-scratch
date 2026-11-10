"""Reflection: generate, critique, revise.

    draft = model(task)
    repeat:
        issues = checks(draft) + critic(draft, rubric)
        if no issues: stop
        draft = model(task, draft, issues)        # same conversation, plus feedback

Two kinds of critic, and the lab compares them:
  * checks -- plain Python functions (word count, required id, banned promises).
    Cheap, exact, never fooled; can only catch what you thought of.
  * critic -- a second model call that reads the draft against a rubric.
    Catches tone and missing content; can be wrong or too lenient.

The critic returns structured output by being *forced* to call a tool
(`tool_choice`). The tool never runs: its input schema is the output format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from . import trace
from .llm import as_assistant_message, text_of

Check = Callable[[str], "str | None"]  # returns a problem description, or None if fine

REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit your review of the draft.",
    "input_schema": {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Each concrete problem, phrased as a short instruction to fix it. Empty if none.",
            },
            "passed": {"type": "boolean", "description": "true only if the draft meets every rubric item."},
        },
        "required": ["issues", "passed"],
    },
}

CRITIC_SYSTEM = (
    "You are a strict reviewer. Judge the draft only against the rubric and the task. "
    "Report every concrete problem as one short, actionable fix. Do not rewrite the draft. "
    "Set passed to true only when there are no problems."
)


@dataclass
class Critique:
    passed: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class Round:
    draft: str
    issues: list[str]
    passed: bool


@dataclass
class ReflectionResult:
    final: str
    rounds: list[Round]
    passed: bool


def run_checks(artifact: str, checks: Iterable[Check]) -> list[str]:
    return [problem for check in checks if (problem := check(artifact))]


def critique(llm: Any, *, task: str, rubric: str, artifact: str, known_issues: Iterable[str] = ()) -> Critique:
    prompt = f"<task>\n{task}\n</task>\n\n<rubric>\n{rubric}\n</rubric>\n\n<draft>\n{artifact}\n</draft>"
    known = list(known_issues)
    if known:
        prompt += "\n\nAutomated checks already found these problems; include them:\n" + "\n".join(
            f"- {issue}" for issue in known
        )
    response = llm(
        system=CRITIC_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "submit_review"},
        max_tokens=800,
    )
    review = next((b.input for b in response.content if b.type == "tool_use"), None)
    if review is None:  # should not happen with a forced tool, but never trust that
        return Critique(False, ["Reviewer returned no structured review."])
    issues = [str(i) for i in review.get("issues", []) if str(i).strip()]
    return Critique(bool(review.get("passed")) and not issues, issues)


def generate(llm: Any, *, system: str | None, messages: list[dict], max_tokens: int = 800) -> str:
    response = llm(system=system, messages=messages, max_tokens=max_tokens)
    messages.append(as_assistant_message(response))
    return text_of(response)


def reflect(
    llm: Any,
    *,
    task: str,
    system: str | None = None,
    rubric: str | None = None,
    checks: Iterable[Check] = (),
    max_rounds: int = 3,
) -> ReflectionResult:
    """Draft, then review up to `max_rounds` times, revising after each failed review."""
    checks = list(checks)
    messages: list[dict] = [{"role": "user", "content": task}]
    draft = generate(llm, system=system, messages=messages)
    rounds: list[Round] = []

    for n in range(1, max_rounds + 1):
        # STEP 1: review. Deterministic checks first, then (optionally) the model critic.
        check_issues = run_checks(draft, checks)
        if rubric:
            review = critique(llm, task=task, rubric=rubric, artifact=draft, known_issues=check_issues)
        else:
            review = Critique(True, [])
        issues = list(dict.fromkeys(check_issues + review.issues))  # de-duplicate, keep order
        passed = review.passed and not check_issues
        if not passed and not issues:
            issues = ["The reviewer rejected the draft without details; tighten it against the rubric."]

        rounds.append(Round(draft, issues, passed))
        trace.block(f"Round {n} draft", draft)
        trace.block(f"Round {n} review: {'PASS' if passed else 'FAIL'}", "\n".join(f"- {i}" for i in issues))

        # STEP 2: stop when it passes, or when we are out of rounds.
        if passed:
            return ReflectionResult(draft, rounds, True)
        if n == max_rounds:
            break

        # STEP 3: revise in the same conversation, so the model sees its own draft.
        feedback = "A reviewer found these problems:\n" + "\n".join(f"- {i}" for i in issues)
        feedback += "\n\nRewrite your reply so it fixes every problem. Output only the new reply."
        messages.append({"role": "user", "content": feedback})
        draft = generate(llm, system=system, messages=messages)

    return ReflectionResult(draft, rounds, False)
