#!/usr/bin/env bash
# Optional LTX-2.5 generate recipe. Expand ≠ generate.
# Live runtime is unverified in this repository until a local run is recorded.
set -euo pipefail

CHECKPOINT="${OMNI_LTX_CHECKPOINT:?Set OMNI_LTX_CHECKPOINT to the LTX-2.5 split root (models/ltx-2.5)}"
PROMPT="${PROMPT:?Set PROMPT to the rendered LTX paragraph}"
OUTPUT="${OUTPUT:-$PWD/outputs/ltx25.mp4}"
PYTHON_BIN="${PYTHON_BIN:-python}"
NUM_FRAMES="${NUM_FRAMES:-121}"
HEIGHT="${HEIGHT:-512}"
WIDTH="${WIDTH:-768}"
FRAME_RATE="${FRAME_RATE:-24}"
SEED="${SEED:-10}"

if [[ ! -d "$CHECKPOINT" ]]; then
  echo "LTX-2.5 checkpoint root not found: $CHECKPOINT" >&2
  exit 2
fi

TRANSFORMER="${CHECKPOINT}/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors"
TEXT_ENCODER="${CHECKPOINT}/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
VIDEO_VAE="${CHECKPOINT}/vae/ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE="${CHECKPOINT}/vae/ltx-2.5-audio-vae-bf16.safetensors"
UPSAMPLER="${CHECKPOINT}/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

for path in "$TRANSFORMER" "$TEXT_ENCODER" "$VIDEO_VAE" "$AUDIO_VAE" "$UPSAMPLER"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing official split file: $path" >&2
    exit 2
  fi
done

mkdir -p "$(dirname "$OUTPUT")"
CMD=(
  "$PYTHON_BIN" -m ltx_pipelines.distilled
  --transformer-path "$TRANSFORMER"
  --text-encoder-path "$TEXT_ENCODER"
  --video-vae-path "$VIDEO_VAE"
  --audio-vae-path "$AUDIO_VAE"
  --spatial-upsampler-path "$UPSAMPLER"
  --prompt "$PROMPT"
  --output-path "$OUTPUT"
  --num-frames "$NUM_FRAMES"
  --frame-rate "$FRAME_RATE"
  --height "$HEIGHT"
  --width "$WIDTH"
  --seed "$SEED"
)
if [[ -n "${OMNI_LTX_UPSTREAM:-}" ]]; then
  cd "$OMNI_LTX_UPSTREAM"
fi
exec "${CMD[@]}"
