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

### ⚠ basictex 装完还不够——要补三个包（2026-10-24 实测）

basictex 是最小安装，**只装 brew cask 不够**。装完 `latex` 能跑，但 manim 的
`MathTex` 仍会失败。实测缺三样：

```bash
# 检查缺什么
for p in standalone babel amsmath amssymb dvisvgm; do
  (kpsewhich $p.sty >/dev/null 2>&1 || kpsewhich $p.cls >/dev/null 2>&1 || which $p >/dev/null 2>&1) \
    && echo "✅ $p" || echo "❌ $p 缺失"
done
```

manim 的 tex template 实际长这样（见 `media/tex/*.tex`）：

```latex
\documentclass[preview]{standalone}    ← 缺 standalone.cls
\usepackage[english]{babel}            ← basictex 自带
\usepackage{amsmath}                   ← 自带
\usepackage{amssymb}                   ← 自带
```

`standalone` 的 `[preview]` 选项又要加载 `preview.sty`，且 manim 只吃 SVG，
必须经 `dvisvgm` 转——这两个 basictex 都没带。

| 缺的 | 干什么用 |
|---|---|
| `standalone.cls` | 裁剪页面到公式墨迹大小 |
| `preview.sty` | standalone 的 `[preview]` 选项依赖它（**容易漏**） |
| `dvisvgm` | 把 LaTeX 的 DVI 转成 SVG（manim 只吃 SVG） |

**正规补法**（要 sudo，agent 无法非交互跑，必须用户在真实终端执行）：

```bash
sudo tlmgr update --self          # basictex 自带的 tlmgr 版本旧，不更新会被拒绝
sudo tlmgr install standalone dvisvgm preview
```

> tlmgr 会要求先 `update --self`，否则直接 `Terminating`。这是 basictex 的常见坑。

**免 sudo 的手工补法**（本机采用的方案，用户无密码时可走这条）：

```bash
# 1. 从 CTAN 镜像直接下 tlnet 的 .tar.xz（免 tlmgr 版本检查）
M=https://mirrors.sjtug.sjtu.edu.cn/ctan/systems/texlive/tlnet/archive
for p in standalone preview; do
  curl -sLO "$M/$p.tar.xz" && mkdir -p "x_$p" && tar xJf "$p.tar.xz" -C "x_$p"
done
# 2. dvisvgm 的元数据包只有 880 字节，真二进制在平台包里；basictex 是 universal
curl -sLO "$M/dvisvgm.universal-darwin.tar.xz" && mkdir -p x_dv && tar xJf dvisvgm.universal-darwin.tar.xz -C x_dv
# 3. 宏包放进用户态 extra，二进制放进 ~/.local/bin
mkdir -p ~/.local/texlive-extra/tex ~/.local/bin
cp -R x_standalone/tex/* x_preview/tex/* ~/.local/texlive-extra/tex/
cp x_dv/bin/universal-darwin/dvisvgm ~/.local/bin/ && chmod +x ~/.local/bin/dvisvgm
```

> ⚠ **别把宏包放进 `~/Library/texmf` 或 `~/texmf`**：basictex 的 `texmf.cnf` 里
> `TEXMFHOME = ./Library/texmf`（相对路径，cwd 一变就失效），且 kpathsea 的
> ls-R 索引在 basictex 上刷不成功。用 `TEXINPUTS` 指到 extra 目录最可靠。

### 🔴🔴 最关键的坑：TEXMFROOT + TEXMFCNF 必须显式设（2026-10-24 实测）

只设 `TEXINPUTS` 时，`latex` 能找到宏包、DVI 也能生成，但 **dvisvgm 会失败**：

```text
warning: kpathsea: configuration file texmf.cnf not found in these directories: ...
```

`TEXINPUTS` 污染了 kpathsea 的搜索起点，dvisvgm 以为自己的 prefix 变了，
于是找不到 `texmf.cnf` → 字体 map 加载失败 → **SVG 里的 glyph 引用全部悬空**
（`use=5 defs=0`）→ 公式字符一个都不显示，画面看起来「全黑」。

**解法**：把根目录与配置目录钉死，两个程序才都正常。已固化在
`backends/manim/scripts/env.sh`：

```bash
export TEXMFROOT=/usr/local/texlive/2026basic
export TEXMFCNF=/usr/local/texlive/2026basic/texmf-dist/web2c
export TEXINPUTS="$HOME/.local/texlive-extra/tex//:"
```

修好的判据（一眼看出是否正常）：

