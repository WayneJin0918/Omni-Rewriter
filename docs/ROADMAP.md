# Roadmap

Current Omni-Rewriter ships as a general **prompt-expansion framework**: transport-neutral
requests, typed profile outputs, deterministic validation, dialect rendering, and bounded LLM
repairs. H3 video, Seedream, and Qwen-Image image PE are its first profiles.

The project helps the community bridge polished demos and the explicit prompt contracts required
by public/open generators. It relies on public evidence rather than attempting to reproduce
undisclosed closed-source behavior. Expansion and generation remain separate. Community
contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Near-term (maintainers)

- [x] Ingest public H3 skill contracts (`references/jahnson-h3-skill-*.txt`) into PE rules,
      harness docs, and Cursor skills.
- [x] Ship low-res RAW vs PE gallery media on the GitHub homepage.
- [x] Add CONTRIBUTING / PR / issue templates / CODE_OF_CONDUCT / SECURITY.
- [x] Publish Video / Image / Unified contribution boards, a model-contribution AI skill, and
      deterministic PR contract checks.
- [ ] Define a stable profile/renderer extension interface for model families beyond H3 and the
      initial image dialects.
- [x] Add opt-in OpenAI-compatible Qwen image generation, Hunyuan custom-vLLM, Omni video/WAN,
      and independent LingBot adapters without coupling them to `expand`.
- [x] Add mock contract tests for image/video submit, polling, base64/URL decoding, download
      limits, WAN mapping, Hunyuan extension fields, and LingBot subprocess/rewriter behavior.
- [x] Publish H3 RAW vs PE demo surfaces under `docs/` (landing, showcase, homepage gallery).
- [ ] Run live SGLang/vLLM-Omni WAN compatibility matrices across pinned runtime releases.
- [ ] Strengthen image validators for quote-language consistency (Chinese `“”` vs English `""`).

## Community / research TODOs

- [ ] **Supervised fine-tune** a smaller writer on validated Omni-Rewriter traces
      (video H3 + Seedream/Qwen image PE), reducing repair rate and latency.
- [ ] **RL / preference optimization** (DPO / GRPO / RLOO) against downstream scores:
      H3 structural conformance, lip-sync / cut adherence judges, image aesthetic + instruction
      following judges.
- [ ] Add a bounded VLM-guided PE loop: generate candidates, judge full temporal/audio evidence,
      select or revise prompts, and record every iteration separately from deterministic repair.
- [ ] Implement the explicit Video, Image, and Unified profile targets in
      [`community-models.md`](community-models.md), one evidence-scoped PR at a time.
- [ ] Multilingual eval suites and public leaderboard hooks.
- [ ] Streaming expand API and batch JSONL expand CLI.
- [x] **Video reconstruct / v2pe (v1):** observe a local short clip (ffmpeg evidence pack →
      `VideoObservation`) then reuse draft/validate/repair to emit H3 `t2va` PE. Expand ≠
      generate; do not inline the source mp4 into `expand`. CLI `omni-rewriter reconstruct`,
      HTTP observation JSON at `POST /v1/reconstruct`. Design:
      [`design/video-reconstruct-pe.md`](design/video-reconstruct-pe.md). Optional generate and
      fl2va/i2va remain later.
- [ ] Safer media sandboxing for untrusted reference images in shared deployments.

Contributions that keep the public contracts (`RewriteRequest`, `ImageRewrite`, `BaseRewrite`,
`Ref2VARewrite`) stable are preferred.
