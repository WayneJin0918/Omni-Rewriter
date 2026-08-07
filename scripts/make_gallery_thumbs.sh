#!/usr/bin/env bash
# Build compact, unlabelled RAW and PE GIFs for the documentation gallery.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="$ROOT/experiments/t2va-base-15s-raw-vs-pe"
OUT="$ROOT/docs/assets/gallery"

FPS=8
WIDTH=360
DURATION=4
MAX_TOTAL_BYTES=$((16 * 1024 * 1024))

# Each entry is scenario:start_seconds. Starts favor representative motion or cuts.
SCENES=(
  "s01_dialogue:4"
  "s06_sneaker:8"
  "s09_noir:5"
  "s10_phone_call:6"
)

command -v ffmpeg >/dev/null || {
  echo "ffmpeg is required to build gallery GIFs" >&2
  exit 1
}

mkdir -p "$OUT"
total_bytes=0

for entry in "${SCENES[@]}"; do
  sid="${entry%%:*}"
  start="${entry##*:}"

  for arm in raw pe; do
    source="$EXP/videos/$arm/${sid}.mp4"
    target="$OUT/${sid}_${arm}.gif"
    [[ -f "$source" ]] || {
      echo "missing source video: $source" >&2
      exit 1
    }

    # Generate and consume a per-clip palette. Labels belong in HTML, not pixels.
    ffmpeg -y -hide_banner -loglevel error \
      -ss "$start" -t "$DURATION" -i "$source" \
      -filter_complex \
      "[0:v]fps=$FPS,scale=$WIDTH:-2:flags=lanczos,split[frames][palette_input];[palette_input]palettegen=max_colors=128:stats_mode=diff[palette];[frames][palette]paletteuse=dither=sierra2_4a:diff_mode=rectangle" \
      -an -loop 0 "$target"
    total_bytes=$((total_bytes + $(stat -c '%s' "$target")))
  done
done

# Remove the old composites, whose labels were burned into the JPEG pixels.
rm -f \
  "$OUT/s01_dialogue_raw_vs_pe.jpg" \
  "$OUT/s06_sneaker_raw_vs_pe.jpg" \
  "$OUT/s09_noir_raw_vs_pe.jpg" \
  "$OUT/s10_phone_call_raw_vs_pe.jpg" \
  "$OUT/readme_hero_raw_vs_pe.jpg"

if (( total_bytes > MAX_TOTAL_BYTES )); then
  echo "gallery GIFs total $total_bytes bytes; limit is $MAX_TOTAL_BYTES" >&2
  exit 1
fi

echo "Gallery written to $OUT ($total_bytes bytes total)"
ls -lh "$OUT"/*.gif
