# PE Validate Action — GitHub Marketplace listing copy

Paste this when publishing the existing composite Action at
https://github.com/marketplace/actions/new
(repository: `WayneJin0918/Omni-Rewriter`, tag `v0.1.0` or later).

Publishing cannot be finished from the API; it needs one click in the GitHub UI.

## Listing fields

| Field | Value |
| --- | --- |
| **Name** | Omni-Rewriter PE Validate |
| **Description** (`action.yml`, &lt;125 chars) | Validate PE JSON envelopes with Omni-Rewriter schema checks. Validate only; expand ≠ generate. |
| **Headline** (Marketplace, ≤120 chars) | Lint prompt-expansion JSON envelopes in CI. Validate only — expand ≠ generate. |
| **Long description** (Marketplace page) | Deterministic schema checks for Omni-Rewriter PE envelopes (`RewriteOutput` or `{request, output}`). Fails the job on invalid H3 / Seedance / Seedream / Qwen-Image JSON. Does not call a Writer and does not generate media. |
| **Categories** | Continuous integration · Code quality |
| **Color / icon** | purple / check-circle (already in `action.yml`) |
| **Primary tag to use** | `WayneJin0918/Omni-Rewriter@v0.1.0` (pin a tag/SHA; avoid floating `@main` in production) |

## README snippet for the Marketplace page

```yaml
- uses: actions/checkout@v4
- uses: WayneJin0918/Omni-Rewriter@v0.1.0
  with:
    files: prompts/**/*.json
    python-version: "3.12"
```

Local equivalent: `python scripts/validate_pe_files.py tests/fixtures/**/*.json`.

## GitHub Marketplace

Publishing the composite Action still needs one checkbox in the GitHub **Release** UI
(“Publish this Action to the GitHub Marketplace”) or
https://github.com/marketplace/actions/new — the API cannot finish listing.

Use tag **`v0.1.0` or newer**. Pin callers to that tag, not `@main`.

## PyPI (first upload)

Package name `omni-rewriter` is unused on PyPI. First upload is **0.1.1** (GitHub `v0.1.0` already
exists and should not be reused as a PyPI version from a later `main`).

GitHub environment `pypi` is already created. This environment has no PyPI token.

1. Sign in at https://pypi.org (2FA required) →
   [Publishing](https://pypi.org/manage/account/publishing/).
2. Add a **pending Trusted Publisher**:
   - PyPI project name: `omni-rewriter`
   - Owner: `WayneJin0918`
   - Repository: `Omni-Rewriter`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`
3. Push the workflow, then either **Actions → Publish to PyPI → Run workflow** or publish GitHub
   Release `v0.1.1`.
4. After the first successful upload: `pip install omni-rewriter`.

## Pin Discussions (manual)

This environment’s GitHub API does not expose `pinDiscussion`. In the repo UI:

1. Open https://github.com/WayneJin0918/Omni-Rewriter/discussions/2
2. Choose **Pin discussion** so Welcome stays at the top.
