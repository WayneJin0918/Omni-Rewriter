# 快速开始

[English](getting-started.md) · [文档索引](index_zh.md)

## 安装

Omni-Rewriter 需要 Python 3.11+。**只做 `validate` 不需要 GPU，也不需要 Writer。** `expand` 需要
OpenAI 兼容聊天接口。生成 checkpoint 是独立 runtime。

```bash
python -m pip install omni-rewriter
curl -fsSL -o kite.json \
  https://raw.githubusercontent.com/WayneJin0918/Omni-Rewriter/v0.1.0/tests/fixtures/t2va_kite.json
omni-rewriter validate kite.json
```

CI 用同一套校验：`uses: WayneJin0918/Omni-Rewriter@v0.1.0`（见
[`pe-validate-action.md`](pe-validate-action.md)）。`expand` 仍需要 Writer。

从 git clone 安装（CLI + 可选 HTTP）：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

通过环境变量配置 backend（项目不会自动加载 `.env`）。Gallery 浏览不需要 GPU。推荐：
**本地 SGLang Qwen3.6-35B-A3B（语言+视觉 Writer）+ 本地 SGLang MiniMax-H3**；托管 API Writer 作为备选。
Expand ≠ generate。

```bash
cp .env.example .env
set -a; source .env; set +a
```

### 推荐：SGLang Qwen3.6-35B-A3B（Writer）+ SGLang H3（~30B FL2VA）

```bash
# 终端 A — 语言+视觉 Qwen chat Writer
# https://huggingface.co/Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_MODEL=Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_SERVED_MODEL_NAME=Qwen/Qwen3.6-35B-A3B
bash scripts/serve/serve_sglang_qwen_writer.sh

# 终端 B — MiniMax-H3 FL2VA（可选生成）
export OMNI_WRITER_H3_MODEL=/path/to/MiniMax-H3/FL2VA
export OMNI_WRITER_H3_NUM_GPUS=8
bash scripts/serve/serve_sglang_h3.sh

# expand 所用 shell
export OMNI_WRITER_BACKEND_BASE_URL=http://127.0.0.1:8000/v1
export OMNI_WRITER_BACKEND_MODEL=Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_H3_BASE_URL=http://127.0.0.1:30010
```

脚本：[`serve_sglang_qwen_writer.sh`](../scripts/serve/serve_sglang_qwen_writer.sh)、
[`serve_sglang_h3.sh`](../scripts/serve/serve_sglang_h3.sh)。H3 客户端说明见
[H3 adapters](dialects/h3-adapters.md)。

### 备选：托管 API Writer

```bash
export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
export OMNI_WRITER_BACKEND_API_KEY=sk-...
```

可直接 `expand` 的请求见 [`examples/requests/`](../examples/requests/)。vLLM Qwen3.5 脚本
（`serve_qwen35_*.sh`）仍可作为 Writer 的备选启动方式。

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

Seedance 视频 PE（默认公开 Seedance 2.5 natural 模板；`seedance_render=fused` 为旧版标签文本；
`seedance_render=json` 输出 JSON）：

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```

详见 [Seedance PE](dialects/seedance-pe_zh.md)。未设置 `video_pe_profile` 时默认仍为 H3。

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
[图像 PE](dialects/image-pe_zh.md)。

## 校验与评测

```bash
omni-rewriter validate output.json
omni-rewriter eval output.json
omni-rewriter eval tests/fixtures/manifest.jsonl --manifest
```

这些命令检查 schema 和方言语法，不生成媒体，也不衡量感知质量。

## 复刻本地成片（v2pe）

把本地短 mp4 读成可校验的 H3 `t2va` PE。成片留在磁盘，`expand` 看不到原始字节。扩写 ≠ 生成。

```bash
omni-rewriter reconstruct clip.mp4 --pack-only --pack-dir /tmp/pe-pack
omni-rewriter validate docs/design/examples/observation_kite.json
omni-rewriter reconstruct --from-observation docs/design/examples/observation_kite.json
omni-rewriter reconstruct clip.mp4 --pack-dir /tmp/pe-pack
```

`POST /v1/reconstruct` 只收 `VideoObservation` JSON，不接收 mp4。本地 smoke：

```bash
PYTHONPATH=src python scripts/smoke_reconstruct.py
```

v1 观察最长 45s。H3 **generate** 仍是公开 4–15s 窗口，更长源片 replay 取前 15s。设计见 [视频复刻 PE](design/video-reconstruct-pe.md)。

## 可选 API

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' --data @examples/requests/t2va_kite.json
```

另有 `GET /health`、`POST /v1/validate`、`POST /v1/reconstruct`（只收观察 JSON），OpenAPI 文档位于 `/docs`。HTTP API 默认绑定
loopback；`create_app` 默认拒绝本地文件媒体路径（仅在受信主机上设置
`OMNI_WRITER_ALLOW_LOCAL_MEDIA=1`）。

## 仅在显式请求时生成

`expand` 返回类型化 JSON 和渲染文本。创建媒体必须显式连接兼容 adapter 或 runner。仓库当前
实现 H3/MiniMax 客户端；其他模型族使用不同上游 runtime，不能默认互换。详见
[生成适配器](dialects/generation-adapters_zh.md)。
