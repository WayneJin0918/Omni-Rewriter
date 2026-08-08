#!/usr/bin/env bash
# Reference HunyuanImage-3.0 server. This requires Tencent's documented vLLM fork.
set -euo pipefail

MODEL="${OMNI_WRITER_HUNYUAN_MODEL:-${OMNI_REWRITER_HUNYUAN_MODEL:?Set OMNI_WRITER_HUNYUAN_MODEL (or OMNI_REWRITER_HUNYUAN_MODEL) to your local HunyuanImage-3.0 checkpoint path}}"
HOST="${OMNI_WRITER_HUNYUAN_HOST:-${OMNI_REWRITER_HUNYUAN_HOST:-127.0.0.1}}"
PORT="${OMNI_WRITER_HUNYUAN_PORT:-${OMNI_REWRITER_HUNYUAN_PORT:-30030}}"
TP="${OMNI_WRITER_HUNYUAN_TP:-${OMNI_REWRITER_HUNYUAN_TP:-8}}"

export VLLM_ENABLE_HUNYUAN_IMAGE3_TASK=1
export MULTI_MODA_SAVE_PATH="${MULTI_MODA_SAVE_PATH:-/tmp/hunyuan_image3/png}"

exec vllm serve "${MODEL}" \
  --trust-remote-code \
  --served-model-name vllm_hunyuan_image3 \
  --host "${HOST}" \
  --port "${PORT}" \
  --max-model-len 10000 \
  --gpu-memory-utilization 0.6 \
  --no-enable-prefix-caching \
  --no-enable-chunked-prefill \
  --max-num-batched-tokens 10000 \
  --max-num-seqs 1 \
  --enforce-eager \
  --trust-request-chat-template \
  --tensor-parallel-size "${TP}" \
  "$@"
