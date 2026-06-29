"""Tests for the event model and SQLite store."""
from datetime import datetime, timedelta, timezone

from edgesentry.events.models import Event
from edgesentry.events.store import EventStore


class TestEventModel:
    def test_auto_id_and_timestamp(self):
        e = Event(kind="person_detected", person_id="P-01", zone="Front Gate")
        assert len(e.id) == 32  # uuid hex
        assert e.ts.tzinfo is not None

    def test_to_sentence_default(self):
        e = Event(person_id="P-05", zone="Back Door", confidence=0.88)
        s = e.to_sentence()
        assert "P-05" in s
        assert "Back Door" in s
        assert "0.88" in s

    def test_to_sentence_custom_text(self):
        e = Event(text="Custom journal entry.")
        assert e.to_sentence() == "Custom journal entry."

    def test_to_sentence_missing_fields(self):
        e = Event()
        s = e.to_sentence()
        assert "unidentified" in s
        assert "monitored area" in s


class TestEventStore:
    def test_add_and_query(self, cfg):
        store = EventStore(cfg)
        e = Event(person_id="P-01", zone="Front Gate", confidence=0.9)
        store.add(e)
        results = store.query(limit=10)
        assert len(results) == 1
        assert results[0].person_id == "P-01"

    def test_count(self, cfg):
        store = EventStore(cfg)
        for i in range(5):
            store.add(Event(person_id=f"P-{i:02d}", zone="Front Gate"))
        assert store.count() == 5
        assert store.count(zone="Front Gate") == 5
        assert store.count(zone="Back Door") == 0

    def test_query_by_zone(self, cfg):
        store = EventStore(cfg)
        store.add(Event(person_id="P-01", zone="Front Gate"))
        store.add(Event(person_id="P-02", zone="Back Door"))
        results = store.query(zone="Back Door")
        assert len(results) == 1
        assert results[0].person_id == "P-02"

    def test_query_by_person(self, cfg):
        store = EventStore(cfg)
        store.add(Event(person_id="P-01", zone="A"))
        store.add(Event(person_id="P-01", zone="B"))
        store.add(Event(person_id="P-02", zone="A"))
        results = store.query(person_id="P-01")
        assert len(results) == 2

    def test_query_since(self, cfg):
        store = EventStore(cfg)
        old = Event(
            person_id="P-01",
            ts=datetime.now(timezone.utc) - timedelta(hours=5),
        )
        recent = Event(person_id="P-02")
        store.add(old)
        store.add(recent)
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        results = store.query(since=since)
        assert len(results) == 1
        assert results[0].person_id == "P-02"

    def test_distinct_people(self, cfg):
        store = EventStore(cfg)
        store.add(Event(person_id="P-01"))
        store.add(Event(person_id="P-01"))
        store.add(Event(person_id="P-02"))
        people = store.distinct_people()
        assert set(people) == {"P-01", "P-02"}

    def test_idempotent_replace(self, cfg):
        store = EventStore(cfg)
        e = Event(person_id="P-01", zone="A")
        store.add(e)
        store.add(e)  # same id, should replace
        assert store.count() == 1
