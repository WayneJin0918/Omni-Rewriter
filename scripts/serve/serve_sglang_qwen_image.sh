#!/usr/bin/env bash
# Reference online endpoint for Qwen-Image-2512.
set -euo pipefail

MODEL="${OMNI_WRITER_IMAGE_MODEL:-${OMNI_REWRITER_IMAGE_MODEL:?Set OMNI_WRITER_IMAGE_MODEL (or OMNI_REWRITER_IMAGE_MODEL) to your local Qwen-Image checkpoint path}}"
HOST="${OMNI_WRITER_IMAGE_HOST:-${OMNI_REWRITER_IMAGE_HOST:-127.0.0.1}}"
PORT="${OMNI_WRITER_IMAGE_PORT:-${OMNI_REWRITER_IMAGE_PORT:-30020}}"
NUM_GPUS="${OMNI_WRITER_IMAGE_GPUS:-${OMNI_REWRITER_IMAGE_GPUS:-2}}"

# Requires an SGLang build whose diffusion registry contains Qwen-Image-2512.
exec sglang serve \
  --model-path "${MODEL}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --num-gpus "${NUM_GPUS}" \
  "$@"
