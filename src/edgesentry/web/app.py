"""Flask application factory."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from edgesentry.agent.agent import Agent
from edgesentry.config import Config
from edgesentry.events.store import EventStore
from edgesentry.web.routes import register_routes


def create_app(cfg: Config, agent: Agent, store: EventStore) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)

    # Stash shared singletons on the app so routes can reach them.
    app.config["ES_CFG"] = cfg
    app.config["ES_AGENT"] = agent
    app.config["ES_STORE"] = store

    register_routes(app)
    return app
