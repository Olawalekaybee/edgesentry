"""The Event schema — one row per thing that happened."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(BaseModel):
    """A single security-relevant occurrence, stored as a fact and a memory."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: datetime = Field(default_factory=_utcnow)
    kind: str = "person_detected"          # person_detected | journal | ...
    person_id: str | None = None
    zone: str | None = None
    confidence: float | None = None
    snapshot_path: str | None = None
    # Human-readable sentence used for embedding/retrieval, e.g.
    # "Person P-12 detected in Front Gate at 14:03 (confidence 0.82)."
    text: str = ""

    def to_sentence(self) -> str:
        """Natural-language form used as the RAG document for this event."""
        if self.text:
            return self.text
        who = self.person_id or "an unidentified person"
        where = self.zone or "the monitored area"
        when = self.ts.strftime("%Y-%m-%d %H:%M:%S UTC")
        conf = f" (confidence {self.confidence:.2f})" if self.confidence else ""
        return f"{who} was detected in {where} at {when}{conf}."
