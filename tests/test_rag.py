"""Tests for the RAG pipeline — uses the FakeEmbedder from conftest."""
from tests.conftest import FakeEmbedder
from edgesentry.events.models import Event
from edgesentry.events.store import EventStore
from edgesentry.rag.vectorstore import VectorStore
from edgesentry.rag.retriever import Retriever


class TestVectorStore:
    def test_add_and_search(self, cfg):
        embedder = FakeEmbedder()
        vs = VectorStore(cfg, embedder)
        e1 = Event(person_id="P-01", zone="Front Gate", confidence=0.9)
        e2 = Event(person_id="P-02", zone="Back Door", confidence=0.8)
        vs.add(e1)
        vs.add(e2)
        results = vs.search("Front Gate person", top_k=2)
        assert len(results) == 2
        assert all("text" in r for r in results)
        assert all("metadata" in r for r in results)

    def test_search_empty_store(self, cfg):
        embedder = FakeEmbedder()
        vs = VectorStore(cfg, embedder)
        results = vs.search("anything", top_k=3)
        assert results == []

    def test_metadata_preserved(self, cfg):
        embedder = FakeEmbedder()
        vs = VectorStore(cfg, embedder)
        e = Event(person_id="P-07", zone="Back Door", kind="person_detected")
        vs.add(e)
        results = vs.search("Back Door", top_k=1)
        meta = results[0]["metadata"]
        assert meta["person_id"] == "P-07"
        assert meta["zone"] == "Back Door"
        assert meta["kind"] == "person_detected"


class TestRetriever:
    def test_semantic_returns_results(self, cfg):
        embedder = FakeEmbedder()
        store = EventStore(cfg)
        vs = VectorStore(cfg, embedder)
        e = Event(person_id="P-01", zone="Front Gate")
        store.add(e)
        vs.add(e)
        retriever = Retriever(cfg, store, vs)
        hits = retriever.semantic("Front Gate")
        assert len(hits) >= 1

    def test_as_context_formats_numbered_list(self, cfg):
        embedder = FakeEmbedder()
        store = EventStore(cfg)
        vs = VectorStore(cfg, embedder)
        for i in range(3):
            e = Event(person_id=f"P-{i:02d}", zone="Front Gate")
            store.add(e)
            vs.add(e)
        retriever = Retriever(cfg, store, vs)
        ctx = retriever.as_context("Front Gate")
        assert ctx.startswith("Relevant past events:")
        assert "1." in ctx

    def test_as_context_empty(self, cfg):
        embedder = FakeEmbedder()
        store = EventStore(cfg)
        vs = VectorStore(cfg, embedder)
        retriever = Retriever(cfg, store, vs)
        ctx = retriever.as_context("anything")
        assert "No relevant" in ctx

    def test_recent(self, cfg):
        embedder = FakeEmbedder()
        store = EventStore(cfg)
        vs = VectorStore(cfg, embedder)
        store.add(Event(person_id="P-01", zone="A"))
        retriever = Retriever(cfg, store, vs)
        sentences = retriever.recent(minutes=60)
        assert len(sentences) == 1
        assert "P-01" in sentences[0]
