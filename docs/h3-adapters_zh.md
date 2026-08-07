# H3 adapters

[English](h3-adapters.md) · [生成 adapter 总览](generation-adapters_zh.md)

Omni-Rewriter 提供两个异步 H3 adapter。它们按已实现 endpoint 契约提供兼容层，不是官方
SDK；生产使用前应核对当前服务文档、模型、字段、配额与可用区域。

## 本地 H3 adapter

`H3Client` 对接 SGLang 风格本地服务：

- `POST /v1/videos` 提交任务；
- `GET /v1/videos/{task_id}` 查询状态；
- 优先下载返回的 `download_url`、`video_url` 或 `url`，否则读取
  `/v1/videos/{task_id}/content`。

```python
import asyncio

from omni_rewriter.adapters import H3Client
from omni_rewriter.config import Settings
from omni_rewriter.models import RewriteRequest


async def main() -> None:
    request = RewriteRequest(
        prompt="A kite turns above a hill.",
        duration_seconds=6,
        metadata={"aspect_ratio": "16:9", "seed": "7"},
    )
    context = (
        "integrated_multimodal_description: [Shot 1] A kite rises.\n\n"
        "overall_soundscape: Soft wind.\n\n"
        "non_diegetic_music: Gentle strings."
    )
    async with H3Client(Settings.from_env().h3_client_config()) as client:
        task_id = await client.submit(request, context)
        result = await client.wait(task_id)
        await client.download(task_id, "result.mp4", result=result)


asyncio.run(main())
```

payload 包含 task、prompt、媒体 conditions、target 与 seed。I2VA、L2VA、FL2VA 均映射到
本地 `fl2va`，但 first/last frame 语义保留在 condition 中。H3 时长必须为 4–15 秒整数。
adapter 仅接受已知 override key，并限制轮询时长和下载大小。

## MiniMax API adapter

`MiniMaxClient` 实现：

- `POST /v2/h3_context_ir`
- `POST /v2/video_generation`
- `POST /v2/video_regeneration`
- `GET /v2/query/video_generation/{task_id}`

通过 `MINIMAX_API_KEY` 配置密钥，默认 API origin 为 `https://api.minimax.io`。如当前账号和
官方文档适用，可将 `MINIMAX_API_BASE` 设置为 `https://api.minimaxi.com`。

Context-IR 请求会把 prompt 与媒体引用映射为有序 content。T2VA 默认比例是 `16:9`，参考
任务默认 `adaptive`。regeneration 要求恰好一个 `source` 视频，并通过 `resolution` metadata
支持 `768P`、`1080P`、`2K`。

## 状态、失败与安全

两个 adapter 都归一化常见排队、运行、成功和失败状态；未知状态直接失败，避免无限轮询。
HTTP 超时限制单次请求，`poll_timeout` 限制整个轮询过程。提交默认不重试，避免重复产生付费
任务；需要重试时应使用目标服务支持的幂等机制并持久化 task ID。

- 密钥只放进进程环境或 secret manager，不写入请求、日志、trace 或仓库。
- 非 loopback 本地 H3 应增加认证与可信网络边界。
- 下载 URL 来自已配置服务；生产部署应使用 egress allowlist 缓解 SSRF。
- 发送到 MiniMax 的 prompt 与 URL 应符合数据分级、同意、留存与区域合规要求。
- 生成文件与服务响应 metadata 均视为不可信输入。

这些 adapter 不捆绑 MiniMax-H3 文档/权重或 Qwen 模型/权重；各自受上游许可和服务条款约束。
