# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the thin public surface (`RewriteRequest` / rewrite outputs, `expand`, `validate_output`,
`create_app`). Adapter modules under `omni_rewriter.adapters.*` may evolve faster within `0.x`.

## [Unreleased]

### Added

- LTX-2.5 video PE profile (`metadata.video_pe_profile=ltx`) with `LTXRewrite`, a single
  flowing-paragraph render, fixtures, `--output ltx`, and an optional official
  `ltx_pipelines.distilled` runner. Live generate is unverified. Expand ≠ generate.
- Video reconstruct v1 (`omni-rewriter reconstruct`): local ffmpeg evidence pack →
  `VideoObservation` → existing draft/validate/repair as H3 `t2va` PE. Source mp4 is not inlined
  into `expand`. HTTP `POST /v1/reconstruct` accepts observation JSON only. Observe cap is 45s;
  optional H3 generate stays on the public integer 4–15s window (`envelope_for_h3_replay`).
  SOURCE vs REPLAY promo thumbs: `docs/assets/gallery/reconstruct/`.

### Changed

- Recommended local language + vision Writer is
  [Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B). Defaults in `Settings`,
  `.env.example`, and `scripts/serve/serve_sglang_qwen_writer.sh` now point at that checkpoint
  (SGLang, TP=4, 32K context, `--reasoning-parser qwen3`). Expand ≠ generate. Live PE quality
  with this Writer is unverified until a local expand/reconstruct run. Qwen3.5 vLLM scripts
  remain as an alternate path.

## [0.1.1] - 2026-08-13

### Added

- Seedance video PE profile (`metadata.video_pe_profile=seedance`) with `SeedanceRewrite`,
  natural/json dual render, sanitized fixtures, and `--output seedance` (PE only; no adapter).
- Validate-only install: `typer` is a core dependency so `pip install omni-rewriter` exposes
  `omni-rewriter validate` with no Writer. Trusted-publishing workflow on GitHub Release.

### Changed

- Seedance PE aligned to public Seedance 2.5 prompt habits: typed `@Image`/`@Video`/`@Audio`
  validation, optional `reference_roles` / `stages` / `preserve` / `unused_materials`, natural
  render as the public template, and `seedance_render=fused` for the legacy labeled dialect.
- Site demo GIFs / showcase thumbs removed from `main` tracking; HTML points at GitHub Pages
  `assets/demos/` URLs. Lean-clone notes in `docs/site/README.md` and `docs/CONTRIBUTING.md`.

## [0.1.0] - 2026-08-09

### Added

- Typed prompt-expansion harness with H3 video, Seedream, and Qwen-Image PE profiles.
- CLI (`omni-rewriter`), optional FastAPI `create_app`, and example `RewriteRequest` JSON under
  `examples/requests/`.
- Generation adapters for local H3 / MiniMax plus optional image and video runners (evidence-scoped).
- Contribution contract checker and community model backlog docs.

### Security

- HTTP `create_app` denies local filesystem media by default (`OMNI_WRITER_ALLOW_LOCAL_MEDIA`).
- Adapter downloads reject non-public resolved hosts; H3 auth headers stay origin-scoped.

[0.1.1]: https://github.com/WayneJin0918/Omni-Rewriter/releases/tag/v0.1.1
[0.1.0]: https://github.com/WayneJin0918/Omni-Rewriter/releases/tag/v0.1.0
