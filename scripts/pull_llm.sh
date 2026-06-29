#!/usr/bin/env bash
# Install Ollama (if needed) and pull the local LLM EdgeSentry uses.
# Runs on the Raspberry Pi 5. The 3B model is a good speed/quality balance on-CPU.
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen2.5:3b-instruct}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama…"
  curl -fsSL https://ollama.com/install.sh | sh
fi

echo "Pulling model: ${MODEL}"
ollama pull "${MODEL}"

echo "Done. Test it with:"
echo "  ollama run ${MODEL} \"Say hello in one short sentence.\""
