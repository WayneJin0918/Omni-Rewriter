#!/usr/bin/env bash
# Reference WAN endpoint via SGLang diffusion.
set -euo pipefail

MODEL="${OMNI_REWRITER_WAN_MODEL:-/pfs/weiyang/Wan2.1-T2V-1.3B}"
HOST="${OMNI_REWRITER_VIDEO_HOST:-127.0.0.1}"
PORT="${OMNI_REWRITER_VIDEO_PORT:-30040}"
NUM_GPUS="${OMNI_REWRITER_VIDEO_GPUS:-1}"

exec sglang serve \
  --model-path "${MODEL}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --num-gpus "${NUM_GPUS}" \
  "$@"
