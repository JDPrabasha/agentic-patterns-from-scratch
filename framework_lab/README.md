# Framework lab: survey the frameworks, pick one, and know when not to

In the first lab you wrote the agent loop yourselves. In this lab your team does four things:

1. **Explore the landscape.** Spike every framework on the shortlist below on the same small task,
   not just the one you already like.
2. **List the trade-offs of each one,** using evidence from your spikes rather than marketing
   pages or reputation.
3. **Justify a selection.** Rebuild Lab 1, the tool-using support agent, on the framework you
   pick, run it through the same seven scenarios, and defend the choice against your own weighted
   criteria.
4. **Say when you would write the loop yourself.** Your answer to "should we use a framework?"
   must include the cases where the answer is no.

There is no "right" framework, and "from scratch" is a valid choice. You are graded on the quality
of your evidence and reasoning, not on which one you pick.

## The shortlist

Cover **every** row. Your facilitator may swap rows; check each project's current docs and version
on the day, because this space changes monthly. A team of three takes two or three each.

| Style | Framework (PyPI package) | What to look for |
|---|---|---|
| Graph / state machine | LangGraph (`langgraph`, `langchain-anthropic`) | Explicit state and edges; how much LangChain comes with it |
| Typed agent | Pydantic AI (`pydantic-ai`) | Typed tools and outputs; how it maps your JSON Schema |
| Role-based multi-agent | CrewAI (`crewai`) | Agents, tasks and crews; what prompt it adds around yours |
| Conversational multi-agent | AutoGen / AG2 (`autogen-agentchat` or `ag2`) | Message-passing between agents; termination rules |
| Code-writing agent | smolagents (`smolagents`) | Tool-calling vs code-acting agents; how it reaches Claude (LiteLLM?) |
| Model-driven SDK | Strands Agents (`strands-agents`) or OpenAI Agents SDK (`openai-agents`, via LiteLLM) | Provider abstraction; what the "agent" object owns |
| Vendor SDK helpers | Anthropic SDK tool runner; Claude Agent SDK (`claude-agent-sdk`) | Thinnest option vs a full agent runtime; tools as functions vs MCP |
| Baseline | From scratch (`agentic/loop.py`) | Your own Lab 1 loop: the yardstick for every row |

## What you hand in

1. **One spike per framework** in `framework_lab/spikes/<name>.py`: a `run()` with the same
   signature as `my_agent.py`, good enough to pass the `tools` scenario (see "Spikes" below).
2. **`framework_lab/my_agent.py`**: the full build on your chosen framework. It must run all seven
   Lab 1 scenarios through `framework_lab/parity.py`. If you chose from scratch, say so in
   `FRAMEWORK` and wire `run()` to the baseline; your justification carries the weight instead.
3. **`framework_lab/JUSTIFICATION.md`**: at most three pages, from the template in that file. It
   has a trade-off matrix with a row per framework, the evidence for your pick, and a "write it
   yourself when" section.
4. **Your parity lines on the class scoreboard** (the lab column says `framework`).
5. **A 3-minute share** at the end: your pick, the runner-up and why it lost, one number that
   surprised you, and one case where you'd write the loop yourself.

## Rules

- Work on a branch: `git switch -c framework/<team>`. Don't change `agentic/`, `shop/` or the
  harness.
- **Spikes don't get `uv add`.** Run them with `uv run --with <package> ...` so seven frameworks'
  dependencies don't collide or inflate your package count. Only the framework you choose is
  added with `uv add <package>`.
- Don't import `agentic.loop` or `agentic.llm` in a spike or in `my_agent.py` (unless you chose
  from scratch). The framework must do the looping and the API calls. You may read `Tool` objects
  from `agentic.tools`, because they are the shared tool definitions.
- Pass every tool's `description` and `input_schema` through unchanged. Lab 1's
  `bad-description` scenario is meaningless otherwise.
- Write your criteria and weights down **before** the survey (step 1). Changing them afterwards is
  allowed, but say so and say why.

## Suggested timing (90 min)

| Time | Step | Output |
|---|---|---|
| 0:00–0:10 | **1. Criteria.** Agree criteria and weights. Split the shortlist between you. | Criteria section |
| 0:10–0:40 | **2. Survey.** Each person spikes their frameworks and fills in their rows of the matrix. Stop at 10 minutes per framework: running out of time is a data point. | Spikes; trade-off matrix |
| 0:40–0:45 | **3. Pick.** Score the matrix against your weights. Pick one and name the runner-up. | Selection section |
| 0:45–1:05 | **4. Build.** Turn the winning spike into `my_agent.py`. Get the error and step-limit scenarios passing. | A working adapter; a "surprises" list |
| 1:05–1:12 | **5. Measure.** `uv run framework_lab/parity.py --impl both --runs 2`. | Evidence table |
| 1:12–1:25 | **6. Justify.** Finish the template, including "write it yourself when". | JUSTIFICATION.md |
| 1:25–1:30 | **7. Share.** Three minutes per team, or a gallery walk. | |

