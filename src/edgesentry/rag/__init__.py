"""RAG layer — the system's semantic memory.

    embedder.py     turns event sentences into vectors (MiniLM, on CPU)
    vectorstore.py  stores/searches those vectors (ChromaDB, file-based)
    retriever.py    high-level "find context relevant to this question" API
                    that the agent and journaler call.

This answers *fuzzy* questions the SQLite store cannot: "anything unusual near
the back door?" maps to nearby vectors even without exact keyword matches.
"""
