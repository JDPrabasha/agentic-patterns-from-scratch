# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A workshop that builds tool use, reflection and planning from primitives on the Anthropic API.
**No agent or orchestration framework, ever.** The only runtime dependencies are `anthropic`
(used only for `client.messages.create` and `models.retrieve`) and `python-dotenv`. Do not add
LangChain, LangGraph, pydantic-ai, agent SDKs or similar to `main`; teaching the primitives is the point.
The one exception is the follow-up framework lab: teams add a framework on their own
`framework/<team>` branch and use it only in `framework_lab/my_agent.py`. On `main`, `my_agent.py`
stays a stub that raises `NotImplementedError`.

## Commands

Use `uv` from the repository root.

```bash
uv sync                                   # install
uv run scripts/check_solutions.py         # offline: full suite against solutions/ (must pass)
uv run python -m unittest                 # offline: 16 tests fail BY DESIGN until Labs 1-2 are written
uv run labs/00_first_call.py --scenario basics [--team NAME] [--model ID]
uv run labs/01_tool_use.py --scenario NAME
uv run labs/02_reflection.py --scenario NAME
uv run labs/03_planning.py --scenario plan-only|plan|react
uv run labs/04_tournament.py [--runs N] [--quiet]
```

## Starter vs solution

This repo is handed to participants. `agentic/loop.py` (steps 3-5) and `agentic/reflection.py`
(steps 2-3) are deliberately incomplete and raise `NotImplementedError`; `solutions/` holds the
complete files. Change both together, and keep the starter's step comments in sync with the
solution. Never "fix" the starter by filling it in.

Labs make real, billed API calls. Run them only when asked. Before finishing a code change, run
`scripts/check_solutions.py` (must pass) and the plain suite (only the by-design failures).

## Layout and conventions

- `agentic/`: the patterns. Keep each file short and readable top to bottom; numbered
  `# STEP n:` comments mark what an instructor walks through. `llm.py` is the only module that
  calls the API.
- `shop/`: the fictional Inkwell Books domain. Tool error messages are written for the model to
  act on. `grading.py` judges state only.
- `labs/`: runnable scripts; `_common.py` sets `sys.path`, loads `.env`, adds `--team` and prints
  tab-separated scoreboard lines from each scenario's `(result, detail)` return; `_bookclub.py` holds
  the task, the tournament knobs and the strategies shared by labs 03 and 04.
- `framework_lab/`: the follow-up lab. `parity.py` runs `my_agent.run()` and the from-scratch
  baseline through the Lab 1 scenarios, meters API calls by wrapping the SDK's `Messages.create`,
  and compares the first request with the given system prompt and tools ("fidelity").
- `README.md` is the participants' 90-minute lab sheet (teams of 3). Facilitator material lives
  outside the repo.
- `tests/fakes.py:ScriptedLLM` replays scripted SDK `Message`s; new behaviour should get an
  offline test with it.
- Default model: `claude-haiku-5-5` (`agentic/llm.py:DEFAULT_MODEL`). The README tables and
  catalogue traps (Hyperion over $20, Neuromancer over budget) must stay in sync with `shop/world.py`.

## Rules

- Never commit `.env` or paste API keys anywhere; `.env` and `runs/` are git-ignored.
