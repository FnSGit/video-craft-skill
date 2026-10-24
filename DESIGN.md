# video-craft 统一视频制作 skill 设计方案

> 状态：设计定稿（2026-10-24），三项决策已确认，进入实现
> 前身：anything2explainer（Remotion 科普讲解 skill）
> 决策依据：用户确认的三项选择——新 skill 取代原 skill；第一版做架构+Remotion+Manim；自动路由+可覆盖

---

## 〇、已确认决策（2026-10-24）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | math.tsx + LaTeX 公式管线归属 | 留在 remotion 后端；与 manim 自带 LaTeX 的能力重复可接受（概念片 vs 推导片各用各的） |
| 2 | Manim 样片时机 | V1 只验证最小闭环（15 秒推导片），完整质量标尺样片留 V2 |
| 3 | Terminal 后端 | **V2 必须做真终端录制**（asciinema 路线），不接受 CodeBlock-only 方案；py-course 已验证 CodeBlock 够用概念讲解，但真命令操作必须真录制 |

---

## 一、问题定义

### 1.1 现状

`anything2explainer` 是一条成熟的**单一渲染后端**视频生产流水线：

- 渲染后端固定为 Remotion 4（React 19 + TypeScript）
- 图元库、渲染脚本、构建规则、QC 判据全部按"黑底 MG 科普片"设计
- 已产出 5+ 部成片，样片《RAG 与知识库》4′35″ 作为质量标尺
- 已衍生出数学/物理能力包（`math.tsx` + LaTeX 公式管线）

### 1.2 已识别的能力边界

anything2explainer 在 SKILL.md 中**主动承认**的边界：

> 不适合以严格推导 / 逐步证明 / 公式变形为主的片子——本流程是「一句解说 = 一个镜头」，推导需要连续演算不切的节奏，而且每步推导没有大数字可当主角，会被自己的 QC 判据反复判不合格（这类内容建议用 Manim）。

这个边界的**根因不是实现不足，而是范式冲突**：

| anything2explainer 的核心假设 | 数学推导的实际需求 |
|---|---|
| 一句解说 = 一个镜头，镜头可切 | 连续演算，上一步产物是下一步输入，不能切 |
| 每镜头一个主角，主角 ≥170px 带光 | 每步推导的公式通常很小，没有"主角" |
| 元素入场后不许完全静止 >3s | 推导中间需要静止让观众看清 |
| 紫柔光给当前重点术语 | 推导里"重点"是每一步，全紫等于全不紫 |

**结论：这不是靠补图元能解决的，必须换渲染范式。**

### 1.3 但大量资产是渲染器无关的

代码级核实结论——anything2explainer 的资产可分为两层：

**渲染器无关层（约占流程价值的 60%）**

| 资产 | 无关性证据 |
|---|---|
| `reference/research-brief.md` | 纯方法论，产出事实文档 |
| `reference/narration-guidance.md` | 13 条文案原则，原文写明"in any language" |
| `reference/narration-storyboard.md` | 分镜令牌系统，时间轴是 JSON |
| `template/scripts/tts_build.py` | 输入 narration.txt，输出 wav + `timeline.json` |
| `template/scripts/render_storyboard.py` | 读 `timeline.json`，输出 markdown 分镜表 |
| `template/scripts/motion_check.py` | **读渲染输出帧图像**，逐帧分析像素变化 |
| `template/scripts/frame_metrics.py` | **读帧图像**，量最大物体高度/柔光/紫色 |
| `template/scripts/sheet.py` | **读帧**生成缩略图网格 |
| `reference/composition-and-light.md` §7 | "持续动作+落位停留"是节奏原则 |
| `reference/lessons.md` 大部分 | 踩坑根因（磁盘/bundle/穿字幕带） |

**关键洞察**：三个 QC 脚本（motion_check / frame_metrics / sheet）是**读像素的**，
不关心帧是谁渲的。换 Manim 渲出来的帧，现有 QC 照样能跑。
这是统一 skill 最有价值的复用点。

**渲染器绑定层（必须按后端隔离）**

| 资产 | 绑定原因 |
|---|---|
| `template/src/**/*.tsx` | React 组件 + Remotion API |
| `template/scripts/render.sh` / `preview.sh` / `still.sh` / `test_render.sh` | 调 `npx remotion render` |
| `template/scripts/new_project.sh` | 复制 Remotion 模板 |
| `template/scripts/selfcheck.py` | 扫 Remotion 组件名（GlitchIn/LightSweep） |
| `template/scripts/gen_mathjax_svg.mjs` | 给 `formula.tsx` 供 SVG |
| `reference/agent-build-rules.md` | 写死"Remotion 4 + React 19" |
| `reference/style-guide.md` / `motion-vocabulary.md` 部分 | 图元命名绑定组件 |

