# Contributing to Omni-Rewriter

Thanks for helping close the gap between **model demos / marketing / private Context-IR** and
what public APIs and open checkpoints actually consume. Contributions of all sizes are welcome.

## Mission reminder

Omni-Rewriter is an open prompt-expansion harness for **video (MiniMax-H3)** and **image
(Seedream / Qwen-Image-Edit dialects)**. It is intentionally not a claim to reverse-engineer any
vendor. Prefer durable contracts, validators, tests, and docs.

## Quick start for contributors

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
```

## What to work on

See [ROADMAP.md](ROADMAP.md). High-value areas:

- New PE dialects / stricter validators
- Generation adapters (expand ≠ generate)
- Experiments and low-res gallery assets
- Docs, translations, examples
- Future SFT / RL data pipelines (design first)

## Pull request checklist

1. Branch from `main`; keep the PR focused.
2. Add or update tests for behavior changes.
3. Run `ruff`, `mypy`, and `pytest` locally.
4. Update docs when contracts or CLI flags change.
5. Do **not** commit secrets, `.env`, full-resolution videos, or huge binaries.
   Low-res JPEGs under `docs/assets/gallery/` are fine.
6. Fill out the PR template and link related issues.

## Commit style

Prefer short imperative subjects:

- `fix: require <d> tags for dialogue scenes`
- `feat: add seedream image PE schema`
- `docs: add harness flowchart`

## Code review expectations

- Public models stay backward compatible unless the PR clearly documents a breaking change.
- Prompt-rule edits should cite the dialect (`H3` / `seedream` / `qwen_image_edit`) and add a test.
- Agent / Cursor skills under `.cursor/skills/` should stay actionable and short.

## Community

- Be respectful (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).
- Open an issue before large refactors when possible.
- Questions about PE quality vs vendor demos belong in issues with reproducible fixtures.

Welcome aboard — the harness gets better when more people stress it against real generators.
