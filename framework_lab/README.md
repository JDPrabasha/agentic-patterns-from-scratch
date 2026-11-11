# Framework lab: survey the frameworks, pick one, and know when not to

In Session 1 you wrote the agent loop yourselves. In this session you build the same support agent
from Lab B again, this time on someone else's loop, and decide whether that was worth it.

**What you build:** the Lab B support agent (looks up and cancels Inkwell Books orders with tools)
as a quick spike on every framework on the shortlist, then in full on the one you pick, measured
side by side with your own loop on the same seven scenarios.

**What you decide:** the trade-offs of each framework, which one you would choose for this agent
and why, and when you would skip every framework and write the loop yourself.

There is no "right" framework, and "from scratch" is a valid choice. You are assessed on the
quality of your evidence and reasoning, not on which one you pick.

## The shortlist

Cover **every** row; how you share the work is up to you. Your facilitator may swap rows. Check
each project's current docs and version on the day, because this space changes monthly.

| Style | Framework (PyPI package) | What to look for |
|---|---|---|
| Graph / state machine | LangGraph (`langgraph`, `langchain-anthropic`) | Explicit state and edges; how much LangChain comes with it |
| Typed agent | Pydantic AI (`pydantic-ai`) | Typed tools and outputs; how it maps your JSON Schema |
| Role-based multi-agent | CrewAI (`crewai`) | Agents, tasks and crews; what prompt it adds around yours |
| Conversational multi-agent | AutoGen / AG2 (`autogen-agentchat` or `ag2`) | Message-passing between agents; termination rules |
| Code-writing agent | smolagents (`smolagents`) | Tool-calling vs code-acting agents; how it reaches Claude (LiteLLM?) |
| Model-driven SDK | Strands Agents (`strands-agents`) or OpenAI Agents SDK (`openai-agents`, via LiteLLM) | Provider abstraction; what the "agent" object owns |
| Vendor SDK helpers | Anthropic SDK tool runner; Claude Agent SDK (`claude-agent-sdk`) | Thinnest option vs a full agent runtime; tools as functions vs MCP |
| Baseline | From scratch (`agentic/loop.py`) | Your own Lab B loop: the yardstick for every row |

## What you hand in

1. **One spike per framework** in `framework_lab/spikes/<name>.py`: a `run()` with the same
   signature as `my_agent.py`, good enough to pass the `tools` scenario.
2. **`framework_lab/my_agent.py`**: the full build on your chosen framework. It must run all seven
   Lab B scenarios through `framework_lab/parity.py`. If you chose from scratch, say so in
   `FRAMEWORK` and wire `run()` to the baseline; your written reasoning carries the weight instead.
3. **`framework_lab/JUSTIFICATION.md`**: at most three pages, from the template in that file.
4. **Your parity lines on the class scoreboard** (the lab column says `framework`), plus one line
   on the class board: your pick, your runner-up, and one rule for when you'd write the loop
   yourself.

## Rules

- Work on a branch: `git switch -c framework/<team>`. Don't change `agentic/`, `shop/` or the
  harness.
- **Spikes don't get `uv add`.** Run them with `uv run --with <package> ...` so several
  frameworks' dependencies don't collide or inflate your package count. Only the framework you
  choose is added with `uv add <package>`.
- Don't import `agentic.loop` or `agentic.llm` in a spike or in `my_agent.py` (unless you chose
  from scratch). The framework must do the looping and the API calls. You may read `Tool` objects
  from `agentic.tools`, because they are the shared tool definitions.
- Pass every tool's `description` and `input_schema` through unchanged. Lab B's
  `bad-description` scenario is meaningless otherwise.
- Write your criteria, weights and predictions down **before** the survey. Changing criteria
  afterwards is allowed, but say so and say why.

## The session (90 min)

| Time | Step | Output |
|---|---|---|
| 0:00–0:10 | **1. Criteria and predictions.** Agree criteria and weights. Then, from each framework's docs only, predict its answers to the six spike questions below. | Criteria; Predictions |
| 0:10–0:40 | **2. Survey.** Spike each framework and read its loop. Stop at about 10 minutes per framework: running out of time is a data point. | Spikes; trade-off matrix |
| 0:40–0:45 | **3. Pick.** Score the matrix against your weights. Name your pick and your runner-up. | Selection |
| 0:45–1:05 | **4. Build.** Turn the winning spike into `my_agent.py`. Get the error and step-limit scenarios passing. Keep a list of surprises. | A working adapter |
| 1:05–1:10 | **5. Measure.** `uv run framework_lab/parity.py --impl both --runs 2`. | Evidence |
| 1:10–1:20 | **6. Challenge round.** Pair up with a team that picked something else (see below). | Notes for your decision |
| 1:20–1:30 | **7. Decide and post.** Finish the decision sections, including the design cases, and post your line to the class board. | JUSTIFICATION.md |