---

## 二、目标架构

```
video-craft/                          ← 新统一 skill（安装于 ~/.pi/agent/skills/）
├── SKILL.md                          ← 入口：路由 + 8 阶段流程 + 4 确认点
├── core/                             ← 渲染器无关，继承自 anything2explainer
│   ├── research-brief.md                 调研流程与事实规则
│   ├── narration-guidance.md             13 条文案原则
│   ├── narration-storyboard.md           解说词/分镜格式与令牌系统
│   ├── tts_build.py                      配音 + timeline.json 生成
│   ├── render_storyboard.py              分镜令牌替换
│   ├── motion_check.py                   节奏 QC（读帧，跨后端）
│   ├── frame_metrics.py                  构图 QC（读帧，跨后端）
│   ├── sheet.py                          缩略图网格（读帧）
│   └── lessons.md                        踩坑与根因
│
├── routing/                          ← 新增：内容形态路由
│   ├── router.md                          判据树 + 覆盖指令
│   └── prompt_classifier.md               给主会话用的判定提示词
│
└── backends/
    ├── remotion/                     ← 从 anything2explainer 迁移（V1 实现）
    │   ├── template/                       React 工程（原 anything2explainer/template）
    │   ├── scripts/                        render/preview/still/test_render/new_project/selfcheck
    │   ├── reference/                      style-guide, motion-vocabulary, composition-and-light,
    │   │                                    agent-build-rules, agent-qc-rules, prompts
    │   └── examples/                       examples/rag（样片）
    │
    ├── manim/                        ← 新建（V1 实现）
    │   ├── template/                       Python 工程骨架
    │   ├── scripts/                        渲染/单帧/preview
    │   ├── reference/                      推导片分镜规范、构建规则、QC 判据
    │   └── examples/                       待补：一条傅里叶推导样片
    │
    ├── hyperframes/                  ← V2 预留（接口 + README）
    │   └── README.md                       设计意图与接入条件
    │
    └── terminal/                     ← V2 预留（接口 + README）
        └── README.md                       设计意图与接入条件
```

### 2.1 分层原则

```
┌─────────────────────────────────────────────┐
│  SKILL.md           路由 + 流程编排           │  变：后端选择
├─────────────────────────────────────────────┤
│  routing/           内容形态判定               │  变：判据树
├─────────────────────────────────────────────┤
│  core/              调研/文案/时间轴/QC       │  不变：所有后端共用
├─────────────────────────────────────────────┤
│  backends/<x>/      图元/渲染/构建规则/QC适配 │  变：按后端
└─────────────────────────────────────────────┘
```

**判定标准**：一个资产该放 core 还是 backend？
- 它是否消费或产出一个中立的中间格式（`timeline.json` / 帧图像 / 解说词文本）？→ core
- 它是否知道"帧是怎么画出来的"？→ backend

---

## 三、内容形态路由设计

### 3.1 判据树

```text
输入：主题 + 时长 + 语言
  │
  ├─[R1] 内容以「连续公式推导 / 证明 / 符号变形」为主体？
  │      判据：解说词含 ≥3 个"由上式可得/代入/化简/因此"类推导连接词，
  │           且画面主体是公式而非概念图示
  │      YES → manim
  │
  ├─[R2] 内容是「产品宣传 / 社交短视频 / PR walkthrough」？
  │      判据：有时长 <60s 倾向，或明确提到产品/版本/发布/changelog
  │      YES → hyperframes（V1 未实现，回退 remotion 并告知）
  │
  ├─[R3] 内容是「命令行操作 / 环境搭建 / 敲代码教学」为主体？
  │      判据：主题是安装/配置/命令教学，且步骤需真实执行可见
  │      YES → terminal（V1 未实现，回退 remotion + CodeBlock 图元并告知）
  │
  └─[R4] 兜底：概念科普讲解（讲清楚 X 是什么/怎么运作）
         YES → remotion（原 anything2explainer 能力）
```

### 3.2 覆盖机制

三条路径，优先级从高到低：

1. **用户显式指定**：调用时说"用 manim 做" / `/video-craft manim <主题>` → 直接采用
2. **主会话判定后告知**：自动判定出后端，在**确认点 0** 说明判定理由，用户可否决
3. **默认兜底**：判定不确定时选 remotion（能力最成熟、有样片标尺）

