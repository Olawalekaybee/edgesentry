# Models

Model weights are **not** committed to git (they are large and license-bound).
This file explains how to obtain each one. After following the steps, this folder
should contain:

```
models/
├── yolov8n.hef          # person detector, compiled for Hailo-8L  (from v1)
├── reid_resnet.hef      # ReID embedding model, compiled for Hailo-8L (from v1)
└── (the LLM lives in Ollama, not here)
```

## 1. Vision models (`.hef`) — from v1

These come straight from your **Pi5 Edge AI Security Monitor**:

1. Start from the ONNX exports of YOLOv8n and your ReID ResNet.
2. Compile them to Hailo-8L `.hef` with the Hailo Dataflow Compiler. See
   [`scripts/convert_onnx_to_hef.sh`](../scripts/convert_onnx_to_hef.sh) and
   `docs/architecture.md`.
3. Drop the resulting `yolov8n.hef` and `reid_resnet.hef` here. Paths are set in
   `config/config.yaml`.

## 2. Embedding model (RAG) — auto-downloaded

`sentence-transformers/all-MiniLM-L6-v2` is fetched automatically on first run
and cached by `sentence-transformers`. No manual step needed.

## 3. LLM — managed by Ollama

The agent's LLM is pulled and served by Ollama, not stored in this folder:

```bash
bash scripts/pull_llm.sh   # pulls qwen2.5:3b-instruct by default
```
