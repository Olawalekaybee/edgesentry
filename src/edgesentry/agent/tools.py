"""Tools the agent can call.

Each tool has two parts:
  1. a JSON schema (the `SPECS`) advertised to the LLM so it knows the tool
     exists and what arguments it takes;
  2. a Python implementation in `ToolBox` that actually runs it.

`ToolBox.dispatch` maps a tool name + arguments coming back from the LLM to the
right implementation and returns a string result to feed back into the chat.
Keeping schema and implementation side by side makes adding a tool a one-stop job.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from edgesentry.config import Config
from edgesentry.events.store import EventStore
from edgesentry.rag.retriever import Retriever

log = logging.getLogger(__name__)


# ── Tool schemas advertised to the LLM (Ollama / OpenAI tool format) ─────────
SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Semantic search over past event memories. Use for "
            "vague or descriptive questions about what was observed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to look for."},
                    "top_k": {"type": "integer", "description": "How many results."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_logs",
            "description": "Precise structured query over the event database. Use "
            "for exact counts and time/zone/person filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes_ago": {
                        "type": "integer",
                        "description": "Only events within the last N minutes.",
                    },
                    "zone": {"type": "string", "description": "Filter by zone name."},
                    "person_id": {"type": "string", "description": "Filter by person."},
                    "count_only": {
                        "type": "boolean",
                        "description": "Return just the count instead of rows.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_alert",
            "description": "Send a Telegram alert. Only when the user asks to be "
            "alerted or to flag something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Alert text."},
                },
                "required": ["message"],
            },
        },
    },
]


class ToolBox:
    def __init__(self, cfg: Config, retriever: Retriever, store: EventStore) -> None:
        self.cfg = cfg
        self.retriever = retriever
        self.store = store
        self.enabled = set(cfg.agent.enabled_tools)
        # Imported lazily so tests don't require network/telegram config.
        self._alerter = None

    def specs(self) -> list[dict]:
        """Only advertise tools that are enabled in config."""
        return [s for s in SPECS if s["function"]["name"] in self.enabled]

    def dispatch(self, name: str, args: dict) -> str:
        if name not in self.enabled:
            return f"Tool '{name}' is not enabled."
        try:
            handler = getattr(self, f"_{name}")
        except AttributeError:
            return f"Unknown tool '{name}'."
        log.info("Tool call: %s(%s)", name, args)
        return handler(**args)

    # ── implementations ──────────────────────────────────────────────────────
    def _search_events(self, query: str, top_k: int | None = None) -> str:
        hits = self.retriever.semantic(query, top_k)
        if not hits:
            return "No matching events found in memory."
        return json.dumps([h["text"] for h in hits], ensure_ascii=False)

    def _query_logs(
        self,
        minutes_ago: int | None = None,
        zone: str | None = None,
        person_id: str | None = None,
        count_only: bool = False,
    ) -> str:
        since = (
            datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
            if minutes_ago
            else None
        )
        if count_only:
            n = self.store.count(since=since, zone=zone, person_id=person_id)
            return json.dumps({"count": n})
        events = self.store.query(
            since=since, zone=zone, person_id=person_id, limit=50
        )
        return json.dumps([e.to_sentence() for e in events], ensure_ascii=False)

    def _send_alert(self, message: str) -> str:
        if self._alerter is None:
            from edgesentry.alerting.telegram import TelegramAlerter

            self._alerter = TelegramAlerter(self.cfg)
        ok = self._alerter.send(message)
        return "Alert sent." if ok else "Alert failed (check Telegram config)."
