# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A workshop that builds tool use, reflection and planning from primitives on the Anthropic API.
**No agent or orchestration framework, ever.** The only runtime dependencies are `anthropic`
(used only for `client.messages.create` and `models.retrieve`) and `python-dotenv`. Do not add
LangChain, LangGraph, pydantic-ai, agent SDKs or similar; teaching the primitives is the point.

## Commands

Use `uv` from the repository root.

```bash
uv sync                                   # install
uv run python -m unittest                 # offline tests: no key, no cost
uv run labs/00_first_call.py [--scenario NAME] [--model ID]
uv run labs/01_tool_use.py
uv run labs/02_reflection.py
uv run labs/03_planning.py
uv run labs/04_capstone.py [--runs N] [--quiet]
```

Labs make real, billed API calls. Run them only when asked. Always run the offline tests before
finishing a code change.

## Layout and conventions

- `agentic/`: the patterns. Keep each file short and readable top to bottom; numbered
  `# STEP n:` comments mark what an instructor walks through. `llm.py` is the only module that
  calls the API.
- `shop/`: the fictional Inkwell Books domain. Tool error messages are written for the model to
  act on. `grading.py` judges state only.
- `labs/`: runnable scripts; `_common.py` sets `sys.path` and loads `.env`; `_bookclub.py` holds
  the strategies shared by labs 03 and 04.
- `tests/fakes.py:ScriptedLLM` replays scripted SDK `Message`s; new behaviour should get an
  offline test with it.
- Default model: `claude-haiku-5-5` (`agentic/llm.py:DEFAULT_MODEL`). The README tables and
  catalogue traps (Hyperion over $20, Neuromancer over budget) must stay in sync with `shop/world.py`.

## Rules

- Never commit `.env` or paste API keys anywhere; `.env` and `runs/` are git-ignored.
