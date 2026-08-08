# Security policy

## Supported versions

Security fixes are accepted against the latest `main` branch of Omni-Rewriter.

## Reporting a vulnerability

Please **do not** open a public issue for sensitive reports. Prefer a private GitHub security
advisory on [WayneJin0918/Omni-Rewriter](https://github.com/WayneJin0918/Omni-Rewriter) when
available, or contact the repository owner via GitHub.

Include:

- Affected component (CLI, API, media loader, adapters)
- Reproduction steps
- Impact assessment

## Scope notes

- Omni-Rewriter fetches optional media with address / redirect / size limits; treat media URIs as
  untrusted input.
- Do not paste API keys into issues, fixtures, or traces.
- Prompt dumps and skill archives under `docs/references/` are sanitized public contracts, not
  credentials.
