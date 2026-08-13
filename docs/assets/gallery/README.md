# Gallery assets

Four-second, low-resolution GIF clips for RAW and prompt-expanded (PE) video
comparisons. The files contain no burned-in labels or side-by-side composites;
use HTML or Markdown labels around the separate assets.

Current README set is the same three PE-win pairs as the site demos (concert
`s15`, kitchen `s14`, rooftop `s13`), kept as compact GIFs on `main` (~3 MiB)
so README embeds work without cloning the full site demo set.

Exact asset paths:

- `docs/assets/gallery/s15_concert_crashzoom_raw.gif`
- `docs/assets/gallery/s15_concert_crashzoom_pe.gif`
- `docs/assets/gallery/s14_kitchen_stations_raw.gif`
- `docs/assets/gallery/s14_kitchen_stations_pe.gif`
- `docs/assets/gallery/s13_rooftop_orbit_raw.gif`
- `docs/assets/gallery/s13_rooftop_orbit_pe.gif`

The fuller site grids load demos from GitHub Pages
(`https://waynejin0918.github.io/Omni-Rewriter/assets/demos/`); see
[`docs/site/README.md`](../../site/README.md).

The standalone comparison page is `docs/assets/gallery/index.html`.
Reconstruct SOURCE vs REPLAY thumbs live in `docs/assets/gallery/reconstruct/`.
For the fuller public landing page (pipeline + all published pairs), see
`docs/h3-pe-showcase/index.html`.

Regenerate the GIFs from local demo videos (directory must contain `videos/raw/`
and `videos/pe/`):

```bash
OMNI_H3_DEMO_VIDEOS=/path/to/local-h3-demos scripts/make_gallery_thumbs.sh
```

The script uses per-clip `palettegen`/`paletteuse` processing and enforces a
16 MiB aggregate GIF limit. Do not commit full `.mp4` outputs; they are
gitignored.
