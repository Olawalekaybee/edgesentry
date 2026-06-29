"""EdgeSentry — an offline agentic-RAG layer for the Pi5 Edge AI Security Monitor.

The package is organised by responsibility:

    perception/  vision on the Hailo NPU (v1): detection, re-id, zones, camera
    events/      structured event facts: model, SQLite store, ingestor
    rag/         semantic memory: embedder, vector store, retriever
    agent/       the local LLM agent: client, tools, orchestration loop
    tasks/       scheduled agentic jobs (hourly journaler)
    alerting/    Telegram + action sinks
    web/         Flask dashboard, SSE live feed, chat endpoint

The v2 layers (events, rag, agent, tasks) depend only on the small `Detection`
data contract in `perception`, so they can be developed and tested without any
camera or NPU attached.
"""

__version__ = "2.0.0"
