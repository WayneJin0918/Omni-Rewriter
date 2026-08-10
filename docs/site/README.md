# Site assets and lean clones

The promotional H3 PE site lives under [`docs/day2-h3-pe/`](../day2-h3-pe/) on
`main` and is published from the `gh-pages` branch root to:

https://waynejin0918.github.io/Omni-Rewriter/

## What stays off `main`

Heavy RAW/PE demo GIFs are **not** tracked on `main`. They ship on `gh-pages`
under `assets/demos/` and are referenced from site HTML via relative
`assets/demos/<clip>.gif` paths (works for local preview and `gh-pages` root).

Also gitignored on `main`:

- `docs/day2-h3-pe/assets/demos/`
- `docs/h3-pe-showcase/thumbs/`
- `docs/promo/out/` (local assemble intermediates)
- `*.mp4` / other full video blobs

A small README gallery (`docs/assets/gallery/`, ~3 MiB of compact GIFs) stays on
`main` so GitHub README embeds keep working without Pages.

## Lean clone (recommended for contributors)

Partial clone + sparse checkout skips site demo trees if they reappear locally:

```bash
git clone --filter=blob:none --sparse https://github.com/WayneJin0918/Omni-Rewriter.git
cd Omni-Rewriter
git sparse-checkout set \
  '/*' \
  '!/docs/day2-h3-pe/assets/demos' \
  '!/docs/h3-pe-showcase/thumbs' \
  '!/docs/promo/out'
```

Notes:

- Deleting blobs from tip shrinks **future** clones of current `main`. Git
  history still contains older media until someone rewrites history (we do
  **not** rewrite/`force-push` by default).
- `--filter=blob:none` already avoids downloading blob contents until checkout
  needs them; sparse-checkout keeps unused paths out of the working tree.
- Promo mp4 and full demo sets belong on `gh-pages` (or local disks), not in
  source PRs.

## Optional local demos

If you need GIFs on disk for offline site preview:

```bash
git fetch origin gh-pages
git checkout origin/gh-pages -- assets/demos
mkdir -p docs/day2-h3-pe/assets
mv assets/demos docs/day2-h3-pe/assets/demos
rmdir assets 2>/dev/null || true
```

Or open the published Pages site once GitHub Pages is enabled for the repo.
