# video-craft INBOX — 已知问题与待办

> 记录已识别但未解决的问题、技术债、和计划项。
> 每条标注来源（实测/设计/用户反馈）与状态。
> 状态：🔴 阻塞 · 🟡 待办 · ✅ 已修 · ⏸ 计划中

---

## 🔴 已知缺陷（未修）

_暂无。V1 发现的阻塞项已全部修掉（见下方「已修」区）。_

---

## 🟡 技术债

### T1. core 脚本的 Python 依赖未 venv 化（来源：lessons.md 遗留）

`core/*.py` 需要 numpy/pillow/scipy/edge-tts。SKILL.md 写了建 venv，
但只有 manim 后端的 `new_project.sh` 会装（`.venv/bin/python`），
remotion 后端没建 venv——用户跑 `tts_build.py` 时会 `ModuleNotFoundError`。

**修复**：remotion 后端的 `new_project.sh` 也应建 venv 并装这些包，
或在 `render.sh`/`preview.sh` 里用 `${VENV:-.venv}/bin/python` 调 core 脚本。

**优先级**：中（remotion 后端的老项目有系统 python 装好的包能用，新机器会踩坑）

### T2. manim 后端无样片（来源：V1 设计决策 → V2 进行中）

remotion 后端有 `examples/rag/`（4′35″ 样片）作为质量标尺。
manim 后端 V1 只验证了最小闭环（DP01 移项，15 秒）。

**V2 计划**：做一条傅里叶变换推导样片（对标 3Blue1Brown 风格），
作为 manim 后端的质量锚点，并校准 QC 阈值（`--still-max 5.0` 是设计推断）。

### T3. `frame_metrics.py` 的主角/光判据不适用于 manim（来源：设计）

`core/frame_metrics.py` 的"主角 ≥170px 带光""紫色碎片"判据是
remotion MG 审美。manim 推导片没有"主角"概念。

V1 的 `--bg flat` 参数只是关掉幕底判据，主角/光判据仍会跑（报噪声）。

**修复**：加 `--no-protagonist` 参数，跳过主角/光相关统计。

**优先级**：低（噪声不影响判定，只污染输出）

---

## 🟢 计划项

### P1. terminal 后端实现（来源：用户确认，V2 必做）

asciinema 录制 + 时间重映射 + 后期合成。详见 `backends/terminal/README.md`。

**关键技术难点**：`.cast` 时间戳与 `timeline.json` 帧号的重映射逻辑。

### P2. hyperframes 后端实现（来源：设计，V3）

HTML 原生渲染。详见 `backends/hyperframes/README.md`。

### P3. selfcheck.py 跨后端通用化（来源：设计，V3）

当前 `selfcheck.py` 扫 Remotion 组件名（GlitchIn/LightSweep），
manim 后端无对应静态自检。

### P4. 跨后端混剪（来源：设计，V4）

同一集里概念引入段用 remotion、推导段用 manim。

---

## ✅ 已修（保留记录，防止重蹈）

### F1. manim 多 Scene 拼接后全片字幕错位（来源：V1 实测，2026-10-24）

**现象**：每个 Scene 的 `self.frame` 从 1 开始，拼接后字幕按场景内相对帧号
查 `timeline.json` → 全片字幕错位。

**修复**：
- `scripts/gen_frame_offsets.py`：从 `分镜表.md` 解析 DPxx 帧区间 → `.frame_offsets.json`
- `common/timed_scene.py`：`_apply_frame_offset()` 读该文件设 `frame_offset`；
  `_update_subtitle()` 用 `self.time * FPS + 1 + offset` 算全片绝对帧号
- `TimedScene.check_frame_budget()` 核对实际帧数与声明区间

**验证**（像素级）：两场景各 60 帧，S01 在 f1-60、S02 在 f61-120，
offset 分别 0 和 60。成片逐帧统计字幕带：DP01 时段有字幕、
DP02 时段字幕从 f101 起出现（FadeIn 前 32 帧不可见），各自归位。

