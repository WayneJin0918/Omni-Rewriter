#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_ROOT="${LINGBOT_VIDEO_ROOT:?Set LINGBOT_VIDEO_ROOT to your local lingbot-video checkout}"
MODEL_DIR="${MODEL_DIR:?Set MODEL_DIR to your local LingBot video checkpoint directory}"
PROMPT_JSON="${PROMPT_JSON:-$UPSTREAM_ROOT/assets/cases/t2v/example_1/prompt.json}"
OUTPUT="${OUTPUT:-$PWD/outputs/lingbot-video.mp4}"
BACKEND="${BACKEND:-diffusers}"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ "$BACKEND" != "diffusers" && "$BACKEND" != "sglang" ]]; then
  echo "BACKEND must be diffusers or sglang." >&2
  exit 2
fi
if [[ ! -f "$UPSTREAM_ROOT/scripts/inference.py" ]]; then
  echo "LingBot inference script not found under: $UPSTREAM_ROOT" >&2
  exit 2
fi
if [[ ! -d "$MODEL_DIR" ]]; then
  echo "LingBot model checkpoint not found: $MODEL_DIR" >&2
  exit 2
fi
if [[ ! -f "$PROMPT_JSON" ]]; then
  echo "LingBot structured caption not found: $PROMPT_JSON" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"
cd "$UPSTREAM_ROOT"
exec "$PYTHON_BIN" scripts/inference.py \
  --backend "$BACKEND" \
  --model_dir "$MODEL_DIR" \
  --mode t2v \
  --prompt_json "$PROMPT_JSON" \
  --output "$OUTPUT" \
  --height "${HEIGHT:-480}" \
  --width "${WIDTH:-832}" \
  --steps "${STEPS:-40}" \
  --guidance_scale "${GUIDANCE_SCALE:-3}" \
  --shift "${SHIFT:-3}" \
  --seed "${SEED:-42}" \
  --fps "${FPS:-24}" \
  --transformer_dtype bf16 \
  --text_encoder_dtype bf16 \
  --vae_dtype fp32
