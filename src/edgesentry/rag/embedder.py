"""Embedder — wraps a small sentence-transformer for CPU use on the Pi 5.

MiniLM (384-dim) is tiny, fast on CPU, and more than good enough for short event
sentences. The model loads lazily on first use so importing this module is cheap
(keeps CI and `--no-perception` startup fast).
"""
from __future__ import annotations

from edgesentry.config import Config


class Embedder:
    def __init__(self, cfg: Config) -> None:
        self._model_name = cfg.rag.embed_model
        self._model = None  # lazy

    def _ensure(self) -> None:
        if self._model is None:
            # Imported here so the heavy dependency only loads when needed.
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name, device="cpu")

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure()
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
