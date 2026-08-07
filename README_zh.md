# Omni-Rewriter

[English README](README.md) · [文档索引](docs/index_zh.md) ·
[快速开始](docs/getting-started_zh.md) · [贡献指南](CONTRIBUTING.md) ·
[架构](docs/architecture_zh.md) · [H3 PE 流程](docs/h3-pe-harness_zh.md) ·
[图像 PE](docs/image-pe_zh.md) · [生成适配器](docs/generation-adapters_zh.md) ·
[评测](docs/evaluation_zh.md) · [路线图](ROADMAP.md)

<p align="center"><a href="docs/assets/gallery/index.html">打开低清 RAW vs PE 视频 gallery</a></p>

## Prompt Expansion 通用框架

Omni-Rewriter 是一个开放、可扩展模型的 **Prompt Expansion（PE）框架**：把口语化的多模态
意图转换成**类型化、可校验、面向生成器的中间文本**。H3 视频、Seedream 风格图像和
Qwen-Image-Edit 风格图像打包是首批方言，不是框架能力的边界。

框架把职责拆开：

1. 与传输协议无关的请求记录意图、媒体、任务与元数据；
2. PE profile 分析需求并起草类型化中间表示；
3. 确定性校验器拒绝错误输出，或在固定预算内修复；
4. renderer 序列化为目标提示词方言；
5. 可选 adapter 才会把渲染结果提交给兼容生成器。

**expand 不等于 generate。** `omni-rewriter expand` 只产出经过校验的文本/JSON；它不会加载
生成权重、启动扩散/视频 runtime，也不会生成媒体。只有应用显式调用适配器或独立 runner
时，才进入生成阶段。

欢迎一起贡献：方言、校验器、适配器、实验、文档，以及后续的 SFT/RL 管线。详见
[CONTRIBUTING.md](CONTRIBUTING.md) 与 [ROADMAP.md](ROADMAP.md)。

本项目提供：

- 类型化输入输出与确定性校验
- 有界的 analyze → draft → repair agent
- MiniMax-H3 视频 PE（T2VA / I2VA / FL2VA / L2VA / Ref2VA）
- Seedream 风格与 Qwen-Image-Edit 风格的图像 PE 方言
- 可选的本地/托管生成适配器（expand ≠ generate）

本项目**不声称**复刻、逆向还原或等同于 MiniMax 官方 Context-IR、Seedream 内部实现，或任何
未公开厂商行为。公开示例与公开请求结构只能支持兼容性 profile，不能证明与私有实现等价。

## 模型与 runtime 兼容性

“PE 状态”表示 Omni-Rewriter 能否为该模型族组织或校验文本；“生成路径”描述上游 runtime，
不表示仓库捆绑该依赖，也不构成端到端保证。

