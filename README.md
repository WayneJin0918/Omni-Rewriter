<div align="center">
  <img src="Logo.png" alt="Omni-Rewriter" width="560">

  <p><strong>An open agentic prompt-expansion harness for image and video generation.</strong></p>
  <p>Turn everyday intent into validated, model-ready prompts through a bounded AI-agent workflow.</p>

  [![Agent Harness](https://img.shields.io/badge/Agentic-PE%20Harness-7C3AED)](docs/architecture.md)
  [![CI](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml/badge.svg)](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml)
  [![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
  [![License](https://img.shields.io/github/license/WayneJin0918/Omni-Rewriter)](LICENSE)
  [![Issues](https://img.shields.io/github/issues/WayneJin0918/Omni-Rewriter)](https://github.com/WayneJin0918/Omni-Rewriter/issues)
  [![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
</div>

---

<p align="center">
  <a href="README_zh.md"><b>中文</b></a> ·
  <a href="docs/index.md"><b>Documentation</b></a> ·
  <a href="docs/getting-started.md"><b>Getting Started</b></a> ·
  <a href="docs/architecture.md"><b>Architecture</b></a> ·
  <a href="docs/generation-adapters.md"><b>Adapters</b></a> ·
  <a href="ROADMAP.md"><b>Roadmap</b></a> ·
  <a href="CONTRIBUTING.md"><b>Contributing</b></a>
</p>

## News

- **2026-08 — H3 workflow refresh:** updated the H3 video PE workflow with validated timeline,
  camera, dialogue, and bounded-repair rules, informed by the
  [public MiniMax-H3 project](https://github.com/MiniMax-AI/MiniMax-H3/tree/main).

## About

Omni-Rewriter is an open, model-extensible **agentic prompt expansion (PE) harness** for image and
video generation. Its AI-agent loop transforms natural multimodal intent into typed, validated,
generator-oriented text through bounded `analyze → draft → validate → repair`.

The framework is deliberately model-agnostic: task schemas, validation, rendering, runtime
adapters, and evaluation are separate extension layers.

> [!NOTE]
> **Current open-source release: Agent Harness.** It delivers agent orchestration, schemas,
> deterministic checks, and bounded repair today; dedicated SFT/RL writer checkpoints remain
> community roadmap items.

> [!IMPORTANT]
> **Expand is not generate.** The core harness produces validated text/JSON. Model loading and
> media generation happen only when an application explicitly invokes an adapter or local runner.

<table>
  <tr>
    <td width="33%" valign="top"><b>Agentic & bounded</b><br>Analyze, draft, validate, and repair with strict schemas and deterministic guardrails.</td>
    <td width="33%" valign="top"><b>Model-extensible</b><br>Profiles and renderers encode public prompt dialects without making them the architecture.</td>
    <td width="33%" valign="top"><b>Runtime-optional</b><br>Expansion remains independent from vendor APIs, online services, and heavyweight local inference.</td>
  </tr>
</table>

<details>
<summary><b>Writer / agent model compatibility</b> — frontier closed and open-weight backends</summary>

<br>

The PE orchestration is writer-model agnostic when the backend can return the required structured
JSON. It can use closed frontier agents such as **GPT-5.6** and **Claude Opus 5** through a
compatible endpoint, as well as open **Qwen / Qwen3 / Qwen3.5** models served locally.

| Writer family | Connection path | Repository evidence |
| --- | --- | --- |
| **GPT-5.6** | OpenAI-compatible chat-completions endpoint | Contract-compatible; provider access and live behavior are environment-specific |
| **Claude Opus 5** | OpenAI-compatible gateway | Gateway path supported; a native Anthropic client is not bundled |
| **Qwen series** | vLLM OpenAI-compatible server | Local launch scripts, structured output, and `enable_thinking` control |
| **Other writers** | Any compatible structured-output endpoint | Supported at the protocol boundary; live compatibility must be verified |

</details>

## How it works

```mermaid
flowchart LR
  A["Generation intent"] --> B["Typed RewriteRequest"]
  B --> C["Analyze"]
  C --> D["Draft"]
  D --> E{"Validate"}
  E -- repairable --> F["Bounded repair"]
  F --> E
  E -- valid --> G["Dialect renderer"]
  G --> H["Validated PE text / JSON"]
  H -. optional .-> I["Online or local adapter"]
  I -.-> J["RAW vs PE evaluation"]
```

The same service layer powers the CLI and HTTP API. See
[architecture](docs/architecture.md) for public schemas and lifecycle details.

## Model ecosystem

One card = one model family. Name on the left, status on the right. Green = available at the
stated evidence level; gray = open for community contribution. Prefer small PRs with a clear
title prefix — see [CONTRIBUTING.md](CONTRIBUTING.md) (vLLM-style reception).

### Video

<table>
  <tr>
    <td width="50%"><table width="100%"><tr><td align="left"><b>MiniMax-H3</b></td><td align="right"><img alt="PE + adapter" src="https://img.shields.io/badge/available-PE%20%2B%20adapter-brightgreen"></td></tr></table></td>
    <td width="50%"><table width="100%"><tr><td align="left"><b>LingBot Video</b></td><td align="right"><img alt="schema + runner" src="https://img.shields.io/badge/available-schema%20%2B%20runner-brightgreen"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>WAN</b></td><td align="right"><img alt="adapter" src="https://img.shields.io/badge/available-adapter-brightgreen"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>Wan2.2</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>HunyuanVideo</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>CogVideoX</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>LTX-Video</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>Mochi 1</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>Step-Video</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td></td>
  </tr>
</table>

### Image

<table>
  <tr>
    <td width="50%"><table width="100%"><tr><td align="left"><b>Seedream-style</b></td><td align="right"><img alt="PE profile" src="https://img.shields.io/badge/available-PE%20profile-brightgreen"></td></tr></table></td>
    <td width="50%"><table width="100%"><tr><td align="left"><b>Qwen-Image / Edit</b></td><td align="right"><img alt="PE + adapter" src="https://img.shields.io/badge/available-PE%20%2B%20adapter-brightgreen"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>HunyuanImage-3.0</b></td><td align="right"><img alt="adapter + A/B" src="https://img.shields.io/badge/available-adapter%20%2B%20A%2FB-brightgreen"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>FLUX.1 / Kontext</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>Stable Diffusion 3.5</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>Kolors</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>PixArt-Sigma</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>Sana</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
</table>

### Unified

<table>
  <tr>
    <td width="50%"><table width="100%"><tr><td align="left"><b>Show-o2</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td width="50%"><table width="100%"><tr><td align="left"><b>Emu3</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>Janus-Pro</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td><table width="100%"><tr><td align="left"><b>BAGEL</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
  </tr>
  <tr>
    <td><table width="100%"><tr><td align="left"><b>OmniGen2</b></td><td align="right"><img alt="wanted" src="https://img.shields.io/badge/wanted-community%20PR-lightgrey"></td></tr></table></td>
    <td></td>
  </tr>
</table>

<p align="center">
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BVideo%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Video-111827?style=for-the-badge&labelColor=0f172a" alt="Open Video PR"></a>
  &nbsp;
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BImage%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Image-111827?style=for-the-badge&labelColor=0f172a" alt="Open Image PR"></a>
  &nbsp;
  <a href="https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1&title=%5BModel%5D%5BUnified%5D%20"><img src="https://img.shields.io/badge/Open%20PR-Unified-111827?style=for-the-badge&labelColor=0f172a" alt="Open Unified PR"></a>
</p>

<p align="center"><sub>Use the <a href=".cursor/skills/omni-rewriter-model-contribution/SKILL.md">model contribution skill</a>. Evidence-scoped details: <a href="docs/generation-adapters.md">compatibility matrix</a> · <a href="docs/community-models.md">full backlog</a>.</sub></p>

## Video RAW vs PE

<table cellspacing="0" cellpadding="0">
  <tr>
    <td width="50%" align="center"><img src="docs/assets/gallery/s01_dialogue_raw.gif" alt="RAW dialogue generation" width="100%"><br><sub>Dialogue · RAW</sub></td>
    <td width="50%" align="center"><img src="docs/assets/gallery/s01_dialogue_pe.gif" alt="PE dialogue generation" width="100%"><br><sub>Dialogue · PE</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/gallery/s06_sneaker_raw.gif" alt="RAW product generation" width="100%"><br><sub>Product motion · RAW</sub></td>
    <td align="center"><img src="docs/assets/gallery/s06_sneaker_pe.gif" alt="PE product generation" width="100%"><br><sub>Product motion · PE</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/gallery/s09_noir_raw.gif" alt="RAW cinematic generation" width="100%"><br><sub>Cinematic scene · RAW</sub></td>
    <td align="center"><img src="docs/assets/gallery/s09_noir_pe.gif" alt="PE cinematic generation" width="100%"><br><sub>Cinematic scene · PE</sub></td>
  </tr>
</table>

<p align="center"><sub>Current video profile: MiniMax-H3.</sub><br><a href="docs/assets/gallery/index.html"><b>Open the complete video gallery →</b></a></p>

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
cp .env.example .env
set -a; source .env; set +a
```

Start an OpenAI-compatible writer backend, then expand a request:

```bash
scripts/serve_qwen35_dev.sh

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
  └─ PE harness          analyze · draft · validate · repair
      └─ dialect         task-specific prompt schema and renderer
          └─ adapter     optional HTTP client or local runner
              └─ eval    structural checks · RAW/PE experiments · galleries
```

- **Core:** typed request/output contracts and deterministic validation.
- **Profiles:** public model-specific prompt grammar and rendering.
- **Adapters:** opt-in runtime mappings; never called by `service.expand`.
- **Evaluation:** reproducible manifests and structure-first checks.
- **Future:** community SFT/RL, additional dialects, adapters, and judges.

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
future SFT/RL work. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and
[ROADMAP.md](ROADMAP.md).

## Scope and license

Omni-Rewriter does not attempt to reproduce undisclosed closed-source behavior. It uses public
contracts and reproducible examples to help the community close the gap between polished demos,
public APIs, and deployable workflows. Untested runtime compatibility is labeled unverified.

Source code is licensed under [Apache License 2.0](LICENSE). Third-party models, services,
documentation, and names remain subject to their own terms. Security guidance is in
[SECURITY.md](SECURITY.md).
