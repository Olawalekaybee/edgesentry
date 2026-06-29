"""Journaler — the agentic self-review task.

On a schedule (default hourly) it pulls the last hour of events, asks the agent
to summarise them into one paragraph, and writes that paragraph back into the
vector store as a `journal` memory. This is what turns EdgeSentry from a Q&A bot
into something that maintains its own evolving long-term memory.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from edgesentry.agent.agent import Agent
from edgesentry.config import Config
from edgesentry.events.models import Event
from edgesentry.rag.retriever import Retriever
from edgesentry.rag.vectorstore import VectorStore

log = logging.getLogger(__name__)


class Journaler:
    def __init__(
        self,
        cfg: Config,
        retriever: Retriever,
        agent: Agent,
        vectors: VectorStore,
    ) -> None:
        self.cfg = cfg
        self.retriever = retriever
        self.agent = agent
        self.vectors = vectors
        self.interval = cfg.journaler.interval_minutes
        self.enabled = cfg.journaler.enabled
        self._scheduler = BackgroundScheduler(daemon=True)

    def start(self) -> None:
        if not self.enabled:
            log.info("Journaler disabled in config.")
            return
        self._scheduler.add_job(
            self.run_once,
            "interval",
            minutes=self.interval,
            id="journaler",
        )
        self._scheduler.start()
        log.info("Journaler scheduled every %d minutes.", self.interval)

    def run_once(self) -> str:
        """Summarise the last interval of events and store it as a memory."""
        sentences = self.retriever.recent(minutes=self.interval)
        summary = self.agent.summarise(sentences)
        journal = Event(kind="journal", text=summary)
        self.vectors.add(journal)
        log.info("Journal entry stored: %s", summary)
        return summary
