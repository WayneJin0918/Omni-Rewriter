#!/usr/bin/env bash
# Reference WAN endpoint via SGLang diffusion.
set -euo pipefail

MODEL="${OMNI_WRITER_WAN_MODEL:-${OMNI_REWRITER_WAN_MODEL:?Set OMNI_WRITER_WAN_MODEL (or OMNI_REWRITER_WAN_MODEL) to your local WAN checkpoint path}}"
HOST="${OMNI_WRITER_VIDEO_HOST:-${OMNI_REWRITER_VIDEO_HOST:-127.0.0.1}}"
PORT="${OMNI_WRITER_VIDEO_PORT:-${OMNI_REWRITER_VIDEO_PORT:-30040}}"
NUM_GPUS="${OMNI_WRITER_VIDEO_GPUS:-${OMNI_REWRITER_VIDEO_GPUS:-1}}"

exec sglang serve \
  --model-path "${MODEL}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --num-gpus "${NUM_GPUS}" \
  "$@"
