#!/usr/bin/env python
"""Benchmark the v2 layers and print a table you can put in the README/video.

Measures: embedding throughput, vector search latency, end-to-end agent latency
(RAG retrieval + LLM). Run on the Pi 5 for headline numbers:

    python scripts/benchmark.py
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edgesentry.agent.agent import Agent
from edgesentry.config import load_config
from edgesentry.events.store import EventStore
from edgesentry.rag.embedder import Embedder
from edgesentry.rag.retriever import Retriever
from edgesentry.rag.vectorstore import VectorStore


def timed(fn, runs: int = 20) -> tuple[float, float]:
    """Return (median_ms, p95_ms) over `runs` calls."""
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000)
    samples.sort()
    p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
    return statistics.median(samples), p95


def main() -> None:
    cfg = load_config()
    embedder = Embedder(cfg)
    store = EventStore(cfg)
    vectors = VectorStore(cfg, embedder)
    retriever = Retriever(cfg, store, vectors)
    agent = Agent(cfg, retriever, store)

    print("Warming up embedder…")
    embedder.embed_one("warmup")

    rows = []
    em_med, em_p95 = timed(lambda: embedder.embed_one("a person near the gate"))
    rows.append(("Embed one sentence", em_med, em_p95))

    vs_med, vs_p95 = timed(lambda: vectors.search("unusual activity", top_k=6))
    rows.append(("Vector search (top-6)", vs_med, vs_p95))

    if agent.llm.health():
        ag_med, ag_p95 = timed(lambda: agent.ask("How many events in the last hour?"), runs=5)
        rows.append(("Agent end-to-end", ag_med, ag_p95))
    else:
        print("(Ollama not reachable — skipping agent benchmark.)")

    print("\n| Stage | Median (ms) | p95 (ms) |")
    print("|-------|-------------|----------|")
    for name, med, p95 in rows:
        print(f"| {name} | {med:.1f} | {p95:.1f} |")


if __name__ == "__main__":
    main()
