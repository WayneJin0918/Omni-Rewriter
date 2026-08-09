# Seedance 视频 PE

[English](seedance-pe.md) · [架构](../architecture_zh.md)

Seedance 是 Omni-Rewriter 的**视频 PE profile**：schema → 校验 → 渲染。它**不会**向
ByteDance Seedance、Dreamina、fal、Replicate 或其他生成服务提交任务。Expand ≠ generate。

该 profile 对齐**公开的 Seedance 2.5 提示习惯**（Dreamina 提示词指南 / `sd25-pe` skill）以及脱敏后的
Omni schema；不复现私有 Context-IR、HDFS 媒体或厂商训练 dump。

## 公开证据（仅 PE 方言）

- Dreamina Seedance 2.5 提示词指南：材料角色、阶段结束态、类型化 `@Image` / `@Video` / `@Audio`、
  音频分隔符、最多约 50 个多模态参考（产品文档口径；**不是** Omni 生成契约）。
- 官方 `sd25-pe` skill：可直接提交的 Prompt 模板。
- 既有 Seedance 公开页面 / API 习惯：自然语言提示与参考标记；2.5 常见讨论时长约至 30 秒。

Runtime / adapter 状态：**未包含**。没有公开适配器与钉扎 live 测试前，不要把 Seedance 生成标为
available。上述产品上限在本仓库中对 API 契约标为 **unverified**。

## 路由

设置 `metadata.video_pe_profile=seedance`（默认视频 profile 仍为 `h3`）。

| 任务 | 媒体 | 说明 |
| --- | --- | --- |
| `t2va` | 无 | 纯文本 Seedance PE |
| `ref2va` | ≥1 个 reference | 类型化角色 + 主体/标记 |

请求/schema 必须提供 `duration_seconds`；图像任务必须省略。**不要**把画幅 / 时长 / 分辨率写进
渲染后的 Prompt 正文。

## 输出 schema（`SeedanceRewrite`）

字段：`task`、`profile=seedance`、`duration_seconds`、`style`、`summary`、
`static_description`、`dynamic_description`、`subjects`、`reference_roles`、`stages`、
`preserve`、`unused_materials`、`instruction`、可选 `non_diegetic_music`、`generate_audio`。

- `reference_roles[]`：每个已激活材料的 `defines` + 可选 `exclude`
- `stages[]`：可选节拍（`time_range` / `event` / 可观察 `end_state`）
- `ref2va` 至少需要一个 subject **或** reference_role
- 类型化标记按媒体类型分别编号：`@Image 1`、`@Video 1`、`@Audio 1`

## 音频分隔符

| 内容 | 语法 |
| --- | --- |
| 音乐 | `(…)` |
| 音效 | `<…>` |
| 对白 | `{…}` |
| 字幕 | `【…】` |

## 渲染模式

| 模式 | metadata | 输出 |
| --- | --- | --- |
| **natural**（默认） | `seedance_render=natural` 或未设置 | 公开 Seedance 2.5 模板（`[Generation Goal]` 等）；参数不进正文 |
| **fused** | `seedance_render=fused` | 旧版融合标签文本（风格特点 / 内容总结 / …） |
| **json** | `seedance_render=json` | 规范 `SeedanceRewrite` JSON |

参考标记：`seedance_ref_style=public`（默认类型化 `@Image N` 等）或 `omni`（扁平 `<|media:N|>`）。

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
omni-rewriter expand examples/requests/seedance_ref2va_pottery.json --output seedance
```

## 脱敏策略

入库样例不得包含 `hdfs://`、`[redacted]`、`[redacted]`、`uttid`、员工路径或内部
`caption_version` 等私有字段。使用 `https://example.test/seedance/...` 占位。样例是**良性演示**，
不是官方 Seedance 训练数据。

## 样例

- `tests/fixtures/seedance/t2va_kitchen.json`
- `tests/fixtures/seedance/ref2va_interview.json`
- `tests/fixtures/seedance/ref2va_pottery.json`
- `examples/requests/seedance_*.json`
