<div align="center">
  <img src="docs/assets/brand/Logo.png" alt="Omni-Rewriter" width="560">

  <p><strong>An open agentic prompt-expansion harness for image and video generation.</strong></p>
  <p>Turn everyday intent into validated, model-ready prompts through a bounded AI-agent workflow.</p>

  [![Agent Harness](https://img.shields.io/badge/Agentic-PE%20Harness-7C3AED)](docs/architecture.md)
  [![CI](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml/badge.svg)](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml)
  [![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
  [![License](https://img.shields.io/github/license/WayneJin0918/Omni-Rewriter)](LICENSE)
  [![Issues](https://img.shields.io/github/issues/WayneJin0918/Omni-Rewriter)](https://github.com/WayneJin0918/Omni-Rewriter/issues)
  [![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](docs/CONTRIBUTING.md)
</div>

---

<p align="center">
  <a href="docs/README_zh.md"><b>中文</b></a> ·
  <a href="docs/index.md"><b>Documentation</b></a> ·
  <a href="docs/getting-started.md"><b>Getting Started</b></a> ·
  <a href="docs/architecture.md"><b>Architecture</b></a> ·
  <a href="docs/generation-adapters.md"><b>Adapters</b></a> ·
  <a href="docs/ROADMAP.md"><b>Roadmap</b></a> ·
  <a href="docs/CONTRIBUTING.md"><b>Contributing</b></a>
</p>

## News

- **2026-08 — H3 workflow refresh:** updated the H3 video PE workflow with validated timeline,
  camera, dialogue, and bounded-repair rules, informed by the
  [public MiniMax-H3 project](https://github.com/MiniMax-AI/MiniMax-H3/tree/main).

## About

Open **Agent Harness** for image/video **prompt expansion (PE)**: schemas, orchestration,
validation, and dialect render — not a bundled PE checkpoint, not a media generator.

<sub>Expand ≠ generate. VLM pairwise scoring is post-hoc only. SFT/RL writers are roadmap.</sub>

## How it works

This is the method. The **Agent Harness** owns the loop; the **Writer LM** is called only for
`Draft` / `Repair`. Validation and render stay deterministic. Output is PE text/JSON — never media.

```mermaid
flowchart LR
  req[RewriteRequest] --> analyze[Analyze]
  analyze --> draft[Draft]
  draft --> validate{Validate}
  validate -->|repairable| repair[Repair]
  repair --> validate
  validate -->|ok| render[Render]
  render --> pe[PE text / JSON]
  writer[(Writer LM)] -.->|structured JSON| draft
  writer -.->|repair JSON| repair
```

| Step | Owner | What happens |
| --- | --- | --- |
| **Analyze** | Harness + Writer | Route video/image, read constraints/media, choose PE profile |
| **Draft** | **Writer LM** | Fill the profile schema as structured JSON |
| **Validate** | Harness | Deterministic checks (timeline, quotes, required fields, dialect rules) |
| **Repair** | **Writer LM** | Bounded retries on repairable failures; otherwise hard-fail |
| **Render** | Harness | Emit PE text for terminal / execute models (T2I, T2V, …) |

Same path for CLI (`omni-rewriter expand`) and HTTP (`POST /v1/expand`). Details:
[architecture](docs/architecture.md).

## Writer LM agents

The harness talks to Writers over one contract: **OpenAI-compatible chat + structured JSON**.
It does not ship a fine-tuned PE checkpoint. How you host the Writer is separate from which
model family you pick.

**How the two Writer classes connect**

- **Core agents (closed frontier)** — GPT-5.6, Claude Opus 5, and similar. Connect via a vendor
  **API** or an OpenAI-compatible gateway (`OMNI_WRITER_BACKEND_BASE_URL` + model name).
- **Terminal / open weights** — QwenLM today; MiMo, Kimi, DeepSeek wanted. Serve locally (or on
  your cluster) with **vLLM** or **SGLang**, then point the same env vars at that OpenAI-compatible
  endpoint.

**Three access modes (same protocol)**

1. **API** — hosted frontier agents; no local GPU required for the Writer.
2. **vLLM** — common path for open-weight Writers (`/v1/chat/completions`, structured output).
3. **SGLang** — alternate OpenAI-compatible serve path for open Writers (also used by optional
   image/video generation adapters outside `expand`).

<p align="center">
  <img alt="closed-source" src="https://img.shields.io/badge/closed--source-supported-brightgreen?style=flat-square&labelColor=be123c" />
  <img alt="GPT-5.6" src="https://img.shields.io/badge/GPT--5.6-supported-brightgreen?style=flat-square&labelColor=be123c" />
  <img alt="Claude Opus 5" src="https://img.shields.io/badge/Claude%20Opus%205-supported-brightgreen?style=flat-square&labelColor=be123c" />
</p>

<p align="center">
  <img alt="open-source" src="https://img.shields.io/badge/open--source-supported-brightgreen?style=flat-square&labelColor=0f766e" />
  <img alt="QwenLM" src="https://img.shields.io/badge/QwenLM-supported-brightgreen?style=flat-square&labelColor=0f766e" />
  <img alt="MiMo wanted" src="https://img.shields.io/badge/MiMo-wanted-lightgrey?style=flat-square&labelColor=0f766e" />
  <img alt="Kimi wanted" src="https://img.shields.io/badge/Kimi-wanted-lightgrey?style=flat-square&labelColor=0f766e" />
  <img alt="DeepSeek wanted" src="https://img.shields.io/badge/DeepSeek-wanted-lightgrey?style=flat-square&labelColor=0f766e" />
</p>

<p align="center"><sub>
Generation adapters stay outside <code>expand</code> — see the
<a href="docs/generation-adapters.md">compatibility matrix</a>.
</sub></p>

## Model ecosystem

PE / generator community board — left color = category (Video / Image / Unified); right =
`available` / `wanted`. Prefer small PRs with a title prefix — see
[CONTRIBUTING.md](docs/CONTRIBUTING.md).

<p align="center">
  <img alt="MiniMax-H3 available" src="https://img.shields.io/badge/MiniMax--H3-available-brightgreen?style=flat-square&labelColor=4f46e5" />
  <img alt="LingBot Video available" src="https://img.shields.io/badge/LingBot%20Video-available-brightgreen?style=flat-square&labelColor=4f46e5" />
  <img alt="WAN available" src="https://img.shields.io/badge/WAN-available-brightgreen?style=flat-square&labelColor=4f46e5" />
  <img alt="HunyuanVideo wanted" src="https://img.shields.io/badge/HunyuanVideo-wanted-lightgrey?style=flat-square&labelColor=4f46e5" />
  <img alt="CogVideoX wanted" src="https://img.shields.io/badge/CogVideoX-wanted-lightgrey?style=flat-square&labelColor=4f46e5" />
  <img alt="LTX-Video wanted" src="https://img.shields.io/badge/LTX--Video-wanted-lightgrey?style=flat-square&labelColor=4f46e5" />
  <img alt="Mochi 1 wanted" src="https://img.shields.io/badge/Mochi%201-wanted-lightgrey?style=flat-square&labelColor=4f46e5" />
  <img alt="Step-Video wanted" src="https://img.shields.io/badge/Step--Video-wanted-lightgrey?style=flat-square&labelColor=4f46e5" />
  <img alt="Seedream available" src="https://img.shields.io/badge/Seedream-available-brightgreen?style=flat-square&labelColor=0d9488" />
  <img alt="Qwen-Image / Edit available" src="https://img.shields.io/badge/Qwen--Image%20%2F%20Edit-available-brightgreen?style=flat-square&labelColor=0d9488" />
  <img alt="HunyuanImage-3.0 available" src="https://img.shields.io/badge/HunyuanImage--3.0-available-brightgreen?style=flat-square&labelColor=0d9488" />
  <img alt="FLUX.1 / Kontext wanted" src="https://img.shields.io/badge/FLUX.1%20%2F%20Kontext-wanted-lightgrey?style=flat-square&labelColor=0d9488" />
  <img alt="Stable Diffusion 3.5 wanted" src="https://img.shields.io/badge/Stable%20Diffusion%203.5-wanted-lightgrey?style=flat-square&labelColor=0d9488" />
  <img alt="Kolors wanted" src="https://img.shields.io/badge/Kolors-wanted-lightgrey?style=flat-square&labelColor=0d9488" />
  <img alt="PixArt-Sigma wanted" src="https://img.shields.io/badge/PixArt--Sigma-wanted-lightgrey?style=flat-square&labelColor=0d9488" />
  <img alt="Sana wanted" src="https://img.shields.io/badge/Sana-wanted-lightgrey?style=flat-square&labelColor=0d9488" />
  <img alt="Show-o2 wanted" src="https://img.shields.io/badge/Show--o2-wanted-lightgrey?style=flat-square&labelColor=d97706" />
  <img alt="Emu3 wanted" src="https://img.shields.io/badge/Emu3-wanted-lightgrey?style=flat-square&labelColor=d97706" />
  <img alt="Janus-Pro wanted" src="https://img.shields.io/badge/Janus--Pro-wanted-lightgrey?style=flat-square&labelColor=d97706" />
  <img alt="BAGEL wanted" src="https://img.shields.io/badge/BAGEL-wanted-lightgrey?style=flat-square&labelColor=d97706" />
  <img alt="OmniGen2 wanted" src="https://img.shields.io/badge/OmniGen2-wanted-lightgrey?style=flat-square&labelColor=d97706" />
</p>

<p align="center">
  <img alt="available" src="https://img.shields.io/badge/status-available-brightgreen?style=flat-square" />
  <img alt="wanted" src="https://img.shields.io/badge/status-wanted-lightgrey?style=flat-square" />
  &nbsp;
  <img alt="Video category" src="https://img.shields.io/badge/category-Video-4f46e5?style=flat-square&labelColor=312e81" />
  <img alt="Image category" src="https://img.shields.io/badge/category-Image-0d9488?style=flat-square&labelColor=115e59" />
  <img alt="Unified category" src="https://img.shields.io/badge/category-Unified-d97706?style=flat-square&labelColor=92400e" />
</p>

<p align="center">
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BVideo%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Video-4f46e5?style=for-the-badge&logo=github&logoColor=white&labelColor=111827" alt="Open Video PR"></a>
  &nbsp;
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BImage%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Image-0d9488?style=for-the-badge&logo=github&logoColor=white&labelColor=111827" alt="Open Image PR"></a>
  &nbsp;
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BUnified%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Unified-d97706?style=for-the-badge&logo=github&logoColor=white&labelColor=111827" alt="Open Unified PR"></a>
</p>

<p align="center"><sub>Use the <a href=".cursor/skills/omni-rewriter-model-contribution/SKILL.md">model contribution skill</a>. Evidence-scoped details: <a href="docs/generation-adapters.md">compatibility matrix</a> · <a href="docs/community-models.md">full backlog</a>.</sub></p>

## Video RAW vs PE

<table cellspacing="0" cellpadding="0">
  <tr>
    <td width="50%" align="center"><img src="docs/assets/gallery/s15_concert_crashzoom_raw.gif" alt="RAW arena concert crash-zoom" width="100%"><br><sub>Concert crash-zoom · RAW</sub></td>
    <td width="50%" align="center"><img src="docs/assets/gallery/s15_concert_crashzoom_pe.gif" alt="PE arena concert crash-zoom" width="100%"><br><sub>Concert crash-zoom · PE</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/gallery/s14_kitchen_stations_raw.gif" alt="RAW kitchen whip-pan montage" width="100%"><br><sub>Kitchen whip-pan · RAW</sub></td>
    <td align="center"><img src="docs/assets/gallery/s14_kitchen_stations_pe.gif" alt="PE kitchen whip-pan montage" width="100%"><br><sub>Kitchen whip-pan · PE</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/gallery/s13_rooftop_orbit_raw.gif" alt="RAW rooftop arc proposal" width="100%"><br><sub>Rooftop arc proposal · RAW</sub></td>
    <td align="center"><img src="docs/assets/gallery/s13_rooftop_orbit_pe.gif" alt="PE rooftop arc proposal" width="100%"><br><sub>Rooftop arc proposal · PE</sub></td>
  </tr>
</table>

<p align="center"><sub>Current video profile: MiniMax-H3. Homepage picks are complex camera/cut/dialogue PE-wins from the 15s stress set (s11–s16).</sub><br>
<a href="https://waynejin0918.github.io/Omni-Rewriter/"><b>H3 PE site →</b></a>
·
<a href="docs/day2-h3-pe/index.html">Local H3 PE page</a>
·
<a href="docs/h3-pe-showcase/index.html">Full 15-pair showcase</a>
·
<a href="docs/assets/gallery/index.html">Compact gallery</a></p>

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
cp .env.example .env
set -a; source .env; set +a
```

Point `.env` at any OpenAI-compatible writer (closed API/gateway or open model on
**vLLM** / **SGLang**), then expand:

```bash
# OMNI_WRITER_BACKEND_BASE_URL + OMNI_WRITER_BACKEND_MODEL in .env

cat > request.json <<'JSON'
{
  "prompt": "A handmade kite catches an evening breeze above a grassy hill.",
  "duration_seconds": 6,
  "metadata": {"aspect_ratio": "16:9", "seed": "7"}
}
JSON

omni-rewriter expand request.json
omni-rewriter expand request.json --output h3
omni-rewriter validate output.json
```

Image tasks must explicitly set `task` and omit `duration_seconds`:

```json
{
  "prompt": "A rain-soaked neon sushi storefront, horizontal poster",
  "task": "t2i",
  "metadata": {"image_pe_profile": "seedream"}
}
```

For the shortest video, T2I, and image-edit paths, see
[Getting Started](docs/getting-started.md).

## Project layers

```text
RewriteRequest
  └─ Agent Harness       analyze · draft · validate · repair · render  (= PE flow)
      └─ PE profile      H3 / Seedream / Qwen-Image-Edit dialect
          └─ adapter     optional vLLM / SGLang / vendor client  (generate, not expand)
              └─ eval    structural checks · RAW/PE demos under docs/
```

- **Harness:** contracts + agent loop (this release).
- **Profiles:** public prompt dialects for video/image generators.
- **Adapters:** opt-in generation clients; never called by `service.expand`.
- **Evaluation:** structure-first checks; VLM pairwise is post-hoc only.

## Documentation

| Guide | English | 中文 |
| --- | --- | --- |
| Documentation index | [Open](docs/index.md) | [打开](docs/index_zh.md) |
| Getting started | [Open](docs/getting-started.md) | [打开](docs/getting-started_zh.md) |
| Architecture | [Open](docs/architecture.md) | [打开](docs/architecture_zh.md) |
| Video prompt expansion | [Open](docs/h3-pe-harness.md) | [打开](docs/h3-pe-harness_zh.md) |
| Image prompt expansion | [Open](docs/image-pe.md) | [打开](docs/image-pe_zh.md) |
| Generation adapters | [Open](docs/generation-adapters.md) | [打开](docs/generation-adapters_zh.md) |
| Evaluation | [Open](docs/evaluation.md) | [打开](docs/evaluation_zh.md) |

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python -m build
```

Contributions are welcome across core schemas, dialects, adapters, evaluation, documentation, and
future SFT/RL work. Start with [CONTRIBUTING.md](docs/CONTRIBUTING.md) and
[ROADMAP.md](docs/ROADMAP.md).

## Scope and license

Omni-Rewriter does not attempt to reproduce undisclosed closed-source behavior. It uses public
contracts and reproducible examples to help the community close the gap between polished demos,
public APIs, and deployable workflows. Untested runtime compatibility is labeled unverified.

Source code is licensed under [Apache License 2.0](LICENSE). Third-party models, services,
documentation, and names remain subject to their own terms. Security guidance is in
[SECURITY.md](docs/SECURITY.md).
