# Contributing to Omni-Rewriter

Thanks for improving a general, open prompt-expansion framework for multimodal generators.
Contributions of all sizes are welcome.

## Mission reminder

Omni-Rewriter separates transport-neutral intent, typed PE profiles, deterministic validation,
dialect rendering, and optional generation adapters. H3 and the initial image profiles are
examples, not the framework boundary. It is intentionally not a claim to reverse-engineer any
vendor. Prefer durable public contracts, validators, tests, and docs.

## Quick start for contributors

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python scripts/check_model_contribution.py
```

## What to work on

See [ROADMAP.md](ROADMAP.md). High-value areas:

- New PE dialects / stricter validators
- Generation adapters (expand ≠ generate)
- Runtime compatibility fixtures with pinned public evidence
- Experiments and low-res gallery assets
- Docs, translations, examples
- Future SFT / RL data pipelines (design first)

The model backlog is deliberately split into
[Video, Image, and Unified boards](docs/community-models.md). Before starting a model-family PR,
use the project skill
[`omni-rewriter-model-contribution`](.cursor/skills/omni-rewriter-model-contribution/SKILL.md).
It provides the implementation order, category-specific checks, and a copyable contribution
template.

## Model contribution contract

Every PR must select exactly one model category in the PR template. Select `Not applicable` for
changes unrelated to a model family.

Model contributions must:

1. Name the model/family and link its public upstream contract.
2. State the exact scope: routing, schema, profile, validator, renderer, fixtures, or adapter.
3. Report PE, adapter, and live-runtime status separately.
4. Add focused tests and RAW/expanded fixtures for behavior changes.
5. Keep runtime claims versioned and evidence-backed; mark untested compatibility `unverified`.

The `Model Contribution Check` workflow validates this contract deterministically. An optional
AI review may add advisory feedback when maintainers configure a review endpoint, but it is not a
substitute for tests, evidence, or human review.

### Optional advisory AI review

The `Advisory AI Model Review` workflow accepts any OpenAI-compatible chat-completions endpoint.
Enable it with repository configuration:

- variable `OMNI_AI_REVIEW_ENABLED=true`
- variable `OMNI_AI_REVIEW_BASE_URL` (including `/v1` when required)
- variable `OMNI_AI_REVIEW_MODEL`
- secret `OMNI_AI_REVIEW_API_KEY`

For fork safety, the workflow runs trusted base-branch code under `pull_request_target`, fetches
the proposed diff only as inert text, exposes no tools to the model, and treats the result as
advisory. Endpoint failure does not bypass or fail the deterministic contribution contract.

## Pull request checklist

1. Branch from `main`; keep the PR focused.
2. Add or update tests for behavior changes.
3. Run `ruff`, `mypy`, and `pytest` locally.
4. Update docs when contracts or CLI flags change.
5. Do **not** commit secrets, `.env`, full-resolution videos, or huge binaries.
   Bounded low-resolution gallery media under `docs/assets/gallery/` are fine.
6. Fill out the PR template and link related issues.

## Commit style

Prefer short imperative subjects:

- `fix: require <d> tags for dialogue scenes`
- `feat: add seedream image PE schema`
- `docs: add harness flowchart`

## Code review expectations

- Public models stay backward compatible unless the PR clearly documents a breaking change.
- Prompt-rule edits should cite the profile/dialect and public evidence, then add a test.
- Adapter PRs must distinguish PE support from generation support, pin the tested runtime/API,
  and label untested routes as unverified.
- Do not infer stock vLLM compatibility from a custom fork, or vLLM-Omni compatibility from an
  upstream support table without an end-to-end repository test.
- Agent / Cursor skills under `.cursor/skills/` should stay actionable and short.

## Community

- Be respectful (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).
- Open an issue before large refactors when possible.
- Questions about PE quality vs vendor demos belong in issues with reproducible fixtures.

Welcome aboard — the harness gets better when more people stress it against real generators.
