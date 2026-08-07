# 评测

[English](evaluation.md) · [文档索引](index_zh.md)

Omni-Rewriter 内置 evaluator 衡量确定性结构一致性。它不生成图像/视频，也不能替代感知、
语义、安全或人工评测。

## 单样本

输入 rewrite 对象，或包含 request/output 的 envelope：

```bash
omni-rewriter eval output.json
```

推荐 envelope，因为它还能检查输出任务和时长是否与请求一致。成功样本报告：

- `schema_pass`：输出满足严格 Pydantic 与方言语法；
- `timeline_pass`：视频输出至少有一个合法镜头；
- `field_completeness` 与 `missing_fields`；
- 渲染字符、镜头、定时镜头和引用数量；
- 唯一、已定义和未定义引用；
- 解析后的输出任务。

无效样本返回结构化校验错误和保守失败指标。

## JSONL manifest

每个非空行必须是单样本 evaluator 可接受的 JSON 对象：

```bash
omni-rewriter eval examples/fixtures/manifest.jsonl --manifest
```

结果包含每个样本及源行号，并聚合 total/passed/failed。任一样本失败、manifest 为空或输入
格式错误时，命令返回非零状态，因此适合作为 CI 格式回归 gate。

## Python 接口与可选 judge

```python
from omni_rewriter.evaluator import BasicEvaluator

result = BasicEvaluator().evaluate(payload)
manifest_result = BasicEvaluator().evaluate_manifest("cases.jsonl")
```

应用可以传入 `Judge` 实现，其可 JSON 序列化结果写入 `judge`，确定性指标保持不变。若 judge
调用远程模型，必须披露数据流、固定版本/配置、限制成本和重试，不能把其分数当作确定性结果。

## 可复现实践

1. 对请求集和验收标准做版本管理。
2. 固定 writer checkpoint、服务参数、prompt、Omni-Rewriter 版本和采样设置。
3. 在隐私策略允许范围内，分开保存 writer 原始响应与校验后输出。
4. 在昂贵生成前先做确定性校验。
5. 对生成媒体增加盲测人工评审和/或单独验证的感知指标。
6. 报告失败与排除样本，不只发布汇总通过率。

## 指标不能证明什么

通过结构校验的文本仍可能不合理、不安全、有偏见、侵犯版权或偏离意图，也可能在不同生成器
或 runtime 版本上表现不同。字符/镜头数只是诊断，不是质量分数；引用 label 一致也不能证明
视觉身份保留。PE profile 通过不等于生成兼容或生成质量通过。
