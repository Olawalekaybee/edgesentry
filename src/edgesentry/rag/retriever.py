"""Retriever — the high-level "give me relevant context" API.

Sits above the SQLite store and the vector store and is what the agent's
`search_events` tool and the journaler use. Formats retrieved memories into a
compact context block ready to drop into an LLM prompt.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from edgesentry.config import Config
from edgesentry.events.store import EventStore
from edgesentry.rag.vectorstore import VectorStore


class Retriever:
    def __init__(self, cfg: Config, store: EventStore, vectors: VectorStore) -> None:
        self.cfg = cfg
        self.store = store
        self.vectors = vectors
        self.top_k = cfg.rag.top_k

    def semantic(self, query: str, top_k: int | None = None) -> list[dict]:
        """Pure semantic search over event memories."""
        return self.vectors.search(query, top_k or self.top_k)

    def recent(self, minutes: int = 60) -> list[str]:
        """All event sentences from the last `minutes` (for the journaler)."""
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [e.to_sentence() for e in self.store.query(since=since, limit=500)]

    def as_context(self, query: str, top_k: int | None = None) -> str:
        """Retrieve memories and format them as a numbered context block."""
        hits = self.semantic(query, top_k)
        if not hits:
            return "No relevant past events were found in memory."
        lines = [f"{i+1}. {h['text']}" for i, h in enumerate(hits)]
        return "Relevant past events:\n" + "\n".join(lines)
