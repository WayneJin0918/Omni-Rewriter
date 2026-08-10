---
name: omni-rewriter-promo-pipeline
description: >-
  Build Omni-Rewriter promo films: validated H3 PE chunks, RAW vs PE proof
  cards with PE audio, designed models finale, and soft-xfade assemble.
  Use when making or regenerating docs/promo media, promo scripts, or agent
  workflows that mirror the maintainer promo pipeline.
---

# Omni-Rewriter promo pipeline

## Mission

Reproduce the maintainer promo workflow: **expand (PE) → generate (H3) → proof cards →
designed finale → assemble**. Expand is not generate. Do not commit full `.mp4` files.

## Hard rules

1. Video tasks require `duration_seconds`; validate with `BaseRewrite` before submit.
2. Promo model matrix **excludes Seedance** (`docs/promo/model_matrix.yaml`).
3. Include roadmap models (`wanted` / `unverified` / `adapter`) honestly—never claim PE for them.
4. No chapter bumpers (`01/02/03`). Soft crossfades only.
5. Never burn VO/dialogue as corner subtitles; quote on-screen product text exactly.
6. Proof audio comes from the **PE** arm only.
7. Models act = short designed **finale** (`build_models_finale.py`): bridge → brand hero →
   staggered T2V|T2I lanes, **one continuous audio bed**. No H3 hanging-board B-roll; no
   slat-glued names. Target full film about **30–35s**. Keep still-plate motion tiny (no sway).
8. After H3 intro, run `fix_intro_pe_card.py` so the PE close-up uses a clean designed card
   (H3 often garbles PE body text).
9. Prefer intro freeze as atmosphere; keep both T2V and T2I named in the lanes beat.
10. Assemble regenerates each outgoing tail as a **designed hold** from the last frame
    (blur/vignette/accent — not raw `tpad` clone) so dialogue survives `acrossfade` and the
    gap still looks intentional.
11. Outro CTA voice: prefer **H3 15s take** with the same warm narrator (S1) + pluck BGM as the
    intro (`omni_promo_outro_vo.json`), then **clip** the usable window (e.g. 0.35–~10s) into
    `build_outro_audio.py --vo-audio … --bgm-vol 0` → `outro_full.mp4` → assemble `--no-endcard`.
    Edge-TTS is fallback only when H3 is unavailable.

## Layout

| Path | Role |
| --- | --- |
| `docs/promo/*.json` | PE envelopes (`request` + `output`) |
| `docs/promo/model_matrix.yaml` | Canonical T2V/T2I names + status |
| `scripts/promo/submit_h3_chunk.py` | Submit one envelope to H3 |
| `scripts/promo/submit_h3_batch.py` | Multi-seed H3 regen on the 8-GPU node |
| `scripts/promo/build_proof_cards.py` | RAW\|PE cards + PE audio |
| `scripts/promo/fix_intro_pe_card.py` | Replace garbled H3 PE close-up with clean card |
| `scripts/promo/build_models_finale.py` | Designed models finale (bridge/brand/lanes) |
| `scripts/promo/assemble_promo.py` | Soft-xfade final film |
| `scripts/promo/build_models_brand_card.py` | Legacy brand card (not default cut) |
| `scripts/promo/burn_names_on_slats.py` | Legacy slat name burn (not default cut) |
| `docs/promo/out/` | Local outputs (gitignored `*.mp4`) |
| `docs/day2-h3-pe/` | Site: promo entry → `home.html` |

## Procedure

### 1. Author / refresh PE

- Intro: edit `docs/promo/omni_promo_chunk_a_messy.json`.
- Validate:

```bash
PYTHONPATH=src python -c "from omni_rewriter.models import BaseRewrite, RewriteRequest; import json; \
p=json.load(open('docs/promo/omni_promo_chunk_a_messy.json')); \
RewriteRequest.model_validate(p['request']); BaseRewrite.model_validate(p['output']); print('ok')"
```

- For H3 grammar details, follow `.cursor/skills/omni-rewriter-h3-pe/SKILL.md`.

### 2. Generate intro (+ optional marathon)

```bash
export OMNI_WRITER_H3_BASE_URL=http://127.0.0.1:30010
PYTHONPATH=src python scripts/promo/submit_h3_chunk.py docs/promo/omni_promo_chunk_a_messy.json \
  --out docs/promo/out/v6/chunk_a_intro_src.mp4
python scripts/promo/fix_intro_pe_card.py \
  --intro docs/promo/out/v6/chunk_a_intro_src.mp4 \
  --out docs/promo/out/v6/chunk_a_intro.mp4
```

Marathon (or any new proof pair): submit RAW and PE envelopes the same way.

### 3. Proof cards

```bash
PYTHONPATH=src python scripts/promo/build_proof_cards.py --manifest docs/promo/out/v6/proof_manifest.json
```

Each item: `raw`, `pe`, `start`, `duration`, `out`. Prefer mid-clip excerpts (~5.5s).

### 4. Assemble

```bash
python scripts/promo/build_models_finale.py \
  --atmosphere docs/promo/out/v6/chunk_a_intro.mp4 \
  --out-dir docs/promo/out/v6/plates/finale \
  --out-finale docs/promo/out/v6/models_finale.mp4 \
  --bridge-seconds 2.2 --brand-seconds 2.6 --lanes-seconds 3.6
python scripts/promo/assemble_promo.py \
  --intro docs/promo/out/v6/chunk_a_intro.mp4 \
  --proof docs/promo/out/v6/proof_0.mp4 docs/promo/out/v6/proof_1.mp4 docs/promo/out/v6/proof_2.mp4 \
  --models-finale docs/promo/out/v6/models_finale.mp4 \
  --work-dir docs/promo/out/v6/work \
  --out docs/promo/out/v6/omni_rewriter_promo_v6.mp4
```

Site preview copy:

```bash
ffmpeg -y -i docs/promo/out/v6/omni_rewriter_promo_v6.mp4 -vf scale=1280:-2 \
  -c:v libx264 -b:v 2200k -c:a aac -b:a 128k -movflags +faststart \
  docs/day2-h3-pe/assets/promo/omni_rewriter_promo.mp4
```

### 5. QA

Reject garbled on-screen PE type (re-run `fix_intro_pe_card.py` if needed). Confirm AAC on the final file. Keep `docs/promo/out/v6/` lean: final mp4 + rebuild sources only (no `regen/`, `qa_*`, or `work*` dumps in commits).

## Related skills

- `.cursor/skills/omni-rewriter-h3-pe/SKILL.md` — H3 PE grammar / validation
- `.cursor/skills/omni-rewriter-model-contribution/SKILL.md` — adding real PE profiles/adapters
