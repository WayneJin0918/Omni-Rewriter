# 视频复刻 PE（Video reconstruct / v2pe）

状态：**v1 已接线**（CLI `omni-rewriter reconstruct` + `POST /v1/reconstruct` 观察 JSON）。  
相关：[`architecture.md`](../architecture.md)、[`dialects/h3-pe-harness.md`](../dialects/h3-pe-harness.md)、示例 [`examples/observation_kite.json`](examples/observation_kite.json)。

## 1. 动机

市面上已有大量 H3 成片和「理想 MV 片段」。要把它们变成可再生成的提示词，难点不是再写一句形容词，而是把成片里已经发生的剪辑契约读出来：

- 镜头切点必须落在真实时长之内，并写成 `[Shot N] At MM:SS.mmm,`
- 运镜、对白 `<d>[Language] …</d>`、声景 / 配乐分层必须符合公开 H3 语法
- 整段 mp4 塞进 VLM 既超上下文，又丢掉时间轴

现有 `omni-rewriter expand` **不能**直接承担这件事：

- [`RewriteRequest`](../../src/omni_rewriter/models/request.py) 遇到视频媒体会 `infer_task` → `ref2va`（生成侧引用，不是读片）
- [`MediaPreparer`](../../src/omni_rewriter/media_input.py) 把整文件打成 data URI（默认 20MB），H3/MV 成片会爆
- `MediaRole.SOURCE` 已存在，但只服务 MiniMax regeneration，不是「读片写 PE」

因此复刻是一条 **独立路径**：证据包 → 观察 JSON → 现有 draft / validate / repair → `BaseRewrite`。

**Expand ≠ generate。** 本设计只产出可校验的 H3 PE。真要出片，仍走已有 H3 adapter，另一步、另命令。  
**不声称**还原私有 Context-IR 或任何厂商内部中间表示。

## 2. 产品边界

| 做 | 不做（本阶段 / v1） |
| --- | --- |
| 本地读用户提供的短视频，抽出可核验证据 | 把整段 mp4 交给 Writer |
| 观察 JSON → 校验过的 H3 `t2va` PE | 自动 generate / 像素级拷贝 |
| 时长以 ffprobe 为准 | 让模型编造 `duration_seconds` |
| 对白有 ASR 则锁定原文；否则短句并标 `inferred` | 假装听清了 MV 歌词 |
| 人物/商标只描述外观 | 承诺身份还原或官方背书 |
| 成片留在用户磁盘 | 把 `.mp4` 提交进 git |

v1 默认输出 **t2va**（纯文复刻）。首尾帧会抽进证据包，供以后升 `i2va` / `fl2va`；那是「绑原片像素」的另一条产品，与文生复刻分开。

「把原片当 Ref2VA `<Video 1>`」也是另一条产品：引用保留，不是读片写分镜。

## 3. 流水线

建议 CLI 名（实现阶段再接线）：`omni-rewriter reconstruct`。

```text
local.mp4
  → ffprobe / ffmpeg          确定性证据包 EvidencePack
  → VLM + 可选 ASR            VideoObservation（带时间戳）
  → RewriteAgent draft/repair 现有 H3 schema + 校验
  → BaseRewrite + render      PE 文本 / JSON
  ╌╌ optional later ╌╌        H3 adapter generate
```

第二段复用 [`RewriteAgent`](../../src/omni_rewriter/agent.py)，不新写一套 repair。第一段 **不** 进入 `service.expand` 的媒体内联路径。

无视觉 Writer 时：`reconstruct` 硬失败，并提示可用抽帧 JSON 手工填写 `VideoObservation`（调试 / 无 GPU）。纯文本 Writer 只能做「已有 Observation → H3」，不能读片。

## 4. 证据包（本地、确定性）

依赖本机 `ffmpeg` / `ffprobe`。建议上限（实现时再钉死）：

- 时长 ≤ 45s（观察 / PE）；H3 **generate** 仍是公开 4–15s 窗口，更长源片 replay 取前 15s
- 帧降采样（短边约 512–768）
- 关键帧最多约 12–16 张 JPEG
- 音频抽成 wav；ASR 可选

| 层 | 来源 | 用途 |
| --- | --- | --- |
| 容器 | ffprobe | 真实 `duration_seconds`、fps、是否有音轨 |
| 镜头切 | 场景检测，或固定步长（如 0.5s） | shot 候选边界 |
| 关键帧 | ffmpeg JPEG，文件名带时间码 | 给 VLM 的「时间盖章」图 |
| 音频 | wav + 可选 ASR | 对白语言 / 原文；无 ASR 则只标有人声 / 无人声 |
| 首尾帧 | t=0 与 t=end | 将来 i2va/fl2va；v1 不写入 t2va 的 `<Picture N>` |

