---
name: video-craft
description: 把任意主题做成视频，按内容形态自动选择渲染后端。黑底 MG 概念科普（Remotion）、连续公式推导证明（Manim）、真终端操作教学（asciinema，V2）、产品宣传短视频（Hyperframes，V3）。内含渲染器无关的公共层（调研规范、口播文案原则、TTS 配音时间轴、分镜令牌系统、读帧 QC 脚本）、后端路由判据树、可插拔渲染后端、多 agent 并行构建协议与 QC 判据。Turn any topic into a narrated video — routes by content shape to the right renderer: motion-graphics concept explainers (Remotion), continuous formula derivations and proofs (Manim), real terminal recordings for command-line teaching (asciinema, V2), and product promos (Hyperframes, V3). Includes a renderer-agnostic core (research brief, narration principles, TTS timeline builder, storyboard tokens, frame-reading QC scripts), a routing decision tree, pluggable backends, and multi-agent build/QC protocols.
---

# video-craft

把任意主题做成视频。**先按内容形态选渲染后端，再走共用的生产流水线。**

前身是 `anything2explainer`（只做 Remotion 科普片）。本次拆分把渲染器无关的资产抽到
`core/`，把渲染相关的隔离到 `backends/`，新增 `routing/` 做后端选择。

## 何时用
- 用户给出主题要一条讲解/推导/教学/宣传视频；或给一篇文章要改成视频。
- 不适用：复刻某条现有视频、真人口播、实拍为主的片子。

## 四个确认点（必须停下来等用户回话）

1. **时长与语言 + 后端推荐**（阶段 1 派调研的同时问）：把 `routing/router.md` 的判定结果
   和时长表一起给用户，一问两答。用户否决推荐就按他的来。
2. **解说词定稿**（阶段 2，配音之前）：全文 + 章节划分 + 字数/预估时长，问「这版文案可以吗」。
   章名与 HUD 小节名单独列一行。多章片再把每个章界的两句并排列出。定稿后帧号全变，别改词。
3. **配音**（跑 `tts_build.py` 之前）：默认中文 edge-tts 云希、英文 kokoro `am_liam`。
   有偏好就让用户自备 wav 放 `script/audio.wav`，手填时间轴。
4. **前 30 秒样片**（阶段 5a，派其余各组之前）：问「风格 / 字号 / 配音语速 / 节奏可以吗」。
   在这里改是 1 个组的成本，等整片渲完再改是全部组。

## 流程（8 阶段）

```text
阶段 0  建项目      → 按路由结果调对应 backend 的 new_project.sh
阶段 1  调研        → core/research-brief.md（并行 1 agent）      【确认点 1】
阶段 2  解说词+时间轴 → core/narration-guidance.md + tts_build.py 【确认点 2、3】
阶段 3  分镜        → 按后端的格式写，core/render_storyboard.py
阶段 4  图元        → 按后端补（remotion: ui.tsx / manim: figures.py）
阶段 5a 打样        → 先做第 1 组，preview.sh 出前 30 秒          【确认点 4】
阶段 5b 并行构建    → 各组 1 agent，用后端的 agent-build-rules.md
阶段 6  渲染        → 后端的 render.sh → mp4 + fin_frames/
阶段 7  QC 与修复   → core/motion_check.py + frame_metrics.py + 后端的 qc-rules
阶段 8  交付        → 交付说明.md（记录所用后端与判定理由）
```

## 路由：先选后端

**必读 `routing/router.md`。** 简短版：

| 内容形态 | 后端 | 状态 |
|---|---|---|
| 连续公式推导 / 证明 / 符号变形 | `manim` | ✅ V1 |
| 概念科普讲解（X 是什么 / 怎么运作 / 为什么） | `remotion` | ✅ V1 |
| 真终端操作教学（安装 / 配置 / 命令执行） | `terminal` | ⏸ V2 |
| 产品宣传 / 社交短视频 / PR walkthrough | `hyperframes` | ⏸ V3 |

**判定不是看题材名，是看解说是否在连续操作符号**：
「傅里叶变换在干什么」→ remotion（讲直觉）；「从傅里叶级数推导傅里叶变换」→ manim（连续推导）。

未实现的后端命中时，**必须告知用户并说明降级方案**，不能静默换后端。

## 前置依赖（新机器必读）

### 所有后端

```bash
# core/ 的 Python 脚本需要这些。用 3.13 建 venv（3.14 缺 wheel 有风险）
uv venv --python 3.13 ~/.venvs/video-craft
uv pip install --python ~/.venvs/video-craft/bin/python numpy pillow scipy edge-tts
```

> ⚠ 没有这个 venv，`tts_build.py` / `motion_check.py` / `frame_metrics.py` 全都跑不起来。
> 这是 anything2explainer 踩过的坑：未文档化的 venv 依赖导致新机器上全流程卡死。

### remotion 后端

```bash
brew install ffmpeg          # 抽帧用
# Node 22+；项目由 new_project.sh 自动 npm install
```