### 3.3 确认点 0（新增，合并进现有确认点 1）

不新增独立交互轮次，而是在原确认点 1（时长与语言）的提问里**附带后端推荐**：

```text
想做多长？中文还是英文？
顺便：这个主题我判定用「Manim（数学推导）」后端，因为解说词会以连续公式推导为主。
如果你其实想要 MG 概念片风格，告诉我，我换成 Remotion 后端。
```

这样既保持"自动判定"的流畅，又保留了覆盖能力，且不增加交互轮次。

---

## 四、核心流程（8 阶段，对齐原 skill）

### 阶段 0 建项目
- **新增**：按路由结果调用对应 backend 的 `new_project` 脚本
- 原有 `template/scripts/new_project.sh` → `backends/remotion/scripts/new_project.sh`
- 新增 `backends/manim/scripts/new_project.sh`

### 阶段 1 调研（20 分，1 agent 并行）
- **不变**：`core/research-brief.md` 原样继承
- **新增**：派单时告知研究员产出用途（影响调研深度——manim 推导片需要更精确的公式与定义来源）

### 阶段 2 解说词与时间轴（20 分，主会话）
- **不变**：`core/narration-guidance.md` + `core/narration-storyboard.md`
- **不变**：`core/tts_build.py` 产出 `timeline.json`
- **新增**：`narration.txt` 增加可选的**后端提示注释**（`# BACKEND manim`），供主会话核对路由

### 阶段 3 分镜（25 分，主会话）
- **分叉**：
  - remotion 后端 → 原 `storyboard_src.md` 令牌流程 + `render_storyboard.py`
  - manim 后端 → 新的推导分镜格式（见 §5.2）
- `render_storyboard.py` 保持 core（读 `timeline.json`，输出 markdown）

### 阶段 4 图元（10 分）
- **分叉**：
  - remotion → `src/ui.tsx` / `fx.tsx` 补语义图标
  - manim → `manim_template/figures.py` 补自定义 Mobject
- 检查产物仍走各后端的 `still` 脚本

### 阶段 5a 打样（15 分，1 agent）
- **不变**：先做第 1 组，`preview.sh` 出前 30 秒给用户确认
- 各后端有自己的 `preview.sh`

### 阶段 5b 并行构建（40 分）
- **分叉**：派单用各后端 `reference/agent-build-rules.md`
- **不变**：并行度、BUILD_NOTES、自检 still 要求

### 阶段 6 渲染（5 分）
- **分叉**：各后端 `render.sh`
- **统一产出**：`renders/<slug>_v1.mp4` + `fin_frames/`（供 core QC 脚本消费）

### 阶段 7 QC 与修复（60–90 分）
- **跨后端复用**：`core/motion_check.py` + `core/frame_metrics.py` + `core/sheet.py`
- **后端特定**：`agent-qc-rules.md`（构图/光判据按后端不同）
- manim 后端新增：公式正确性核对（对照调研文档逐式验证）

### 阶段 8 交付
- **不变**：`交付说明.md` 格式
- **新增**：记录所用后端与判定理由

---

## 五、Manim 后端详细设计

### 5.1 工程骨架

```text
backends/manim/template/
├── pyproject.toml              # uv 管理，Python 3.14
├── manim.cfg                   # 1280x720@30fps，与 remotion 后端画幅一致
├── .venv/                      # uv venv（不入库）
├── narration.txt               # 解说词（同 core 格式）
├── script/                     # tts_build.py 产出
│   ├── timeline.json
│   ├── timeline.md
│   └── 分镜表.md
├── scenes/                     # 每个镜头一个 Scene 文件
│   ├── SC01.py
│   ├── SC02.py
│   └── ...
├── figures.py                  # 自定义 Mobject（复用）
├── common/
│   ├── style.py                # 配色/字号（对齐 remotion 调色板）
│   └── subtitle.py             # 字幕 Mobject（复用 tts_build 产出的 subs）
└── scripts/
    ├── new_project.sh
    ├── render.sh               # manim render 全片
    ├── still.sh                # 单帧导出
    ├── preview.sh              # 前 N 秒
    └── test_render.sh          # 低画质快渲
```

### 5.2 推导片分镜格式

与 remotion 后端的关键差异：**分镜单元是"推导步"而非"镜头"**。

