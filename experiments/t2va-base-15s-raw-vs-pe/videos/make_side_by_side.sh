#!/usr/bin/env bash
set -euo pipefail

echo "[s01_dialogue] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s01_dialogue.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s01_dialogue.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s01_dialogue.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s01_dialogue_raw_vs_pe.mp4"

echo "[s02_multilingual] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s02_multilingual.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s02_multilingual.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s02_multilingual.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s02_multilingual_raw_vs_pe.mp4"

echo "[s03_wetland] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s03_wetland.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s03_wetland.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s03_wetland.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s03_wetland_raw_vs_pe.mp4"

echo "[s04_cyclist] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s04_cyclist.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s04_cyclist.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s04_cyclist.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s04_cyclist_raw_vs_pe.mp4"

echo "[s05_wok] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s05_wok.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s05_wok.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s05_wok.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s05_wok_raw_vs_pe.mp4"

echo "[s06_sneaker] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s06_sneaker.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s06_sneaker.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s06_sneaker.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s06_sneaker_raw_vs_pe.mp4"

echo "[s07_bowling] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s07_bowling.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s07_bowling.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s07_bowling.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s07_bowling_raw_vs_pe.mp4"

echo "[s08_jazz] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s08_jazz.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s08_jazz.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s08_jazz.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s08_jazz_raw_vs_pe.mp4"

echo "[s09_noir] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s09_noir.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s09_noir.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s09_noir.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s09_noir_raw_vs_pe.mp4"

echo "[s10_phone_call] rebuilding comparison"
ffmpeg -y -hide_banner -loglevel error \
  -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/raw/s10_phone_call.mp4" -i "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/pe/s10_phone_call.mp4" \
  -filter_complex "\
[0:v]drawbox=x=16:y=16:w=110:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='RAW':fontsize=28:fontcolor=white:x=34:y=24[v0];\
[1:v]drawbox=x=16:y=16:w=320:h=46:color=black@0.65:t=fill,\
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PE  Omni-Writer':fontsize=28:fontcolor=white:x=34:y=24[v1];\
[v0][v1]hstack=inputs=2[main];\
[main]pad=iw:ih+168:0:0:black[padded];\
[padded]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/_prompt_bars/s10_phone_call.txt':fontsize=26:fontcolor=white:\
x=24:y=h-168+28:line_spacing=8[vout];\
[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,volume=1.2[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 32000 -ac 2 \
  -shortest -movflags +faststart \
  "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s10_phone_call_raw_vs_pe.mp4"

echo "Done -> /pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side"
ls -lh "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side"/*.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "/pfs/weiyang/Omni-Writer/experiments/t2va-base-15s-raw-vs-pe/videos/side_by_side/s01_dialogue_raw_vs_pe.mp4"
