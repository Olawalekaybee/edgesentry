"""The agent orchestration loop.

A small, readable ReAct-style loop:

    1. Send the user's question + system prompt + tool specs to the LLM.
    2. If the LLM asks to call tools, run them and feed results back.
    3. Repeat up to `max_tool_iterations`, then return the LLM's final text.

This is intentionally simple — no heavyweight agent framework — so it is easy to
read, debug, and run on a Pi. That readability is a feature for a portfolio repo.
"""
from __future__ import annotations

import json
import logging

from edgesentry.agent.llm import OllamaClient
from edgesentry.agent.prompts import AGENT_SYSTEM, JOURNALER_SYSTEM
from edgesentry.agent.tools import ToolBox
from edgesentry.config import Config
from edgesentry.events.store import EventStore
from edgesentry.rag.retriever import Retriever

log = logging.getLogger(__name__)


class Agent:
    def __init__(self, cfg: Config, retriever: Retriever, store: EventStore) -> None:
        self.cfg = cfg
        self.llm = OllamaClient(cfg)
        self.tools = ToolBox(cfg, retriever, store)
        self.max_iters = cfg.agent.max_tool_iterations

    def ask(self, question: str) -> str:
        """Answer a user question, using tools as needed."""
        messages: list[dict] = [
            {"role": "system", "content": AGENT_SYSTEM},
            {"role": "user", "content": question},
        ]
        tool_specs = self.tools.specs()

        for _ in range(self.max_iters):
            msg = self.llm.chat(messages, tools=tool_specs)
            tool_calls = msg.get("tool_calls") or []

            if not tool_calls:
                return (msg.get("content") or "").strip()

            # Echo the assistant turn, then run each requested tool.
            messages.append(msg)
            for call in tool_calls:
                fn = call["function"]
                name = fn["name"]
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args or "{}")
                result = self.tools.dispatch(name, args)
                messages.append(
                    {"role": "tool", "name": name, "content": result}
                )

        # Out of iterations — ask once more for a plain answer.
        messages.append(
            {"role": "user", "content": "Answer now using what you have."}
        )
        final = self.llm.chat(messages)
        return (final.get("content") or "").strip()

    def summarise(self, event_sentences: list[str]) -> str:
        """Used by the journaler to compress an hour of events into a note."""
        if not event_sentences:
            return "No activity in the last hour."
        joined = "\n".join(f"- {s}" for s in event_sentences)
        msg = self.llm.chat(
            [
                {"role": "system", "content": JOURNALER_SYSTEM},
                {"role": "user", "content": f"Events:\n{joined}"},
            ]
        )
        return (msg.get("content") or "").strip()
