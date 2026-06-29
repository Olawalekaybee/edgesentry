"""Ingestor — perception output → durable Event → SQLite + vector memory.

Includes debouncing: a person who lingers in view should not generate a new
event every single frame. We only emit a fresh event for a given (person_id,
zone) pair once per `event_debounce_seconds`.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
from PIL import Image

from edgesentry.config import Config
from edgesentry.events.models import Event
from edgesentry.events.store import EventStore
from edgesentry.perception import Detection
from edgesentry.rag.vectorstore import VectorStore

log = logging.getLogger(__name__)


class EventIngestor:
    def __init__(self, cfg: Config, store: EventStore, vectors: VectorStore) -> None:
        self.cfg = cfg
        self.store = store
        self.vectors = vectors
        self.debounce = cfg.perception.event_debounce_seconds
        self.snapshot_dir = Path(cfg.events.snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._last_seen: dict[tuple[str | None, str | None], float] = {}

    def ingest(self, frame: np.ndarray, detections: list[Detection]) -> list[Event]:
        """Persist new (debounced) detections as events + memories."""
        now = time.monotonic()
        created: list[Event] = []
        for det in detections:
            key = (det.person_id, det.zone)
            if now - self._last_seen.get(key, 0) < self.debounce:
                continue
            self._last_seen[key] = now

            snapshot_path = self._save_snapshot(frame, det)
            event = Event(
                kind="person_detected",
                person_id=det.person_id,
                zone=det.zone,
                confidence=det.confidence,
                snapshot_path=snapshot_path,
            )
            self.store.add(event)                       # precise facts
            self.vectors.add(event)                     # semantic memory
            created.append(event)
            log.info("Event: %s", event.to_sentence())
        return created

    def _save_snapshot(self, frame: np.ndarray, det: Detection) -> str | None:
        try:
            x1, y1, x2, y2 = det.bbox
            crop = frame[max(0, y1): y2, max(0, x1): x2]
            path = self.snapshot_dir / f"{int(time.time()*1000)}.jpg"
            Image.fromarray(crop[..., ::-1]).save(path)  # BGR→RGB
            return str(path)
        except Exception as exc:  # snapshots are best-effort, never fatal
            log.warning("Snapshot failed: %s", exc)
            return None
