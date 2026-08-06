---
name: omni-rewriter-h3-pe
description: >-
  Expand user video/image intents into Omni-Rewriter validated PE for MiniMax-H3
  (t2va/i2va/fl2va/l2va/ref2va) and Seedream / Qwen-Image-Edit image dialects.
  Use when writing prompts.py rules, RewriteRequest fixtures, PE repairs, or
  comparing raw vs expanded outputs.
---

# Omni-Rewriter PE skill

## Mission

Omni-Rewriter bridges the gap between **model demos / marketing / private Context-IR** and what
open or public APIs actually need: typed, validated, generator-ready prompts. Prefer harness
improvements (schema, validators, repairs, dialects) over claiming to reverse-engineer vendors.

## When expanding video (H3)

1. Confirm task routing (`t2va` / `i2va` / `fl2va` / `l2va` / `ref2va`).
2. Plan with six layers: invariants → state → transitions → evidence → observation → serialization.
3. Emit exact H3 grammar:
   - `[Shot 1]` then `[Shot N] At MM:SS.mmm,`
   - dialogue as `<d>[Language] ...</d>` with speakers outside tags
   - camera as natural English (type + optional amplitude/speed)
   - FL2VA: exact endpoints; prefer one continuous reachable path
   - Ref2VA: complete Base timeline first; references only add retention/provenance
4. Run package validation / tests; do not hand-wave timeline or markup errors.

Source skill archives: `docs/references/jahnson-h3-skill-{t2va,fl2va,ref2va}.txt`.

## When expanding image

1. Task is `t2i` / `i2i` / `image_edit`; omit `duration_seconds`.
2. Profile `seedream` or `qwen_image_edit` via `metadata.image_pe_profile`.
3. Single-paragraph `prompt` + `ratio` in
   `{21:9,16:9,3:2,4:3,1:1,3:4,2:3,9:16}` or `[image N]`.
4. Preserve on-canvas quoted text exactly; match quote style to instruction language.

See `docs/image-pe.md`.

## Repo contribution norms

- Keep public contracts stable: `RewriteRequest`, `BaseRewrite`, `Ref2VARewrite`, `ImageRewrite`.
- Add tests for every validator/rule change.
- Prefer small PRs; fill the PR template; link issues.
- Do not commit full-resolution generated videos; low-res gallery thumbs under `docs/assets/` are OK.
- Read `CONTRIBUTING.md` and `ROADMAP.md` before large features (SFT/RL are future work).
