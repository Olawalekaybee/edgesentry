# EdgeSentry — Agentic RAG for Offline Edge AI Security

> **An offline AI security system that remembers what it sees and answers questions about it — running entirely on a Raspberry Pi 5 + Hailo-8L. No cloud. No API costs.**

EdgeSentry is the **v2 agentic layer** built on top of the
[Pi5 Edge AI Security Monitor](#relationship-to-v1). The v1 system detects and
re-identifies people on-device using the Hailo-8L NPU. EdgeSentry adds a **memory**
(a local vector store of every event) and a **voice** (a local LLM agent you can
ask questions in plain English) — all still 100% offline.

Instead of staring at a dashboard, you can now ask:

> *"Has the same person shown up more than twice today?"*
> *"Summarise everything unusual that happened in Zone 2 this afternoon."*
> *"When did someone last enter the back gate?"*

---

## What this adds on top of v1

| Capability | v1 (Pi5 Security Monitor) | v2 (EdgeSentry) |
|------------|---------------------------|-----------------|
| Person detection (YOLOv8) | ✅ on Hailo NPU | ✅ reused |
| Person re-identification (ReID) | ✅ on Hailo NPU | ✅ reused |
| Zone awareness + Telegram alerts | ✅ | ✅ reused |
| Live dashboard | ✅ Flask/SSE | ✅ + chat box |
| **Searchable event memory (RAG)** | ❌ | ✅ vector store |
| **Natural-language Q&A over footage** | ❌ | ✅ local LLM agent |
| **Tool-calling agent (search / SQL / alert)** | ❌ | ✅ |
| **Hourly self-summarising journal** | ❌ | ✅ |

Everything runs on the Pi. The LLM runs on the Pi 5 CPU/RAM; the vision models run
on the Hailo NPU exactly as in v1.

---

## Architecture

```
                    ┌────────────────────────────────────────────────┐
                    │                Raspberry Pi 5 (128 GB)          │
                    │                                                 │
  Camera ──────────►│  ┌──────────────┐                               │
                    │  │  PERCEPTION  │  Hailo-8L NPU                  │
                    │  │  YOLOv8 +    │  (~14 ms / frame)             │
                    │  │  ResNet ReID │                               │
                    │  └──────┬───────┘                               │
                    │         │ detections                            │
                    │         ▼                                       │
                    │  ┌──────────────┐     ┌────────────────────┐    │
                    │  │   EVENTS     │────►│   EVENT STORE       │    │
                    │  │  ingestor    │     │   SQLite (facts)    │    │
                    │  └──────┬───────┘     └─────────┬──────────┘    │
                    │         │                       │               │
                    │         ▼                       │               │
                    │  ┌──────────────┐               │               │
                    │  │     RAG      │               │               │
                    │  │  embedder +  │◄──────────────┘               │
                    │  │  vectorstore │  (semantic memory)            │
                    │  └──────┬───────┘                               │
                    │         │ retrieved context                     │
                    │         ▼                                       │
                    │  ┌──────────────────────────────┐              │
                    │  │           AGENT              │              │
                    │  │  Local LLM (Qwen2.5-3B)      │              │
                    │  │  + tools:                    │              │
                    │  │   • search_events (RAG)      │              │
                    │  │   • query_logs   (SQL)       │              │
                    │  │   • send_alert   (Telegram)  │              │
                    │  └──────┬───────────────────────┘              │
                    │         │                                       │
   You ◄────────────│  ┌──────▼───────┐   ┌────────────────────┐     │
   (browser chat)   │  │     WEB      │   │  TASKS             │     │
                    │  │  Flask + SSE │   │  hourly journaler  │     │
                    │  │  + chat API  │   │  (self-review)     │     │
                    │  └──────────────┘   └────────────────────┘     │
                    └────────────────────────────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full data flow and design
decisions.

---

## Quick start (developing over SSH in VS Code)

> These steps assume you SSH into your Pi 5 from VS Code (Remote-SSH extension) and
> open this folder there.

```bash
# 1. Clone onto the Pi
git clone https://github.com/<you>/edgesentry.git
cd edgesentry

# 2. Create a virtual environment (system-site-packages to reuse Hailo runtime)
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Pull the local LLM (uses Ollama — see scripts/pull_llm.sh)
bash scripts/pull_llm.sh

# 5. Copy and edit configuration
cp .env.example .env        # add your Telegram token etc.
#   review config/config.yaml

# 6. (Optional) seed fake events so you can test the agent without a camera
python scripts/seed_demo_data.py

# 7. Run
python -m edgesentry          # starts perception + web + agent
# open http://<pi-ip>:8000 in your browser
```

To run **only the web + agent** against seeded data (no camera/Hailo needed — great
for laptop development):

```bash
python -m edgesentry --no-perception
```

---

## Repository layout

```
edgesentry/
├── config/              # YAML config + zone polygons
├── docs/                # architecture, setup, benchmarks, demo script
├── src/edgesentry/
│   ├── perception/      # v1 vision: YOLOv8 + ReID on Hailo, zones, camera
│   ├── events/          # event model, SQLite log, detection→event ingestor
│   ├── rag/             # embedder, vector store, retriever
│   ├── agent/           # LLM client, tools, agent loop, prompts
│   ├── tasks/           # scheduled agentic jobs (hourly journaler)
│   ├── alerting/        # Telegram + action sinks
│   └── web/             # Flask dashboard + chat + SSE
├── models/              # model files (git-ignored; manifest explains how to get them)
├── scripts/             # model conversion, LLM pull, demo seeding, benchmarks
├── tests/               # hardware-independent unit tests (run in CI)
└── .github/workflows/   # CI
```

Each subpackage has a short `__init__.py` docstring describing its single
responsibility, so the codebase is easy to navigate.

---

## Tech stack

- **Vision (NPU):** YOLOv8 + ResNet ReID compiled to Hailo `.hef` (from v1)
- **Event facts:** SQLite (zero-config, file-based, perfect for the edge)
- **Semantic memory:** `sentence-transformers` (MiniLM) + ChromaDB
- **Agent LLM:** Qwen2.5-3B-Instruct via **Ollama** (CPU, quantised)
- **Web:** Flask + Server-Sent Events
- **Tests/CI:** pytest, GitHub Actions

All chosen to run comfortably within the Pi 5's resources with zero external calls.

---

## Relationship to v1

This repo is designed to sit alongside (or extend) the original
**Pi5 Edge AI Security Monitor**. The `perception/` package contains thin adapters
that wrap your existing v1 detection/ReID/zone code. If you keep v1 as a separate
repo, install it as a dependency and import it from the adapters; if you fold v1
into this repo, drop the v1 modules straight into `perception/`. Either way, the
v2 layers (`events`, `rag`, `agent`, `tasks`) depend only on the small `Detection`
data contract defined in `perception/__init__.py`.

---

## License

MIT — see [LICENSE](LICENSE).
