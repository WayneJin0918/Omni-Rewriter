# Gallery assets

Four-second, low-resolution GIF clips for RAW and prompt-expanded (PE) video
comparisons. The files contain no burned-in labels or side-by-side composites;
use HTML or Markdown labels around the separate assets.

Current homepage set favors the strongest PE-win scenarios from the 15s H3 base
experiment (VLM pairwise + visual review): bilingual kitchen dialogue, wok action
sync, neon cyclist, and rainy bus-stop dialogue.

Exact asset paths:

- `docs/assets/gallery/s02_multilingual_raw.gif`
- `docs/assets/gallery/s02_multilingual_pe.gif`
- `docs/assets/gallery/s05_wok_raw.gif`
- `docs/assets/gallery/s05_wok_pe.gif`
- `docs/assets/gallery/s04_cyclist_raw.gif`
- `docs/assets/gallery/s04_cyclist_pe.gif`
- `docs/assets/gallery/s01_dialogue_raw.gif`
- `docs/assets/gallery/s01_dialogue_pe.gif`

The standalone comparison page is `docs/assets/gallery/index.html`.
For the fuller public landing page (pipeline + all published pairs), see
`docs/h3-pe-showcase/index.html`.

Regenerate the GIFs from the gitignored experiment videos with:

```bash
scripts/make_gallery_thumbs.sh
```

The script uses per-clip `palettegen`/`paletteuse` processing and enforces a
16 MiB aggregate GIF limit. Do not commit full `.mp4` outputs; they are
gitignored.