## Spikes

A spike is the smallest `run()` that gets one tool call through the framework to Claude and back.
Copy `my_agent.py` to `spikes/<name>.py`, implement `run()`, then:

```bash
uv run --with pydantic-ai framework_lab/parity.py --agent framework_lab/spikes/pydantic_ai.py --scenario tools
uv run --with pydantic-ai framework_lab/parity.py --agent framework_lab/spikes/pydantic_ai.py --scenario bad-error
```

Answer the same six questions for every framework, first as a prediction from the docs, then from
the spike. They are the requirements in `my_agent.py`'s docstring, plus cost:

1. **Schema:** can it take an existing JSON Schema and description unchanged? (The harness's
   "sent to the API" column tells you.)
2. **Errors:** does a `ToolError` reach the model as a tool error, or crash the run? (`bad-error`)
3. **Step limit:** is there a `max_steps` equivalent, and what happens when it is hit?
4. **Visibility:** can you see the raw request? Does the harness meter it, or show "unmeasured"?
5. **Weight:** how many packages does `uv run --with <package>` pull in? How many lines is the spike?
6. **Time:** minutes from package name to a passing `tools` scenario, and which doc page got you there.

### Read the loop

Every framework on the list has a loop like your `run_agent` somewhere inside it. For each one,
open its installed source (`uv run --with <package> python -c "import <module>; print(<module>.__file__)"`
gets you there) and find:

- where it calls the model,
- where it runs the tool the model asked for,
- where it decides to stop.

Write the file and line in the matrix. If you can't find them in a few minutes, that is a finding
about debuggability. Where does it do something your loop doesn't, such as retries, extra
prompts, or parsing the model's text instead of `tool_use` blocks?

## What the harness measures for you

```bash
uv run framework_lab/parity.py                         # my_agent.py on all 7 scenarios
uv run framework_lab/parity.py --impl both --runs 2    # side by side with the from-scratch loop
uv run framework_lab/parity.py --scenario bad-error    # one scenario
uv run --with <pkg> framework_lab/parity.py --agent framework_lab/spikes/<name>.py --scenario tools
PARITY_DEBUG=1 uv run framework_lab/parity.py          # full traceback if your agent crashes
```

| Column | How it's measured | Why it matters for your decision |
|---|---|---|
| outcome | The shop's state and the tool-call log, as in Lab B | Did the framework change the agent's behaviour, for better or worse? |
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

## Challenge round

Pair up with a team that picked a different framework (or from scratch). Each team gets five
minutes:

- Present your pick in one minute: the criterion that decided it and the number that backs it.
- The other team argues for your runner-up, or for writing the loop yourself, using their own
  matrix. Where do your matrices disagree about the same framework, and why?

Afterwards, note anything that changed your mind. Changing your pick at this point is allowed if
you say why.

## When to write the loop yourself

Your decision has to include the cases where the answer is "no framework". Decide each of these
design cases as a team: framework (which one) or your own loop, and the one fact that decides it.

| Case | The agent |
|---|---|
| A | An internal helpdesk bot: one model, four read-only tools, answers in a chat window. Two engineers maintain it. |
| B | An expense-approval workflow that pauses for a manager's sign-off, sometimes for days, and must survive restarts. |
| C | A research assistant where a planner hands sub-questions to three specialist agents and merges their answers. |
| D | A latency-sensitive agent on a tight budget that must use prompt caching and a model feature released last week. |
| E | Your own: an agent from your day job. |

Questions that help:

- What does the framework give you that would take you weeks to write: durable state,
  human-in-the-loop checkpoints, tracing, multi-agent hand-offs? Do you actually need those?
- Do you need exact control of the request (caching, tool choice, message order, new features on
  release day) that a framework hides or lags behind on?
- Who debugs it at 2 a.m., and can they read the framework's loop as easily as 60 lines of yours?
- What does the dependency cost over two years of upgrades and security patches?

## How you'll be assessed

| Criterion | Strong | Weak |
|---|---|---|
| Coverage | Every shortlisted framework spiked and its loop located, or a recorded reason why not. | One or two looked at; the rest judged by reputation. |
| Trade-offs | Each row of the matrix has a real strength and a real cost, from the spike. Predictions that turned out wrong are kept and explained. | Pros-only rows, or rows copied from a framework's homepage. |
| Parity | All 7 scenarios run on the pick. Differences from the baseline are explained, not hidden. | Scenarios crash or are skipped without comment. |
| Justification | The pick follows from the weighted criteria; the runner-up and why it lost are named; the challenge round is answered. | The pick was made first and the criteria fitted to it afterwards. |
| Write-it-yourself | Each design case decided with a concrete reason, tied to evidence from this session. | "Frameworks are always better" or "always worse". |
| Honesty | Pre-build criteria kept or changes explained. Model variance acknowledged (2+ runs). | Criteria written after the fact to fit the choice. |
