# 快速开始

[English](getting-started.md) · [文档索引](index_zh.md)

## 安装

Omni-Rewriter 需要 Python 3.11+。Python 包负责扩写和校验提示词；模型服务与生成 checkpoint
属于独立的 runtime 选择。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

通过环境变量配置 OpenAI-compatible writer backend。项目不会自动加载 `.env`。Gallery 浏览不需要
GPU；`expand` 需要任意能返回结构化 JSON 的 chat 端点。

```bash
cp .env.example .env
# Hosted Writer（无需本地 checkpoint）：
# export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
# export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
# export OMNI_WRITER_BACKEND_API_KEY=sk-...
set -a; source .env; set +a
```

可直接 `expand` 的请求见 [`examples/requests/`](../examples/requests/)。仓库内 Qwen/vLLM
脚本只是 Writer 的开发便利工具，不是图像/视频生成 runtime。

## 扩写视频意图

视频任务必须提供 `duration_seconds`：

```json
{
  "prompt": "一只手工风筝在傍晚微风中飞过草坡。",
  "duration_seconds": 6,
  "metadata": {"aspect_ratio": "16:9"}
}
```

```bash
omni-rewriter expand examples/requests/t2va_kite.json
omni-rewriter expand examples/requests/t2va_kite.json --output h3
```

无媒体时推断为 `t2va`；首帧、尾帧、首尾帧组合及任意引用分别路由到 `i2va`、`l2va`、
`fl2va` 和 `ref2va`。

Seedance 视频 PE（默认融合 natural 文本；`seedance_render=json` 输出 JSON）：

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```

详见 [Seedance PE](seedance-pe_zh.md)。未设置 `video_pe_profile` 时默认仍为 H3。

## 扩写图像意图

图像任务必须省略 `duration_seconds`：

```json
{
  "prompt": "制作雨夜霓虹店铺海报，标题文字必须原样保留。",
  "task": "t2i",
  "metadata": {"image_pe_profile": "seedream"}
}
```

`seedream` 输出视觉蓝图式 render；`qwen_image_edit` 输出命令式编辑指令。请求与比例限制见
[图像 PE](image-pe_zh.md)。

## 校验与评测

```bash
omni-rewriter validate output.json
omni-rewriter eval output.json
omni-rewriter eval tests/fixtures/manifest.jsonl --manifest
```

这些命令检查 schema 和方言语法，不生成媒体，也不衡量感知质量。

## 可选 API

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' --data @examples/requests/t2va_kite.json
```

另有 `GET /health`、`POST /v1/validate`，OpenAPI 文档位于 `/docs`。HTTP API 默认绑定
loopback；`create_app` 默认拒绝本地文件媒体路径（仅在受信主机上设置
`OMNI_WRITER_ALLOW_LOCAL_MEDIA=1`）。

## 仅在显式请求时生成

`expand` 返回类型化 JSON 和渲染文本。创建媒体必须显式连接兼容 adapter 或 runner。仓库当前
实现 H3/MiniMax 客户端；其他模型族使用不同上游 runtime，不能默认互换。详见
[生成适配器](generation-adapters_zh.md)。
