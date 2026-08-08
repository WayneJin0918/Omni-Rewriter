# 图像 PE（Seedream / Qwen-Image-Edit）

[English](image-pe.md) · [框架架构](architecture_zh.md)

图像 PE 是 Omni-Rewriter 通用框架中的 profile family，与 H3 视频共用
analyze → draft → deterministic validate → bounded repair 生命周期。

该 profile 只输出 prompt 文本与元数据，不运行 Seedream、Qwen-Image、SGLang 或其他图像
生成器。公开提示词形状不能证明与私有模型内部实现等价。

## 任务

| 任务 | 用途 | 时长 |
| --- | --- | --- |
| `t2i` | 文生图，可带可选引用 | 必须省略 `duration_seconds` |
| `i2i` | 带引用的图生图 | 必须省略；要求媒体 |
| `image_edit` | 编辑型方言，默认 Qwen-Image-Edit 规则 | 必须省略；要求媒体 |

视频任务仍然要求 `duration_seconds`；图像任务会拒绝该字段。

## Profiles

通过 `metadata.image_pe_profile` 选择：

- `seedream`：`t2i` / `i2i` 默认值；输出不使用主观情绪词的视觉蓝图和标签化 render。
- `qwen_image_edit`：`image_edit` 默认值；输出命令式编辑指令，`render()` 为 prompt 正文。

## 输出 schema

```json
{
  "task": "t2i",
  "profile": "seedream",
  "prompt": "单段视觉描述……",
  "ratio": "16:9"
}
```

`ratio` 只能是 `21:9`、`16:9`、`3:2`、`4:3`、`1:1`、`3:4`、`2:3`、`9:16`
或 `[image N]`。画面内引用文字必须原样保留；引号样式应与指令语言一致。

Seedream render：

```text
<prompt>
……
</prompt>
<ratio>
16:9
</ratio>
```

## 示例

```json
{
  "prompt": "做一张横版海报，主标题写“夏日限定”，霓虹寿司店门口，雨夜反光地面",
  "task": "t2i",
  "metadata": {"image_pe_profile": "seedream"}
}
```

```bash
omni-rewriter expand request.json
omni-rewriter expand request.json --output image
```

扩写结果可以交给应用自有 adapter，但 runtime 兼容性必须单独验证。Qwen-Image-2512 的
SGLang-Diffusion 上游证据和其他模型路径见
[生成适配器](generation-adapters_zh.md)。
