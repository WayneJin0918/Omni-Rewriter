# Agent notes

Omni-Rewriter is maintained as a typed PE harness. Before changing prompts or models:

1. Read `docs/h3-pe-harness.md` and `.cursor/skills/omni-rewriter-h3-pe/SKILL.md`.
2. Preserve public contracts in `src/omni_rewriter/models/`.
3. Add/adjust tests under `tests/`.
4. Update docs if task routing or render formats change.

Do not commit secrets, full videos, or private vendor dumps beyond the sanitized skill archives
already under `docs/references/`.
