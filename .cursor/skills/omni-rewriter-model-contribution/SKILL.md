---
name: omni-rewriter-model-contribution
description: >-
  Scaffold and review new Video, Image, or Unified model contributions for
  Omni-Rewriter. Use when adding a PE profile, task route, validator, renderer,
  fixture, generation adapter, compatibility claim, or model-support pull
  request.
---

# Omni-Rewriter model contribution

## Start here

1. Read `docs/architecture.md`, `docs/community-models.md`, and the relevant profile guide.
2. Classify the contribution as exactly one of `video`, `image`, or `unified`.
3. Copy the structure in [CONTRIBUTION_TEMPLATE.md](CONTRIBUTION_TEMPLATE.md).
4. Keep prompt expansion and media generation as separate deliverables.

## Required implementation order

1. **Evidence** — link the public upstream prompt/API/runtime contract. Do not infer private
   behavior or equate stock vLLM, custom vLLM forks, and vLLM-Omni.
2. **Routing** — map public user intent to an existing task, or justify a new transport-neutral
   task without breaking current `RewriteRequest` users.
3. **Schema** — add or reuse a strict typed output. Unknown fields must remain rejected.
4. **Validation** — encode deterministic constraints before adding repair instructions.
5. **Renderer** — serialize the validated output into the target public dialect.
6. **Repair** — pass only the invalid candidate, errors, and required invariants; keep retries
   bounded.
7. **Fixtures and tests** — cover valid, invalid, boundary, and RAW-vs-expanded cases.
8. **Adapter, optional** — add generation only when a public contract exists. Pin the tested
   runtime and label every untested path `unverified`.
9. **Docs** — update the supported matrix only to the exact demonstrated level: PE, adapter, or
   live runtime.

## Category checklist

### Video

- Require `duration_seconds`.
- Define timeline, camera, motion, cut, continuity, dialogue, and audio behavior where applicable.
- Test timestamp bounds and task/media-role combinations.

### Image

- Omit `duration_seconds`.
- Define ratio/resolution, visible-text quoting, reference retention, and edit locality.
- Test T2I, I2I, and edit routes only when the model contract supports them.

### Unified

- Define explicit routing between understanding and each generation mode.
- Do not treat one shared checkpoint as proof of one shared prompt dialect.
- State which output modalities are actually implemented and tested.

## Pull request contract

Use a vLLM-style title prefix and fill Purpose / Test Plan / Test Result:

- `[Model][Video] ...`, `[Model][Image] ...`, or `[Model][Unified] ...`
- exactly one category checkbox;
- model/family and public evidence URL;
- contribution scope;
- PE, adapter, and live-runtime status separately;
- update the matching README model-ecosystem card when status changes.

Run:

```bash
python scripts/check_model_contribution.py
ruff check .
mypy src
pytest
python -m build
```

The deterministic contribution check is merge-blocking. The optional AI review is advisory and
must never override tests, public evidence, or maintainer review.
