# Model contribution template

## Scope

- Category: `video` | `image` | `unified`
- Model/family:
- Public upstream:
- Tasks:
- Deliverables: profile | routing | schema | validator | renderer | fixtures | adapter | live test

## Contract map

| Layer | Existing contract reused or proposed change |
| --- | --- |
| Request/task routing | |
| Typed output | |
| Deterministic validation | |
| Dialect rendering | |
| Bounded repair | |
| Optional generation adapter | |

## Evidence

- Prompt or model contract:
- API/runtime contract:
- Tested version/commit:
- Untested compatibility explicitly labeled:

## Fixtures

- Minimal valid:
- Boundary:
- Invalid:
- RAW vs expanded:
- Reference media, if applicable:

## Expected files

```text
src/omni_rewriter/models/...
src/omni_rewriter/prompts.py
src/omni_rewriter/render.py
src/omni_rewriter/adapters/...    # optional, separate from expand
tests/...
docs/...
```

Prefer the smallest subset that proves one layer. Do not add an adapter merely to make a profile
PR appear end-to-end.