证据包是文件与探针字段，不是 PE。Writer 只看到降采样帧 + 探针摘要，看不到原始 2K 成片。

## 5. `VideoObservation`（Writer 只填这个）

对齐现有 [`AnalysisPlan`](../../src/omni_rewriter/agent.py) 的六层，但每条观察带时间。模型 **禁止** 改写 probe 给出的 `duration_seconds`。

```json
{
  "duration_seconds": 6.0,
  "invariants": ["…"],
  "shots": [
    {
      "index": 1,
      "start": "00:00.000",
      "end": "00:03.000",
      "visual_job": "…",
      "camera": "Static",
      "on_screen_state": "…"
    }
  ],
  "dialogue": [
    {
      "at": "00:04.200",
      "speaker": "S1",
      "language": "English",
      "text": "…",
      "inferred": false
    }
  ],
  "soundscape": "…",
  "music": "…",
  "uncertainties": ["…"]
}
```

约束：

- `shots[].camera` 使用公开 H3 运镜词表：Push In / Pull Out / Pan / Truck / Tilt / Pedestal / Arc Shot / Tracking Shot / Static / Shake / POV / Zoom / Roll（可加幅度 / 速度）
- `dialogue` 不得写入 `soundscape` / `music`
- `inferred: true` 的对白在 draft 里仍须写成合法 `<d>`，但观察层保留标记，便于人工改
- `uncertainties` 交给 repair，不要在观察里装懂

Draft 阶段把观察序列化进现有 H3 draft prompt，目标仍是 [`BaseRewrite`](../../src/omni_rewriter/models/base.py)：时间轴、markup、引用编号走同一套确定性校验。观察错了会在 `validate_timeline` 爆掉——这是这条路径比「让 VLM 直接写长 prompt」有价值的原因。

## 6. 与 `expand` 的关系

| | `expand` | `reconstruct`（设计） |
| --- | --- | --- |
| 输入 | 短意图 ± 引用媒体 | 本地成片 → 证据包 → 观察 |
| 媒体角色 | 首尾帧 / reference | 被观察对象，不是 Ref2VA 材料 |
| Writer | 可纯文本 | 观察步必须能吃图 |
| 输出 | 同一套 `BaseRewrite` / 方言 render | 同左（v1 = H3 t2va） |
| Generate | 永不默认调用 | 同左 |

公共契约（`RewriteRequest`、`BaseRewrite`）本阶段 **不改路由**。实现时若要共用 HTTP，应新增 `POST /v1/reconstruct`，而不是给 `/v1/expand` 塞一个巨型 mp4。

## 7. 版权、肖像、安全

- 默认只读本地路径；HTTP 成片沿用现有媒体沙箱思路，实现时再开
- 用户对成片有权使用；流水线不上传、不把媒体写入仓库
- MV / 广告里的可识别人脸与商标：观察与 PE 只写外观与场面，不写「就是某明星 / 某品牌广告片」
- 不把抽帧 JPEG 当开源样例提交

## 8. 风险

1. **质量上限是观察，不是 repair 次数。** 切点看错，H3 语法再对也是错片。
2. **无 ASR 的口型 / 歌词会编词。** 必须 `inferred`；组会演示应优先有对白轨道的短片。
3. **VLM 会漏切或多切。** 证据包里的候选边界是先验，观察可以合并，不能发明 probe 时长之外的时间码。
4. **与 Ref2VA 混淆。** 对外文案写清：reconstruct = 文生复刻契约；`<Video 1>` = 引用保留。

## 9. 实现顺序（v1 已完成 1–4）

1. ~~`EvidencePack` + ffmpeg 探针（无 Writer）~~
2. ~~`VideoObservation` Pydantic + fixture~~
3. ~~观察 → `RewriteRequest.prompt`（把观察 JSON 当作结构化意图）+ 现有 agent~~
4. ~~`omni-rewriter reconstruct path.mp4`~~
5. （更后）可选 generate；Seedance 方言；fl2va 升格

本地 Writer：`OMNI_WRITER_BACKEND_*` 指向带图的 OpenAI-compatible 服务。推荐
[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)（`scripts/serve/serve_sglang_qwen_writer.sh`）。
Live PE 质量对本 checkpoint 仍标 unverified，直到实际跑过 `reconstruct`。

## 10. 示例

合成观察（无成片）见 [`examples/observation_kite.json`](examples/observation_kite.json)。该文件同时带 `request` / `output`，可直接：

```bash
omni-rewriter validate docs/design/examples/observation_kite.json
omni-rewriter reconstruct --from-observation docs/design/examples/observation_kite.json
omni-rewriter reconstruct clip.mp4 --pack-only --pack-dir /tmp/pe-pack
omni-rewriter reconstruct clip.mp4
```
