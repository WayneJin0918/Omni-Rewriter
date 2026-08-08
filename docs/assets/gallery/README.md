# Gallery assets

Four-second, low-resolution GIF clips for RAW and prompt-expanded (PE) video
comparisons. The files contain no burned-in labels or side-by-side composites;
use HTML or Markdown labels around the separate assets.

Current homepage set favors the strongest complex camera / cut / dialogue PE-wins
from the published MiniMax-H3 pairs: concert crash-zoom (`s15`), kitchen whip-pan
(`s14`), and rooftop arc (`s13`).

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

Regenerate the GIFs from local demo videos (directory must contain `videos/raw/`
and `videos/pe/`):

```bash
OMNI_H3_DEMO_VIDEOS=/path/to/local-h3-demos scripts/make_gallery_thumbs.sh
```

The script uses per-clip `palettegen`/`paletteuse` processing and enforces a
16 MiB aggregate GIF limit. Do not commit full `.mp4` outputs; they are
gitignored.
