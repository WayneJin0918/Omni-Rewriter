# Omni-Rewriter

[English README](README.md) · [架构](docs/architecture.md) ·
[H3 适配器](docs/h3-adapters.md) · [评测](docs/evaluation.md)

Omni-Rewriter 是一个独立、非官方、可本地运行的 Context-IR 替代方案：它将自然语言视频意图和
可选媒体引用转换为经过严格校验、面向 H3 的中间文本。项目包含类型化输入/输出、确定性校验、
有界的分析—起草—修复流程，以及本地和托管视频生成服务适配器。

本项目**不声称**复刻、逆向还原或等同于 MiniMax 官方 Context-IR，也不代表任何未公开的内部
实现。适配器只针对其代码明确实现的公开 API 形状。

## 能力

- 自动路由 T2VA、I2VA、首尾帧 FL2VA、尾帧 L2VA 和任意参考 Ref2VA。
- 对接 OpenAI-compatible 多模态 writer，附带本地 Qwen/vLLM 启动脚本。
- Pydantic 严格结构、时间轴/引用语法校验，以及次数受限的自动修复。
- CLI、可选 FastAPI 服务、本地 H3 与 MiniMax API 客户端。
- 单样本及 JSONL 清单的确定性评测。
- 有大小/MIME/重定向限制且默认阻断非公网地址的媒体加载。

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
[架构文档](docs/architecture.md)。

`H3Client` 对接本地 SGLang 风格 `/v1/videos` 服务；`MiniMaxClient` 对接 MiniMax 的
Context-IR、视频生成和视频再生成接口。两者都是显式调用的 Python 客户端，并不会在
`expand` 后自动提交视频任务。详见 [H3 适配器文档](docs/h3-adapters.md)。

## 配置

writer 主要变量为 `OMNI_WRITER_BACKEND_BASE_URL`、`OMNI_WRITER_BACKEND_MODEL`、
`OMNI_WRITER_BACKEND_API_KEY`、`OMNI_WRITER_TIMEOUT`、`OMNI_WRITER_RETRIES`、
`OMNI_WRITER_TEMPERATURE`、`OMNI_WRITER_MAX_TOKENS`、
`OMNI_WRITER_ENABLE_THINKING` 和 `OMNI_WRITER_MAX_REPAIRS`。

本地 H3 使用 `OMNI_WRITER_H3_BASE_URL`、`OMNI_WRITER_H3_API_KEY` 及
`OMNI_WRITER_H3_*` 超时、轮询和下载上限变量。MiniMax 使用 `MINIMAX_API_KEY`、
`MINIMAX_API_BASE` 及 `MINIMAX_*` 超时/轮询变量。默认值和完整列表见
[英文 README 的配置表](README.md#configuration) 与 [.env.example](.env.example)。

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
[评测文档](docs/evaluation.md)。

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
