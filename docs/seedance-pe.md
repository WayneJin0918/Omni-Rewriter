# Seedance video PE

[中文](seedance-pe_zh.md) · [Framework architecture](architecture.md)

Seedance is a **video PE profile** in Omni-Rewriter: schema → validate → dual render. It does **not**
submit jobs to ByteDance Seedance, fal, Replicate, or any other generator. Expand ≠ generate.

This profile is inspired by public Seedance 2.0 prompt habits and a *sanitized* internal PE shape.
It does **not** reproduce private Context-IR, HDFS media, or vendor training dumps.

## Public evidence (PE dialect only)

- Official product page: [Seedance 2.0](https://seed.bytedance.com/en/seedance2_0)
- Public API prompt habits (fal / Replicate references): natural-language prompts; quoted dialogue
  for lip-sync; reference tokens such as `@Video1` / `[Video1]`; typical durations about 4–15s;
  multimodal image/video/audio references.

Runtime/adapter status: **not included**. Do not mark Seedance generation “available” without a
public adapter and pinned live test.

## Routing

Set `metadata.video_pe_profile=seedance` (default video profile remains `h3`).

| Task | Media | Notes |
| --- | --- | --- |
| `t2va` | none | Text-only Seedance PE |
| `ref2va` | ≥1 reference | Multi-ref subjects + tokens |

`duration_seconds` is required. Image tasks must omit it.

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
  "instruction": "… quoted dialogue …",
  "non_diegetic_music": "…",
  "generate_audio": true
}
```

`subjects[]` entries: `id`, optional `media_index` (1-based), `appearance`, optional `voice`.
`ref2va` requires at least one subject. Instruction/media indices must exist on the request.

## Dual render

| Mode | Metadata | Output |
| --- | --- | --- |
| **natural** (default) | `seedance_render=natural` or unset | Fused execute-model text (风格特点 / 内容总结 / 静态描述 / 动态描述 / 生动指令) |
| **json** | `seedance_render=json` | Canonical `SeedanceRewrite` JSON |

Reference token style:

- `seedance_ref_style=public` (default) → `@VideoN`
- `seedance_ref_style=omni` → `<|media:N|>`

CLI:

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
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
- Example requests under `examples/requests/seedance_*.json`
