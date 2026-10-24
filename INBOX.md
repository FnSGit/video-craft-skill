# video-craft INBOX — 已知问题与待办

> 记录已识别但未解决的问题、技术债、和计划项。
> 每条标注来源（实测/设计/用户反馈）与优先级。

---

## 🔴 已知缺陷

### 1. manim 拼接后全片字幕错位（来源：V1 实测，2026-10-24）

**现象**：`TimedScene` 的帧号是场景内相对的（从 0 累计）。
`render.sh` 用 `ffmpeg concat` 拼接各 Scene 的 mp4 后，字幕 updater 查
`timeline.json` 用的帧号是场景内相对帧号，不是全片绝对帧号 →
**拼接后字幕位置错位**。

**影响**：单场景测渲时字幕正确（验证公式/动画够用），
整片字幕会错位（交付级不可用）。

**V1 规避**：单场景测渲验证公式与动画；整片字幕由后期烧制（未实现）。

**修复方案**（V2 必修）：
- 方案 A：给 `TimedScene` 加 `frame_offset` 参数，每个 Scene 的起始帧
  由 `render_storyboard.py` 从分镜表注入
- 方案 B：改成"整片一个 Scene"模式，manim 的 `Scene` 内用
  `self.next_section()` 切分，不用多 Scene 拼接
- 方案 C：后期烧字幕——`render.sh` 不在 manim 里渲字幕，
  用 ffmpeg drawtext 后期烧（绕过 updater 机制）

**优先级**：高（阻塞 manim 后端交付级使用）

---

## 🟡 技术债

### 4. basictex 装完仍不够——需补 standalone + dvisvgm（来源：V1 实测，2026-10-24）

`brew install --cask basictex` 装完，`latex` 可用，但 manim 的 `MathTex` 仍失败：

```text
! LaTeX Error: File `standalone.cls' not found.
ValueError: latex error converting to dvi
```

manim 的 tex template 用 `\documentclass[preview]{standalone}`，且必须经
`dvisvgm` 转 SVG——basictex 最小安装两个都没带。

**修复**：`sudo tlmgr install standalone dvisvgm`（需 sudo，agent 无法非交互跑，
必须用户在真实终端执行）。

**已文档化**：`backends/manim/README.md` §零 新增「basictex 装完还不够」小节 +
「完整 LaTeX 安装清单（新机器照抄）」四步。

**优先级**：中（不影响 V1 的 text 模式验证；但 manim 后端要用真公式就必须补）

### 5. core 脚本的 Python 依赖未 venv 化（来源：lessons.md 遗留）

`core/*.py` 需要 numpy/pillow/scipy/edge-tts。SKILL.md 写了建 venv，
但 `new_project.sh` 只给 manim 后端装了（`.venv/bin/python`），
remotion 后端没建 venv——用户跑 `tts_build.py` 时会 `ModuleNotFoundError`。

**修复**：remotion 后端的 `new_project.sh` 也应建 venv 并装这些包，
或在 `render.sh`/`preview.sh` 里用 `${VENV:-.venv}/bin/python` 调 core 脚本。

**优先级**：中（remotion 后端的老项目有系统 python 装好的包能用，
新机器会踩坑）

### 6. manim 后端无样片（来源：V1 设计决策）

remotion 后端有 `examples/rag/`（4′35″ 样片）作为质量标尺。
manim 后端 V1 只验证了最小闭环（DP01 移项，15 秒），没有完整样片。

**影响**：新做 manim 推导片时没有"和样片风格一致"的锚点，
QC 判据的阈值（`--still-max 5.0`）是设计推断，未在真实长片上校准。

**计划**：V2 做一条傅里叶变换推导样片（对标 3Blue1Brown 风格）。

**优先级**：中

### 7. `frame_metrics.py` 的主角/光判据不适用于 manim（来源：设计）

`core/frame_metrics.py` 的"主角 ≥170px 带光""紫色碎片"判据是
remotion MG 审美。manim 推导片没有"主角"概念。

V1 的 `--bg flat` 参数只是关掉幕底判据，主角/光判据仍会跑（报噪声）。

**修复**：加 `--no-protagonist` 参数，跳过主角/光相关统计。

**优先级**：低（噪声不影响判定，只污染输出）

---

## 🟢 计划项

### 8. terminal 后端实现（来源：用户确认，V2 必做）

asciinema 录制 + 时间重映射 + 后期合成。详见
`backends/terminal/README.md`。

**关键技术难点**：`.cast` 时间戳与 `timeline.json` 帧号的重映射逻辑。

### 9. hyperframes 后端实现（来源：设计，V3）

HTML 原生渲染。详见 `backends/hyperframes/README.md`。

### 10. selfcheck.py 跨后端通用化（来源：设计，V3）

当前 `selfcheck.py` 扫 Remotion 组件名（GlitchIn/LightSweep），
manim 后端无对应静态自检。

### 11. 跨后端混剪（来源：设计，V4）

同一集里概念引入段用 remotion、推导段用 manim。
