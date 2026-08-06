#!/usr/bin/env bash
# Build low-res RAW vs PE gallery stills for the GitHub README.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP="$ROOT/experiments/t2va-base-15s-raw-vs-pe"
OUT="$ROOT/docs/assets/gallery"
mkdir -p "$OUT"
export PATH="${PATH}:/pfs/weiyang/Miniconda3/bin"

SCENES=(s01_dialogue s06_sneaker s09_noir s10_phone_call)
for sid in "${SCENES[@]}"; do
  raw="$EXP/videos/raw/${sid}.mp4"
  pe="$EXP/videos/pe/${sid}.mp4"
  [[ -f "$raw" && -f "$pe" ]] || { echo "skip missing $sid"; continue; }
  ffmpeg -y -hide_banner -loglevel error -ss 7 -i "$raw" -ss 7 -i "$pe" -filter_complex \
    "[0:v]scale=320:-2,setsar=1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=18:fontcolor=white:x=12:y=10:box=1:boxcolor=black@0.55[v0];[1:v]scale=320:-2,setsar=1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE':fontsize=18:fontcolor=white:x=12:y=10:box=1:boxcolor=black@0.55[v1];[v0][v1]hstack=inputs=2" \
    -frames:v 1 -update 1 -q:v 8 "$OUT/${sid}_raw_vs_pe.jpg"
done

ffmpeg -y -hide_banner -loglevel error \
  -i "$OUT/s01_dialogue_raw_vs_pe.jpg" \
  -i "$OUT/s06_sneaker_raw_vs_pe.jpg" \
  -i "$OUT/s09_noir_raw_vs_pe.jpg" \
  -i "$OUT/s10_phone_call_raw_vs_pe.jpg" \
  -filter_complex "vstack=inputs=4,scale=640:-2" -frames:v 1 -update 1 -q:v 10 \
  "$OUT/readme_hero_raw_vs_pe.jpg"

echo "Gallery written to $OUT"
ls -lh "$OUT"
