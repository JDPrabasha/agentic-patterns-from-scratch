# Framework selection: <team name>

> Three pages at most. Write the Criteria and Predictions sections before the survey. Every claim
> in the matrix, Evidence and Abstraction cost should point to a harness number, a line of code,
> or a doc page you actually used.

## 1. Criteria (written before the survey)

Weights add to 100. Examples: fidelity to our prompts and tools; error handling; step limits;
debuggability; code size; dependencies; docs quality; how much we'd have to learn.

| Criterion | Weight | Why it matters for this agent |
|---|---|---|
| | | |

## 2. Predictions (from the docs, before any code)

For each framework, predict the answers to the six spike questions from its docs alone. Keep this
section as written; the surprises are the point.

| Framework | Schema unchanged? | Tool errors reach the model? | Step limit? | Raw request visible? | Weight | Minutes to `tools` |
|---|---|---|---|---|---|---|
| | | | | | | |

## 3. Trade-off matrix (one row per framework)

Fill a row from each spike (`framework_lab/spikes/<name>.py`). "tools" and "bad-error" are the
parity outcomes for that spike. "Loop lives at" is the file and line where the framework calls the
model, runs tools, and decides to stop. If you couldn't get a spike working in about 10 minutes,
say what stopped you: that is the finding.

| Framework (version) | tools / bad-error | Schema unchanged? | Step limit | See raw request? | Loop lives at | Packages added | Spike lines | Minutes | Biggest strength | Biggest cost |
|---|---|---|---|---|---|---|---|---|---|---|
| From scratch (`agentic/`) | | yes | `max_steps` | yes | `agentic/loop.py` | 0 | | — | | |
| LangGraph | | | | | | | | | | |
| Pydantic AI | | | | | | | | | | |
| CrewAI | | | | | | | | | | |
| AutoGen / AG2 | | | | | | | | | | |
| smolagents | | | | | | | | | | |
| Strands / OpenAI Agents SDK | | | | | | | | | | |
| Anthropic tool runner / Claude Agent SDK | | | | | | | | | | |

Where were your predictions most wrong, and what does that say about judging a framework from its
docs? ___

## 4. Selection

Score each framework 1–5 per criterion and weight it. Show the top three.

| Framework | Weighted score | Deciding factor |
|---|---|---|
| | | |
| | | |
| | | |

- **We chose:** ___
- **Runner-up:** ___, and it lost because ___
- **Ruled out early:** ___, because ___

## 5. Evidence for the pick

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

## 6. Abstraction cost

What did the framework hide, take over, or make harder? Give at least three, each with a concrete
example from this build.

| What we lost | Example from our build | How we worked around it (or couldn't) |
|---|---|---|
| Visibility (e.g. could we see the exact request?) | | |
| Control (e.g. step limits, how tool errors reach the model, retries) | | |
| Simplicity (e.g. concepts we had to learn, lines of glue code) | | |

What did it **give** us that our own loop (`agentic/loop.py`) does not? Be just as concrete.

## 7. Challenge round

- **We paired with:** ___ (they picked ___)
- **Their strongest argument against our pick:** ___
- **Where our matrices disagreed about the same framework, and why:** ___
- **Did we change anything?** ___

## 8. When we would write the loop ourselves

Decide each design case from the brief: a framework (which one) or your own loop, and the one fact
that decides it. Tie the reason to something from the matrix, the build, or Session 1.

| Case | Framework or own loop? | The deciding fact |
|---|---|---|
| A · Internal helpdesk bot | | |
| B · Approval workflow that pauses for days | | |
| C · Planner with three specialist agents | | |
| D · Latency-sensitive, needs caching and a brand-new feature | | |
| E · Ours: ___ | | |

Our rules, in one line each:
- **Write the loop ourselves when:** ___
- **Reach for <our pick> when:** ___
- **Reach for a different framework when:** ___

## 9. Did our criteria change?

If yes, what changed, when, and why: ___
