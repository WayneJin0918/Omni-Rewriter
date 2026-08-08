# H3 PE showcase

In-repo demo grid for Omni-Rewriter's MiniMax-H3 prompt-expansion profile
(all published pairs, compact layout).

- Open [`index.html`](index.html) locally.
- **H3 PE promotional site:** [`../day2-h3-pe/`](../day2-h3-pe/) and
  https://waynejin0918.github.io/Omni-Rewriter/ (served from the `gh-pages`
  branch when GitHub Pages is enabled).
- Low-res RAW vs PE GIF thumbs live in `thumbs/` (no full `.mp4` blobs).
- Regenerate thumbs from the gitignored experiment videos:

```bash
scripts/make_h3_pe_showcase_thumbs.sh
```

Published pairs: **14** from `experiments/t2va-base-15s-raw-vs-pe/`
(`s01–s09`, `s11–s15`; dropped weak `s10` phone-call and `s16` train match-cut),
including the camera/cut stress set (`s11–s15`).

Homepage highlights the best three stress demos (concert crash-zoom, kitchen
whip-pan, rooftop arc) in `docs/assets/gallery/`.
