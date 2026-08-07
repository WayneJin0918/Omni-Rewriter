#!/usr/bin/env bash
# Reference OpenAI-compatible WAN video endpoint via vLLM-Omni.
set -euo pipefail

MODEL="${OMNI_REWRITER_WAN_MODEL:-/pfs/weiyang/Wan2.1-T2V-1.3B}"
HOST="${OMNI_REWRITER_VIDEO_HOST:-127.0.0.1}"
PORT="${OMNI_REWRITER_VIDEO_PORT:-30040}"

# vLLM-Omni is an optional runtime and is not installed by omni-rewriter.
# WAN family/version support must be checked against the selected vLLM-Omni release.
exec vllm serve "${MODEL}" \
  --omni \
  --host "${HOST}" \
  --port "${PORT}" \
  "$@"
