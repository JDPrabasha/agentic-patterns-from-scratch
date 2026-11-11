"""Lab A — Setup check (and, after the lab, why "memory" is just a list).

Run:  uv run labs/a_first_call.py --scenario basics --team <your-team>
      uv run labs/a_first_call.py --scenario memory        (after the lab)
Read: agentic/llm.py
"""

import json

import _common  # noqa: F401  (sets up paths and .env)

from agentic import as_assistant_message, text_of, trace


def basics(llm):
    """The whole interface: a request dict in, a Message out."""
    messages = [{"role": "user", "content": "In one sentence, what is an AI agent?"}]
    trace.block(
        "Request (this dict is everything the model receives)",
        json.dumps({"model": llm.model, "max_tokens": 200, "messages": messages}, indent=2),
    )
    response = llm(messages=messages, max_tokens=200)
    trace.block("Response (as returned by the SDK)", response.model_dump_json(indent=2, exclude_none=True))
    trace.note(f"stop_reason={response.stop_reason!r}  — always check this before trusting the text")
    return "setup ok", f"stop_reason={response.stop_reason}"


def memory(llm):
    """The API is stateless. Conversation memory is you resending the history."""
    first = [{"role": "user", "content": "Hi, I'm Maya. My order number is ORD-1042."}]
    trace.user(first[0]["content"])
    r1 = llm(messages=first, max_tokens=200)
    trace.assistant(text_of(r1))

    question = {"role": "user", "content": "What's my order number?"}
    trace.note("Second call WITHOUT the earlier messages:")
    trace.user(question["content"])
    r2 = llm(messages=[question], max_tokens=200)
    trace.assistant(text_of(r2))

    trace.note("Third call WITH the earlier messages appended:")
    history = first + [as_assistant_message(r1), question]
    trace.block("messages sent", json.dumps(history, indent=2))
    r3 = llm(messages=history, max_tokens=200)
    trace.assistant(text_of(r3))


def max_tokens(llm):
    """A reply cut off by max_tokens looks like a normal reply unless you check stop_reason."""
    response = llm(
        messages=[{"role": "user", "content": "Explain how a bookshop decides when to reorder stock."}],
        max_tokens=30,
    )
    trace.assistant(text_of(response))
    trace.note(f"stop_reason={response.stop_reason!r} — the text above is truncated, not finished.")


SCENARIOS = {
    "basics": ("one request, one response", basics),
    "memory": ("statelessness: history is a list you resend", memory),
    "max-tokens": ("a truncated reply and stop_reason", max_tokens),
}

if __name__ == "__main__":
    _common.run("labA", "Lab A: setup check and the raw Messages API call.", SCENARIOS)
