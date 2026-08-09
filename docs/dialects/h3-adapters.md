# H3 adapters

Omni-Rewriter has two asynchronous adapters. They are compatibility-oriented clients based on the
implemented endpoint contracts; they are not official SDKs. Consult the current service
documentation before production use because endpoint fields, models, quotas, and availability
can change.

## Local H3 adapter

`H3Client` targets an SGLang-style local service:

- `POST /v1/videos` submits a task.
- `GET /v1/videos/{task_id}` queries it.
- a returned `download_url`, `video_url`, or `url` is downloaded when present; otherwise
  `/v1/videos/{task_id}/content` is used.

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
    rendered_context = (
        "integrated_multimodal_description: [Shot 1] A kite rises.\n\n"
        "overall_soundscape: Soft wind.\n\n"
        "non_diegetic_music: Gentle strings."
    )
    async with H3Client(Settings.from_env().h3_client_config()) as client:
        task_id = await client.submit(request, rendered_context)
        result = await client.wait(task_id)
        await client.download(task_id, "result.mp4", result=result)


asyncio.run(main())
```

The payload includes task, prompt, media conditions, target settings, and seed. I2VA, L2VA, and
FL2VA all map to the local server's `fl2va` task while preserving first/last-frame semantics in
conditions. `short_edge`, `aspect_ratio`, and `seed` come from request metadata. H3 durations must
be integer seconds from 4 through 15.

The local adapter accepts only known top-level override keys and has a bounded polling deadline
and download size. An optional bearer token is sent when `OMNI_WRITER_H3_API_KEY` is set.

## MiniMax API adapter

`MiniMaxClient` implements these paths:

- `POST /v2/h3_context_ir`
- `POST /v2/video_generation`
- `POST /v2/video_regeneration`
- `GET /v2/query/video_generation/{task_id}` for polling

Set `MINIMAX_API_KEY`; the default global API origin is `https://api.minimax.io`. If applicable
to your account and current MiniMax documentation, the mainland China origin can be selected with
`MINIMAX_API_BASE=https://api.minimaxi.com`.

```python
import asyncio

from omni_rewriter.adapters import MiniMaxClient
from omni_rewriter.config import Settings
from omni_rewriter.models import RewriteRequest


async def main() -> None:
    request = RewriteRequest(
        prompt="A kite turns above a hill.",
        duration_seconds=6,
        metadata={"model": "MiniMax-H3", "ratio": "16:9"},
    )
    settings = Settings.from_env()
    async with MiniMaxClient(settings.minimax_client_config()) as client:
        task_id = await client.submit_h3_context_ir(request)
        result = await client.wait(task_id)
        print(result)


asyncio.run(main())
```

Context-IR requests map the prompt and every media reference into ordered content items. The
default ratio is `16:9` for T2VA and `adaptive` for reference tasks. Regeneration requires exactly
one `source` video and supports `768P`, `1080P`, or `2K` through the `resolution` metadata key.
Raw mappings can be supplied when a caller needs an API field not represented by
`RewriteRequest`.

## Status and failures

Both adapters normalize common queued/running, success, and failure status strings. Unknown
statuses fail closed instead of polling forever. Transport failures and malformed/error responses
raise typed Omni-Rewriter exceptions. A timeout covers each HTTP call, while `poll_timeout` bounds
the overall polling loop.

Retries are not performed for generation submissions because blind retries may duplicate paid or
expensive jobs. Applications needing retries should use an idempotency mechanism supported by the
target service and persist task IDs.

## Security

- Keep API keys in the process environment or a secret manager; never place them in requests,
  logs, traces, source, or `.env.example`.
- Keep local H3 on a trusted network and use authentication when it is not loopback-only.
- The local H3 downloader trusts the configured H3 service's result URL. Apply egress filtering
  and an allowlist proxy to mitigate SSRF; the byte cap limits size, not destination.
- Validate destination paths and avoid overwriting caller-sensitive locations.
- MiniMax receives prompts and referenced URLs. Apply your data-classification, consent,
  retention, and regional-compliance requirements before sending data.
- Treat generated files and service response metadata as untrusted.

## Licensing and service terms

These adapters do not bundle MiniMax-H3 documentation, MiniMax-H3 weights, Qwen models, or Qwen
weights. MiniMax services/documents/models and Qwen models are governed by their respective
licenses and terms. Apache-2.0 covers only the repository content identified in `LICENSE` and
`NOTICE`.
