"""Tests for the Flask web routes — no server needed, uses Flask test client."""
import json

from tests.conftest import FakeEmbedder, FakeLLM
from edgesentry.agent.agent import Agent
from edgesentry.events.models import Event
from edgesentry.events.store import EventStore
from edgesentry.rag.retriever import Retriever
from edgesentry.rag.vectorstore import VectorStore
from edgesentry.web.app import create_app


def _make_app(cfg):
    embedder = FakeEmbedder()
    store = EventStore(cfg)
    vs = VectorStore(cfg, embedder)
    retriever = Retriever(cfg, store, vs)
    agent = Agent(cfg, retriever, store)
    agent.llm = FakeLLM([{"content": "Test answer."}] * 20)
    app = create_app(cfg, agent=agent, store=store)
    app.config["TESTING"] = True
    return app, store


class TestIndex:
    def test_index_returns_html(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.get("/")
            assert resp.status_code == 200
            assert b"EdgeSentry" in resp.data


class TestChatEndpoint:
    def test_chat_returns_answer(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.post("/api/chat",
                          json={"message": "How many events?"},
                          content_type="application/json")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert "answer" in data

    def test_chat_empty_message(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.post("/api/chat",
                          json={"message": ""},
                          content_type="application/json")
            assert resp.status_code == 400

    def test_chat_no_body(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.post("/api/chat",
                          data="",
                          content_type="application/json")
            assert resp.status_code == 400


class TestEventsEndpoint:
    def test_events_empty(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.get("/api/events")
            assert resp.status_code == 200
            assert json.loads(resp.data) == []

    def test_events_returns_rows(self, cfg):
        app, store = _make_app(cfg)
        store.add(Event(person_id="P-01", zone="Front Gate"))
        store.add(Event(person_id="P-02", zone="Back Door"))
        with app.test_client() as c:
            resp = c.get("/api/events?limit=10")
            data = json.loads(resp.data)
            assert len(data) == 2
            assert all("person_id" in row for row in data)

    def test_events_limit(self, cfg):
        app, store = _make_app(cfg)
        for i in range(10):
            store.add(Event(person_id=f"P-{i:02d}"))
        with app.test_client() as c:
            data = json.loads(c.get("/api/events?limit=3").data)
            assert len(data) == 3


class TestHealthEndpoint:
    def test_health(self, cfg):
        app, _ = _make_app(cfg)
        with app.test_client() as c:
            resp = c.get("/api/health")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert "llm_ok" in data
