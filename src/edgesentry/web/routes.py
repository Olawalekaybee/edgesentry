"""HTTP routes.

The key v2 route is POST /api/chat: it forwards the user's natural-language
question to the Agent and returns the answer as JSON. /api/events exposes recent
history for the dashboard table.
"""
from __future__ import annotations

import logging

from flask import Flask, current_app, jsonify, render_template, request

log = logging.getLogger(__name__)


def register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        cfg = current_app.config["ES_CFG"]
        return render_template("index.html", title=cfg.web.title)

    @app.post("/api/chat")
    def chat():
        agent = current_app.config["ES_AGENT"]
        data = request.get_json(silent=True) or {}
        question = (data.get("message") or "").strip()
        if not question:
            return jsonify({"error": "empty message"}), 400
        try:
            answer = agent.ask(question)
        except Exception as exc:  # never 500 the UI; surface a clean message
            log.exception("Agent error")
            return jsonify({"error": f"agent error: {exc}"}), 502
        return jsonify({"answer": answer})

    @app.get("/api/events")
    def events():
        store = current_app.config["ES_STORE"]
        limit = int(request.args.get("limit", 50))
        rows = store.query(limit=limit)
        return jsonify([
            {
                "ts": e.ts.isoformat(),
                "person_id": e.person_id,
                "zone": e.zone,
                "kind": e.kind,
                "text": e.to_sentence(),
            }
            for e in rows
        ])

    @app.get("/api/health")
    def health():
        agent = current_app.config["ES_AGENT"]
        return jsonify({"llm_ok": agent.llm.health()})
