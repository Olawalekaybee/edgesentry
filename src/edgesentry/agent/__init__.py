"""Agent layer — the local LLM that reasons over events and acts.

    llm.py      minimal Ollama HTTP client (chat + tool calling)
    tools.py    the tools the agent may call (search memory, query facts, alert)
    prompts.py  the system prompt that defines the agent's role and rules
    agent.py    the orchestration loop: prompt → maybe call tools → final answer

The agent runs entirely on the Pi's CPU via Ollama. It decides *which* store to
consult: the vector memory for fuzzy questions, the SQLite logs for exact counts.
"""
