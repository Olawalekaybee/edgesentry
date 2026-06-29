"""Entry point: `python -m edgesentry`.

Wires the components together and starts them. Use --no-perception to run only
the web + agent + RAG against existing/seeded data (handy for laptop dev where
there is no camera or Hailo NPU).
"""
from __future__ import annotations

import argparse
import logging
import threading

from edgesentry.config import load_config
from edgesentry.events.store import EventStore
from edgesentry.events.ingestor import EventIngestor
from edgesentry.rag.embedder import Embedder
from edgesentry.rag.vectorstore import VectorStore
from edgesentry.rag.retriever import Retriever
from edgesentry.agent.agent import Agent
from edgesentry.tasks.journaler import Journaler
from edgesentry.web.app import create_app

log = logging.getLogger("edgesentry")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="EdgeSentry — offline agentic RAG security.")
    p.add_argument(
        "--no-perception",
        action="store_true",
        help="Skip camera/Hailo; run web + agent against existing data only.",
    )
    p.add_argument("--config", default="config/config.yaml", help="Path to config YAML.")
    return p.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    )
    args = parse_args()
    cfg = load_config(args.config)

    # ── Shared singletons (one process, shared instances) ────────────────────
    store = EventStore(cfg)
    embedder = Embedder(cfg)
    vectors = VectorStore(cfg, embedder)
    retriever = Retriever(cfg, store, vectors)
    agent = Agent(cfg, retriever, store)

    # ── Perception → events → memory pipeline (optional) ─────────────────────
    if not args.no_perception:
        # Imported lazily so the Hailo runtime is only required when actually
        # running perception (keeps laptop/CI runs import-clean).
        from edgesentry.perception.camera import Camera
        from edgesentry.perception.detector import Detector
        from edgesentry.perception.reid import ReID
        from edgesentry.perception.zones import ZoneMap

        ingestor = EventIngestor(cfg, store, vectors)
        camera = Camera(cfg)
        detector = Detector(cfg)
        reid = ReID(cfg)
        zones = ZoneMap(cfg)

        def perception_loop() -> None:
            log.info("Perception loop started (Hailo NPU).")
            for frame in camera.frames():
                detections = detector.detect(frame)
                detections = reid.annotate(frame, detections)
                detections = zones.annotate(detections)
                ingestor.ingest(frame, detections)

        threading.Thread(target=perception_loop, daemon=True, name="perception").start()
    else:
        log.info("Running with --no-perception (web + agent only).")

    # ── Scheduled agentic journaler ──────────────────────────────────────────
    journaler = Journaler(cfg, retriever, agent, vectors)
    journaler.start()

    # ── Web server (blocks) ──────────────────────────────────────────────────
    app = create_app(cfg, agent=agent, store=store)
    app.run(host=cfg.web.host, port=cfg.web.port, threaded=True)


if __name__ == "__main__":
    main()
