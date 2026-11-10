# Agentic Patterns from Scratch

A hands-on workshop that builds the three core agent patterns, **tool use**, **reflection** and
**planning**, from primitives. There is no agent framework and no orchestration library. Each
pattern is a short Python file you can read in one sitting, running on Claude through the
Anthropic API.

**The rule:** the only thing allowed to talk to a model is one call,
`client.messages.create(...)`, from the official `anthropic` SDK. Everything else is plain
Python: loops, lists, dicts and functions. No LangChain, LangGraph, CrewAI, agent SDKs or
workflow engines.

The point is that once you have written the loop yourself, a framework is something you can
choose for convenience, not a black box you need.

| Lab | Pattern | You build / read | The lesson |
|---|---|---|---|
| 00 | The call | `agentic/llm.py` | One request in, one message out. "Memory" is a list you resend. Always check `stop_reason`. |
| 01 | Tool use | `agentic/tools.py`, `agentic/loop.py` | An agent is a `while` loop. Tool descriptions and error messages are the model's only guide. |
| 02 | Reflection | `agentic/reflection.py` | Generate → critique → revise. Code checks are exact; a model critic sees tone. Use both. |
| 03 | Planning | `agentic/planning.py` | Plan with structure, validate it, execute each step in a fresh context, replan on failure. |
| 04 | Capstone | `labs/_bookclub.py` | Combine all three, grade the *world* (not the transcript), and measure across runs. |

## Repository map

```
agentic/          the patterns (about 850 lines including comments; nothing beyond the SDK)
  llm.py          the only module that calls the API: model choice, retries, token counts
  tools.py        Tool, ToolBox, ToolError
  loop.py         run_agent: the tool-use loop
  reflection.py   reflect, critique
  planning.py     make_plan, validate_plan, order_steps, execute_plan, replan
  trace.py        coloured terminal trace + JSONL in runs/
shop/             Inkwell Books, a fake bookstore for the agents to act on
  world.py        books, customers, orders, supplier budget, outbox
  tools.py        the shop's methods described as tools
  grading.py      checks the shop's final state for the book-club task
labs/             one runnable script per lab
tests/            offline tests with a scripted fake model (no key, no cost)
```

Everything in the shop is fictional: people, orders, prices, emails. Nothing leaves your machine
except the model calls.

## Setup

1. **Get an API key.** Sign in at the [Claude Console](https://console.anthropic.com), add a
   little credit under **Billing**, then **API Keys → Create Key**. Copy it straight away; the
   Console shows it once. A full workshop run on `claude-haiku-5-5` costs well under a dollar.
   Setting a monthly spend limit is a good idea for a shared workshop.
2. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/)**, then reopen your
   terminal and check `uv --version`. uv downloads Python 3.12 if you need it.
3. **Install and configure:**

   ```bash
   git clone <this repository> && cd agentic-patterns-from-scratch
   uv sync
   cp .env.example .env        # Windows: copy .env.example .env
   ```

   Open `.env` and replace `your-key-here` with your key. `.env` is git-ignored. Never paste a
   key into code, chat or a commit.

4. **Check everything works offline** (no key needed, no cost):

   ```bash
   uv run python -m unittest
   ```

Every lab accepts `--scenario NAME` to run one scenario and `--model ID` to pick a model
(otherwise it uses `ANTHROPIC_MODEL` from `.env`, then `claude-haiku-5-5`). Use `--help` to list
the scenarios. Each run also writes a JSONL trace to `runs/`.

Models are not deterministic. Any scenario below can turn out differently on your run, and
that is part of what the workshop teaches.

---

## Lab 00: The call

**Read** `agentic/llm.py`. It is short, and it is the only place in the
repository that touches the network.

```bash
uv run labs/00_first_call.py
```

| Scenario | What to look at |
|---|---|
| `basics` | The request is a small dict and the response is a typed `Message`. Find `content`, `stop_reason` and `usage`. |
| `memory` | Ask "what's my order number?" without the history and the model cannot know. With the history appended, it can. The API is stateless; memory is your `messages` list. |
| `max-tokens` | A reply cut off at 30 tokens looks like a normal reply. Only `stop_reason == "max_tokens"` tells you it is unfinished. |

