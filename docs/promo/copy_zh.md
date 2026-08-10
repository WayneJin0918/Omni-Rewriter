# Omni-Rewriter — 中文宣传稿

## 标语

**从随口一句，到可投产的提示词。**

## 一句话

Omni-Rewriter 是开源的提示词扩展（PE）框架：把日常的视频 / 图像意图，变成可校验、可修复、可对接生成后端的结构化提示。

## 短文案（社交 / README）

大多数提示停在「许愿」。Omni-Rewriter 补上缺失的结构——时长、镜头语法、对白标签与修复闭环——让 MiniMax-H3 等配置档先拿到更稳的 PE，再交给生成。开源，欢迎试用与贡献。

## 中长文案（落地页 / 媒体）

Omni-Rewriter 是开放、可扩展模型接入的 **提示词扩展（PE）** 框架。你给出一句随意的人话；框架负责起草类型化结构、做确定性校验，并在边界内修复，直到可以交给生成后端。

面向公众的 MiniMax-H3 PE 配置档，用同种子对照展示扩展前后的差异：时间轴、对白与运镜往往更清楚。图像侧（Seedream / Qwen-Image 等）与社区适配器同一思路——兼容性声明如实标注。

## 行动号召

- 进入主站了解更多
- Star 仓库：https://github.com/WayneJin0918/Omni-Rewriter

## 语气注意

- 少写「先看短片再点进去」这类站内导览口吻；宣传讲产品价值即可。
- 少喊「扩展 ≠ 生成」口号；需要时用「先整理结构，再交给生成」自然带过。
- 不宣称复现私有厂商 Context-IR，或不经核验的运行时兼容。
- 默认宣传矩阵不含 Seedance，除非明确加入。

## 小红书

配图/视频：promo 短片或对照截图。语气偏实测分享，少硬广。

**标题（任选）**
1. 别再只会说「帮我做一个酷炫视频」了
2. 开源工具：把废话 prompt 扩成可投产版本
3. 同一种子，差的不是运气是结构

**正文**
做视频 / 图像生成最崩溃的，不是模型不够强，是 prompt 太「许愿」。

一句「make a cool video somehow」，模型当然会猜。  
我们开源了 Omni-Rewriter：先做 **提示词扩展（PE）**——补时长、镜头、对白、校验和修复——再交给生成。

主站能看到 MiniMax-H3 上扩展前后的对照，结构差在哪一目了然。

🔗 GitHub：WayneJin0918/Omni-Rewriter

#AIGC #提示词工程 #开源项目 #AI视频 #Prompt

## 群聊传播

适合微信 / Slack / Discord 直接粘贴。语气偏软介绍，不喊口号；侧重 PE 流水线与当前 T2V / T2I 模型矩阵（不含 Seedance）。状态含已落地 PE / 适配中 / 规划中，群聊里点到即可，不必逐条甩徽章。

### 短版

分享一下开源项目 Omni-Rewriter：把随口一句视频/图像意图，走完分析 → 起草 → 校验 → 有界修复 → 渲染，整理成可对接生成后端的结构化提示词（PE）。目前覆盖 T2V 与 T2I 多条模型线（含已落地 PE、适配中与规划中）。欢迎围观～
GitHub：https://github.com/WayneJin0918/Omni-Rewriter
主站：https://waynejin0918.github.io/Omni-Rewriter/

### 中版

Omni-Rewriter 是开源的提示词扩展（PE）框架：一句日常意图进来后，按「分析 / 起草 / 校验 / 有界修复 / 方言渲染」走完流水线，再交给可选的生成适配。

当前矩阵偏 T2V 与 T2I（不含 Seedance），覆盖已落地 PE、适配中与规划中：
· T2V：MiniMax-H3、LingBot Video、WAN、HunyuanVideo、CogVideoX、LTX-Video、Mochi 1、Step-Video
· T2I：Seedream、Qwen-Image、HunyuanImage-3.0、FLUX.1 / Kontext、Stable Diffusion 3.5、Kolors、PixArt-Sigma、Sana

感兴趣可以看看仓库和主站～
GitHub：https://github.com/WayneJin0918/Omni-Rewriter
主站：https://waynejin0918.github.io/Omni-Rewriter/

### 长版（群公告，参考开源项目介绍口吻）

大家好，借贵群宣传一下我们最近为社区做的一点小贡献：

(1) 我们开源了 Omni-Rewriter：一个面向图像与视频生成的开源提示词扩展（PE）框架。代码与文档站已公开：
https://github.com/WayneJin0918/Omni-Rewriter
https://waynejin0918.github.io/Omni-Rewriter/
希望把「随口一句意图 → 可校验、可对接后端的结构化提示词」这条链路，做成社区可复用的基础能力。

(2) 方法上，Omni-Rewriter 是一个有界的 Agent Harness 流水线：Analyze（分析路由）→ Draft（按方言 schema 起草）→ Validate（确定性校验）→ Repair（有界修复）→ Render（输出 PE 文本/JSON）。Writer LM 只参与起草与修复；校验与渲染保持确定性。先把结构整理清楚，再交给可选的生成适配。

(3) 当前模型矩阵覆盖 T2V 与 T2I（宣传矩阵不含 Seedance），并如实区分已落地 PE / 适配中 / 规划中：
· T2V：MiniMax-H3（PE）、LingBot Video（适配中）、WAN（待核验）、HunyuanVideo / CogVideoX / LTX-Video / Mochi 1 / Step-Video（规划中）
· T2I：Seedream、Qwen-Image（PE）、HunyuanImage-3.0（适配中）、FLUX.1 / Kontext、Stable Diffusion 3.5、Kolors、PixArt-Sigma、Sana（规划中）
其中 MiniMax-H3 是目前对外展示较完整的视频 PE 实例；欢迎对照主站示例与仓库文档一起看。

欢迎大家 star、试用，也欢迎一起交流、提 issue / PR～后续我们会持续迭代，为社区贡献更多内容～