| 模型族 | PE 状态 | 有证据的生成路径 | Omni-Rewriter 集成 |
| --- | --- | --- | --- |
| MiniMax H3 | 已实现视频 profile | MiniMax 公开 API 或兼容 `/v1/videos` 服务 | 已实现 `MiniMaxClient`、`H3Client` |
| Seedream 风格图像 | 已实现图像 profile | 厂商 API/runtime | PE 已实现；厂商专用 adapter 欢迎社区贡献 |
| Qwen-Image / Qwen-Image-Edit | 已实现图像/编辑打包 | Qwen-Image-2512 获得 SGLang-Diffusion 原生支持（[SGLang v0.5.7](https://github.com/sgl-project/sglang/releases/tag/v0.5.7)、[registry](https://github.com/sgl-project/sglang/blob/main/python/sglang/multimodal_gen/registry.py)） | 已实现 `OpenAIImagesClient`，包含本地 T2I/Edit 配方与真实 A/B |
| HunyuanImage-3.0 | 可使用 Seedream 风格 T2I PE | 上游文档要求[模型专用 vLLM fork](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/vllm_infer/README.md) | 已实现 `HunyuanImageVLLMClient` 与本地配方 |
| Wan | 可映射 H3 风格视频 PE | SGLang/vLLM-Omni 支持随版本变化 | 已实现 `OmniVideosClient` + `WanOmniAdapter`；live 兼容性取决于 runtime |
| LingBot Video | 类型化结构 caption | 上游独立推理 runner | 已实现 `LingBotCaption`、有界本地 runner 与可选两阶段 rewriter |
| vLLM-Omni 路径 | 不作预设 | 上游[支持矩阵](https://docs.vllm.ai/projects/vllm-omni/en/latest/models/supported_models/)列出多个图像/视频模型族 | **本仓库未验证**，不声明端到端兼容 |

runtime 支持变化很快；请锁定上游版本，并在自己的环境验证 payload、硬件支持和输出质量。
证据范围与集成边界见[生成适配器文档](docs/generation-adapters_zh.md)。

## 能力

- **视频 PE：** 自动路由 T2VA / I2VA / FL2VA / L2VA / Ref2VA，并做 H3 语法校验
 （规则参考 `docs/references/` 中的公开 H3 skill 归档）。
- **图像 PE：** `t2i` / `i2i` / `image_edit`，支持 Seedream 对齐与 Qwen-Image-Edit 对齐方言
 （`prompt` + `ratio`，Seedream 标签化渲染）。
- 对接 OpenAI-compatible 多模态 writer，附带本地 Qwen/vLLM 启动脚本。
- Pydantic 严格结构、时间轴/引用语法校验，以及次数受限的自动修复。
- CLI、可选 FastAPI 服务，以及 H3/MiniMax、OpenAI 图像、Omni 视频/WAN、Hunyuan vLLM 与 LingBot adapter。
- 单样本及 JSONL 清单的确定性评测；视频与图像 raw-vs-PE 对比实验（仓库内仅放低清 GIF/WebP）。
- 有大小/MIME/重定向限制且默认阻断非公网地址的媒体加载。

## Gallery（RAW vs PE）

<table>
  <tr><th>场景</th><th>RAW</th><th>Omni-Rewriter PE</th></tr>
  <tr><td><code>s01_dialogue</code></td><td><img src="docs/assets/gallery/s01_dialogue_raw.gif" width="360" alt="s01 RAW"></td><td><img src="docs/assets/gallery/s01_dialogue_pe.gif" width="360" alt="s01 PE"></td></tr>
  <tr><td><code>s06_sneaker</code></td><td><img src="docs/assets/gallery/s06_sneaker_raw.gif" width="360" alt="s06 RAW"></td><td><img src="docs/assets/gallery/s06_sneaker_pe.gif" width="360" alt="s06 PE"></td></tr>
  <tr><td><code>s09_noir</code></td><td><img src="docs/assets/gallery/s09_noir_raw.gif" width="360" alt="s09 RAW"></td><td><img src="docs/assets/gallery/s09_noir_pe.gif" width="360" alt="s09 PE"></td></tr>
  <tr><td><code>s10_phone_call</code></td><td><img src="docs/assets/gallery/s10_phone_call_raw.gif" width="360" alt="s10 RAW"></td><td><img src="docs/assets/gallery/s10_phone_call_pe.gif" width="360" alt="s10 PE"></td></tr>
</table>

本地实验视频存在后，可运行 `scripts/make_gallery_thumbs.sh` 重新生成。

### 真实图像生成

<table>
  <tr><th>模型/任务</th><th>RAW</th><th>Omni-Rewriter PE</th></tr>
  <tr><td>Qwen-Image-2512 T2I</td><td><img src="docs/assets/gallery/image/qwen_t2i_raw.webp" width="360" alt="Qwen T2I RAW"></td><td><img src="docs/assets/gallery/image/qwen_t2i_pe.webp" width="360" alt="Qwen T2I PE"></td></tr>
  <tr><td>Qwen-Image-Edit-2511</td><td><img src="docs/assets/gallery/image/qwen_edit_raw.webp" width="360" alt="Qwen Edit RAW"></td><td><img src="docs/assets/gallery/image/qwen_edit_pe.webp" width="360" alt="Qwen Edit PE"></td></tr>
  <tr><td>HunyuanImage-3.0 T2I</td><td><img src="docs/assets/gallery/image/hunyuan_t2i_raw.webp" width="360" alt="Hunyuan RAW"></td><td><img src="docs/assets/gallery/image/hunyuan_t2i_pe.webp" width="360" alt="Hunyuan PE"></td></tr>
</table>

[打开包含提示词与参考图的图像 gallery](docs/assets/gallery/image/index.html)。

## 快速开始

需要 Python 3.11+、可用的本地 checkpoint，以及与模型规模匹配的 GPU 资源。vLLM 是启动脚本
的运行时依赖，不属于 Omni-Rewriter 的 Python 安装依赖。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

启动开发 writer：

```bash
scripts/serve_qwen35_dev.sh
```

默认 checkpoint 为 `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen3.5-9B`，服务模型名为
`Qwen/Qwen3.5-9B`。大模型生产配置：

```bash
scripts/serve_qwen35_prod.sh
```

两份脚本均可覆盖模型、模型名、上下文长度、TP 和显存比例，并可追加 vLLM 参数：

```bash
OMNI_WRITER_MODEL=/models/Qwen3.5-9B \
OMNI_WRITER_SERVED_MODEL_NAME=my-qwen \
OMNI_WRITER_MAX_MODEL_LEN=16384 \
OMNI_WRITER_TENSOR_PARALLEL_SIZE=2 \
OMNI_WRITER_GPU_MEMORY_UTILIZATION=0.88 \
scripts/serve_qwen35_dev.sh --disable-log-requests
```

准备环境变量。程序只读取进程环境，不会自动加载 `.env`：

```bash
cp .env.example .env
set -a; source .env; set +a
```

创建 `request.json`：

```json
{
  "prompt": "一只手工风筝在傍晚微风中飞过草坡。",
  "duration_seconds": 6,
  "metadata": {"aspect_ratio": "16:9", "seed": "7"}
}
```

使用 CLI：

```bash
omni-rewriter expand request.json
omni-rewriter expand request.json --output h3
omni-rewriter validate output.json
omni-rewriter eval output.json
omni-rewriter eval examples/fixtures/manifest.jsonl --manifest
```

启动 API：

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' --data @request.json
```

另有 `GET /health` 与 `POST /v1/validate`；FastAPI schema 位于 `/docs`。

## 请求与任务路由

统一请求包含：

- `prompt`：必填文本；
- `duration_seconds`：正数；H3 适配器进一步限制为 4–15 的整数；
- `media`：最多 32 个 image/video/audio 引用，含语义 `role` 和 `uri`；
- `task`：可省略；
- `metadata`：字符串键值，用于比例、种子、分辨率等适配器参数。

无媒体推断为 `t2va`；单个首帧为 `i2va`；单个尾帧为 `l2va`；首帧加尾帧为
`fl2va`；其他非空组合为 `ref2va`。显式任务必须与媒体匹配，但任意非空媒体可以显式选择
`ref2va`。

## 架构与适配器

核心链路依次执行：请求校验与路由、媒体安全加载、多模态分析、结构化起草、确定性校验、
有限次数修复，以及 H3 文本渲染。CLI 和 HTTP 共用同一 service 层。完整边界和输出格式见
[架构文档](docs/architecture_zh.md)。

`H3Client` 对接本地 SGLang 风格 `/v1/videos` 服务；`MiniMaxClient` 对接 MiniMax 的
Context-IR、视频生成和视频再生成接口。两者都是显式调用的 Python 客户端，并不会在
`expand` 后自动提交视频任务。通用边界与 runtime 证据见
[生成适配器文档](docs/generation-adapters_zh.md)，H3 具体字段见
[H3 适配器英文文档](docs/h3-adapters.md)。

## 配置

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `OMNI_WRITER_BACKEND_BASE_URL` | `http://127.0.0.1:8000/v1` | OpenAI-compatible writer URL |
| `OMNI_WRITER_BACKEND_MODEL` | `Qwen/Qwen3.5-122B-A10B` | writer 服务模型名 |
| `OMNI_WRITER_BACKEND_API_KEY` | 未设置 | 可选 writer bearer token |
| `OMNI_WRITER_TIMEOUT` | `120` | writer 请求超时（秒） |
| `OMNI_WRITER_RETRIES` | `2` | writer 瞬时错误重试次数 |
| `OMNI_WRITER_TEMPERATURE` | `0.2` | writer 采样温度 |
| `OMNI_WRITER_MAX_TOKENS` | 未设置 | 可选 completion 上限 |
| `OMNI_WRITER_ENABLE_THINKING` | `false` | Qwen chat-template thinking 开关 |
| `OMNI_WRITER_MAX_REPAIRS` | `2` | 最大校验修复次数 |
| `OMNI_WRITER_H3_BASE_URL` | `http://127.0.0.1:30000` | 本地 H3 服务 |
| `OMNI_WRITER_H3_API_KEY` | 未设置 | 可选本地 H3 bearer token |
| `OMNI_WRITER_H3_TIMEOUT` | `60` | 本地 H3 请求超时 |
| `OMNI_WRITER_H3_POLL_INTERVAL` | `2` | 轮询间隔 |
| `OMNI_WRITER_H3_POLL_TIMEOUT` | `900` | 总轮询截止时间 |
| `OMNI_WRITER_H3_MAX_DOWNLOAD_BYTES` | `2147483648` | 视频下载上限 |
| `MINIMAX_API_KEY` | 未设置 | MiniMax bearer token |
| `MINIMAX_API_BASE` | `https://api.minimax.io` | MiniMax API origin |
| `MINIMAX_TIMEOUT` | `60` | MiniMax 请求超时 |
| `MINIMAX_POLL_INTERVAL` | `2` | MiniMax 轮询间隔 |
| `MINIMAX_POLL_TIMEOUT` | `900` | MiniMax 总轮询截止时间 |

兼容旧变量 `OMNI_WRITER_BASE_URL`、`OMNI_WRITER_MODEL`、`OMNI_WRITER_API_KEY` 和
`MINIMAX_BASE_URL`。脚本专用 vLLM 变量见[架构文档](docs/architecture_zh.md)。

## 安全与 SSRF

- HTTP(S) 媒体会在初始请求和每次重定向前解析主机；默认拒绝私有、回环、链路本地及其他
  非公网地址，并限制重定向、超时、MIME 和字节数。
- API 同时允许读取本地路径。若直接暴露给不可信调用者，可能泄露服务账号可读文件；生产环境
  必须在应用边界禁用/授权本地路径，并使用低权限账号、容器、网络出口过滤及身份认证。
- DNS 检查不等于完整沙箱。本地 H3 服务返回的下载 URL 也应视为不可信，必须限制服务网络出口。
- 不要提交 `.env`、密钥、敏感 trace、用户提示词或生成媒体；远程暴露前增加 TLS、认证、
  授权、速率限制和内容安全策略。

## 评测与限制

内置评测检查 schema、时间轴、字段完整度、镜头/时间戳数量和引用定义一致性，不调用模型。
它不评估视频感知质量、提示词忠实度、安全性或人类偏好。详见
[评测文档](docs/evaluation_zh.md)。

本项目不是官方 MiniMax 软件；本地格式通过不保证任何生成器的等价行为或质量。服务不内置
认证、限流、审核、持久化、队列或分布式 worker。媒体默认每项上限 20 MiB，且仅允许固定
MIME 集合。

## 开发

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python -m build
```

项目代码使用 Apache-2.0，见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。仓库不包含
MiniMax-H3 文档或权重，也不包含 Qwen 模型/权重；它们分别受各自许可和使用条款约束。
