# 社区模型待办

[English](community-models.md) · [贡献指南](../CONTRIBUTING.md)

这里明确列出欢迎社区补充的提示词配置。“待办”不代表“已支持”。完整贡献必须把提示词扩写与
媒体生成分开，并为运行时或接口声明提供公开上游依据。

## Video｜视频

| 模型族 | 公开上游 | 首期贡献目标 |
| --- | --- | --- |
| WAN | [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | Wan2.2 原生 PE 配置（同属 WAN 族）、任务路由、校验器、渲染器、样例 |
| HunyuanVideo | [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | 文生视频/图生视频配置、校验器、可选适配器 |
| CogVideoX | [THUDM/CogVideo](https://github.com/THUDM/CogVideo) | 文生视频/图生视频方言、样例、可选适配器 |
| LTX-Video | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | 视频/音频约束、渲染器、运行时样例 |
| Mochi 1 | [genmoai/mochi](https://github.com/genmoai/mochi) | 文生视频配置、校验器、RAW/PE 样例 |
| Step-Video | [stepfun-ai/Step-Video-T2V](https://github.com/stepfun-ai/Step-Video-T2V) | 文生视频/TI2V 配置、校验器、可选适配器 |

## Image｜图像

| 模型族 | 公开上游 | 首期贡献目标 |
| --- | --- | --- |
| FLUX.1 / Kontext | [black-forest-labs/flux](https://github.com/black-forest-labs/flux) | 文生图/编辑配置、保留规则、样例 |
| Stable Diffusion 3.5 | [Stability-AI/sd3.5](https://github.com/Stability-AI/sd3.5) | 文生图/控制配置、负面提示词策略 |
| Kolors | [Kwai-Kolors/Kolors](https://github.com/Kwai-Kolors/Kolors) | 中英双语文生图配置与多语言评测 |
| PixArt-Sigma | [PixArt-alpha/PixArt-sigma](https://github.com/PixArt-alpha/PixArt-sigma) | 文生图配置、分辨率与比例校验 |
| Sana | [NVlabs/Sana](https://github.com/NVlabs/Sana) | 文生图配置、渲染器、运行时样例 |

## Unified｜统一多模态

“统一多模态”指在同一模型契约下组合多模态理解与生成，或组合多种生成任务；并不表示下列
每个模型都具备视频生成能力。

| 模型族 | 公开上游 | 首期贡献目标 |
| --- | --- | --- |
| Show-o2 | [showlab/Show-o](https://github.com/showlab/Show-o) | 理解 + 图像/视频生成请求映射 |
| Emu3 | [baaivision/Emu3](https://github.com/baaivision/Emu3) | 理解/生成路由与离散输出契约 |
| Janus-Pro | [deepseek-ai/Janus](https://github.com/deepseek-ai/Janus) | 理解/文生图路由、渲染器、样例 |
| BAGEL | [ByteDance-Seed/BAGEL](https://github.com/ByteDance-Seed/BAGEL) | 理解/文生图/编辑路由与保留规则 |
| OmniGen2 | [VectorSpaceLab/OmniGen2](https://github.com/VectorSpaceLab/OmniGen2) | 文生图/编辑/上下文生成请求映射与样例 |

## 完成标准

只有满足以下条件，模型才能从待办列表移入“已支持”矩阵：

1. 提供强类型任务/配置契约和确定性校验。
2. 提供渲染器；若结构化输出本身就是最终方言，则给出明确依据。
3. 提供 RAW 与扩写后样例以及针对性测试。
4. 每项运行时或接口兼容声明都有公开证据。
5. 文档分别标明提示词扩写、适配器和端到端运行状态。
6. 不提交密钥、私有提示词转储、模型权重或完整分辨率视频。

可以使用项目 Skill
[`omni-rewriter-model-contribution`](../.cursor/skills/omni-rewriter-model-contribution/SKILL.md)
生成贡献骨架并运行检查。
