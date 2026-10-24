# Manim 后端

> 状态：V1 实现（最小闭环）· 2026-10-24
> 定位：**连续公式推导 / 证明 / 符号变形** 类视频
> 与 remotion 后端的分工见 `../../routing/router.md` R1

---

## 零、本地环境实测结论（2026-10-24，macOS arm64）

**这些是实测出来的，不是文档抄的。在新机器上搭环境前先读这节。**

### 已解决

| 项 | 状态 | 说明 |
|---|---|---|
| Python | ✅ 3.14.7 | `uv venv --python 3.14` |
| manim | ✅ v0.22.0 | `uv pip install manim`，**但需要下面的 cairo/pango** |
| cairo / pango | ✅ 已装 | `brew install pkg-config cairo pango`——**pycairo 编译必需** |
| ffmpeg | ✅ 9.0.1 | 系统已有 |

### ⚠ pycairo 编译失败（首次安装必踩）

直接 `uv pip install manim` 会失败：

```text
pycairo (v1.29.2) build failed ... meson-log.txt
hint: `pycairo` was included because `manim` depends on `pycairo`
```

根因：pycairo 要从源码编译，需要 cairo 的 `.pc` 文件，而 macOS 默认没有
cairo，也没有 `pkg-config`。安装：

```bash
brew install pkg-config cairo pango
```

装完再 `uv pip install manim` 即可（3.14 实测通过）。

### 🔴 LaTeX 缺失——manim 后端的硬约束

`MathTex` / `Tex` **必须**有 `latex` 可执行文件。实测报错：

```text
FileNotFoundError: [Errno 2] No such file or directory: 'latex'
```

本机没有 LaTeX。可选方案：

| 方案 | 体积 | 命令 | 评价 |
|---|---|---|---|
| **basictex**（MacTeX 最小版） | ~100MB | `brew install --cask basictex` | **推荐**。够 manim 用，装完需 `sudo tlmgr update --self` 并按需补包 |
| texlive（brew formula） | 重 | `brew install texlive` | ❌ 不推荐。要拉 openjdk + python@3.15 等 25 个依赖 |
| mactex（完整） | ~5GB | `brew install --cask mactex` | ❌ 过重 |
| 免 LaTeX 的 `Text()` | 0 | 无需安装 | ⚠️ 只能用纯文本，**无法排公式** |

**当前状态**：V1 的模板与脚本**两条路都支持**——
- `MANIM_TEX=latex`（默认）：用 `MathTex`，需先装 basictex
- `MANIM_TEX=text`：用 `Text()` 排近似公式，零依赖，但排版质量低

**V1 验收用的是 `MANIM_TEX=text`**（本机无 LaTeX，不想为验证装 100MB+）。
真正做推导片前必须先装 basictex——`MathTex` 的公式质量是推导片的生命线。

### ⚠ basictex 装完还不够——要补两个包（2026-10-24 实测）

basictex 是最小安装，**只装 brew cask 不够**。装完 `latex` 能跑，但 manim 的
`MathTex` 仍会失败。实测缺失两个东西。检查命令：

```bash
for p in standalone babel amsmath amssymb dvisvgm; do
  (kpsewhich $p.sty >/dev/null 2>&1 || kpsewhich $p.cls >/dev/null 2>&1 || which $p >/dev/null 2>&1) \
    && echo "✅ $p" || echo "❌ $p 缺失"
done
```

manim 的 tex template 实际长这样（见 `media/tex/*.tex`）：

```latex
\documentclass[preview]{standalone}
\usepackage[english]{babel}
\usepackage{amsmath}
\usepackage{amssymb}
```

basictex 自带 babel / amsmath / amssymb，但缺：

| 缺的 | 干什么用 | 装法 |
|---|---|---|
| `standalone.cls` | 裁剪页面到公式墨迹大小 | `sudo tlmgr install standalone` |
| `dvisvgm` | 把 LaTeX 的 DVI 输出转成 SVG（manim 只吃 SVG） | `sudo tlmgr install dvisvgm` |

一条命令补齐：

```bash
sudo tlmgr install standalone dvisvgm
```

> `sudo` 会弹窗要密码，**agent 无法非交互执行**，必须用户在真实终端跑。
> 这也是 `brew install --cask basictex` 本身要手动跑的原因（pkg 安装器要 sudo）。

### 完整 LaTeX 安装清单（新机器照抄）

```bash
# 1. basictex（要 sudo，弹窗输密码）
brew install --cask basictex

# 2. 补 manim 需要的包（要 sudo）
sudo tlmgr install standalone dvisvgm

# 3. 把 texlive 加进 PATH（basictex 装在 /usr/local/texlive/2026basic）
echo 'export PATH="/usr/local/texlive/2026basic/bin/universal-darwin:$PATH"' >> ~/.zshrc

# 4. 验证
kpsewhich standalone.cls && which dvisvgm && which latex
```

### 已验证可用的最小渲染

`Text()` mobject + `self.play()` 可以正常出 mp4（`-ql` 低画质）。

---

## 一、工程骨架

