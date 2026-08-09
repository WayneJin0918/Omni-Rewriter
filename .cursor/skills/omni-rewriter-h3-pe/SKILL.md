---
name: omni-rewriter-h3-pe
description: >-
  Extend Omni-Rewriter's validated prompt-expansion framework and its H3 video
  and Seedream / Qwen-Image-Edit image profiles. Use when writing profile rules,
  RewriteRequest fixtures, PE repairs, renderers, adapters, or raw-vs-expanded
  comparisons.
---

# Omni-Rewriter PE skill

## Mission

Omni-Rewriter is a model-extensible PE framework: transport-neutral intent → typed profile →
deterministic validation/bounded repair → dialect render → optional explicit generation adapter.
H3 and the initial image dialects are profiles, not framework limits. Prefer schema, validators,
repairs, renderers, and public contracts over claims about private vendor internals.

## Framework rules

1. **Expand is not generate.** Expansion returns validated text/JSON; adapters and independent
   runners are opt-in consumers.
2. A PE profile does not prove generation-runtime compatibility.
3. Cite public runtime/API evidence, pin tested versions, and label untested paths unverified.
4. Do not treat stock vLLM, model-specific vLLM forks, and vLLM-Omni as interchangeable.
5. Preserve transport-neutral public contracts and keep model-specific mapping at profile/adapter
   boundaries.

## When expanding video (Seedance)

1. Set `metadata.video_pe_profile=seedance` (default remains H3).
2. Support `t2va` / `ref2va` only for this profile; require `duration_seconds`.
3. Emit `SeedanceRewrite` fields: style, summary, static/dynamic descriptions, subjects,
   optional `reference_roles` / `stages` / `preserve` / `unused_materials`, instruction,
   optional BGM, `generate_audio`. Follow public Seedance 2.5 habits (typed `@Image` /
   `@Video` / `@Audio`, role+exclude lines, observable stage end states, `{dialogue}` /
   `<sfx>` / `(music)` delimiters). Do not claim private vendor internals.
4. Render via `seedance_render=natural|fused|json` (default natural = public 2.5 template) and
   `seedance_ref_style=public|omni` (default public type-local `@Video 1`).
5. Never commit private dump markers or vendor-internal corpus metadata. See
   `docs/dialects/seedance-pe.md` and `assert_sanitized_seedance_payload`. No generation
   adapter in this profile pass.

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

See `docs/dialects/image-pe.md`.

## Runtime evidence

- Qwen-Image-2512: native SGLang-Diffusion registration.
- HunyuanImage-3.0: upstream model-specific vLLM fork.
- Wan: provider Omni-style video APIs.
- LingBot-World: independent upstream runner.
- vLLM-Omni model-family claims: unverified here until an end-to-end repository test exists.

Use `docs/dialects/generation-adapters.md` for evidence links and wording.

## Repo contribution norms

- Keep public contracts stable: `RewriteRequest`, `BaseRewrite`, `Ref2VARewrite`, `ImageRewrite`,
  `SeedanceRewrite`.
- Add tests for every validator/rule change.
- Prefer small PRs; fill the PR template; link issues.
- Do not commit full-resolution generated videos; low-res gallery thumbs under `docs/assets/` are OK.
- Read `docs/CONTRIBUTING.md` and `docs/ROADMAP.md` before large features (SFT/RL are future work).
