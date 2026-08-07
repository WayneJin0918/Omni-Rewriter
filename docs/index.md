# Omni-Rewriter documentation

[中文索引](index_zh.md) · [Project README](../README.md)

Omni-Rewriter is a typed, validated prompt-expansion framework for multimodal generation. It
expands intent into a target PE dialect; media generation remains an explicit, separate step.

## Start here

- [Getting started](getting-started.md) — install, expand, validate, and choose a profile.
- [Architecture](architecture.md) — framework layers, contracts, lifecycle, and trust boundaries.
- [Generation adapters](generation-adapters.md) — the expand/generate boundary and runtime
  compatibility evidence.
- [Evaluation](evaluation.md) — deterministic conformance checks and their limits.

## PE profiles

- [H3 PE harness](h3-pe-harness.md) — video routing, timeline grammar, and bounded repair.
- [Image PE](image-pe.md) — Seedream-style and Qwen-Image-Edit-style image packing.
- [H3 adapters](h3-adapters.md) — implemented local H3 and MiniMax clients.
- [Public H3 references](references/README.md) — sanitized sources used to tighten H3 rules.

## Project governance

- [Community model backlog](community-models.md) — Video, Image, and Unified contribution boards.
- [Roadmap](../ROADMAP.md)
- [Contributing](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
- [Code of conduct](../CODE_OF_CONDUCT.md)

## Scope

The framework provides schemas, analysis/draft/repair orchestration, deterministic validation, and
dialect rendering. A PE profile does not imply a bundled checkpoint or compatible generation
runtime. Omni-Rewriter does not claim access to or parity with private vendor Context-IR systems.
