# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the thin public surface (`RewriteRequest` / rewrite outputs, `expand`, `validate_output`,
`create_app`). Adapter modules under `omni_rewriter.adapters.*` may evolve faster within `0.x`.

## [Unreleased]

### Added

- Seedance video PE profile (`metadata.video_pe_profile=seedance`) with `SeedanceRewrite`,
  natural/json dual render, sanitized fixtures, and `--output seedance` (PE only; no adapter).

## [0.1.0] - 2026-08-09

### Added

- Typed prompt-expansion harness with H3 video, Seedream, and Qwen-Image-Edit PE profiles.
- CLI (`omni-rewriter`), optional FastAPI `create_app`, and example `RewriteRequest` JSON under
  `examples/requests/`.
- Generation adapters for local H3 / MiniMax plus optional image and video runners (evidence-scoped).
- Contribution contract checker and community model backlog docs.

### Security

- HTTP `create_app` denies local filesystem media by default (`OMNI_WRITER_ALLOW_LOCAL_MEDIA`).
- Adapter downloads reject non-public resolved hosts; H3 auth headers stay origin-scoped.

[0.1.0]: https://github.com/WayneJin0918/Omni-Rewriter/releases/tag/v0.1.0