```markdown
# script/storyboard_src.md（manim 后端）

## 全局约束
- 推导主线：从 <起点式> 到 <终点式>，共 N 步
- 视觉基调：黑底、白公式、当前操作行高亮（不用紫色 budget 规则——见下）
- 字幕：每块 ≤16 字，跟随解说词
- 场景衔接：推导连续，**允许场景内不切**；仅在"一个推导阶段完成"时切场景

## 推导步 DP01
- 解说：<对应字幕块>
- 起点状态：<屏幕上已有的公式>
- 操作：Transform(<式A>) → <式B>
- 高亮：<被操作的部分，用颜色/下划线/框>
- 停留：操作后静止 <N> 帧让观众看清

## 推导步 DP02
...
```

### 5.3 Manim 的 QC 判据适配

`core/motion_check.py` 可直接用（读帧），但判据阈值需按推导片调整：

| 判据 | remotion 后端 | manim 后端 |
|---|---|---|
| 最长静止 | ≤3.0s（>3s 中） | ≤5.0s（推导需要看清时间） |
| 末拍稳定期 | ≥30 帧 | 不适用（推导步无"离场"概念） |
| 静止占比 | 只报不判 | 只报不判 |

`core/frame_metrics.py` 的构图判据（主角 ≥170px 带光）**不适用于 manim**——
改用 manim 特定判据：公式是否超出安全区、当前操作步是否高亮可见。

### 5.4 与 Remotion 后端的画幅/风格对齐

为保证同一系列不同集可以混用后端，manim 后端需对齐：

| 项 | 值 | 来源 |
|---|---|---|
| 画幅 | 1280×720 @ 30fps | remotion 模板 |
| 背景 | 纯黑 `#000000` | remotion `--bg` |
| 主文字色 | 白 `#FFFFFF` | remotion 调色板 |
| 强调色 | 紫 `#A78BFA`（但推导片放宽 budget） | remotion 调色板 |
| 字幕 | 44px 白字黑边，y637–690 | remotion 字幕规范 |
| 字体 | 中文思源黑体 / 英文 Fira Sans | remotion `public/fonts` |

---

## 六、迁移计划

### 6.1 Git 策略

`anything2explainer` 当前状态：
- 分支 `feat/math-pack`，有 1 个未提交改动（`reference/lessons.md` +32 行）
- 远程 `mine`（FnSGit/anything2explainer）+ `origin`（Vincentwei1021/anything2explainer）
- `template/node_modules` 613M（已 gitignore）
- `examples/rag` 5.1M（样片，在库内）

**迁移步骤**：

1. **先在 anything2explainer 提交未完成的 math-pack 工作**（遵守 AGENTS.md「改完即 commit」）
   - `feat/math-pack` 合入 `main` 或保持为长期分支
2. **在 ai-video workspace 建新仓库** `~/Projects/ai-video/video-craft-skill/`
   - 不 fork anything2explainer，避免继承 613M node_modules 历史
3. **按架构拷贝文件**（git mv 保留历史的方案放弃，改为新仓库干净导入）
   - `core/` ← anything2explainer 的中性资产
   - `backends/remotion/` ← anything2explainer 的 Remotion 绑定资产
4. **原 skill 处理**：`~/.pi/agent/skills/anything2explainer` 保留但标记 deprecated
   - SKILL.md frontmatter description 前加 `[DEPRECATED] 请改用 video-craft`
   - 保留原因：历史项目（linear-function / transformer / a2e-fourier）仍可能引用
5. **新 skill 安装**：`~/.pi/agent/skills/video-craft`
6. **各阶段 commit + push**

### 6.2 迁移文件清单

| 目标 | 来源 | 操作 |
|---|---|---|
| `SKILL.md` | 新写 | 基于原 SKILL.md 改写（加路由层） |
| `core/research-brief.md` | `reference/research-brief.md` | 原样拷贝 |
| `core/narration-guidance.md` | `reference/narration-guidance.md` | 原样拷贝 |
| `core/narration-storyboard.md` | `reference/narration-storyboard.md` | 拷贝 + 拆出后端特定章节 |
| `core/tts_build.py` | `template/scripts/tts_build.py` | 拷贝 |
| `core/render_storyboard.py` | `template/scripts/render_storyboard.py` | 拷贝 |
| `core/motion_check.py` | `template/scripts/motion_check.py` | 拷贝 + 参数化判据阈值 |
| `core/frame_metrics.py` | `template/scripts/frame_metrics.py` | 拷贝 + 参数化 |
| `core/sheet.py` | `template/scripts/sheet.py` | 原样拷贝 |
| `core/lessons.md` | `reference/lessons.md` | 拷贝 + 补 manim 教训 |
| `routing/router.md` | 新写 | §3.1 判据树 |
| `routing/prompt_classifier.md` | 新写 | 判定提示词 |
| `backends/remotion/template/` | `template/src` + `template/public` + 配置 | 整体拷贝 |
| `backends/remotion/scripts/` | `template/scripts/` 的 remotion 绑定脚本 | 拷贝 + 改路径 |
| `backends/remotion/reference/` | `reference/` 的 remotion 特定文件 | 拷贝 |
| `backends/remotion/examples/` | `examples/` | 拷贝 |
| `backends/manim/*` | 新写 | §5 设计 |

