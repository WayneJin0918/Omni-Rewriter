# H3 PE site (entry + home)

Promotional site for Omni-Rewriter’s MiniMax-H3 prompt-expansion instance
(rose / pink visual theme).

## Pages

| File | Role |
| --- | --- |
| [`index.html`](index.html) | **Entry** — full-bleed promo demo, then CTA into the main site |
| [`home.html`](home.html) | **Main homepage** — interactive PE pipeline + RAW/PE grid |
| [`assets/promo/`](assets/promo/) | Poster + promo mp4 (mp4 is gitignored on `main`; copy when syncing `gh-pages`) |

## Local preview

```bash
# from repo root — ensure the web mp4 exists
cp docs/promo/out/v6/omni_rewriter_promo_v6.mp4 \
  docs/day2-h3-pe/assets/promo/omni_rewriter_promo.mp4
# or re-encode smaller:
# ffmpeg -i docs/promo/out/v6/omni_rewriter_promo_v6.mp4 -vf scale=1280:-2 \
#   -c:v libx264 -b:v 2200k -c:a aac -b:a 128k -movflags +faststart \
#   docs/day2-h3-pe/assets/promo/omni_rewriter_promo.mp4

python -m http.server 8765 --directory docs/day2-h3-pe
# open http://127.0.0.1:8765/
```

## Deploy (`gh-pages`)

GitHub Pages: https://waynejin0918.github.io/Omni-Rewriter/

After edits on `main`, sync **this directory** to the `gh-pages` branch **root** and push.
Include `assets/promo/omni_rewriter_promo.mp4` on `gh-pages` even though `*.mp4` is ignored on `main`.

Source: https://github.com/WayneJin0918/Omni-Rewriter
