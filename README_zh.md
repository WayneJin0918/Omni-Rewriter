<div align="center">
  <img src="Logo.png" alt="Omni-Rewriter" width="560">

  <p><strong>面向图像与视频生成的开源 Agentic Prompt Expansion Harness。</strong></p>
  <p>通过有界 AI Agent 工作流，将自然语言意图转换为经过校验、可直接交给生成器的提示词。</p>

  [![Agent Harness](https://img.shields.io/badge/Agentic-PE%20Harness-7C3AED)](docs/architecture_zh.md)
  [![CI](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml/badge.svg)](https://github.com/WayneJin0918/Omni-Rewriter/actions/workflows/ci.yml)
  [![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
  [![License](https://img.shields.io/github/license/WayneJin0918/Omni-Rewriter)](LICENSE)
  [![Issues](https://img.shields.io/github/issues/WayneJin0918/Omni-Rewriter)](https://github.com/WayneJin0918/Omni-Rewriter/issues)
  [![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
</div>

---

<p align="center">
  <a href="README.md"><b>English</b></a> ·
  <a href="docs/index_zh.md"><b>文档</b></a> ·
  <a href="docs/getting-started_zh.md"><b>快速开始</b></a> ·
  <a href="docs/architecture_zh.md"><b>架构</b></a> ·
  <a href="docs/generation-adapters_zh.md"><b>适配器</b></a> ·
  <a href="ROADMAP.md"><b>路线图</b></a> ·
  <a href="CONTRIBUTING.md"><b>参与贡献</b></a>
</p>

## 最新动态

- **2026-08 — H3 工作流更新：**更新 H3 视频 PE 工作流中的时间轴、运镜、对白和有界修复
  规则，参考 [MiniMax-H3 公开项目](https://github.com/MiniMax-AI/MiniMax-H3/tree/main)。

## 项目简介

Omni-Rewriter 是一个开放、面向多模型扩展的**图像与视频 Agentic Prompt Expansion（PE）
Harness**。它通过有界 `analyze → draft → validate → repair` Agent 循环，把自然语言意图
与多模态参考转换为强类型、经过校验、面向生成器的中间文本。

框架本身不绑定具体模型：任务结构、校验规则、方言渲染、运行时适配器与评测都是彼此独立的
扩展层。

> [!NOTE]
> **当前开源版本：Agent Harness。** 现阶段提供 Agent 编排、强类型契约、确定性校验与有界
> 修复；专用 SFT/RL 扩写模型仍属于社区路线图。

> [!IMPORTANT]
> **扩写不等于生成。** 核心流程只输出经过校验的文本或 JSON。只有应用显式调用适配器或
> 本地运行器时，才会加载模型并生成媒体。

<table>
  <tr>
    <td width="33%" valign="top"><b>Agent 驱动、有界执行</b><br>在严格契约和确定性护栏下完成分析、起草、校验与修复。</td>
    <td width="33%" valign="top"><b>面向多模型扩展</b><br>配置档与渲染器描述公开提示词方言，但不将其固化为架构边界。</td>
    <td width="33%" valign="top"><b>与运行时解耦</b><br>提示词扩写不依赖厂商 API、在线服务或重型本地推理环境。</td>
  </tr>
</table>

<details>
<summary><b>扩写 Agent 模型兼容性</b> — 前沿闭源模型与开源权重模型</summary>

<br>

只要后端能够返回所需的结构化 JSON，PE 编排就不绑定具体扩写模型。它既可以通过兼容接口
使用 **GPT-5.6**、**Claude Opus 5** 等前沿闭源 Agent，也可以在本地运行开源的
**Qwen / Qwen3 / Qwen3.5** 系列。

| 扩写模型族 | 接入方式 | 仓库内依据 |
| --- | --- | --- |
| **GPT-5.6** | 兼容 OpenAI Chat Completions 的接口 | 协议契约兼容；访问权限与实际表现取决于部署环境 |
| **Claude Opus 5** | 兼容 OpenAI 协议的网关 | 支持网关路径；仓库暂未内置 Anthropic 原生客户端 |
| **Qwen 系列** | vLLM 提供的 OpenAI 兼容服务 | 本地启动脚本、结构化输出及 `enable_thinking` 控制 |
| **其他扩写模型** | 任意兼容结构化输出的接口 | 在协议边界上可接入；端到端兼容性需要实际验证 |

</details>

## 工作流程

```mermaid
flowchart LR
  A["生成意图"] --> B["类型化 RewriteRequest"]
  B --> C["Analyze"]
  C --> D["Draft"]
  D --> E{"Validate"}
  E -- 可修复 --> F["有界 Repair"]
  F --> E
  E -- 通过 --> G["方言 Renderer"]
  G --> H["已校验 PE 文本 / JSON"]
  H -. 可选 .-> I["在线或本地 Adapter"]
  I -.-> J["RAW vs PE 评测"]
```

CLI 与 HTTP API 共用相同 service 层。公共 schema 与完整生命周期见
[架构文档](docs/architecture_zh.md)。

<details>
<summary><b>已支持的配置档与集成</b> — 点击展开按证据标注的兼容矩阵</summary>

<br>

| 模态 | 模型族 | 提示词扩写 | 可选生成路径 | 状态 |
| --- | --- | --- | --- | --- |
| 视频 | **MiniMax-H3** | T2VA、I2VA、FL2VA、L2VA、Ref2VA | MiniMax API 或 H3 专用本地契约 | 提示词扩写 + 适配器 |
| 视频 | **LingBot Video** | 强类型结构化描述 | 独立本地运行器与可选两阶段扩写器 | 数据结构 + 本地运行器 |
| 视频 | **WAN** | 通过公开请求字段映射视频扩写结果 | SGLang 或 vLLM-Omni 风格视频接口 | 适配器；在线兼容性取决于版本 |
| 图像 | **Seedream 风格前沿图像配置** | 文生图、图生图、图像编辑；提示词 + 比例封装 | 由服务商提供运行时 | 提示词扩写 |
| 图像 | **Qwen-Image / Edit** | 图像生成与编辑方言 | 兼容 SGLang 的图像接口 / 本地 Diffusers | PE + 适配器 + 文生图 A/B |
| 图像 | **HunyuanImage-3.0** | 通过通用图像配置生成视觉蓝图 | 已记录的定制 vLLM 分支 / 本地运行器 | 适配器 + A/B |

运行时支持只按公开证据和实际测试结果声明。具备某种提示词配置，并不表示已经证明端到端生成
兼容。精确契约与限制见[兼容性矩阵](docs/generation-adapters_zh.md)。

</details>

## 社区模型待办

绿色条目代表已在对应证据范围内支持；灰色条目是开放的社区贡献目标。点击“发起贡献”进入
PR 流程，然后使用[模型贡献 Skill](.cursor/skills/omni-rewriter-model-contribution/SKILL.md)
生成代码与文档骨架。公开上游链接和验收标准见[社区模型待办](docs/community-models_zh.md)。

### Video｜视频

| 模型族 | 状态 | 下一步 |
| --- | --- | --- |
| MiniMax-H3 | ![已支持](https://img.shields.io/badge/已支持-PE%20%2B%20适配器-brightgreen) | 经过校验的视频 PE 和可选适配器 |
| LingBot Video | ![已支持](https://img.shields.io/badge/已支持-数据结构%20%2B%20运行器-brightgreen) | 结构化描述和独立运行器 |
| WAN | ![已支持](https://img.shields.io/badge/已支持-适配器-lightgreen) | 按版本记录的运行时兼容性 |
| Wan2.2 · HunyuanVideo · CogVideoX · LTX-Video · Mochi 1 · Step-Video | ![待贡献](https://img.shields.io/badge/待贡献-社区%20PR-lightgrey) | [发起贡献](https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1) |

### Image｜图像

| 模型族 | 状态 | 下一步 |
| --- | --- | --- |
| Seedream 风格配置 | ![已支持](https://img.shields.io/badge/已支持-PE%20配置-brightgreen) | 文生图/图生图/编辑蓝图与比例契约 |
| Qwen-Image / Edit | ![已支持](https://img.shields.io/badge/已支持-PE%20%2B%20适配器-brightgreen) | 适配器和可复现文生图 A/B |
| HunyuanImage-3.0 | ![已支持](https://img.shields.io/badge/已支持-适配器%20%2B%20A%2FB-lightgreen) | 已记录的本地运行器 |
| FLUX.1 / Kontext · Stable Diffusion 3.5 · Kolors · PixArt-Sigma · Sana | ![待贡献](https://img.shields.io/badge/待贡献-社区%20PR-lightgrey) | [发起贡献](https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1) |

### Unified｜统一多模态

| 模型族 | 状态 | 下一步 |
| --- | --- | --- |
| Show-o2 · Emu3 · Janus-Pro · BAGEL · OmniGen2 | ![待贡献](https://img.shields.io/badge/待贡献-社区%20PR-lightgrey) | [发起贡献](https://github.com/WayneJin0918/Omni-Rewriter/compare?quick_pull=1) |

统一多模态贡献必须明确区分理解与生成任务。共享 checkpoint 不代表已经支持所有模态。

> [!TIP]
> 一个聚焦的 PR 可以只提交配置档、校验器和样例。运行时适配器与端到端兼容性可以拆成后续
> PR。

## RAW 与 PE 效果对比

<p align="center"><b>视频提示词扩写</b></p>
<table>
  <tr>
    <th></th>
    <th>人物对话</th>
    <th>产品运动</th>
    <th>电影化场景</th>
  </tr>
  <tr>
    <th>RAW</th>
    <td><img src="docs/assets/gallery/s01_dialogue_raw.gif" alt="RAW 人物对话" width="240"></td>
    <td><img src="docs/assets/gallery/s06_sneaker_raw.gif" alt="RAW 产品运动" width="240"></td>
    <td><img src="docs/assets/gallery/s09_noir_raw.gif" alt="RAW 电影化场景" width="240"></td>
  </tr>
  <tr>
    <th>PE</th>
    <td><img src="docs/assets/gallery/s01_dialogue_pe.gif" alt="PE 人物对话" width="240"></td>
    <td><img src="docs/assets/gallery/s06_sneaker_pe.gif" alt="PE 产品运动" width="240"></td>
    <td><img src="docs/assets/gallery/s09_noir_pe.gif" alt="PE 电影化场景" width="240"></td>
  </tr>
</table>

<p align="center"><b>图像提示词扩写 · 与视频相同宽度的 RAW / PE 对比</b></p>
<table>
  <tr>
    <th></th>
    <th>Qwen-Image 文生图 · 海报构图</th>
  </tr>
  <tr>
    <th>RAW</th>
    <td><img src="docs/assets/gallery/image/qwen_t2i_raw.webp" alt="RAW Qwen-Image 海报" width="240"></td>
  </tr>
  <tr>
    <th>PE</th>
    <td><img src="docs/assets/gallery/image/qwen_t2i_pe.webp" alt="PE Qwen-Image 海报" width="240"></td>
  </tr>
</table>

<p align="center">
  <a href="docs/assets/gallery/index.html"><b>打开完整视频 Gallery</b></a> ·
  <a href="docs/assets/gallery/image/index.html"><b>打开含提示词的图像 Gallery</b></a>
</p>

### Seedream 风格图像 PE KPI

<table>
  <tr>
    <td width="240"><img src="docs/assets/gallery/image/seedream_profile_kpi.svg" alt="Seedream 风格提示词扩写 KPI" width="240"></td>
    <td valign="middle"><b>开源配置档的结构保证</b><br><sub>单段视觉蓝图、经过校验的比例选择、画面文字原样保留、明确的参考图操作，以及有界修复。</sub><br><br><sub>这是提示词配置的 KPI，不是闭源服务生成的图片。待存在稳定、可公开复现的推理契约后，再在完整 Gallery 中补充服务商 A/B。</sub></td>
  </tr>
</table>

<table>
  <tr>
    <td align="center" width="25%"><b>3 类任务</b><br><sub>文生图 · 图生图 · 图像编辑</sub></td>
    <td align="center" width="25%"><b>8 + 参考图</b><br><sub>经过校验的比例模式</sub></td>
    <td align="center" width="25%"><b>统一输出</b><br><sub>prompt + ratio</sub></td>
    <td align="center" width="25%"><b>有限次数</b><br><sub>确定性校验与修复</sub></td>
  </tr>
</table>

Seedream 是这个通用配置档所参考的一项公开示例。这些是开源 PE 契约提供的结构保证，
不代表掌握闭源服务的内部实现，也不是对下游生成质量的承诺。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
cp .env.example .env
set -a; source .env; set +a
```

启动兼容 OpenAI API 的提示词扩写模型服务，然后处理请求：

```bash
scripts/serve_qwen35_dev.sh

cat > request.json <<'JSON'
{
  "prompt": "一只手工风筝在傍晚微风中飞过草坡。",
  "duration_seconds": 6,
  "metadata": {"aspect_ratio": "16:9", "seed": "7"}
}
JSON

omni-rewriter expand request.json
omni-rewriter expand request.json --output h3
omni-rewriter validate output.json
```

图像任务必须显式指定 `task`，并省略 `duration_seconds`：

```json
{
  "prompt": "雨夜霓虹寿司店门口的横版海报",
  "task": "t2i",
  "metadata": {"image_pe_profile": "seedream"}
}
```

视频、T2I 与图像编辑的最短路径见[快速开始文档](docs/getting-started_zh.md)。

## 项目分层

```text
RewriteRequest
  └─ PE harness          analyze · draft · validate · repair
      └─ dialect         面向具体任务的提示词结构与渲染器
          └─ adapter     可选 HTTP client 或本地 runner
              └─ eval    结构检查 · RAW/PE 实验 · Gallery
```

- **核心层：** 强类型输入输出契约与确定性校验。
- **配置档：** 基于公开契约的模型提示词语法与渲染。
- **适配器：** 可选运行时映射，绝不由 `service.expand` 自动调用。
- **评测层：** 可复现实验清单与结构优先评测。
- **后续方向：** 社区 SFT/RL、更多方言、适配器与评测器。

## 文档导航

| 指南 | 中文 | English |
| --- | --- | --- |
| 文档索引 | [打开](docs/index_zh.md) | [Open](docs/index.md) |
| 快速开始 | [打开](docs/getting-started_zh.md) | [Open](docs/getting-started.md) |
| 架构 | [打开](docs/architecture_zh.md) | [Open](docs/architecture.md) |
| H3 Prompt Expansion | [打开](docs/h3-pe-harness_zh.md) | [Open](docs/h3-pe-harness.md) |
| 图像 Prompt Expansion | [打开](docs/image-pe_zh.md) | [Open](docs/image-pe.md) |
| 生成适配器 | [打开](docs/generation-adapters_zh.md) | [Open](docs/generation-adapters.md) |
| 评测 | [打开](docs/evaluation_zh.md) | [Open](docs/evaluation.md) |

## 开发与贡献

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python -m build
```

欢迎贡献核心 schema、方言、adapter、评测、文档与未来 SFT/RL 工作。请从
[CONTRIBUTING.md](CONTRIBUTING.md) 与 [ROADMAP.md](ROADMAP.md) 开始。

## 范围与许可

Omni-Rewriter 并非为了复现闭源系统的未公开行为，而是依据公开契约和可复现实验，帮助社区
弥合产品演示、公开 API 与实际部署流程之间的差距。未经测试的运行时兼容性会明确标记为
“未验证”。

源码使用 [Apache License 2.0](LICENSE)。第三方模型、服务、文档与名称遵循各自条款。
安全说明见 [SECURITY.md](SECURITY.md)。
