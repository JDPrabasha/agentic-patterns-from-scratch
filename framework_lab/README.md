# Framework lab: rebuild Lab 1 on a framework, and justify it

In the first lab you wrote the agent loop yourselves. In this lab your team rebuilds Lab 1, the
tool-using support agent, on an agent framework you choose. Then you write a short, evidence-based
justification of that choice, including **what the abstraction cost you**.

There is no "right" framework. You are graded on the quality of your evidence and reasoning, not
on which one you pick.

## What you hand in

1. **`framework_lab/my_agent.py`**: a `run()` function built on your framework. It must pass the
   same seven Lab 1 scenarios through `framework_lab/parity.py`.
2. **`framework_lab/JUSTIFICATION.md`**: at most two pages, written from the template in that
   file.
3. **Your parity lines on the class scoreboard** (the lab column says `framework`).
4. **A 3-minute share** at the end: your choice, one number that surprised you, and one cost you
   didn't expect.

## Rules

- Any Python agent framework that can call Claude through the Anthropic API is allowed, unless
  your facilitator gives a shortlist. LangGraph, used by the workshop this one was rebuilt from,
  is one option.
- Work on a branch: `git switch -c framework/<team>`. Add the framework with `uv add <package>`.
  Don't change `agentic/`, `shop/` or the harness.
- Don't import `agentic.loop` or `agentic.llm` in `my_agent.py`. The framework must do the
  looping and the API calls. You may read `Tool` objects from `agentic.tools`, because they are
  the shared tool definitions.
- Pass every tool's `description` and `input_schema` through unchanged. Lab 1's
  `bad-description` scenario is meaningless otherwise.
- Write your selection criteria down **before** you build (step 1). Changing them afterwards is
  allowed, but say so and say why.

## Suggested timing (90 min)

| Time | Step | Output |
|---|---|---|
| 0:00–0:10 | **1. Choose.** List two or three candidates, write your criteria and their weights, and pick one. | The Criteria and Candidates sections of JUSTIFICATION.md |
| 0:10–0:50 | **2. Build.** Implement `run()` in `my_agent.py`. Get `tools` working first, then the error and step-limit scenarios. | A working adapter; a "surprises" list as you go |
| 0:50–1:05 | **3. Measure.** `uv run framework_lab/parity.py --impl both --runs 2`. Paste your lines. | The Evidence table |
| 1:05–1:25 | **4. Justify.** Fill in the rest of the template. | JUSTIFICATION.md |
| 1:25–1:30 | **5. Share.** Three minutes per team, or a gallery walk. | |

## What the harness measures for you

```bash
uv run framework_lab/parity.py                         # your agent on all 7 scenarios
uv run framework_lab/parity.py --impl both --runs 2     # side by side with the from-scratch loop
uv run framework_lab/parity.py --scenario bad-error    # one scenario
PARITY_DEBUG=1 uv run framework_lab/parity.py          # full traceback if your agent crashes
```

| Column | How it's measured | Why it matters for your justification |
|---|---|---|
| outcome | The shop's state and the tool-call log, as in Lab 1 | Did the framework change the agent's behaviour, for better or worse? |
| tools | Tool functions wrapped by the harness | Does the framework call tools more often or less often, or retry them silently? |
| api / tokens | The harness wraps the Anthropic SDK's `Messages.create` | Does the framework add model calls or tokens (planning steps, retries, extra prompts)? "unmeasured" means it bypasses the SDK, so you can't see what it sends. That is a cost in itself. |
| "sent to the API" | The first request your framework sends is compared with the system prompt, tool descriptions and schemas you gave it | Did the framework add hidden instructions, rewrite your descriptions or change your schemas? |
| Code you maintain | Lines in `my_agent.py` vs the from-scratch loop, tools and llm modules | Fewer lines of yours, but how many lines of theirs now matter to you? |
| Packages installed | Count of installed distributions | Compare with a fresh checkout of `main`. Every dependency has to be kept up to date and secure. |

The harness can't measure some costs, and they often matter most. Record them as you go:
- How long it took to find how to pass an existing JSON Schema, or how to turn an exception into a
  tool error.
- Whether you can see the raw messages when something goes wrong.
- Which defaults you had to discover and override, such as retries, step limits or temperature.
- How the framework's version churn shows up in its docs.

## How you'll be assessed

| Criterion | Strong | Weak |
|---|---|---|
| Parity | All 7 scenarios run. Differences from the baseline are explained, not hidden. | Scenarios crash or are skipped without comment. |
| Evidence | Claims cite harness numbers, code, or doc pages you actually used. | Claims come from marketing pages or general reputation. |
| Abstraction cost | Names specific things you lost: visibility, control or simplicity. Each comes with an example from your build. | "It was a bit harder to debug." |
| Judgement | States when you would *not* use this framework, and when you'd write the loop yourself. | Recommends the framework for everything. |
| Honesty | Pre-build criteria kept or changes explained. Model variance acknowledged (2+ runs). | Criteria written after the fact to fit the choice. |
