# Omni-Rewriter documentation

[中文索引](index_zh.md) · [Project README](../README.md)

Omni-Rewriter is a typed, validated **agentic prompt-expansion harness** for multimodal
generation. It expands intent into a target PE dialect; media generation remains an
explicit, separate step.

## Start here

- [Getting started](getting-started.md)
- [Architecture](architecture.md)
- [Evaluation](evaluation.md)

## Dialects & adapters

Canonical pages: [`dialects/`](dialects/README.md)

- [Video PE (H3)](dialects/h3-pe-harness.md)
- [Seedance PE](dialects/seedance-pe.md)
- [Image PE](dialects/image-pe.md)
- [H3 adapters](dialects/h3-adapters.md)
- [Generation adapters](dialects/generation-adapters.md)
- [Community model backlog](dialects/community-models.md)
- [Public H3 references](references/README.md)
- [Example requests](../examples/requests/)

## Public demos & promo

See [`site/README.md`](site/README.md).

- [H3 PE site](day2-h3-pe/index.html) — promo entry → [`home.html`](day2-h3-pe/home.html)
- [H3 PE showcase](h3-pe-showcase/index.html) — full RAW vs PE grid
- [Compact video gallery](assets/gallery/) · [SOURCE vs REPLAY reconstruct](assets/gallery/reconstruct/) · [Image gallery](assets/gallery/image/)
- [Promo pipeline](promo/README.md) · [Promo copy EN](promo/copy_en.md) / [中文](promo/copy_zh.md)

## Project governance

- [Roadmap](ROADMAP.md)
- [Video reconstruct PE](design/video-reconstruct-pe.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Agent notes](AGENTS.md)

## Scope

Schemas, analysis/draft/repair orchestration, deterministic validation, and dialect
rendering. A PE profile does not imply a bundled checkpoint or compatible generation
runtime.