`LLM` turns the SDK's built-in retries off (`max_retries=0`) and does its own exponential
backoff on 429, 5xx and connection errors, so you can see retries happen in the trace.

**Exercises**
1. Add a `system` argument to the `basics` scenario and compare the replies.
2. Make `LLM` record the cost of each call from its token counts and print a running total.

## Lab 01: Tool use

**Read** `agentic/tools.py`, then `agentic/loop.py`. Here is the whole agent loop:

```python
for step in range(1, max_steps + 1):
    response = llm(messages=messages, system=system, tools=toolbox.specs())
    messages.append(as_assistant_message(response))
    if response.stop_reason != "tool_use":
        return AgentResult(text_of(response), messages, step, response.stop_reason)
    results = [run each tool_use block -> {"type": "tool_result", "tool_use_id": ..., ...}]
    messages.append({"role": "user", "content": results})
return AgentResult("", messages, max_steps, "max_steps")
```

To the model, a tool is a name, a description and a JSON Schema. It never sees your Python.
`ToolBox.run` never raises an exception. Unknown tools, bad arguments, `ToolError`s and crashes
all come back as text with `is_error: true`, because the model can only recover from what it
can read.

```bash
uv run labs/01_tool_use.py
```

| Scenario | Setup | What usually happens |
|---|---|---|
| `no-tools` | none | The model cannot know where the order is. |
| `tools` | `get_order` | One tool call, then an answer: two model calls. |
| `parallel` | `search_catalog` | The model asks for Dune and Neuromancer in one turn. The loop must answer every `tool_use` block, each paired by `tool_use_id`. |
| `bad-description` | only `cancel_order`, described as "Look up the current status of an order" | The model trusts the description and **cancels the order**. |
| `good-description` | `get_order` plus an honest, destructive-sounding `cancel_order` | It looks the order up; the order survives. |
| `bad-error` | `"1042"` gets back "Order not found." | The agent believes it and gives up. |
| `good-error` | `"1042"` gets back the expected format, e.g. `ORD-1042` | The agent retries with `ORD-1042` and succeeds. The trace lists every id it tried. |
| `step-limit` | a tool that always fails | If the model keeps retrying, `max_steps` is what stops it. |

**Exercises**
1. Write a `get_customer_orders` tool for Maya and let the agent answer "what have I ordered?".
2. Add a confirmation gate: before any tool whose name starts with `cancel_`, ask the human at
   the terminal (`input()`) and return "Cancelled by the user" as an error if they say no. This
   is human-in-the-loop in five lines.
3. Write `tool_from_function(fn)` that builds the JSON Schema from type hints and the docstring.
   Compare it with writing schemas by hand.

## Lab 02: Reflection

**Read** `agentic/reflection.py`. The loop is:

```
draft = model(task)
repeat up to max_rounds:
    issues = python_checks(draft) + critic(draft, rubric)
    if no issues: stop
    draft = model(same conversation + "fix these issues")
```

The critic returns structured output by being **forced** to call a `submit_review` tool
(`tool_choice={"type": "tool", ...}`). That tool never runs; its input schema *is* the output
format. This is the simplest reliable way to get JSON from a model.

The task is a reply to Maya, whose book arrived damaged and who wants a refund, to keep the
book, and a $25 gift card. Policy allows the first two, not the third.

```bash
uv run labs/02_reflection.py
```

| Scenario | Feedback | Watch for |
|---|---|---|
| `one-shot` | none (scored once) | How many of the six checks a first draft passes. |
| `self-critique` | the model critic with a rubric | Catches tone and missing content; can be lenient or invent problems. |
| `checks-only` | six Python checks (order id, ≤120 words, no placeholders, no gift card, no amount above $18, sign-off) | Exact and never fooled, but blind to anything you did not write a check for. |
| `grounded` | checks feed the critic | Usually the best of both, at the cost of more calls. Compare call counts. |

A design rule worth noticing: the critic can never overrule a failing check
(`passed = review.passed and not check_issues`).

**Exercises**
1. Add a check that the reply does not blame the courier, and see which scenarios catch it.
2. Give the critic a *different* model from the writer (`LLM("claude-sonnet-5-5")`). Does a
   stronger critic help a weaker writer?
