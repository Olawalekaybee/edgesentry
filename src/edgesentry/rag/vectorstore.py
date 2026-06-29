"""VectorStore — a thin wrapper over ChromaDB (local, file-based, no server).

Stores one document per event (its natural-language sentence) plus metadata
(person_id, zone, timestamp) so results can be filtered as well as ranked. We
pass our own MiniLM embeddings in rather than letting Chroma pick a model, so
the embedding choice stays in one place (the Embedder).
"""
from __future__ import annotations

from pathlib import Path

from edgesentry.config import Config
from edgesentry.events.models import Event
from edgesentry.rag.embedder import Embedder


class VectorStore:
    def __init__(self, cfg: Config, embedder: Embedder) -> None:
        self.embedder = embedder
        Path(cfg.rag.vector_dir).mkdir(parents=True, exist_ok=True)

        import chromadb  # local import keeps module import cheap

        self._client = chromadb.PersistentClient(path=cfg.rag.vector_dir)
        self._col = self._client.get_or_create_collection(
            name=cfg.rag.collection, metadata={"hnsw:space": "cosine"}
        )

    def add(self, event: Event) -> None:
        sentence = event.to_sentence()
        self._col.add(
            ids=[event.id],
            documents=[sentence],
            embeddings=[self.embedder.embed_one(sentence)],
            metadatas=[
                {
                    "ts": event.ts.isoformat(),
                    "kind": event.kind,
                    "person_id": event.person_id or "",
                    "zone": event.zone or "",
                }
            ],
        )

    def search(self, query: str, top_k: int = 6) -> list[dict]:
        """Return the top_k most semantically similar event sentences."""
        res = self._col.query(
            query_embeddings=[self.embedder.embed_one(query)],
            n_results=top_k,
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        return [
            {"text": d, "metadata": m, "distance": dist}
            for d, m, dist in zip(docs, metas, dists)
        ]
