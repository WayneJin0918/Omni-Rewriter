# Roadmap

Current Omni-Rewriter ships as an **agent harness**: typed schemas, deterministic validation,
and bounded LLM repairs. This already covers **video (H3)** and **image (Seedream /
Qwen-Image-Edit dialects)** prompt expansion.

The project exists to **bridge demos / marketing / private Context-IR** and what open or public
generators actually need. Community contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Near-term (maintainers)

- [x] Ingest public H3 skill contracts (`docs/references/jahnson-h3-skill-*.txt`) into PE rules,
      harness docs, and Cursor skills.
- [x] Ship low-res RAW vs PE gallery stills on the GitHub homepage.
- [x] Add CONTRIBUTING / PR / issue templates / CODE_OF_CONDUCT / SECURITY.
- [ ] Wire optional generation adapters for Seedream / Qwen-Image / Qwen-Image-Edit APIs
      (expand ≠ generate, same pattern as H3 / MiniMax adapters).
- [ ] Expand `experiments/image-pe-raw-vs-pe` with real image A/B once a generator is available.
- [ ] Finish camera/cut stress video set (`s11`–`s16`) expand + generate against H3.
- [ ] Strengthen image validators for quote-language consistency (Chinese `“”` vs English `""`).

## Community / research TODOs

- [ ] **Supervised fine-tune** a smaller writer on validated Omni-Rewriter traces
      (video H3 + Seedream/Qwen image PE), reducing repair rate and latency.
- [ ] **RL / preference optimization** (DPO / GRPO / RLOO) against downstream scores:
      H3 structural conformance, lip-sync / cut adherence judges, image aesthetic + instruction
      following judges.
- [ ] Add more image dialects: Flux, SD3, Ideogram, Kling image, Midjourney-style packing.
- [ ] Add more video dialects beyond MiniMax-H3 Base / Ref.
- [ ] Multilingual eval suites and public leaderboard hooks.
- [ ] Streaming expand API and batch JSONL expand CLI.
- [ ] Safer media sandboxing for untrusted reference images in shared deployments.

Contributions that keep the public contracts (`RewriteRequest`, `ImageRewrite`, `BaseRewrite`,
`Ref2VARewrite`) stable are preferred.
