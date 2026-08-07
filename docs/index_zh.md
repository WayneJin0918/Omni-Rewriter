# Omni-Rewriter 文档

[English index](index.md) · [项目中文 README](../README_zh.md)

Omni-Rewriter 当前开源的是面向多模态生成的强类型、可校验 **Agentic Prompt Expansion
Harness**。它把意图扩写为目标 PE 方言；媒体生成是显式且独立的后续步骤。

## 从这里开始

- [快速开始](getting-started_zh.md)：安装、扩写、校验和 profile 选择。
- [架构](architecture_zh.md)：框架分层、契约、生命周期和信任边界。
- [生成适配器](generation-adapters_zh.md)：expand/generate 边界与 runtime 兼容性证据。
- [评测](evaluation_zh.md)：确定性一致性检查及其局限。

## 视频与图像配置

- [Video PE](h3-pe-harness_zh.md)：当前 H3 视频路由、时间轴语法与有界修复。
- [Day Two H3 PE 站点](day2-h3-pe/index.html)：红粉宣传落地页（同步 `gh-pages`）。
- [H3 PE showcase](h3-pe-showcase/index.html)：面向 MiniMax-H3 的公开 RAW vs PE 落地页。
- [图像 PE](image-pe_zh.md)：Seedream 风格与 Qwen-Image-Edit 风格打包。
- [H3 adapters（英文）](h3-adapters.md)：已实现的本地 H3 与 MiniMax 客户端。
- [公开 H3 参考资料](references/README.md)：用于收紧 H3 规则的脱敏资料。

## 项目治理

- [社区模型待办](community-models_zh.md)：Video、Image 与 Unified 三类贡献清单。
- [路线图](../ROADMAP.md)
- [贡献指南](../CONTRIBUTING.md)
- [安全策略](../SECURITY.md)
- [行为准则](../CODE_OF_CONDUCT.md)

## 范围

框架提供 schema、分析/起草/修复编排、确定性校验和方言渲染。支持某个 PE profile 不代表
仓库捆绑对应 checkpoint 或生成 runtime。Omni-Rewriter 依据公开契约，帮助社区弥合产品
演示、公开 API 与可复现部署流程之间的差距。
