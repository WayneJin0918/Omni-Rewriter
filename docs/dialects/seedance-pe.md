# Seedance video PE

[中文](seedance-pe_zh.md) · [Framework architecture](../architecture.md)

Seedance is a **video PE profile** in Omni-Rewriter: schema → validate → dual/triple render. It does
**not** submit jobs to ByteDance Seedance, Dreamina, fal, Replicate, or any other generator.
Expand ≠ generate.

This profile follows **public Seedance 2.5 prompt habits** (Dreamina prompt guide / `sd25-pe`
skill) and a sanitized Omni schema. It does **not** reproduce private Context-IR, HDFS media, or
vendor training dumps.

## Public evidence (PE dialect only)

- Dreamina Seedance 2.5 Prompt Guide (Lark): material roles, staged end states, typed `@Image` /
  `@Video` / `@Audio` tokens, audio delimiters, up to ~50 multimodal refs (documented product
  guidance; not an Omni generation contract).
- Official `sd25-pe` skill package (Volcengine / Ark docs skill feed): submit-ready Prompt templates
  for text-only, multi-reference, edit, extension, and keyframes.
- Product pages / prior Seedance 2.0 public API habits: natural-language prompts; reference tokens;
  typical short clips (commonly discussed up to about 30s for 2.5).

Runtime/adapter status: **not included**. Do not mark Seedance generation “available” without a
public adapter and pinned live test. Product UI limits above are **unverified** as API contracts
here.

## Routing

Set `metadata.video_pe_profile=seedance` (default video profile remains `h3`).

| Task | Media | Notes |
| --- | --- | --- |
| `t2va` | none | Text-only Seedance PE |
| `ref2va` | ≥1 reference | Typed roles + subjects/tokens |

`duration_seconds` is required on the request/schema (generation parameter). Image tasks must omit
it. Do **not** put aspect ratio / duration / resolution sentences into the rendered Prompt body.

## Output schema (`SeedanceRewrite`)

```json
{
  "task": "t2va",
  "profile": "seedance",
  "duration_seconds": "8",
  "style": "…",
  "summary": "…",
  "static_description": "…",
  "dynamic_description": "…",
  "subjects": [],
  "reference_roles": [],
  "stages": [],
  "preserve": [],
  "unused_materials": [],
  "instruction": "… {dialogue} …",
  "non_diegetic_music": "…",
  "generate_audio": true
}
```

Field notes:

- `subjects[]`: `id`, optional `media_type` + type-local `media_index`, `appearance`, optional `voice`.
- `reference_roles[]`: activated materials with `defines` + optional `exclude` (inherit/ignore).
- `stages[]`: optional beats with `time_range`, `event`, observable `end_state`.
- `preserve[]` / `unused_materials[]`: consistency + explicit unused `@Image`/`@Video`/`@Audio` lines.
- `ref2va` requires at least one subject **or** reference_role.
- Public caps encoded as soft product guidance: ≤30 images, ≤10 videos, ≤10 audio, ≤50 total.

## Reference tokens

| Style | Metadata | Tokens |
| --- | --- | --- |
| **public** (default) | `seedance_ref_style=public` | Type-local `@Image 1`, `@Video 1`, `@Audio 1` (compact `@Video1` / `[Video1]` accepted) |
| **omni** | `seedance_ref_style=omni` | Flat `<|media:N|>` for video-shaped compact refs |

Indices for `@Image` / `@Video` / `@Audio` are **per media type** in request order.

## Audio delimiters (public habit)

| Content | Syntax |
| --- | --- |
| Music | `(…)` |
| Sound effect | `<…>` |
| Dialogue | `{…}` |
| Subtitle | `【…】` |

Plain quoted dialogue remains accepted. Prefer declaring spoken language when it matters.

## Render modes

| Mode | Metadata | Output |
| --- | --- | --- |
| **natural** (default) | `seedance_render=natural` or unset | Public Seedance 2.5 template (`[Generation Goal]`, roles, stages, preserve). Parameters stay out of the body. |
| **fused** | `seedance_render=fused` | Legacy labeled execute-model text (风格特点 / 内容总结 / …) including `duration_seconds` |
| **json** | `seedance_render=json` | Canonical `SeedanceRewrite` JSON |

CLI:

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
omni-rewriter expand examples/requests/seedance_ref2va_pottery.json --output seedance
# JSON render when metadata.seedance_render=json:
omni-rewriter expand examples/requests/seedance_ref2va_interview.json --output seedance
```

## Sanitization policy

Checked-in fixtures must never contain `hdfs://`, `[redacted]`, `[redacted]`, `uttid`, employee
paths, or internal `caption_version` / private dump fields. Use synthetic
`https://example.test/seedance/...` placeholders. Fixtures are **benign demos**, not official
Seedance training data.

## Fixtures

- `tests/fixtures/seedance/t2va_kitchen.json`
- `tests/fixtures/seedance/ref2va_interview.json`
- `tests/fixtures/seedance/ref2va_pottery.json` (typed `@Image` / `@Video` roles + exclusions)
- Example requests under `examples/requests/seedance_*.json`
