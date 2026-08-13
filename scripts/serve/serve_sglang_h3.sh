#!/usr/bin/env bash
# Serve MiniMax-H3 (FL2VA / ~30B-class) via SGLang diffusion for optional generate.
# Expand stays on the Writer endpoint; point OMNI_WRITER_H3_BASE_URL here after ready.
set -euo pipefail

MODEL="${OMNI_WRITER_H3_MODEL:?Set OMNI_WRITER_H3_MODEL to your MiniMax-H3 FL2VA checkpoint path}"
HOST="${OMNI_WRITER_H3_HOST:-127.0.0.1}"
PORT="${OMNI_WRITER_H3_PORT:-30010}"
NUM_GPUS="${OMNI_WRITER_H3_NUM_GPUS:-8}"
ULYSSES="${OMNI_WRITER_H3_ULYSSES_DEGREE:-${NUM_GPUS}}"
PERF="${OMNI_WRITER_H3_PERFORMANCE_MODE:-speed}"

# Prefer `sglang serve` when present; fall back to python -m entry.
# Stock SGLang diffusion infers FL2VA from the checkpoint; --model-variant is a fork flag.
if command -v sglang >/dev/null 2>&1; then
  exec sglang serve \
    --model-path "${MODEL}" \
    --model-type diffusion \
    --num-gpus "${NUM_GPUS}" \
    --ulysses-degree "${ULYSSES}" \
    --performance-mode "${PERF}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --trust-remote-code \
    "$@"
fi

exec python -m sglang.cli.main serve \
  --model-path "${MODEL}" \
  --model-type diffusion \
  --num-gpus "${NUM_GPUS}" \
  --ulysses-degree "${ULYSSES}" \
  --performance-mode "${PERF}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --trust-remote-code \
  "$@"
