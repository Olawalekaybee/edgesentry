"""Tests for agent tools and the ReAct orchestration loop.

Uses FakeLLM + FakeEmbedder from conftest — no Ollama needed.
"""
import json

from tests.conftest import FakeEmbedder, FakeLLM
from edgesentry.agent.tools import ToolBox
from edgesentry.agent.agent import Agent
from edgesentry.events.models import Event
from edgesentry.events.store import EventStore
from edgesentry.rag.retriever import Retriever
from edgesentry.rag.vectorstore import VectorStore


def _make_retriever_and_store(cfg):
    embedder = FakeEmbedder()
    store = EventStore(cfg)
    vs = VectorStore(cfg, embedder)
    retriever = Retriever(cfg, store, vs)
    return retriever, store, vs


class TestToolBox:
    def test_search_events_returns_json(self, cfg):
        retriever, store, vs = _make_retriever_and_store(cfg)
        e = Event(person_id="P-01", zone="Front Gate")
        store.add(e)
        vs.add(e)
        tb = ToolBox(cfg, retriever, store)
        result = tb.dispatch("search_events", {"query": "Front Gate"})
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert any("P-01" in s for s in parsed)

    def test_query_logs_count(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        for i in range(3):
            store.add(Event(person_id=f"P-{i:02d}", zone="Back Door"))
        tb = ToolBox(cfg, retriever, store)
        result = tb.dispatch("query_logs", {"count_only": True})
        assert json.loads(result)["count"] == 3

    def test_query_logs_with_zone_filter(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        store.add(Event(person_id="P-01", zone="Front Gate"))
        store.add(Event(person_id="P-02", zone="Back Door"))
        tb = ToolBox(cfg, retriever, store)
        result = tb.dispatch("query_logs", {"zone": "Back Door"})
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert "P-02" in parsed[0]

    def test_disabled_tool_rejected(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        # Remove send_alert from enabled list.
        object.__setattr__(cfg.agent, "enabled_tools", ["search_events", "query_logs"])
        tb = ToolBox(cfg, retriever, store)
        result = tb.dispatch("send_alert", {"message": "hi"})
        assert "not enabled" in result

    def test_unknown_tool(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        tb = ToolBox(cfg, retriever, store)
        result = tb.dispatch("does_not_exist", {})
        assert "not enabled" in result or "Unknown" in result

    def test_specs_filters_by_enabled(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        object.__setattr__(cfg.agent, "enabled_tools", ["search_events"])
        tb = ToolBox(cfg, retriever, store)
        specs = tb.specs()
        names = [s["function"]["name"] for s in specs]
        assert "search_events" in names
        assert "query_logs" not in names


class TestAgentLoop:
    def test_simple_text_reply(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        agent = Agent(cfg, retriever, store)
        # Replace the real LLM with a fake that returns a plain answer.
        agent.llm = FakeLLM([{"content": "All clear — nothing unusual."}])
        answer = agent.ask("Anything unusual?")
        assert answer == "All clear — nothing unusual."
        assert len(agent.llm.calls) == 1

    def test_tool_call_then_answer(self, cfg):
        retriever, store, vs = _make_retriever_and_store(cfg)
        store.add(Event(person_id="P-01", zone="Front Gate"))
        vs.add(Event(person_id="P-01", zone="Front Gate"))
        agent = Agent(cfg, retriever, store)
        # Turn 1: LLM asks to call search_events.
        # Turn 2: LLM answers based on tool result.
        agent.llm = FakeLLM([
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_events",
                            "arguments": {"query": "Front Gate"},
                        }
                    }
                ],
            },
            {"content": "P-01 was at the Front Gate."},
        ])
        answer = agent.ask("Who was at the Front Gate?")
        assert "P-01" in answer
        assert len(agent.llm.calls) == 2  # initial + after tool

    def test_summarise_no_events(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        agent = Agent(cfg, retriever, store)
        result = agent.summarise([])
        assert result == "No activity in the last hour."

    def test_summarise_with_events(self, cfg):
        retriever, store, _ = _make_retriever_and_store(cfg)
        agent = Agent(cfg, retriever, store)
        agent.llm = FakeLLM([{"content": "Two people visited the front gate."}])
        result = agent.summarise(["P-01 at Front Gate", "P-02 at Front Gate"])
        assert "Two people" in result
