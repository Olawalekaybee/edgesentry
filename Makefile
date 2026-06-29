# EdgeSentry — convenience commands.
# Run `make help` to see everything.

.DEFAULT_GOAL := help
PYTHON := python

.PHONY: help install llm seed run run-web test lint clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies
	pip install -r requirements.txt

llm:  ## Pull the local LLM via Ollama
	bash scripts/pull_llm.sh

seed:  ## Seed the event store + vector DB with demo data
	$(PYTHON) scripts/seed_demo_data.py

run:  ## Run the full system (perception + web + agent)
	$(PYTHON) -m edgesentry

run-web:  ## Run web + agent only, no camera/Hailo (laptop dev)
	$(PYTHON) -m edgesentry --no-perception

test:  ## Run unit tests (hardware-independent, CI-safe)
	pytest -q

clean:  ## Remove caches and runtime data
	rm -rf .pytest_cache __pycache__ src/**/__pycache__ data/ .coverage htmlcov
