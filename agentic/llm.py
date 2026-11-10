"""The only module that talks to the Anthropic API.

An "LLM" here is just a function: (system, messages, tools) -> Message.
Everything agentic in this repository is built on top of that one call.

What this wrapper adds, and nothing more:
  * picks the model (argument, then $ANTHROPIC_MODEL, then DEFAULT_MODEL)
  * retries rate limits / overloads with exponential backoff (we turn the
    SDK's own retries off so you can see this happen)
  * counts calls and tokens
  * traces every call
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import anthropic

from . import trace

DEFAULT_MODEL = "claude-haiku-5-5"

# 429 rate limit, 5xx (including 529 overloaded) and network failures are worth
# retrying. Anything else (bad request, auth, unknown model) is a bug: fail fast.
RETRYABLE = (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError)


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def __str__(self) -> str:
        return f"{self.calls} calls, {self.input_tokens} in / {self.output_tokens} out tokens"


class LLM:
    def __init__(self, model: str | None = None, *, client: Any = None, max_retries: int = 4):
        self.model = model or os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODEL
        # max_retries=0: the SDK would otherwise retry silently. We do it ourselves below.
        self.client = client if client is not None else anthropic.Anthropic(max_retries=0)
        self.max_retries = max_retries
        self.usage = Usage()

    def __call__(
        self,
        *,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        tool_choice: dict | None = None,
        max_tokens: int = 1024,
    ) -> Any:
        # STEP 1: build the request. This dict *is* the whole interface to the model.
        request: dict[str, Any] = {"model": self.model, "max_tokens": max_tokens, "messages": messages}
        if system:
            request["system"] = system
        if tools:
            request["tools"] = tools
        if tool_choice:
            request["tool_choice"] = tool_choice

        # STEP 2: send it, retrying only the errors that are worth retrying.
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                response = self.client.messages.create(**request)
                break
            except RETRYABLE as exc:
                if attempt == self.max_retries:
                    raise
                wait = min(2**attempt, 30)
                trace.warn(f"{type(exc).__name__} from the API; retrying in {wait}s")
                time.sleep(wait)
        seconds = time.perf_counter() - started

        # STEP 3: account for it.
        self.usage.calls += 1
        self.usage.input_tokens += response.usage.input_tokens
        self.usage.output_tokens += response.usage.output_tokens
        trace.llm_call(
            response.model,
            seconds,
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.stop_reason,
        )
        return response


def text_of(response: Any) -> str:
    """Join the text blocks of a response (ignoring tool_use blocks)."""
    return "".join(block.text for block in response.content if block.type == "text").strip()


def as_assistant_message(response: Any) -> dict:
    """Turn a response into a plain-dict assistant message we can send back next turn.

    The API is stateless: "memory" is just us appending this to the list and
    resending the whole list. We copy only the fields the API needs.
    """
    content: list[dict] = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        else:  # e.g. thinking blocks: pass through unchanged
            content.append(block.model_dump(exclude_none=True))
    return {"role": "assistant", "content": content}
