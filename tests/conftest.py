"""Shared test fixtures.

These tests are deliberately hardware-independent (no camera, no Hailo, no
Ollama) so they run in CI. We point config at a temp dir and use lightweight
fakes where a real model would be heavy or networked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `src/` importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edgesentry.config import load_config


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    """A Config pointed entirely at a temp directory."""
    monkeypatch.setenv("WEB_PORT", "8000")
    c = load_config("config/config.yaml")
    # Redirect all data paths into tmp so tests never touch real data.
    object.__setattr__(c.events, "db_path", str(tmp_path / "events.sqlite"))
    object.__setattr__(c.events, "snapshot_dir", str(tmp_path / "snaps"))
    object.__setattr__(c.rag, "vector_dir", str(tmp_path / "chroma"))
    return c


class FakeEmbedder:
    """Deterministic tiny embeddings — no model download, fast in CI."""

    def __init__(self, *_args, **_kwargs):
        pass

    def _vec(self, text: str) -> list[float]:
        # 8-dim bag-of-chars hash; good enough for store/search plumbing tests.
        v = [0.0] * 8
        for ch in text:
            v[ord(ch) % 8] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / norm for x in v]

    def embed(self, texts):
        return [self._vec(t) for t in texts]

    def embed_one(self, text):
        return self._vec(text)


class FakeLLM:
    """Scriptable stand-in for the Ollama client."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []

    def chat(self, messages, tools=None):
        self.calls.append({"messages": messages, "tools": tools})
        return self._replies.pop(0)

    def health(self):
        return True
