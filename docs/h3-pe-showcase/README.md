# H3 PE showcase

In-repo demo grid for Omni-Rewriter's MiniMax-H3 prompt-expansion profile
(all published pairs, compact layout).

- Open [`index.html`](index.html) locally.
- **H3 PE promotional site:** [`../day2-h3-pe/`](../day2-h3-pe/) and
  https://waynejin0918.github.io/Omni-Rewriter/ (served from the `gh-pages`
  branch when GitHub Pages is enabled).
- Low-res RAW vs PE GIF thumbs live in `thumbs/` (no full `.mp4` blobs).
- To regenerate thumbs from local videos, set `OMNI_H3_DEMO_VIDEOS` to a directory
  that contains `videos/raw/` and `videos/pe/`, then run:

```bash
OMNI_H3_DEMO_VIDEOS=/path/to/local-h3-demos scripts/make_h3_pe_showcase_thumbs.sh
```

Published pairs: **15** (`s01–s09`, `s11–s15`, `s19`).

Homepage highlights the best three stress demos (concert crash-zoom, kitchen
whip-pan, rooftop arc) in `docs/assets/gallery/`.
