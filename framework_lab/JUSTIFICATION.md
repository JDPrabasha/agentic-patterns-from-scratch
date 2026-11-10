# Framework selection: <team name>

> Two pages at most. Write the Criteria and Candidates sections before you build. Every claim in
> Evidence and Abstraction cost should point to a harness number, a line of code, or a doc page
> you actually used.

## 1. Criteria (written before building)

Weights add to 100. Examples: fidelity to our prompts and tools; error handling; step limits;
debuggability; code size; dependencies; docs quality; how much we'd have to learn.

| Criterion | Weight | Why it matters for this agent |
|---|---|---|
| | | |

## 2. Candidates

| Framework (version) | Why considered | Why rejected / chosen (one line) |
|---|---|---|
| From scratch (`agentic/`) | Baseline | |
| | | |
| | | |

## 3. Evidence

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
- Time to the first passing scenario: ___ min. Time to all seven: ___ min.

## 4. Abstraction cost

What did the framework hide, take over, or make harder? Give at least three, each with a concrete
example from this build.

| What we lost | Example from our build | How we worked around it (or couldn't) |
|---|---|---|
| Visibility (e.g. could we see the exact request?) | | |
| Control (e.g. step limits, how tool errors reach the model, retries) | | |
| Simplicity (e.g. concepts we had to learn, lines of glue code) | | |

What did it **give** us that our own loop (`agentic/loop.py`) does not? Be just as concrete.

## 5. Decision

- **We chose:** ___, because ___ (refer to your weighted criteria).
- **We would NOT use it when:** ___
- **We would write the loop ourselves when:** ___
- **Did our criteria change during the build?** If yes, what changed and why: ___
