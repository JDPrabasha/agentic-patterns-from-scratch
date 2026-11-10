# Framework selection: <team name>

> Three pages at most. Write the Criteria section before the survey. Every claim in the matrix,
> Evidence and Abstraction cost should point to a harness number, a line of code, or a doc page
> you actually used.

## 1. Criteria (written before the survey)

Weights add to 100. Examples: fidelity to our prompts and tools; error handling; step limits;
debuggability; code size; dependencies; docs quality; how much we'd have to learn.

| Criterion | Weight | Why it matters for this agent |
|---|---|---|
| | | |

## 2. Trade-off matrix (one row per framework)

Fill a row from each spike (`framework_lab/spikes/<name>.py`). "tools" and "bad-error" are the
parity outcomes for that spike. If you couldn't get a spike working in 10 minutes, say what
stopped you: that is the finding.

| Framework (version) | Spiked by | tools / bad-error | Schema unchanged? | Step limit | See raw request? | Packages added | Spike lines | Minutes | Biggest strength | Biggest cost |
|---|---|---|---|---|---|---|---|---|---|---|
| From scratch (`agentic/`) | — | | yes | `max_steps` | yes | 0 | | — | | |
| LangGraph | | | | | | | | | | |
| Pydantic AI | | | | | | | | | | |
| CrewAI | | | | | | | | | | |
| AutoGen / AG2 | | | | | | | | | | |
| smolagents | | | | | | | | | | |
| Strands / OpenAI Agents SDK | | | | | | | | | | |
| Anthropic tool runner / Claude Agent SDK | | | | | | | | | | |

## 3. Selection

Score each framework 1–5 per criterion and weight it. Show the top three.

| Framework | Weighted score | Deciding factor |
|---|---|---|
| | | |
| | | |
| | | |

- **We chose:** ___
- **Runner-up:** ___, and it lost because ___
- **Ruled out early:** ___, because ___

## 4. Evidence for the pick

Paste from `uv run framework_lab/parity.py --impl both --runs 2`.

| Scenario | Baseline outcome | Ours (run 1 / run 2) | API calls (base → ours) | Tokens (base → ours) | Sent to API |
|---|---|---|---|---|---|
| tools | | | | | |
| parallel | | | | | |
| bad-description | | | | | |
| good-description | | | | | |
| bad-error | | | | | |
| good-error | | | | | |
| step-limit | | | | | |

- Code we maintain: `my_agent.py` = ___ lines vs from-scratch ___ lines.
- Packages installed: ___ on `main` → ___ on our branch.
- Time from spike to all seven scenarios: ___ min.

## 5. Abstraction cost

What did the framework hide, take over, or make harder? Give at least three, each with a concrete
example from this build.

| What we lost | Example from our build | How we worked around it (or couldn't) |
|---|---|---|
| Visibility (e.g. could we see the exact request?) | | |
| Control (e.g. step limits, how tool errors reach the model, retries) | | |
| Simplicity (e.g. concepts we had to learn, lines of glue code) | | |

What did it **give** us that our own loop (`agentic/loop.py`) does not? Be just as concrete.

## 6. When we would write the loop ourselves

At least three concrete conditions, each tied to something from the matrix, the build, or your
Lab 1 wish list. "When it's simple" is not concrete; "one model, under ten tools, and we need
prompt caching on the system prompt, which <framework> doesn't expose" is.

1. ___
2. ___
3. ___

And the reverse: **we would reach for <our pick> (or another framework) when** ___

## 7. Did our criteria change?

If yes, what changed, when, and why: ___
