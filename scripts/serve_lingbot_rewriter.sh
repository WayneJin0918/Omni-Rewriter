#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
BASE_MODEL="${REWRITER_BASE_MODEL:?Set REWRITER_BASE_MODEL to your local writer checkpoint path}"
ADAPTER="${REWRITER_ADAPTER:?Set REWRITER_ADAPTER to your LingBot rewriter LoRA directory}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-31000}"
TP_SIZE="${TP_SIZE:-1}"

if [[ ! -d "$BASE_MODEL" ]]; then
  echo "Rewriter base checkpoint not found: $BASE_MODEL" >&2
  exit 2
fi
if [[ ! -f "$ADAPTER/adapter_config.json" ]]; then
  echo "LingBot rewriter adapter not found: $ADAPTER" >&2
  exit 2
fi

# Requests with model=lingbot-expand use the unmodified base model.
# Requests with model=lingbot-map select the loaded LingBot mapping LoRA.
exec "$PYTHON_BIN" -m sglang.launch_server \
  --model-path "$BASE_MODEL" \
  --served-model-name lingbot-expand \
  --lora-paths "lingbot-map=$ADAPTER" \
  --host "$HOST" \
  --port "$PORT" \
  --tp-size "$TP_SIZE"
