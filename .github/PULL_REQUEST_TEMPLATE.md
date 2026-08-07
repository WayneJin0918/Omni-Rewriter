## Summary

<!-- 1-3 bullets: what and why -->

-

## Type of change

- [ ] Bug fix
- [ ] New PE profile / dialect / validator / repair rule
- [ ] Model family contribution
- [ ] Adapter or CLI/API surface
- [ ] Docs / skills / examples
- [ ] Experiments / low-res gallery assets
- [ ] CI / tooling
- [ ] Breaking change (describe migration)

## Model contribution contract

<!-- Choose exactly one category for every PR. Use Not applicable for unrelated changes. -->

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

## Test plan

- [ ] `ruff check .`
- [ ] `mypy src`
- [ ] `pytest`
- [ ] Added/updated tests for the changed contract
- [ ] Docs updated if public behavior changed

## Notes for reviewers

<!-- Link issues, profiles/runtimes affected, public contract evidence, screenshots if UI -->

## Compatibility claims

- [ ] Expansion and generation support are described separately
- [ ] Runtime/API versions and evidence links are documented
- [ ] Untested or inferred compatibility is labeled unverified
- [ ] No claim depends on private vendor internals

## Checklist

- [ ] No secrets or `.env` files
- [ ] No full-resolution videos (`.mp4`); only bounded low-resolution gallery media if needed
- [ ] Public models remain compatible or breaking change is called out
- [ ] I read `CONTRIBUTING.md`
