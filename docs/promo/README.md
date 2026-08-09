# Omni-Rewriter promo pipeline

Warm, card-forward product film. **H3 generate is optional and separate from expand.**

## Story map

1. **Intro** (`t2va`) — messy prompt → Analyze/Draft/Validate/Repair/Render cards
2. **Proof** — refined RAW|PE cards (concert → kitchen → marathon) with **PE audio**
3. **Models** — short designed **finale**: bridge → Omni-Rewriter hero → staggered
   T2V|T2I list ([`model_matrix.yaml`](model_matrix.yaml), **no Seedance**; no hanging B-roll)
4. **End** — `github.com/WayneJin0918/Omni-Rewriter`

Target cut about **30–35s** (`designed_finale` + clean PE card fix). Soft crossfades only.
Do not commit full `.mp4` outputs. Keep `docs/promo/out/` free of `regen/` / `qa_*` / `work*` dumps.

## Scripts

| Script | Purpose |
| --- | --- |
| [`scripts/promo/submit_h3_chunk.py`](../../scripts/promo/submit_h3_chunk.py) | Submit a PE envelope to H3 |
| [`scripts/promo/build_proof_cards.py`](../../scripts/promo/build_proof_cards.py) | RAW\|PE cards + PE audio |
| [`scripts/promo/build_models_finale.py`](../../scripts/promo/build_models_finale.py) | Designed models finale |
| [`scripts/promo/build_models_brand_card.py`](../../scripts/promo/build_models_brand_card.py) | Legacy brand card |
| [`scripts/promo/submit_h3_batch.py`](../../scripts/promo/submit_h3_batch.py) | Multi-seed H3 regen (8-GPU node) |
| [`scripts/promo/burn_names_on_slats.py`](../../scripts/promo/burn_names_on_slats.py) | Legacy slat name burn |
| [`scripts/promo/build_model_plates.py`](../../scripts/promo/build_model_plates.py) | Optional still plates |
| [`scripts/promo/assemble_promo.py`](../../scripts/promo/assemble_promo.py) | Soft-xfade final cut |

Agent skill: [`.cursor/skills/omni-rewriter-promo-pipeline/SKILL.md`](../../.cursor/skills/omni-rewriter-promo-pipeline/SKILL.md).

## Quick assemble (after local generates exist)

```bash
python scripts/promo/build_models_finale.py \
  --atmosphere docs/promo/out/v6/chunk_a_intro.mp4 \
  --out-dir docs/promo/out/v6/plates/finale \
  --out-finale docs/promo/out/v6/models_finale.mp4
python scripts/promo/assemble_promo.py \
  --intro docs/promo/out/v6/chunk_a_intro.mp4 \
  --proof docs/promo/out/v6/proof_0.mp4 docs/promo/out/v6/proof_1.mp4 docs/promo/out/v6/proof_2.mp4 \
  --models-finale docs/promo/out/v6/models_finale.mp4 \
  --work-dir docs/promo/out/v6/work \
  --out docs/promo/out/v6/omni_rewriter_promo_v6.mp4
```

## PE fixtures

- `omni_promo_chunk_a_messy.json` — intro (also models atmosphere)
- `omni_promo_chunk_b_ship.json` — legacy hanging-board (not in default cut)
- `s17_city_marathon_raw.json` / `s17_city_marathon_pe.json` — marathon proof pair
