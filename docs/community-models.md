# Community model backlog

[中文](community-models_zh.md) · [Contribution guide](CONTRIBUTING.md)

This is the explicit profile backlog for community contributions. An entry means “wanted,” not
“supported.” A complete contribution separates prompt expansion from generation and cites a public
upstream contract.

## Video

| Model family | Public upstream | Initial contribution target |
| --- | --- | --- |
| WAN | [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | Wan2.2 native PE profile (same WAN family), task routing, validator, renderer, fixtures |
| HunyuanVideo | [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | T2V/I2V profile, validator, optional adapter |
| CogVideoX | [THUDM/CogVideo](https://github.com/THUDM/CogVideo) | T2V/I2V dialect, fixtures, optional adapter |
| LTX-Video | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | Video/audio constraints, renderer, runtime fixture |
| Mochi 1 | [genmoai/mochi](https://github.com/genmoai/mochi) | T2V profile, validator, RAW/PE fixture |
| Step-Video | [stepfun-ai/Step-Video-T2V](https://github.com/stepfun-ai/Step-Video-T2V) | T2V/TI2V profile, validator, optional adapter |

## Image

| Model family | Public upstream | Initial contribution target |
| --- | --- | --- |
| FLUX.1 / Kontext | [black-forest-labs/flux](https://github.com/black-forest-labs/flux) | T2I/edit profile, preservation rules, fixtures |
| Stable Diffusion 3.5 | [Stability-AI/sd3.5](https://github.com/Stability-AI/sd3.5) | T2I/control profile, negative-prompt policy |
| Kolors | [Kwai-Kolors/Kolors](https://github.com/Kwai-Kolors/Kolors) | Chinese/English T2I profile and multilingual eval |
| PixArt-Sigma | [PixArt-alpha/PixArt-sigma](https://github.com/PixArt-alpha/PixArt-sigma) | T2I profile, resolution/ratio validation |
| Sana | [NVlabs/Sana](https://github.com/NVlabs/Sana) | T2I profile, renderer, runtime fixture |

## Unified

“Unified” covers models that combine multimodal understanding and generation, or several
generation modes, behind one model contract. It does not imply that every entry generates video.

| Model family | Public upstream | Initial contribution target |
| --- | --- | --- |
| Show-o2 | [showlab/Show-o](https://github.com/showlab/Show-o) | Understanding + image/video generation request mapping |
| Emu3 | [baaivision/Emu3](https://github.com/baaivision/Emu3) | Understanding/generation routing and tokenized-output contract |
| Janus-Pro | [deepseek-ai/Janus](https://github.com/deepseek-ai/Janus) | Understanding/T2I routing, renderer, fixtures |
| BAGEL | [ByteDance-Seed/BAGEL](https://github.com/ByteDance-Seed/BAGEL) | Understanding/T2I/edit routing and preservation rules |
| OmniGen2 | [VectorSpaceLab/OmniGen2](https://github.com/VectorSpaceLab/OmniGen2) | T2I/edit/in-context request mapping and fixtures |

## Definition of done

A model is not moved from this backlog to the supported matrix until the PR includes:

1. A typed task/profile contract and deterministic validation.
2. A renderer or explicit proof that the structured output is the final dialect.
3. RAW and expanded fixtures plus focused tests.
4. Public evidence for every runtime or API claim.
5. Documentation that labels PE, adapter, and live-runtime status separately.
6. No secrets, private prompt dumps, checkpoints, or full-resolution video blobs.

Use the project skill
[`omni-rewriter-model-contribution`](../.cursor/skills/omni-rewriter-model-contribution/SKILL.md)
to scaffold the change and run the contribution checks.
