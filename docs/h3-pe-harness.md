# H3 PE profile

[中文](h3-pe-harness_zh.md) · [Framework architecture](architecture.md)

```mermaid
flowchart TD
  A[RewriteRequest<br/>prompt + media + task] --> B{Task family}
  B -->|video t2va/i2va/fl2va/l2va/ref2va| C[Media preparer]
  B -->|image t2i/i2i/image_edit| C
  C --> D[Analyze<br/>AnalysisPlan JSON]
  D --> E[Draft<br/>schema-guided LLM]
  E --> F[Deterministic Pydantic validate]
  F -->|ok| G[RewriteResult<br/>render for target dialect]
  F -->|fail| H{repairs left?}
  H -->|yes| I[Repair with validation errors]
  I --> F
  H -->|no| J[RepairExhaustedError]
  G --> K{Consumer}
  K --> L[H3 / MiniMax video API]
  K --> M[Seedream / Qwen-Image* packing]
  K --> N[Eval / compare site]
```

## Why this exists

H3 is one video profile in the broader Omni-Rewriter prompt-expansion framework. It turns casual
video intent into typed H3-oriented text with deterministic grammar checks and bounded repair.
Profile support does not imply bundled generation or official vendor status; it gives the
community a reproducible bridge from public examples and APIs to validated prompts.

## Video PE layers (H3)

Inspired by the public H3 skill contracts archived under `docs/references/`:

1. Invariants
2. State
3. Transitions
4. Evidence
5. Observation plan (camera / edit)
6. Serialization (`BaseRewrite` or `Ref2VARewrite`)

```mermaid
flowchart LR
  U[User intent] --> Inv[Invariants]
  Inv --> St[State sequence]
  St --> Tr[Transitions + persistence]
  Tr --> Ev[Visible/audible evidence]
  Ev --> Obs[Observation plan]
  Obs --> Ser[H3 fields]
```

## Image PE

```mermaid
flowchart LR
  U[User image intent] --> P{profile}
  P -->|seedream| S[emotion-free visual blueprint]
  P -->|qwen_image_edit| Q[imperative edit instruction]
  S --> R[prompt + ratio]
  Q --> R
  R --> Out["<prompt>/<ratio> or plain prompt"]
```

## Related docs and skills

- `docs/index.md` — framework documentation
- `docs/architecture.md` — package layout
- `docs/image-pe.md` — image dialects
- `docs/h3-pe-harness.md` — this page
- `docs/references/jahnson-h3-skill-*.txt` — source skill dumps used to tighten rules
- `.cursor/skills/omni-rewriter-h3-pe/` — Cursor skill for contributors/agents
