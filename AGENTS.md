# Agent notes

Omni-Rewriter is maintained as a typed, model-extensible prompt-expansion framework. H3 video and
the initial image dialects are profiles, not the framework boundary. Before changing prompts,
profiles, runtimes, or models:

1. Read `docs/architecture.md`, the relevant profile guide, and
   `.cursor/skills/omni-rewriter-h3-pe/SKILL.md`.
2. Preserve public contracts in `src/omni_rewriter/models/`.
3. Add/adjust tests under `tests/`.
4. Update docs if task routing or render formats change.
5. Keep `expand` separate from generation; document adapter/runtime evidence and label untested
   compatibility as unverified.

Do not commit secrets, full videos, or private vendor dumps beyond the sanitized skill archives
already under `docs/references/`. Do not claim to reproduce private Context-IR internals.
