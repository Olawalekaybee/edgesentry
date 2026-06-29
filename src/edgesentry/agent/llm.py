"""Minimal Ollama chat client.

Talks to a local Ollama server over HTTP. Supports tool calling via Ollama's
OpenAI-compatible `tools` field, which Qwen2.5-Instruct models handle well. No
external SDK — just `requests` — to keep the dependency surface tiny on the Pi.
"""
from __future__ import annotations

import requests

from edgesentry.config import Config


class OllamaClient:
    def __init__(self, cfg: Config) -> None:
        self.host = cfg.agent.ollama_host.rstrip("/")
        self.model = cfg.agent.ollama_model
        self.temperature = cfg.agent.temperature

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Send a chat request; return the assistant message dict.

        The returned dict may contain `content` (text) and/or `tool_calls`
        (a list the agent loop will execute and feed back).
        """
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if tools:
            payload["tools"] = tools
        resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]

    def health(self) -> bool:
        try:
            requests.get(f"{self.host}/api/tags", timeout=5).raise_for_status()
            return True
        except requests.RequestException:
            return False
