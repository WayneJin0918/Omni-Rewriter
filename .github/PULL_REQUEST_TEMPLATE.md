PLEASE FILL IN THE PR DESCRIPTION AND ENSURE EVERY CHECKLIST ITEM HAS BEEN CONSIDERED.

## Purpose

<!-- What and why. Link related issues with Fixes #NN when applicable. -->

## Test Plan

<!-- Exact commands and fixtures used to validate the change. -->

```bash
ruff check .
mypy src
pytest
python scripts/check_model_contribution.py
```

## Test Result

<!-- Paste key before/after or pass/fail results. -->

## Model contribution

<!-- Required for model-family work. Choose exactly one category. -->

- Category:
  - [ ] Video
  - [ ] Image
  - [ ] Unified
  - [ ] Not applicable
- Model / family:
- Public evidence URL:
- Contribution scope: <!-- routing / schema / profile / validator / renderer / fixtures / adapter -->
- PE status: <!-- implemented / changed / not applicable -->
- Adapter status: <!-- tested / unverified / not included / not applicable -->
- Live runtime status: <!-- tested + version / unverified / not tested / not applicable -->

---

### Essential Elements of an Effective PR Description Checklist

- [ ] The purpose of the PR is clear, and related issues are linked when applicable.
- [ ] The PR title uses a required prefix from `CONTRIBUTING.md`
      (for example `[Model][Video] Add Wan2.2 PE profile`).
- [ ] The test plan and test results are filled in.
- [ ] Docs / README model-ecosystem cards are updated when support status changes.
- [ ] Expansion and generation claims are described separately; untested paths are labeled
      `unverified`.
- [ ] No secrets, `.env` files, checkpoints, or full-resolution `.mp4` videos are included.

**BEFORE SUBMITTING, PLEASE READ `CONTRIBUTING.md`.**
