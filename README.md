# Agentic Patterns from Scratch: the lab

You heard about tool use, reflection and planning in the lecture. In the next 90 minutes your
team writes them yourselves, in plain Python on the Anthropic API, then competes with the other
teams on a graded task.

**The rule:** the only thing that talks to the model is one call, `client.messages.create(...)`.
Everything else is loops, lists, dicts and functions you can read. No LangChain, LangGraph or
other agent framework.

## Before the lab (at home, about 10 minutes)

One laptop per team needs this working. If two of you set it up, you have a spare.

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/)**, reopen the
   terminal, and check `uv --version`. uv installs Python 3.12 for you.
2. **Get the code and install it:**

   ```bash
   git clone <repository URL from your facilitator>
   cd agentic-patterns-from-scratch
   uv sync
   cp .env.example .env          # Windows: copy .env.example .env
   ```

3. **Edit `.env`:** paste the API key you were given (or your own, from
   [console.anthropic.com](https://console.anthropic.com)) and set your team name:

   ```env
   ANTHROPIC_API_KEY=sk-ant-...
   TEAM=Team Ada
   ```

   `.env` is git-ignored. Never paste a key into code, chat or a commit.

4. **Check it works without the model** (free):

   ```bash
   uv run python -m unittest tests.test_core
   ```

   You should see `OK`. Some *other* tests fail on purpose until you write Labs 1 and 2.

## How this lab works

**Teams of 3.** Rotate roles at every lab, so everyone drives once:

| Role | Job |
|---|---|
| **Driver** | Types and runs the commands. |
| **Navigator** | Reads the trace aloud ("it's calling `cancel_order`…"), watches the clock. |
| **Recorder** | Writes down the team's prediction *before* each run, pastes results into the class scoreboard, speaks in the debriefs. |

**Every lab has the same rhythm:** build → predict → run → post → discuss.

- **Core** steps are the path everyone finishes. **Stretch** steps are for teams that finish
  early; skip them without guilt.
- **Predict before you run.** Write a one-line guess, then compare. Being wrong is the
  interesting part.
- **Post to the scoreboard.** After each run, the terminal prints lines like this:

  ```
  Team Ada	lab1	bad-description	ORDER CANCELLED	2	850	status=cancelled
  ```

  Copy them and paste them into the next empty row of the shared class scoreboard. The columns
  are tab-separated, so they land in the right cells. Eight teams running the same scenario
  shows you how much a model's behaviour varies; one run can't.
- **Stuck for 5 minutes?** Ask the team next to you. Still stuck? Use the reference solution and
  keep going:

  ```bash
  uv run scripts/use_solution.py loop          # or: reflection
  ```

  Your attempt is kept as `agentic/loop.mine.py`. Compare the two afterwards; they are short.

**Keep a "wish list".** Whenever you think "a library should do this for me", the Recorder notes
it. You'll bring the list to the next lab, where you survey the agent frameworks, rebuild Lab 1 on
the one you pick, and decide when you'd write the loop yourself instead.

Every run also saves a trace to `runs/`. `uv run scripts/replay.py` plays the newest one back
without calling the model.

---

## Lab 0 · Setup check (5 min)

```bash
uv run labs/00_first_call.py --scenario basics
```

This is one model call. You see the exact request dict you sent and the response you got back.
Find `content`, `stop_reason` and `usage` in it. Post your `setup ok` line to the scoreboard:
the facilitator watches for teams that haven't.

## Lab 1 · Tool use (25 min)

### Build (core, 10 min)

Open `agentic/loop.py`. `run_agent` is the whole agent: call the model, run the tools it
asks for, send the results back, repeat. Steps 1, 2 and 6 are written. **Your team writes
steps 3 to 5**; the comments in the file say exactly what each step does.

Check your work against a fake model (no key, no cost):

```bash
uv run python -m unittest tests.test_lab1_loop -v
```

When all six tests pass, your loop works. Read `agentic/tools.py` too: notice that
`ToolBox.run` never raises an exception. Every failure comes back as text the model can read.

### Predict, then run (core, 10 min)

For each scenario, the Recorder writes a prediction first, then the Driver runs:

```bash
uv run labs/01_tool_use.py --scenario <name>
```

| Scenario | Setup | Predict |
|---|---|---|
| `tools` | a `get_order` tool | How many model calls will it take to answer? |
| `bad-description` | the only tool is `cancel_order`, but its description says "Look up the current status of an order" | Will the customer's order survive? |
| `good-description` | honest `get_order` and `cancel_order` | Does the order survive now? |
| `bad-error` | the customer says "1042"; the tool expects `ORD-1042` and replies "Order not found." | Will the agent recover? |

Post each scenario's line to the scoreboard.

### Challenge (stretch, 5 min)

In `labs/01_tool_use.py`, rewrite `TEAM_ERROR_MESSAGE`: the error the agent sees for a wrongly
formatted id. It may describe the format, but it must not contain `ORD-1042` itself. Run
`--scenario good-error` twice and post both results. The class votes on the best message.

More to try: `parallel` (two tool calls in one turn), `step-limit` (a tool that always fails),
`no-tools`.

### Discuss (in your team, then 1 team shares)

> The model never sees your Python, only a tool's name, description and schema. What does that
> mean for who should write tool descriptions and error messages, and how they should be tested?

## Lab 2 · Reflection (20 min)

### Build (core, 7 min)

Open `agentic/reflection.py`. `reflect` writes a draft, reviews it, and revises it until it
passes or runs out of rounds. The review (step 1) is written. **Your team writes steps 2 and 3:**
when to stop, and how to ask for a revision in the same conversation.

```bash
uv run python -m unittest tests.test_lab2_reflection -v
```

### Run and compare (core, 8 min)

The task: Maya's book arrived damaged. She wants a refund, to keep the book, and a $25 gift card.
Policy allows the first two, not the third. Seven Python checks score the final reply: the order
id is present, at most 120 words, no placeholders, no gift card offered, no amount above $18,
signed "Inkwell Books Support", plus `team_check`, which passes until you write it in the stretch
step.

**Predict:** how many of the checks will a single first draft pass?

```bash
uv run labs/02_reflection.py --scenario one-shot
uv run labs/02_reflection.py --scenario grounded      # Python checks + a model critic, up to 3 rounds
```

Compare the score and the number of model calls, and post both lines. If time allows, try
`self-critique` (model critic only) and `checks-only` (Python checks only).

### Write a check and swap (stretch, 5 min)

1. Fill in `team_check` in `labs/02_reflection.py` with a rule of your own, such as "never blames
   the courier".
2. Swap final drafts with a neighbouring team. Your newest one is in `runs/last-draft.txt`.
   Paste theirs into `labs/draft.txt` and run:

   ```bash
   uv run labs/02_reflection.py --scenario check-draft
   ```

   This makes no model calls. Does your check catch something their critic missed?

### Discuss

> When should feedback come from code, and when from a model? In `reflect`, a passing model review
> can never overrule a failing Python check. Agree or disagree?

## Lab 3 · Planning and the tournament (30 min)

The task (`GOAL` in `labs/_bookclub.py`): the book club's six members will read one science-fiction
book under $20. Make sure there are enough copies, restocking within a $60 supplier budget. Place
one single-copy order per member, then email each member their own order id. The grader in
`shop/grading.py` checks the shop's real orders, spend and emails, never what the agent *says*
it did. Lab 3 uses your Lab 1 loop.

### Plan and peer review (core, 10 min)

```bash
uv run labs/03_planning.py --scenario plan-only
```

This makes one model call and writes the plan to `labs/plan.json`. Nothing is executed yet.
**Swap screens with a neighbouring team** and review their plan for two minutes:

- The catalogue has traps. Will the plan notice that *Hyperion* is fully in stock but costs $22?
  That *Neuromancer* is $16, but restocking five copies costs $80?
- Does it check the supplier cost before committing to a book?

You may fix your own plan by editing `labs/plan.json` by hand: you are the human in the loop.
Then execute it, step by step, each step in a fresh conversation:

```bash
uv run labs/03_planning.py --scenario plan
```

Post your result. Read `agentic/planning.py` while it runs: `validate_plan`, `execute_plan` and
`replan` are all short.

### Tournament (core, 15 min)

`labs/04_tournament.py` runs the full pipeline, `plan-reflect`:

1. The model writes a plan, a critic reviews it, and the model revises it.
2. The plan is executed step by step.
3. A verify pass checks the real state and fixes any gaps.

Every run uses a fresh shop.

**Rules:**
1. Change **one** setting in the "TOURNAMENT KNOBS" block of `labs/_bookclub.py`: the system
   prompt, the plan rubric, the verify prompt, the review rounds, or the step and replan limits.
   Or don't change any of those, and pass `--model` instead.
2. Don't change `GOAL`, `shop/`, the grader or `agentic/planning.py`.
3. Run it twice and post both lines:

   ```bash
   uv run labs/04_tournament.py --runs 2 --quiet
   ```

**Scoring:** highest average checks passed (out of 6) wins. Ties go to the team with fewer
average tokens. Write your change in the scoreboard's "Our change" column.

### Discuss

> Planning and reflection cost extra model calls. Looking at the scoreboard, where did the extra
> structure pay for itself, and where was it overhead?

## Debrief (10 min)

The facilitator walks the scoreboard. The winning team and the most surprising team each get two
minutes. Last question for everyone:

> Now that you have written the loop yourselves, when would you reach for a framework, and what
> would you check that it does for you?

---

## Next lab: survey the frameworks, pick one, and know when not to

In the follow-up lab your team spikes every framework on a shortlist (LangGraph, Pydantic AI,
CrewAI, AutoGen, smolagents and others) against the same harness, and lists the trade-offs of
each. You then rebuild Lab 1 on the one you pick, run it through the same seven scenarios with
`framework_lab/parity.py`, justify the choice against your own criteria, and say when you would
skip every framework and write the loop yourself. Bring your wish list. The brief is in
[`framework_lab/README.md`](framework_lab/README.md).

## After the lab

- `uv run labs/00_first_call.py --scenario memory`: the API is stateless, and "memory" is the
  list you resend each time.
- `uv run labs/03_planning.py --scenario react`: no plan at all, just one loop with every tool.
  Compare its tokens with `plan`.
- `uv run labs/04_tournament.py --scenario react --runs 3 --quiet`: compare strategies, not just
  settings.
- Ideas to build:
  - A confirmation gate before any `cancel_` tool that asks the human with `input()`.
  - Running independent plan steps in parallel.
  - Giving the critic a different model from the writer.
  - A second model that plays the customer, with its own message list. That is all
    "multi-agent" means at this level.

## Reference

```
agentic/          the patterns
  llm.py          the only module that calls the API: model choice, retries, token counts
  tools.py        Tool, ToolBox, ToolError
  loop.py         run_agent            <- you write steps 3-5 (Lab 1)
  reflection.py   reflect, critique    <- you write steps 2-3 (Lab 2)
  planning.py     make_plan, validate_plan, execute_plan, replan
  trace.py        terminal trace, JSONL in runs/, scoreboard lines
shop/             Inkwell Books: a fake bookstore (every person, order and email is fictional)
labs/             00 setup · 01 tool use · 02 reflection · 03 planning · 04 tournament
solutions/        reference loop.py and reflection.py
scripts/          use_solution.py · replay.py · check_solutions.py
framework_lab/    the follow-up lab: brief, spikes/, my_agent.py stub, parity.py harness, JUSTIFICATION.md
tests/            offline tests with a scripted fake model (tests/fakes.py)
```

| Command | What it does |
|---|---|
| `uv run python -m unittest tests.test_lab1_loop -v` | Check your Lab 1 loop |
| `uv run python -m unittest tests.test_lab2_reflection -v` | Check your Lab 2 reflection |
| `uv run python -m unittest` | Everything (passes fully once Labs 1 and 2 are done) |
| `uv run scripts/use_solution.py loop` / `--undo` | Swap the reference solution in and out |
| `uv run scripts/replay.py [file] [--delay 0.5]` | Replay a saved trace, no model calls |
| `uv run scripts/check_solutions.py` | Run every test against the reference solutions |
| `uv run framework_lab/parity.py --impl both` | Follow-up lab: your framework agent vs the from-scratch loop |

Every lab accepts `--team`, `--model` and `--scenario`. Use `--help` to list the scenarios. The
default model is `claude-haiku-5-5`. Set `ANTHROPIC_MODEL` in `.env` or pass `--model` to change it.

This is a framework-free rebuild of [nuwank7/agentic-workshop](https://github.com/nuwank7/agentic-workshop).
The original used a LangGraph agent and a LangGraph checkpointer; here they are `run_agent` and
the `messages` list you resend. Its misleading-tool and misleading-error demos are Lab 1, and its
grading of the environment's final state is Lab 3's grader. Reflection and planning are new.