3. Reflection is not free: log tokens per round and find the point where extra rounds stop
   improving the score.

## Lab 03: Planning

**Read** `agentic/planning.py`, then `labs/_bookclub.py`.

The task: *the book club (six members) will read one science-fiction book under $20; make sure
there are enough copies, restocking within a $60 supplier budget; place one single-copy order
per member; email each member their own order id.* The catalogue has two traps:

- **Hyperion** is science fiction and fully in stock, but costs $22.
- **Neuromancer** is $16, but there is one copy and restocking five costs $80.

Dune, Foundation and The Left Hand of Darkness all work. The grader (`shop/grading.py`) checks
the shop's actual orders, supplier spend and outbox, never what the agent claims.

```bash
uv run labs/03_planning.py
```

| Scenario | How it works |
|---|---|
| `react` | One `run_agent` call with the whole goal and all twelve tools (`max_steps=30`). |
| `plan` | `make_plan` (forced `submit_plan` tool, can see but not call the tools) → `validate_plan` (ids, dependencies, cycles) → `execute_plan`: each step runs in a **fresh** conversation that holds only the goal and earlier results. A step that ends in `FAILED:` or hits its step limit triggers `replan` for the remaining work. |

Things to compare in the trace: total input tokens (the `react` context grows with every tool
result; plan steps stay small), where each strategy chooses the book, and whether it gets a
supplier quote before committing.

**Exercises**
1. Pass each step only the results of the steps it `depends_on` instead of all earlier results.
   What happens to tokens and to correctness?
2. Make `execute_plan` run independent steps (no shared dependencies) in parallel with
   `concurrent.futures.ThreadPoolExecutor`.
3. Change the shop so Dune's supplier is out of stock (`restock` raises a `ToolError`) and watch
   a replan happen.

## Lab 04: Capstone

`plan-reflect` combines everything:

1. **Plan**, then **critique the plan** against a rubric and revise it. This is cheap, because
   nothing has happened yet.
2. **Execute** step by step with tools, replanning on failure.
3. **Verify the outcome:** a fresh agent inspects the real state with read-only tools, fixes
   only what is missing, and reports a checklist. This is reflection on results, not on text.

```bash
uv run labs/04_capstone.py                        # react, plan, plan-reflect once each
uv run labs/04_capstone.py --runs 3 --quiet       # just the comparison table
uv run labs/04_capstone.py --scenario plan-reflect --model claude-sonnet-5-5
```

It prints a table of checks passed, model calls and tokens per run. One run proves little; look
at the spread over several, and at what the extra structure costs.

**Exercises**
1. Add a `--max-cost` budget that stops a strategy once its token spend passes a limit.
2. Turn the verify pass's checklist into structured output (a forced tool) and compare it with
   the grader. When does the agent's self-assessment disagree with reality?
3. Replace the scripted customer request with a second model playing the customer, with its own
   separate message list. That is all "multi-agent" means at the primitive level.

---

## Tests

```bash
uv run python -m unittest
```

These 39 tests run offline against `tests/fakes.py:ScriptedLLM`, which returns real SDK
`Message` objects from a script. They cover the loop (pairing, parallel calls, step cap,
truncation), the retrying wrapper, reflection rounds, plan validation, execution and replanning,
the shop and grader, and two full book-club runs from start to grade. Writing a scripted fake
is also the best way to test your own agents without paying for model calls.

## From the original workshop

This is a framework-free rebuild of the ideas in
[nuwank7/agentic-workshop](https://github.com/nuwank7/agentic-workshop), which used LangGraph
and τ²-bench.

| Original | Here |
|---|---|
| LangGraph `create_agent` / tool nodes | `agentic/loop.py:run_agent`, a `for` loop |
| LangGraph checkpointer with a `thread_id` | the `messages` list you keep and resend (Lab 00 `memory`) |
| LangChain callback handler for tracing | `agentic/trace.py`, explicit calls |
| `wrong-tool-description`, `wrong-error-message` | Lab 01 `bad-description`, `bad-error` |
| τ²-bench telecom tasks graded on environment state | Inkwell Books book-club task graded by `shop/grading.py` |
| (not covered) | Reflection (Lab 02) and planning with replanning (Lab 03) |
