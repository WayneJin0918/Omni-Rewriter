# Source vs Omni-Rewriter

Promo thumbs for video reconstruct. Each GIF is a **labeled left/right composite**:
left **Source**, right **Omni-Rewriter**. Compare uses the first 10s of each clip.
Expand ≠ generate. Public MiniMax-H3 generate stays on the integer 4–15s window.
Do not commit full `.mp4` files.

Exact GIF paths:

- `h3_t2va_10s_compare.gif`
- `h3_cinematic_15s_compare.gif`
- `seedance_ornithopter_20s_compare.gif`
- `h3_montage_40s_compare.gif`

Labeled mp4s and the concatenated 10s reel (gitignored):

```text
outputs/reconstruct-demo/compare/*_source_vs_h3_omni_replay.mp4
outputs/reconstruct-demo/compare/source_vs_omni_rewriter_10s_reel.mp4
```

Regenerate:

```bash
PYTHONPATH=src python scripts/promo/build_reconstruct_cards.py
```