```text
backends/manim/template/
├── pyproject.toml              # uv 管理，Python 3.14，依赖 manim
├── manim.cfg                   # 1280x720@30fps，黑底——与 remotion 后端画幅一致
├── .venv/                      # uv venv（不入库）
├── narration.txt               # 解说词（core 格式，与 remotion 后端同源）
├── config.json                 # {"slug": ..., "backend": "manim"} 供 core  ���本识别
├── script/                     # core/tts_build.py 产出
│   ├── timeline.json
│   ├── timeline.md
│   ├── audio.wav               # 中立配音产物
│   └── 分镜表.md
├── scenes/                     # 每个推导步一个 Scene 文件
│   ├── DP01.py
│   ├── DP02.py
│   └── ...
├── common/
│   ├── style.py                # 配色/字号，对齐 remotion 调色板
│   ├── formula.py              # MathTex/Text 双后端封装（按 MANIM_TEX 切换）
│   └── subtitle.py             # 字幕 Mobject，读 timeline.json
└── scripts/
    ├── new_project.sh
    ├── render.sh
    ├── still.sh
    ├── preview.sh
    └── test_render.sh
```

---

## 二、推导片分镜格式

与 remotion 后端的根本差异：**分镜单元是「推导步」，不是「镜头」**。

remotion 后端：一句解说 = 一个镜头，可切、有主角、有离场。
manim 后端：一步推导 = 一个 Scene 内的一段，**连续不切**，没有"主角带光"概念。

`script/storyboard_src.md`（manim 版）：

```markdown
## 全局约束
- 推导主线：从 <起点式> 到 <终点式>，共 N 步
- 视觉基调：黑底、白公式、当前操作项用紫色高亮（manim 端放宽紫色 budget——
  推导片每步都有重点，全不紫等于全紫，规则见 agent-build-rules.md）
- 字幕：每块 ≤16 字，跟随解说词（common/subtitle.py 读 timeline.json）
- 场景切分：仅在「一个推导阶段完成」时切 Scene；阶段内连续演算不切

## 推导步 DP01
- 解说：<字幕块文本>
- 起点状态：屏幕上已有 <哪些式>
- 操作：Transform(<式A>) → <式B>  /  Write(<新式>)  /  高亮 <子式>
- 高亮：<被操作的部分，紫框/下划线/变色>
- 停留：操作后静止 <N> 帧让观众看清

## 推导步 DP02
...
```

---

## 三、与 Remotion 后端的画幅/风格对齐

同一系列的不同集可以混用后端，所以 manim 端必须对齐 remotion 的视觉基调：

| 项 | 值 | 来源 |
|---|---|---|
| 画幅 | 1280×720 @ 30fps | remotion 模板 |
| 帧率 | 30 fps | 同上 |
| 背景 | 纯黑 `#000000` | remotion `--bg` |
| 主文字/公式色 | 白 `#FFFFFF` | remotion 调色板 |
| 强调色 | 紫 `#A78BFA` | remotion 调色板 |
| 字幕 | 底部 44px 白字黑边，y637–690 | remotion 字幕规范 |
| 安全区 | 内容不压字幕带 y637–690 | 同上 |
| 字体 | 中文 Noto Sans SC / 英文 Fira Sans | remotion `public/fonts` |

> manim 的坐标原点是画面中心，remotion 是左上角。换算见 `common/style.py`。

---

## 四、QC 判据适配

core 的三个读帧脚本（`motion_check.py` / `frame_metrics.py` / `sheet.py`）**直接可用**，
因为它们只读像素，不关心帧是谁渲的。但判据阈值要按推导片调整：

| 判据 | remotion 后端 | manim 后端 |
|---|---|---|
| 最长静止 | ≤3.0s | **≤5.0s**——推导需要看清时间 |
| 末拍稳定期 | ≥30 帧 | **不适用**——推导步无"离场"概念 |
| 静止占比 | 只报不判 | 只报不判 |
| 主角 ≥170px 带光 | 判 | **不判**——改用：公式是否超出安全区、当前操作步是否高亮可见 |

调用方式：

```bash
# 节奏体检（manim 端阈值）
python3 core/motion_check.py --frames fin_frames --still-max 5.0 --no-hold

# 构图（manim 端关掉主角/光判据）
python3 core/frame_metrics.py --frames fin_frames --bg flat --no-protagonist
```

---

## 五、脚本用法

```bash
# 建项目
backends/manim/scripts/new_project.sh <目标目录> <slug>

# 配音 + 时间轴（core 脚本）
cd <项目根> && python3 scripts/tts_build.py

# 分镜令牌替换（core 脚本）
cd <项目根> && python3 scripts/render_storyboard.py

# 单步测渲（低画质快验）
scripts/test_render.sh DP01

# 出静帧
scripts/still.sh DP01 45 /abs/out/dir

# 前 N 秒样片
scripts/preview.sh 30

# 整片渲染
VER=v1 scripts/render.sh
```

---

## 六、V1 范围与遗留

### V1 已做

- 工程骨架 + uv/pyproject + manim.cfg（画幅与 remotion 对齐）
- `common/style.py`（配色/字号/坐标换算）+ `formula.py`（MathTex/Text 双后端）
- `common/subtitle.py`（读 `timeline.json` 上字幕）
- 5 个脚本（new_project / render / still / preview / test_render）
- 推导步分镜格式规范
- QC 判据适配说明

### V1 明确遗留

- **样片**：只验证最小闭环，完整质量标尺样片（对标 remotion 的 `examples/rag/`）留 V2
- **basictex 安装**：本机未装，`MathTex` 路径未在真实 LaTeX 环境验证过
- **`agent-build-rules.md` / `agent-qc-rules.md`**：V1 只有分镜格式，多 agent 构建协议留 V2
- **`selfcheck.py`**：remotion 特定，manim 端未做对应静态自检
