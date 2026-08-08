# 生成适配器与 runtime 兼容性

[English](generation-adapters.md) · [文档索引](index_zh.md)

## 边界：expand 不等于 generate

Omni-Rewriter 核心契约止于类型化 rewrite JSON 和渲染后的 PE 文本。`expand` 不会推断本机已
安装生成 runtime，不会把每个 profile 自动转换成所有厂商 payload，也不会提交生成任务。

adapter 是显式边界客户端，必须定义 payload 映射、认证、轮询、超时、幂等预期、下载上限和
版本假设。只有对精确路径完成集成测试，才能声称某个 prompt profile 与生成 runtime 兼容。

## 兼容性矩阵

| 模型族 | Prompt Expansion 支持 | 文档化生成 runtime/API | 仓库状态 |
| --- | --- | --- | --- |
| MiniMax H3 | 已实现 Base/Ref 视频 profile | MiniMax 公开 API；兼容本地 `/v1/videos` 服务 | 已实现 `MiniMaxClient`、`H3Client`，见 [H3 adapters](h3-adapters.md) |
| Seedream 图像 | 已实现 `seedream` 打包 | 厂商服务 | 未捆绑厂商专用生成 adapter |
| Qwen-Image / Qwen-Image-Edit | 已实现图像/编辑打包 | Qwen-Image-2512 在 SGLang-Diffusion 原生注册 | `OpenAIImagesClient`；本地 Diffusers A/B 配方 |
| HunyuanImage-3.0 | 可使用 Seedream T2I 打包 | 上游模型专用 vLLM fork | `HunyuanImageVLLMClient`；上游本地 runner 配方 |
| Wan | 可映射 H3 风格视频输出 | SGLang/vLLM-Omni 契约随版本变化 | `OmniVideosClient` + `WanOmniAdapter` |
| LingBot Video | `LingBotCaption` schema | 上游独立 runner | 有界 subprocess runner + 可选两阶段 rewriter |
| vLLM-Omni 路径 | 不推断兼容 | 上游发布广泛图像/视频支持矩阵 | **本仓库未验证** |

## 证据与限定

### Qwen-Image-2512：SGLang-Diffusion 原生支持

SGLang [v0.5.7 release](https://github.com/sgl-project/sglang/releases/tag/v0.5.7) 宣布
Qwen-Image-2512 day-zero 支持，其
[multimodal registry](https://github.com/sgl-project/sglang/blob/main/python/sglang/multimodal_gen/registry.py)
注册了 `Qwen/Qwen-Image-2512`。`OpenAIImagesClient` 将已校验 prompt 映射到
`/v1/images/generations`，并有界处理 base64 或 URL 结果；mock transport 测试覆盖该契约。
仓库仍不认证所有 SGLang 版本、硬件 backend、量化或 LoRA 组合。

### HunyuanImage-3.0：定制 vLLM fork

腾讯的 [vLLM 推理指南](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/vllm_infer/README.md)
要求安装 `feature/hunyuan_image_3.0` fork/branch，并启动模型专用服务。它是独立 runtime，
不能据此认定为 Omni-Rewriter writer backend 服务文本模型的 stock vLLM 能生成 Hunyuan 图像。
`HunyuanImageVLLMClient` 只实现该文档中的扩展字段与顶层 base64 `image`，不把它描述为
stock OpenAI 兼容接口。

### Wan：Omni 风格视频 API

Alibaba Model Studio 文档提供异步
[Wan 文生视频](https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference)
和[引用生视频](https://help.aliyun.com/en/model-studio/wan-video-to-video-api-reference) API。
`OmniVideosClient` 实现可配置 JSON/multipart submit → poll → content 契约；
`WanOmniAdapter` 映射模型、时长、尺寸、seed 与参考媒体。具体 endpoint 仍需按锁定的
SGLang/vLLM-Omni 版本验证。

### LingBot-World：独立 runner

LingBot-World 上游提供自己的
[`generate.py` / `torchrun` 推理路径](https://github.com/Robbyant/lingbot-world#inference)。
因此本项目使用显式有界 subprocess runner，不声称 LingBot 实现 `/v1/videos`。可选 rewriter
客户端将 base expansion 与 LoRA JSON mapping 保持为两个独立阶段。

### vLLM-Omni：上游列出，本地未验证

vLLM-Omni [支持模型表](https://docs.vllm.ai/projects/vllm-omni/en/latest/models/supported_models/)
目前列出 Qwen-Image、HunyuanImage 和 Wan 等变体。快速变化的上游表格不等于
Omni-Rewriter 集成测试。在加入可复现 adapter 测试前，端到端 prompt 形状、endpoint 行为、
版本兼容与生成质量均标记为**本仓库未验证**。

## 本地参考配方

以下脚本是可选运行配方，不属于核心依赖：

- `scripts/serve_sglang_qwen_image.sh`：加载
  `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-2512`。
- `scripts/serve_hunyuan_image3_vllm.sh`：通过腾讯 vLLM fork 启动 HunyuanImage-3.0。
- `scripts/serve_sglang_wan.sh`、`scripts/serve_vllm_omni_wan.sh`：WAN 参考启动脚本；
  使用前必须核对 runtime 版本支持。
- `scripts/serve_lingbot_rewriter.sh`：Qwen3.6-27B base expansion 加
  `/pfs/weiyang/lingbot-video-rewriter-lora` JSON mapping。
- `scripts/run_lingbot_video.sh`：通过 `/pfs/weiyang/lingbot-video` 与
  `/pfs/weiyang/lingbot-video-moe-30b-a3b` 独立生成。

LingBot 两阶段流程不替换默认 Omni-Rewriter agent，也不接入 `service.expand`。

## Adapter 贡献要求

新 adapter 应保持 opt-in 并与 `service.expand` 分离；映射到锁定版本的公开契约；拒绝不支持
任务/元数据；限制轮询、下载、重试与重定向；避免盲目重试付费或非幂等提交；提供 mocked
契约测试和明确标记的可选 live test；记录数据披露、密钥、许可、配额与版本证据；不得声称
了解私有内部实现或达到质量等价。
