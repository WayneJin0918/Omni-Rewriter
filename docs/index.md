# Omni-Rewriter documentation

[中文索引](index_zh.md) · [Project README](../README.md)

Omni-Rewriter's current open-source release is a typed, validated **agentic prompt-expansion
harness** for multimodal generation. It expands intent into a target PE dialect; media generation
remains an explicit, separate step.

## Start here

- [Getting started](getting-started.md) — install, expand, validate, and choose a profile.
- [Architecture](architecture.md) — framework layers, contracts, lifecycle, and trust boundaries.
- [Generation adapters](generation-adapters.md) — the expand/generate boundary and runtime
  compatibility evidence.
- [Evaluation](evaluation.md) — deterministic conformance checks and their limits.

## Video and image profiles

- [Video PE](h3-pe-harness.md) — current H3 routing, timeline grammar, and bounded repair.
- [Day Two H3 PE site](day2-h3-pe/index.html) — rose/pink Day Two landing (also `gh-pages`).
- [H3 PE showcase](h3-pe-showcase/index.html) — public RAW vs PE landing page for MiniMax-H3.
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
runtime. Omni-Rewriter uses public contracts to help the community bridge polished demos, public
APIs, and reproducible deployment workflows.