### manim 后端

```bash
brew install pkg-config cairo pango     # pycairo 编译必需，缺了 manim 装不上
brew install --cask basictex            # MathTex 真公式排版必需；缺了退回 ASCII 近似
```

> 不装 basictex 也能跑（自动 `MANIM_TEX=text`），但公式只能用 `a/b` 这种 ASCII 近似。
> **推导片必须装 basictex**——公式排版质量是推导片的生命线。

## 目录结构

```text
video-craft/
├── SKILL.md                   ← 本文件
├── routing/
│   └── router.md              后端判据树 + 覆盖机制 + 边界案例
├── core/                      渲染器无关，所有后端共用
│   ├── research-brief.md          调研流程与事实规则
│   ├── narration-guidance.md      13 条口播文案原则
│   ├── narration-storyboard.md    解说词/分镜格式与令牌系统
│   ├── tts_build.py               配音 + timeline.json
│   ├── render_storyboard.py       分镜令牌替换
│   ├── motion_check.py            节奏 QC（读帧，跨后端）
│   ├── frame_metrics.py           构图 QC（读帧，跨后端）
│   ├── sheet.py                   缩略图网格（读帧）
│   └── lessons.md                 踩坑与根因
└── backends/
    ├── remotion/              概念科普片（原 anything2explainer）
    │   ├── template/               React 工程
    │   ├── scripts/                render/preview/still/test_render/new_project/selfcheck
    │   ├── reference/              style-guide/motion-vocabulary/composition-and-light/
    │   │                            agent-build-rules/agent-qc-rules/prompts/math-physics
    │   └── examples/rag/           样片（质量标尺）
    ├── manim/                 推导片
    │   ├── template/               Python 工程（common/ + scenes/）
    │   ├── scripts/
    │   ├── reference/
    │   └── README.md               环境实测结论（cairo/latex/pycairo）
    ├── hyperframes/           V3 预留
    │   └── README.md
    └── terminal/              V2 预留（用户已确认必做）
        └── README.md
```

## 核心文件速查

| 想干什么 | 用哪个 |
|---|---|
| 判定该用哪个后端 | `routing/router.md` |
| 派调研 agent | `core/research-brief.md` |
| 写解说词 | 先读 `core/narration-guidance.md`，格式看 `core/narration-storyboard.md` |
| 生成配音 + 时间轴 | `core/tts_build.py` |
| 生成分镜表 | `core/render_storyboard.py` |
| 节奏 QC | `core/motion_check.py` |
| 构图 QC | `core/frame_metrics.py` |
| 通读成片 | `core/sheet.py` |
| 建项目 | `backends/<后端>/scripts/new_project.sh` |
| 派构建 agent | `backends/<后端>/reference/agent-build-rules.md` |
| 派 QC agent | `backends/<后端>/reference/agent-qc-rules.md` |

## 后端特定的分镜格式

| 后端 | 分镜单元 | 格式 |
|---|---|---|
| remotion | 一个镜头（一句解说配一个画面） | `backends/remotion/reference/narration-storyboard.md` 的 `{S12.from-8}` 令牌 |
| manim | 一个推导步 | `backends/manim/reference/storyboard.md` 的 DP 格式 |

## QC 阈值按后端调

`core/motion_check.py` 的默认阈值是为 remotion 概念片定的，其它后端要调：

```bash
# remotion（默认）
python3 core/motion_check.py --frames fin_frames

# manim 推导片：静止上限放宽到 5s（操作后要留时间看清），关掉 hold 判据（无离场概念）
python3 core/motion_check.py --frames fin_frames --shots DP01:1-170 --still-max 5.0 --no-hold

# terminal 教学片（V2）：等命令输出时静止更久，预计 8-10s
```

## 硬性原则（所有后端通用）

1. **原创**：画面全部代码绘制或真实录制；不得使用任何现有视频的帧或片段。
2. **事实有出处**：画面上每个数字、术语、年份、人名必须能在调研文档里找到来源 URL。
3. **全片一个示例语境**：解说与画面用同一个贯穿例子。
4. **定稿后不改词**：帧号会被硬编码，改一个字全片重对位。
5. **后端要告知**：路由判定结果、降级方案，都必须让用户知道，不静默决定。

## 样片与质量标尺

- remotion 后端：`backends/remotion/examples/rag/`（4′35″，44 句、44 镜头）
  —— 开工前先看 `examples/rag/frames/overview_*.jpg` 建立标尺。
- manim 后端：**V1 无样片**，只验证了最小闭环。完整标尺样片留 V2。
- 反面对照：`backends/remotion/examples/contrast/`

## 从 anything2explainer 迁移来的项目

`~/Projects/ai-video/` 下的 `linear-function` / `transformer` / `a2e-fourier` / `py-course`
都是原 skill 做的，仍用旧布局（`template/scripts/`）。它们**继续可用**——
原 skill 保留为 deprecated 状态，不要删。

新项目一律用本 skill 的新布局。
