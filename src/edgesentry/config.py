"""Typed configuration loader.

Reads `config/config.yaml`, layers `.env` / environment variables on top, and
exposes a single immutable `Config` object with dotted access (cfg.web.port).
Keeping config in one typed place means every module receives the same object
and there are no magic strings scattered around the codebase.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


# ── Section dataclasses (typed, so editors autocomplete cfg.<section>.<field>) ─

@dataclass(frozen=True)
class PerceptionCfg:
    camera_source: object
    detector_hef: str
    reid_hef: str
    confidence_threshold: float
    zones_file: str
    event_debounce_seconds: int


@dataclass(frozen=True)
class EventsCfg:
    db_path: str
    snapshot_dir: str
    keep_snapshots_days: int


@dataclass(frozen=True)
class RagCfg:
    embed_model: str
    vector_dir: str
    collection: str
    top_k: int


@dataclass(frozen=True)
class AgentCfg:
    ollama_host: str
    ollama_model: str
    max_tool_iterations: int
    temperature: float
    enabled_tools: list[str]


@dataclass(frozen=True)
class JournalerCfg:
    enabled: bool
    interval_minutes: int


@dataclass(frozen=True)
class WebCfg:
    host: str
    port: int
    title: str


@dataclass(frozen=True)
class TelegramCfg:
    bot_token: str
    chat_id: str


@dataclass(frozen=True)
class Config:
    app_name: str
    data_dir: str
    perception: PerceptionCfg
    events: EventsCfg
    rag: RagCfg
    agent: AgentCfg
    journaler: JournalerCfg
    web: WebCfg
    telegram: TelegramCfg


def load_config(path: str = "config/config.yaml") -> Config:
    """Load YAML, overlay environment, return a typed Config."""
    load_dotenv()  # reads .env if present
    raw = yaml.safe_load(Path(path).read_text())

    perception = PerceptionCfg(
        camera_source=raw["perception"]["camera_source"],
        detector_hef=raw["perception"]["detector_hef"],
        reid_hef=raw["perception"]["reid_hef"],
        confidence_threshold=float(raw["perception"]["confidence_threshold"]),
        zones_file=raw["perception"]["zones_file"],
        event_debounce_seconds=int(raw["perception"]["event_debounce_seconds"]),
    )
    events = EventsCfg(
        db_path=raw["events"]["db_path"],
        snapshot_dir=raw["events"]["snapshot_dir"],
        keep_snapshots_days=int(raw["events"]["keep_snapshots_days"]),
    )
    rag = RagCfg(
        embed_model=raw["rag"]["embed_model"],
        vector_dir=raw["rag"]["vector_dir"],
        collection=raw["rag"]["collection"],
        top_k=int(raw["rag"]["top_k"]),
    )
    agent = AgentCfg(
        ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct"),
        max_tool_iterations=int(raw["agent"]["max_tool_iterations"]),
        temperature=float(raw["agent"]["temperature"]),
        enabled_tools=list(raw["agent"]["enabled_tools"]),
    )
    journaler = JournalerCfg(
        enabled=bool(raw["tasks"]["journaler"]["enabled"]),
        interval_minutes=int(raw["tasks"]["journaler"]["interval_minutes"]),
    )
    web = WebCfg(
        host=os.getenv("WEB_HOST", "0.0.0.0"),
        port=int(os.getenv("WEB_PORT", "8000")),
        title=raw["web"]["title"],
    )
    telegram = TelegramCfg(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )

    return Config(
        app_name=raw["app"]["name"],
        data_dir=raw["app"]["data_dir"],
        perception=perception,
        events=events,
        rag=rag,
        agent=agent,
        journaler=journaler,
        web=web,
        telegram=telegram,
    )