### F2. manim 真公式链路全坏：TEXMFROOT/TEXMFCNF 缺失（来源：V1 实测，2026-10-24）

**现象**：basictex 装完、`latex` 可用、渲染"成功"，但公式字符不可见。

**根因**：`TEXINPUTS` 污染 kpathsea 搜索起点 → dvisvgm 报 `texmf.cnf not found`
→ 字体 map 加载失败 → SVG glyph 引用悬空（**use=5 defs=0**）。

**修复**：`scripts/env.sh` 显式设 `TEXMFROOT` + `TEXMFCNF`。修后 `use=5 defs=5`。

**顺带修掉**：
- `manim.cfg` 的 `pixel_width` 不生效（0.22 的 `-q` 标志优先级更高）
  → 画幅权威来源改为命令行 `-qm`（1280×720@30fps）
- `still.sh` 误用 `-t`（那是 `--transparent` 不是动画进度）→ 改用 `-s --format=png`
- 系统缺 Fira Code / Noto Sans SC，`Text()` 渲染空白 → brew 装两个字重

### F3. basictex 装完仍不够（来源：V1 实测，2026-10-24）

`brew install --cask basictex` 装完 `latex` 可用，但 manim 的 `MathTex` 仍失败。
缺三个：`standalone.cls`、`preview.sty`（standalone 的 `[preview]` 选项依赖，**容易漏**）、
`dvisvgm` 二进制。

**正规补法**：`sudo tlmgr update --self && sudo tlmgr install standalone dvisvgm preview`
（tlmgr 不先自更新会直接 `Terminating`）。

**免 sudo 手工补法**：从 CTAN 镜像下 tlnet `.tar.xz`，宏包放 `~/.local/texlive-extra/tex`，
dvisvgm 二进制（`dvisvgm.universal-darwin`，注意元数据包只有 880 字节）放 `~/.local/bin`。

> ⚠ 别放 `~/Library/texmf` 或 `~/texmf`：basictex 的 `texmf.cnf` 里
> `TEXMFHOME = ./Library/texmf` 是**相对路径**，cwd 一变就失效，且 ls-R 索引刷不成功。

### F4. zsh 的 `$(cmd)` 不按换行分词（来源：2026-10-24）

`SCENES=$(ls ... | sort)` 后 `for S in $SCENES` 在 zsh 里拿到的是**单个含 \\n 的字符串**，
导致 manim 收到 `scenes/DP01\nDP02.py` 这种坏路径，且 `set -e` + `>/dev/null 2>&1`
把真实错误吞掉，表现为"渲染到一半静默退出"。

**修复**：用 `${(f)"$(...)"}` 显式按行拆数组；manim 调用去掉静默，失败时打印可复现的命令。

### F5. 视觉/截图判断画面内容不可靠（来源：2026-10-24 两次误判）

**同一天误判两次，都因为「看图下结论」：**

- **误判 1**：`ffmpeg scale=1:1` 单像素采样判断"全黑" → 黑底主导假阴性，实际正常
- **误判 2**：`agent_browser_screenshot` 看 JPEG 抽帧连续显示纯黑，据此推断
  "mp4 编码丢内容""manim 0.22 bug""ffmpeg 与 PNG alpha 交互有问题"——**全是错的**。
  numpy 直读 rawvideo：原始 PNG 9013 个非黑像素，编码后 9005 个，几乎无损耗。

**规则（强制）**：判断"画面有没有内容"只能用像素统计：
- ❌ 看图 / 截图工具（对大面积纯黑+少量白字的图显示有问题）
- ❌ `ffmpeg scale=1:1` 单像素采样
- ❌ `-frames:v 1` 取帧（取到首帧，FadeIn 开始时全透明）
- ✅ numpy/PIL 统计非黑像素 + 目标区域 crop
- ✅ 取特定帧用 `-vf "select=eq(n\,49)"`（0 起）

**相关坑**：`FadeIn` 前 ~32 帧在 JPEG 量化下亮度接近 0，抽样别取前 1/3 帧。
