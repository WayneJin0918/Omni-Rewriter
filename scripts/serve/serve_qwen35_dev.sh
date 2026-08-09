#!/usr/bin/env bash
set -euo pipefail

MODEL="${OMNI_WRITER_MODEL:?Set OMNI_WRITER_MODEL to your local Qwen3.5 checkpoint path}"
SERVED_MODEL_NAME="${OMNI_WRITER_SERVED_MODEL_NAME:-Qwen/Qwen3.5-9B}"
HOST="${OMNI_WRITER_VLLM_HOST:-127.0.0.1}"
PORT="${OMNI_WRITER_VLLM_PORT:-8000}"
MAX_MODEL_LEN="${OMNI_WRITER_MAX_MODEL_LEN:-16384}"
TENSOR_PARALLEL_SIZE="${OMNI_WRITER_TENSOR_PARALLEL_SIZE:-1}"
GPU_MEMORY_UTILIZATION="${OMNI_WRITER_GPU_MEMORY_UTILIZATION:-0.90}"

exec vllm serve "${MODEL}" \
  --served-model-name "${SERVED_MODEL_NAME}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --trust-remote-code \
  --max-model-len "${MAX_MODEL_LEN}" \
  --tensor-parallel-size "${TENSOR_PARALLEL_SIZE}" \
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
  "$@"
