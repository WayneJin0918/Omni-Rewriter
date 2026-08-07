# Gallery assets

Four-second, low-resolution GIF clips for RAW and prompt-expanded (PE) video
comparisons. The files contain no burned-in labels or side-by-side composites;
use HTML or Markdown labels around the separate assets.

Current homepage set favors the strongest complex camera / cut / dialogue PE-wins
from the MiniMax-H3 15s stress scenarios (`s11–s16`): concert crash-zoom multicuts,
kitchen whip-pan montage, and rooftop arc proposal.

Exact asset paths:

- `docs/assets/gallery/s15_concert_crashzoom_raw.gif`
- `docs/assets/gallery/s15_concert_crashzoom_pe.gif`
- `docs/assets/gallery/s14_kitchen_stations_raw.gif`
- `docs/assets/gallery/s14_kitchen_stations_pe.gif`
- `docs/assets/gallery/s13_rooftop_orbit_raw.gif`
- `docs/assets/gallery/s13_rooftop_orbit_pe.gif`

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