```bash
F=$(ls media/tex/*.svg | head -1)
echo "use=$(rg -o "xlink:href='#" $F | wc -l) defs=$(rg -o "id='g" $F | wc -l)"
# 正常：use=5 defs=5（引用数与定义数相等）
# 异常：use=5 defs=0（字体没嵌入，公式不可见）
```

### ⚠ manim 0.22 的画幅：-q 标志覆盖 manim.cfg

`manim.cfg` 里写 `pixel_width = 1280` **不生效**——0.22 的 quality 机制
（默认 `high_quality` = 1920×1080@60fps）优先级更高。

所以画幅的权威来源是**命令行的 `-qm`**（= 1280×720@30fps，正好与 remotion
后端对齐），`manim.cfg` 里只留 `background_color`。所有脚本已统一用 `-qm`。

### ⚠ manim 0.22 没有「按帧号出静图」

`-t` 是 `--transparent`（透明背景），不是动画进度。要静图用：

```bash
manim render -s --format=png -qm scenes/DP01.py DP01
```

`-s` 会 fast-forward 所有动画存最后一帧。要中间态只能改场景动画时长，
或先渲片段再 ffmpeg 抽帧。

### ✅ 多 Scene 字幕对齐（V2 已实现）

manim 多 Scene 拼接时，每个 Scene 的 `self.frame` 默认从 1 开始，拼接后
字幕会按场景内相对帧号查 `timeline.json` → **全片字幕错位**。

V2 已修：

1. `scripts/gen_frame_offsets.py` 从 `分镜表.md` 解析每个 `DPxx` 的帧区间，
   生成 `.frame_offsets.json`
2. `common/timed_scene.py` 的 `_apply_frame_offset()` 在渲染时读该文件，
   设 `self.frame_offset`；`_update_subtitle()` 用 `self.time * FPS + 1 + offset`
   算全片绝对帧号
3. `TimedScene.check_frame_budget()` 核对实际帧数与声明区间（差 >2 帧告警）

分镜表格式（两种都认）：

```markdown
| DP01 | 1-60 |
| DP02 | 61-120 |
```

或

```markdown
## 推导步 DP01
- 帧区间：1-60
```

实测验证（2026-10-24）：两场景各 60 帧，timeline 里 S01 在 f1-60、S02 在 f61-120，
frame_offset 分别为 0 和 60。成片逐帧统计字幕带像素：DP01 时段有字幕、
DP02 时段字幕从 f101 起出现（FadeIn 32 帧不可见），各自归位无错位。

### 🔴 字体必须装（否则文字全不可见）

manim 用 Pango 找字体，缺字体会让 `Text()` 渲染成空白：

```text
WARNING  Font Fira Code not in [...]
```

```bash
brew install --cask font-fira-code font-noto-sans-sc   # 无需 sudo
```

### 完整安装清单（新机器照抄）

```bash
# 1. cairo/pango（pycairo 编译必需，无需 sudo）
brew install pkg-config cairo pango

# 2. 中英文字体（无需 sudo）
brew install --cask font-fira-code font-noto-sans-sc

# 3. basictex（要 sudo，弹窗输密码）
brew install --cask basictex

# 4. 补 standalone / preview / dvisvgm
#    有 sudo 密码：sudo tlmgr update --self && sudo tlmgr install standalone dvisvgm preview
#    无密码：用上面「免 sudo 的手工补法」

# 5. PATH 固化
echo 'export PATH="/usr/local/texlive/2026basic/bin/universal-darwin:$HOME/.local/bin:$PATH"' >> ~/.zshrc

# 6. 验证（use 与 defs 应相等）
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

- ~~**样片**：只验证最小闭环~~ → **V2 已完成**：《梯度下降的公式》12 推导步 /
  112.6s / 3379 帧，见 `examples/gradient-descent/`，QC 判据已校准
  （见 `reference/qc-criteria.md`）
- ~~**basictex 安装**：本机未装~~ → **已装并验证**：`MathTex` 真公式渲染通过
- **`agent-build-rules.md` / `agent-qc-rules.md`**：V2 只有分镜格式 + QC 判据文档，
  多 agent 并行构建协议留 V3
- **`selfcheck.py`**：remotion 特定，manim 端未做对应静态自检
- **覆盖层**（片头章节卡 / HUD / 进度条 / 片尾）：manim 端未实现，
  样片片头 45 帧是黑屏 + 字幕。与 remotion 后端的明显差距，留 V3
