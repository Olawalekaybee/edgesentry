"""SQLite event store — the source of truth for *precise* questions.

Deliberately tiny and dependency-free (Python's built-in sqlite3). Exposes a few
structured query helpers that the agent's `query_logs` tool calls to get exact
answers (counts, filters by zone / person / time window).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from edgesentry.config import Config
from edgesentry.events.models import Event

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            TEXT PRIMARY KEY,
    ts            TEXT NOT NULL,
    kind          TEXT NOT NULL,
    person_id     TEXT,
    zone          TEXT,
    confidence    REAL,
    snapshot_path TEXT,
    text          TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts   ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_zone ON events(zone);
CREATE INDEX IF NOT EXISTS idx_events_pid  ON events(person_id);
"""


class EventStore:
    def __init__(self, cfg: Config) -> None:
        self.path = cfg.events.db_path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── writes ───────────────────────────────────────────────────────────────
    def add(self, event: Event) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO events "
            "(id, ts, kind, person_id, zone, confidence, snapshot_path, text) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                event.id,
                event.ts.isoformat(),
                event.kind,
                event.person_id,
                event.zone,
                event.confidence,
                event.snapshot_path,
                event.to_sentence(),
            ),
        )
        self._conn.commit()

    # ── reads (used by the agent's query_logs tool) ──────────────────────────
    def query(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        zone: str | None = None,
        person_id: str | None = None,
        kind: str | None = None,
        limit: int = 200,
    ) -> list[Event]:
        sql = "SELECT * FROM events WHERE 1=1"
        params: list[object] = []
        if since:
            sql += " AND ts >= ?"; params.append(since.isoformat())
        if until:
            sql += " AND ts <= ?"; params.append(until.isoformat())
        if zone:
            sql += " AND zone = ?"; params.append(zone)
        if person_id:
            sql += " AND person_id = ?"; params.append(person_id)
        if kind:
            sql += " AND kind = ?"; params.append(kind)
        sql += " ORDER BY ts DESC LIMIT ?"; params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_event(r) for r in rows]

    def count(
        self,
        *,
        since: datetime | None = None,
        zone: str | None = None,
        person_id: str | None = None,
    ) -> int:
        sql = "SELECT COUNT(*) AS n FROM events WHERE 1=1"
        params: list[object] = []
        if since:
            sql += " AND ts >= ?"; params.append(since.isoformat())
        if zone:
            sql += " AND zone = ?"; params.append(zone)
        if person_id:
            sql += " AND person_id = ?"; params.append(person_id)
        return int(self._conn.execute(sql, params).fetchone()["n"])

    def distinct_people(self, *, since: datetime | None = None) -> list[str]:
        sql = "SELECT DISTINCT person_id FROM events WHERE person_id IS NOT NULL"
        params: list[object] = []
        if since:
            sql += " AND ts >= ?"; params.append(since.isoformat())
        rows = self._conn.execute(sql, params).fetchall()
        return [r["person_id"] for r in rows]

    @staticmethod
    def _row_to_event(r: sqlite3.Row) -> Event:
        return Event(
            id=r["id"],
            ts=datetime.fromisoformat(r["ts"]).astimezone(timezone.utc),
            kind=r["kind"],
            person_id=r["person_id"],
            zone=r["zone"],
            confidence=r["confidence"],
            snapshot_path=r["snapshot_path"],
            text=r["text"] or "",
        )
