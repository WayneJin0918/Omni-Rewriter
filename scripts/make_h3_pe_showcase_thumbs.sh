#!/usr/bin/env bash
# Build compact, unlabelled RAW/PE GIF thumbs for the H3 PE showcase page.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="${OMNI_H3_DEMO_VIDEOS:?Set OMNI_H3_DEMO_VIDEOS to a local dir with videos/raw and videos/pe}"
OUT="$ROOT/docs/h3-pe-showcase/thumbs"

FPS=6
WIDTH=280
DURATION=3.0
MAX_TOTAL_BYTES=$((16 * 1024 * 1024))

# scenario:start_seconds — pick a beat that shows the scenario's stress point.
SCENES=(
  "s01_dialogue:4"
  "s02_multilingual:2"
  "s03_wetland:3"
  "s04_cyclist:5"
  "s05_wok:6"
  "s06_sneaker:3"
  "s07_bowling:8"
  "s08_jazz:4"
  "s09_noir:5"
  # camera / cut stress set
  "s11_museum_reveal:6"
  "s12_alley_chase:4"
  "s13_rooftop_orbit:5"
  "s14_kitchen_stations:3"
  "s15_concert_crashzoom:2"
  "s19_fencing_duel:3"
)

command -v ffmpeg >/dev/null || {
  echo "ffmpeg is required to build showcase GIFs" >&2
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

    ffmpeg -y -hide_banner -loglevel error \
      -ss "$start" -t "$DURATION" -i "$source" \
      -filter_complex \
      "[0:v]fps=$FPS,scale=$WIDTH:-2:flags=lanczos,split[frames][palette_input];[palette_input]palettegen=max_colors=80:stats_mode=diff[palette];[frames][palette]paletteuse=dither=sierra2_4a:diff_mode=rectangle" \
      -an -loop 0 "$target"
    total_bytes=$((total_bytes + $(stat -c '%s' "$target")))
  done
done

if (( total_bytes > MAX_TOTAL_BYTES )); then
  echo "showcase GIFs total $total_bytes bytes; limit is $MAX_TOTAL_BYTES" >&2
  exit 1
fi

echo "Showcase thumbs written to $OUT ($total_bytes bytes total)"
ls -lh "$OUT"/*.gif
