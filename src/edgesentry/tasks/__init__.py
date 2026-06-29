"""Scheduled agentic tasks.

    journaler.py  every hour, summarise new events into a single 'journal'
                  memory and store it back in the vector DB. Over time this gives
                  the agent a compressed long-term memory instead of thousands of
                  raw rows — the agentic 'self-review' behaviour.
"""
