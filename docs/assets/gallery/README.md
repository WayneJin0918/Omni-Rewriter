# Gallery assets

Four-second, low-resolution GIF clips for RAW and prompt-expanded (PE) video
comparisons. The files contain no burned-in labels or side-by-side composites;
use HTML or Markdown labels around the separate assets.

Exact asset paths:

- `docs/assets/gallery/s01_dialogue_raw.gif`
- `docs/assets/gallery/s01_dialogue_pe.gif`
- `docs/assets/gallery/s06_sneaker_raw.gif`
- `docs/assets/gallery/s06_sneaker_pe.gif`
- `docs/assets/gallery/s09_noir_raw.gif`
- `docs/assets/gallery/s09_noir_pe.gif`
- `docs/assets/gallery/s10_phone_call_raw.gif`
- `docs/assets/gallery/s10_phone_call_pe.gif`

The standalone comparison page is `docs/assets/gallery/index.html`.

Regenerate the GIFs from the gitignored experiment videos with:

```bash
scripts/make_gallery_thumbs.sh
```

The script uses per-clip `palettegen`/`paletteuse` processing and enforces a
16 MiB aggregate GIF limit. Do not commit full `.mp4` outputs; they are
gitignored.
