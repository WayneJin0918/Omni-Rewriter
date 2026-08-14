# LTX-2.5 视频 PE

[English](ltx-pe.md) · [架构](../architecture_zh.md)

LTX-2.5 是 Omni-Rewriter 的**视频 PE profile**：schema → 校验 → 单段段落渲染。`expand`
不会下载 Lightricks 权重，也不会调用 `ltx_pipelines`。Expand ≠ generate。

本 profile 遵循 **LTX-2 公开提示词指南**：一段连贯的时间顺序描述、摄影指导式措辞、从动作
起笔、控制在约 200 词。不复现未公开的训练字幕或私有 prompt enhancer。

## 公开证据

- [Lightricks/LTX-2](https://github.com/Lightricks/LTX-2) README「Prompting for LTX-2」：单段
  连贯段落；动作、动作细节、外貌、环境、机位、光线、突发变化；约 200 词；
  [How to prompt for LTX-2](https://ltx.video/blog/how-to-prompt-for-ltx-2)。
- 官方 distilled CLI：`python -m ltx_pipelines.distilled`，LTX-2.5 分文件权重，`--prompt`，
  `--num-frames`（`8 * k + 1`），宽高可被 32 整除，可选 `--image PATH FRAME_IDX STRENGTH`。
- 权重：[Lightricks/LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5)。论文：
  [arXiv:2601.03233](https://arxiv.org/abs/2601.03233)。

PE：**已实现**。Adapter：可选官方 CLI runner（`LTXVideoRunner` / `scripts/run_ltx25.sh`）。
Live runtime：本仓库**未验证**，直到留下本地生成记录。请用环境变量
`OMNI_LTX_CHECKPOINT` 指向分文件根目录（官方布局 `models/ltx-2.5`），不要提交机器路径。

## 路由

设置 `metadata.video_pe_profile=ltx`（默认视频 profile 仍为 `h3`）。

| 任务 | 媒体 | 生成时映射 |
| --- | --- | --- |
| `t2va` | 无 | 文生音视频 |
| `i2va` | 1 张图 | `--image PATH 0 STRENGTH` |
| `l2va` | 1 张图 | `--image PATH last STRENGTH` |
| `fl2va` | 2 张图 | 首帧 0 + 尾帧 `num_frames-1` |
| `ref2va` | ≥1 张图 | 每张静帧一条 `--image` |

请求/schema 必须带 `duration_seconds`。图像任务必须省略。不要把画幅、时长、分辨率写进
段落正文。runner 使用官方默认 24 fps，且 `num_frames = 8 * k + 1`（5 秒 → 121 帧）。

## 输出 schema（`LTXRewrite`）

字段：`task`、`profile=ltx`、`duration_seconds`、`action`、`movements`、`appearance`、
`environment`、`camera`、`lighting`、`audio`、`changes`、`generate_audio`。

默认渲染为单段段落（`ltx_render=paragraph`）；`ltx_render=json` 输出 JSON。

```bash
omni-rewriter expand examples/requests/ltx_t2va_workshop.json --output ltx
omni-rewriter expand examples/requests/ltx_i2va_portrait.json --output ltx
```

## 样例

- `tests/fixtures/ltx/t2va_workshop.json`
- `tests/fixtures/ltx/i2va_portrait.json`
- `examples/requests/ltx_*.json`