### 6.3 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| `motion_check.py` 路径假设项目根 | manim 项目结构不同 | 参数化 `--project-root`，默认从 cwd 推断 |
| `tts_build.py` 输出 `timeline.json` 路径写死 | manim 项目结构不同 | 同样参数化，两后端用相同相对路径 `script/timeline.json` |
| `render_storyboard.py` 的令牌是 remotion 语义 | manim 分镜格式不同 | core 版只做通用令牌替换（`{S12.from}` 等），后端特定令牌在后端脚本扩展 |
| 原 skill 的 4 个历史项目依赖旧路径 | 历史项目无法再跑新 skill | 原 skill 保留 deprecated 但不删除；新 skill 只服务新项目 |
| 653M 仓库历史 | 新仓库 clone 慢 | 新仓库干净导入，不带 node_modules 历史 |

---

## 七、V1 交付范围与验收

### 7.1 V1 必交付

- [ ] `SKILL.md` 含路由层 + 8 阶段流程 + 4 确认点（含合并后的确认点 0）
- [ ] `core/` 9 个中性资产就位，脚本可独立运行
- [ ] `routing/` 判据树 + 分类提示词
- [ ] `backends/remotion/` 完整迁移，**验证能用新路径跑通一次 30 秒打样**
- [ ] `backends/manim/` 工程骨架 + 渲染脚本 + **验证能渲出一条 15 秒推导片**
- [ ] `backends/hyperframes/README.md` + `backends/terminal/README.md`（设计意图）
- [ ] 原 `anything2explainer` 标记 deprecated
- [ ] 全部 commit + push 到新远程

### 7.2 V1 验收测试

| 测试 | 通过标准 |
|---|---|
| remotion 后端打样 | 用新 skill 路径跑通阶段 0→5a，产出前 30 秒 mp4 |
| manim 后端最小闭环 | 用新 skill 跑一个 3 步公式推导，产出 mp4，`core/motion_check.py` 能读它的帧 |
| 路由判定 | 给 5 个测试主题（RAG/傅里叶推导/装 Python/产品发布/梯度下降直觉），判定结果符合预期 |
| core 脚本独立性 | `tts_build.py` + `render_storyboard.py` 在两后端项目里都能跑 |

### 7.3 V1 明确不做

- Hyperframes / Terminal 后端的实际实现（只留 README）
- Manim 样片（V1 只验证最小闭环，样片留 V2）
- 跨后端混剪（同一集里 remotion + manim 混合）
- `selfcheck.py` 的跨后端通用化（V1 保持 remotion 特定）

---

## 八、后续演进（V2+）

| 版本 | 内容 |
|---|---|
| V2 | 补 manim 样片（傅里叶变换推导）；**实现 terminal 后端（asciinema 真终端录制 + 后处理配音/字幕叠加）——必须项** |
| V3 | 实现 hyperframes 后端；`selfcheck.py` 通用化 |
| V4 | 跨后端混剪能力（数学片的概念引入段用 remotion，推导段用 manim） |

---

## 附：与原 anything2explainer SKILL.md 的差异摘要

| 维度 | anything2explainer | video-craft |
|---|---|---|
| 渲染后端 | 固定 Remotion | 路由选择（V1: remotion/manim） |
| 入口确认点 | 4 个 | 4 个（确认点 1 内含后端推荐） |
| core 资产位置 | `reference/` + `template/scripts/` 混合 | 独立 `core/` |
| QC 脚本归属 | `template/scripts/` | `core/`（跨后端） |
| 分镜格式 | 单一令牌格式 | 按后端分（remotion 令牌 / manim 推导步） |
| 图元库 | `template/src/ui.tsx` | `backends/remotion/template/src/ui.tsx` |
| 样片 | `examples/rag/` | `backends/remotion/examples/` |
| 原 skill 命运 | — | deprecated，保留供历史项目 |
