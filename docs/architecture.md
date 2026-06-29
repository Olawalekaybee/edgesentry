# Architecture

This document explains **how** EdgeSentry works and **why** each component was
chosen. It is written for reviewers and collaborators

---

## Design principles

1. **Fully offline.** No cloud LLM, no external API, no internet required at
   runtime. Everything runs on the Raspberry Pi 5 + Hailo-8L.
2. **Two stores, not one.** SQLite holds structured facts (exact counts and
   filters); ChromaDB holds semantic memories (fuzzy similarity). The agent
   decides which to query based on the question — matching how a human would
   pick a spreadsheet vs. free-text search.
3. **Lazy imports, thin contracts.** Heavy dependencies (Hailo SDK,
   sentence-transformers) import only when used, so you can run and test the v2
   layers on a laptop. The only contract between perception and everything else
   is the `Detection` dataclass.
4. **Readable agent loop.** The ReAct loop is ~40 lines of plain Python. No
   LangChain, no CrewAI, no framework. Portfolio reviewers (and you) can read
   the entire orchestration in one screen.

---

## Data flow

```
Frame from camera
       │
       ▼
┌──────────────┐
│  Detector    │  YOLOv8n on Hailo NPU → bounding boxes + confidence
│  (14ms/frame)│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    ReID      │  ResNet on Hailo NPU → person embedding → person_id
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   ZoneMap    │  Point-in-polygon test → zone name
└──────┬───────┘
       │ Detection(bbox, confidence, person_id, zone)
       │
       ▼
┌──────────────┐        ┌────────────────────┐
│   Ingestor   │───────►│  EventStore        │  SQLite — precise facts
│  (debounced) │        │  events.sqlite      │
│              │        └────────────────────┘
│              │
│              │        ┌────────────────────┐
│              │───────►│  VectorStore       │  ChromaDB — semantic memory
│              │        │  MiniLM embeddings  │
└──────────────┘        └─────────┬──────────┘
                                  │
                                  │ retrieved context
                                  ▼
                        ┌────────────────────┐
                        │      Agent         │  Qwen2.5-3B via Ollama
                        │   ReAct loop:      │
                        │    1. read question │
                        │    2. pick tool     │
                        │    3. call tool     │
                        │    4. answer        │
                        └─────────┬──────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼              ▼
               Flask chat    Telegram       Journaler
               (user asks)   (alerts)      (hourly self-
                                            review → store)
```

---

## Component details

### Perception (Hailo-8L NPU)

| Model | Task | Latency | Power |
|-------|------|---------|-------|
| YOLOv8n `.hef` | Person detection | ~14 ms/frame | <5 W NPU total |
| ResNet ReID `.hef` | Person re-identification | ~8 ms/crop | |

Both run on the Hailo NPU. The CPU does not touch these workloads at all, leaving
room for the LLM. The perception loop runs in a daemon thread; it yields
`Detection` objects through the `Ingestor`.

### Ingestor + debouncing

A person standing in frame at 30 FPS would generate 1,800 events per minute. The
ingestor debounces by (person_id, zone) — a new event is only emitted once per
`event_debounce_seconds` (default 30s) for a given person in a given zone.

### Event store (SQLite)

Zero-config, file-based, indexed on `ts`, `zone`, and `person_id`. Powers the
agent's `query_logs` tool for questions like "how many people in the Front Gate
in the last 2 hours?" where an exact COUNT + WHERE is better than fuzzy search.

### Vector store (ChromaDB + MiniLM)

Each event is converted to a natural-language sentence
("P-01 was detected in Front Gate at 14:03") and embedded using
`all-MiniLM-L6-v2` (384-dim, ~30ms/embed on Pi CPU). The embedding is stored in
a local ChromaDB (file-backed, HNSW index, cosine distance). Powers the agent's
`search_events` tool for questions like "anything unusual near the back door?"
where semantic similarity beats exact keyword matching.

### Agent (Qwen2.5-3B-Instruct via Ollama)

A quantised 3B-parameter LLM running on the Pi 5's CPU. The ReAct loop:

1. Receives the user's question + system prompt + tool specifications.
2. The LLM decides whether it can answer directly or needs to call a tool.
3. If a tool call is requested, the loop executes it and feeds the result back.
4. Repeats up to `max_tool_iterations` (default 4), then returns the final text.

Available tools:

| Tool | Backend | Best for |
|------|---------|----------|
| `search_events` | Vector store | Fuzzy, descriptive questions |
| `query_logs` | SQLite | Exact counts, time/zone/person filters |
| `send_alert` | Telegram API | User-requested notifications |

### Journaler (agentic self-review)

Every hour, the journaler pulls the last hour of raw event sentences, asks the
agent to summarise them into a single paragraph, and stores that paragraph back
into the vector store as a `journal` memory. This compresses thousands of raw
events into a few high-level narratives, giving the agent a growing long-term
memory that remains efficient to search.

### Web dashboard

Flask serves:
- `GET /` — dashboard with live feed + chat box + recent events table.
- `POST /api/chat` — forwards the user's message to the agent, returns the answer.
- `GET /api/events` — recent events JSON for the table.
- `GET /api/health` — LLM online/offline status.

---

## Resource budget on the Pi 5 (4 GB / 8 GB)

| Component | RAM | Notes |
|-----------|-----|-------|
| Hailo NPU runtime | ~200 MB | Off-loaded to NPU memory |
| MiniLM embedder | ~100 MB | Loaded lazily on first embed |
| ChromaDB | ~50 MB | HNSW index, grows with events |
| Ollama (Qwen 3B Q4) | ~2 GB | Largest single cost |
| Flask + Python | ~100 MB | |
| **Total** | **~2.5 GB** | Fits comfortably on 4 GB Pi 5 |

The 128 GB storage is more than enough for months of event data, snapshots, and
the vector index.

---

## Testing strategy

All tests are hardware-independent:
- `FakeEmbedder` generates deterministic 8-dim vectors (no model download).
- `FakeLLM` returns scripted responses (no Ollama needed).
- `EventStore` tests use a temp-dir SQLite.
- The Flask test client runs routes without starting a server.

This lets CI run on any GitHub Actions runner (Ubuntu x86) while the real system
runs on aarch64 + Hailo.