## Spikes

A spike is the smallest `run()` that gets one tool call through the framework to Claude and back.
Copy `my_agent.py` to `spikes/<name>.py`, implement `run()`, then:

```bash
uv run --with pydantic-ai framework_lab/parity.py --agent framework_lab/spikes/pydantic_ai.py --scenario tools
uv run --with pydantic-ai framework_lab/parity.py --agent framework_lab/spikes/pydantic_ai.py --scenario bad-error
```

For each framework, answer the same six questions in the matrix. They are the requirements in
`my_agent.py`'s docstring, plus cost:

1. **Schema:** can it take an existing JSON Schema and description unchanged? (The harness's
   "sent to the API" column tells you.)
2. **Errors:** does a `ToolError` reach the model as a tool error, or crash the run? (`bad-error`)
3. **Step limit:** is there a `max_steps` equivalent, and what happens when it is hit?
4. **Visibility:** can you see the raw request? Does the harness meter it, or show "unmeasured"?
5. **Weight:** how many packages does `uv run --with <package>` pull in? How many lines is the spike?
6. **Time:** minutes from `pip` name to a passing `tools` scenario, and which doc page got you there.

## What the harness measures for you

```bash
uv run framework_lab/parity.py                         # my_agent.py on all 7 scenarios
uv run framework_lab/parity.py --impl both --runs 2    # side by side with the from-scratch loop
uv run framework_lab/parity.py --scenario bad-error    # one scenario
uv run --with <pkg> framework_lab/parity.py --agent framework_lab/spikes/<name>.py --scenario tools
PARITY_DEBUG=1 uv run framework_lab/parity.py          # full traceback if your agent crashes
```

| Column | How it's measured | Why it matters for your justification |
|---|---|---|
| outcome | The shop's state and the tool-call log, as in Lab 1 | Did the framework change the agent's behaviour, for better or worse? |
| tools | Tool functions wrapped by the harness | Does the framework call tools more often or less often, or retry them silently? |
| api / tokens | The harness wraps the Anthropic SDK's `Messages.create` | Does the framework add model calls or tokens (planning steps, retries, extra prompts)? "unmeasured" means it bypasses the SDK, so you can't see what it sends. That is a cost in itself. |
| "sent to the API" | The first request your framework sends is compared with the system prompt, tool descriptions and schemas you gave it | Did the framework add hidden instructions, rewrite your descriptions or change your schemas? |
| Code you maintain | Lines in your agent file vs the from-scratch loop, tools and llm modules | Fewer lines of yours, but how many lines of theirs now matter to you? |
| Packages installed | Count of installed distributions | Compare with a fresh checkout of `main`. Every dependency has to be kept up to date and secure. |

The harness can't measure some costs, and they often matter most. Record them as you go:
- How long it took to find how to pass an existing JSON Schema, or how to turn an exception into a
  tool error.
- Whether you can see the raw messages when something goes wrong.
- Which defaults you had to discover and override, such as retries, step limits or temperature.
- How the framework's version churn shows up in its docs.

## When to write the loop yourself

This is a required section of your justification, not a footnote. Use your Lab 1 wish list and the
matrix to say, concretely, when your team would skip every framework on the list. Questions to
start from:

- How small is the agent? One loop, a handful of tools, one model: is a framework paying for itself?
- Do you need exact control of the request (prompt caching, tool-choice, message order, beta
  features on release day) that a framework hides or lags behind on?
- Who debugs it at 2 a.m., and can they read the framework's code as easily as 60 lines of yours?
- What does the framework give you that would take you weeks: durable state, human-in-the-loop
  checkpoints, tracing, multi-agent hand-offs? Do you actually need those?
- What does the dependency cost over two years of upgrades and security patches?

## How you'll be assessed

| Criterion | Strong | Weak |
|---|---|---|
| Coverage | Every shortlisted framework spiked, or a recorded reason why it couldn't be. | One or two looked at; the rest judged by reputation. |
| Trade-offs | Each row of the matrix has a real strength and a real cost, from the spike. | Pros-only rows, or rows copied from a framework's homepage. |
| Parity | All 7 scenarios run on the pick. Differences from the baseline are explained, not hidden. | Scenarios crash or are skipped without comment. |
| Justification | The pick follows from the weighted criteria; the runner-up and why it lost are named. | The pick was made first and the criteria fitted to it afterwards. |
| Write-it-yourself | Concrete conditions under which you'd use no framework, tied to evidence. | "Frameworks are always better" or "always worse". |
| Honesty | Pre-build criteria kept or changes explained. Model variance acknowledged (2+ runs). | Criteria written after the fact to fit the choice. |
