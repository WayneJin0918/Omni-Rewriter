# Seedance 视频 PE

[English](seedance-pe.md) · [架构](architecture_zh.md)

Seedance 是 Omni-Rewriter 的**视频 PE profile**：schema → 校验 → 双渲染。它**不会**向
ByteDance Seedance、fal、Replicate 或其他生成服务提交任务。Expand ≠ generate。

该 profile 参考公开的 Seedance 2.0 提示习惯，以及一份**脱敏后**的内部 PE 形状；不复现私有
Context-IR、HDFS 媒体或厂商训练 dump。

## 公开证据（仅 PE 方言）

- 官方产品页：[Seedance 2.0](https://seed.bytedance.com/en/seedance2_0)
- 公开 API 习惯（fal / Replicate 等）：自然语言提示；引号对话便于口型；`@Video1` / `[Video1]`
  一类参考标记；时长常见约 4–15 秒；支持图像/视频/音频参考。

Runtime / adapter 状态：**未包含**。没有公开适配器与钉扎 live 测试前，不要把 Seedance 生成标为
available。

## 路由

设置 `metadata.video_pe_profile=seedance`（默认视频 profile 仍为 `h3`）。

| 任务 | 媒体 | 说明 |
| --- | --- | --- |
| `t2va` | 无 | 纯文本 Seedance PE |
| `ref2va` | ≥1 个 reference | 多参考主体与标记 |

必须提供 `duration_seconds`；图像任务必须省略。

## 输出 schema（`SeedanceRewrite`）

字段：`task`、`profile=seedance`、`duration_seconds`、`style`、`summary`、
`static_description`、`dynamic_description`、`subjects`、`instruction`、可选
`non_diegetic_music`、`generate_audio`。

`ref2va` 至少需要一个 subject；指令中的媒体索引必须落在请求 media 范围内。

## 双渲染

| 模式 | metadata | 输出 |
| --- | --- | --- |
| **natural**（默认） | `seedance_render=natural` 或未设置 | 融合执行文本（风格特点 / 内容总结 / 静态描述 / 动态描述 / 生动指令） |
| **json** | `seedance_render=json` | 规范 `SeedanceRewrite` JSON |

参考标记：`seedance_ref_style=public`（默认 `@VideoN`）或 `omni`（`<|media:N|>`）。

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```

## 脱敏策略

入库样例不得包含 `hdfs://`、`[redacted]`、`[redacted]`、`uttid`、员工路径或内部
`caption_version` 等私有字段。使用 `https://example.test/seedance/...` 占位。样例是**良性演示**，
不是官方 Seedance 训练数据。

## 样例

- `tests/fixtures/seedance/t2va_kitchen.json`
- `tests/fixtures/seedance/ref2va_interview.json`
- `examples/requests/seedance_*.json`
