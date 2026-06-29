"""Alerting / action sinks.

    telegram.py  send a message to Telegram (reused from v1). Exposed to the
                 agent as the `send_alert` tool so the LLM can notify you when
                 you ask it to flag something.
"""
