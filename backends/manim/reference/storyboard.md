# Manim 后端分镜规范（推导步格式）

> 与 remotion 后端的根本差异：**分镜单元是「推导步」，不是「镜头」**。
> remotion：一句解说 = 一个镜头，可切、有主角、有离场。
> manim：一步推导 = 一个 Scene 内的一段，**连续不切**，没有"主角带光"概念。

---

## 一、为什么不能用 remotion 的分镜格式

remotion 的分镜假设在 manim 端全部崩塌：

| remotion 假设 | manim 推导片的现实 |
|---|---|
| 一句解说 = 一个镜头 | 一步推导可能横跨 3–5 句解说 |
| 元素入场后不许静止 >3s | 操作后必须静止让观众看清（3–6s 正常） |
| 每镜头一个主角 ≥170px 带光 | 公式通常 200–400px 宽但没有"主角"概念 |
| 末拍落位后停 30–45 帧再离场 | 推导步没有"离场"——上一步的式子是下一步的输入 |
| 紫柔光只给核心术语 | 每步都有重点，全紫等于全不紫 |
| 镜头衔接靠前一镜头 α=0 + 后一镜头首帧 | 推导连续，靠 `Transform` 直接变形 |

所以 manim 端用自己的分镜单元：**推导步（Derivation Step, DPxx）**。

---

## 二、分镜文件格式

`script/storyboard_src.md`（manim 版）：

```markdown
# <片名> 分镜（manim 推导片）

## 全局约束
- 推导主线：从 <起点式> 到 <终点式>，共 N 步
- 场景切分：仅在一个「推导阶段」完成时切 Scene；阶段内连续演算不切
- 视觉基调：黑底、白公式、当前操作项紫色高亮
- 字幕：每块中文 ≤16 字 / 英文 ≤48 字符，由 common/subtitle.py 读 timeline.json 上
- 紫色使用：每步的操作对象用紫框/下划线；**不要求**"每镜头 ≤1 处"（remotion 的规则在这里不适用）
- 事实清单：<画面出现的每个符号的定义与来源，逐条对照调研文档>

## 推导步 DP01  <这一步在干什么，如「移项把 b 孤立出来」>
- 解说：<对应字幕块文本，来自 narration.txt>
- 帧区间：{S01.from}-{S03.to}          ← 用 core/render_storyboard.py 的令牌
- 起点状态：屏幕上已有 <哪些式>
- 操作：Transform(<式A>) → <式B>       ← 或 Write / 高亮 / 框选
- 高亮：<被操作的部分，字符区间或语义描述>
- 停留：操作后静止 <N> 帧
- 注意：<易错点，如"这里的等号是从上一步继承的，不能重新写入场动画">

## 推导步 DP02
...
```

---

## 三、场景切分原则

**切 Scene**（`scenes/DPxx.py` 一个文件）：
- 一个推导阶段完成（如"已推出核心公式"）
- 需要清屏换一个语境（如"先看一维情形"）
- 解说词里有一个**自然停顿**（`narration.txt` 的空行分段）

**不切 Scene**（同一文件内连续 play）：
- 连续代入/化简/移项
- 上一步的输出是下一步的输入

经验值：一条 3–5 分钟推导片，**6–12 个 Scene**。少于 5 个说明切太粗（单文件过长难调试），
多于 15 个说明切太碎（丢了连续性）。

---

## 四、TimedScene 帧级计时

manim 的 `self.wait(秒)` 是秒级，与 `timeline.json` 的帧号对不上。
用 `common/timed_scene.py` 的 `TimedScene`：

```python
from common import Formula, TimedScene

class DP01(TimedScene):
    def construct(self):
        a = Formula(r"a = b + c")
        a.move_to([0, 1.2, 0])
        self.show(a, frames=45)        # FadeIn 入场，占 45 帧
        self.hold(30)                  # 静止 30 帧（推导片核心节奏）
        box = a.box_around(2, 5)       # 框住 'b + c'
        self.show(box, frames=20)
        self.hold(30)
        b = Formula(r"b = a - c")
        b.move_to([0, 1.2, 0])
        self.play_for(Transform(a, b), frames=45)
        self.hold(45)
```

### 帧号如何与 timeline.json 对齐

`TimedScene` 内部用 `self.time`（秒）反推帧号：

```python
self.frame = int(self.time * FPS + 0.5) + 1
```

字幕 updater 每帧按这个帧号查 `timeline.json`。所以：
- **每个 Scene 的帧数必须与分镜表的帧区间一致**
- Scene 之间的帧号连续（manim 逐个渲染后用 ffmpeg concat 拼接）

⚠ 这是 V1 的已知弱点：`TimedScene` 的帧号从 0 开始累计，**拼接时不自动偏移**。
所以单场景渲染时 `self.frame` 是场景内相对帧号，不是全片绝对帧号。
字幕在单场景测渲时位置正确，但整片拼接后**字幕会错位**。

**V1 的规避**：单场景测渲时验证公式与动画；整片字幕由 `render.sh` 后期烧
（V1 未实现，见 `backends/manim/README.md` §六遗留）。
**V2 必修**：给 `TimedScene` 加 `frame_offset` 参数，或改成"读全片帧号"模式。

---

## 五、公式排版

### latex 模式（默认，需 basictex）

```python
f = Formula(r"\frac{dy}{dx} = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}")
f.highlight(0, 4)          # 高亮 dy/dx
box = f.box_around(0, 4)   # 或加框
```

`MathTex` 按字符/符号切成 submobject，`[i]` 可逐个访问。字符区间要靠
`still.sh` 出图数出来（V1 没有自动定位工具）。

### text 模式（零依赖，ASCII 近似）

```python
# MANIM_TEX=text 时
Formula(r"\frac{a}{b} = c")   # 渲染成 (a)/(b) = c
```

只用于验证流程。**推导片不要用 text 模式交付。**

---

## 六、安全区

字幕带在 remotion 的 y637–690 → manim 坐标 y ∈ [-330, -277]。
公式与标注不得进入该区间。`common/style.py` 提供：

```python
from common import style
style.SUBTITLE_BAND          # (-330, -277)
style.is_in_subtitle_band(mob)
```

常用安全位置（manim 中心原点坐标）：

| 内容 | y |
|---|---|
| 主公式 | 1.0 ~ 1.5 |
| 次级式/推导中间态 | -0.5 ~ 0.5 |
| 标注文字 | 2.0 ~ 2.8 |
| 字幕（自动） | -303 |

---

## 七、QC 检查点

### 构建期（每个 DP 至少）

```bash
scripts/test_render.sh DP01          # 低画质快渲，验证能跑
scripts/still.sh DP01 45 /abs/out    # 出静帧看公式排版
```

### 组级/成片

```bash
# 节奏（manim 阈值）
python3 core/motion_check.py --frames fin_frames --shots DP01:1-170 --still-max 5.0 --no-hold

# 构图（manim 关掉主角/光判据）
python3 core/frame_metrics.py --frames fin_frames --bg flat

# 通读
python3 core/sheet.py fin_frames qc/sheet_v1.html
```

### 推导片特有的 QC（人工）

1. **公式正确性**：每个式子的数学正确性，对照调研文档逐式验证
   ——这是推导片的命门，`motion_check.py` 查不出来。
2. **变形连续性**：`Transform` 的两端是否语义等价（不能 A 变成 B 但 B 不是 A 的推论）
3. **高亮准确性**：紫框框住的是不是真正被操作的部分
4. **术语一致**：同一个符号全片用同一个写法（`f(x)` 不要一会儿 `f(x)` 一会儿 `f_x`）

---

## 八、与 core/render_storyboard.py 的配合

`core/render_storyboard.py` 是渲染器无关的令牌替换器，manim 端同样可用：

```markdown
## 推导步 DP01
- 帧区间：{S01.from}-{S03.to}
```

支持 `{S12.from}` `{S12.to}` `{S12.c3}`（第 3 个字幕块起始帧）`{C2}`（第 2 章起始帧）
`{TOTAL}`，均可带 `±整数`。

manim 端不需要 remotion 的 `{S12.from-8}` 这类"提前 8 帧入场"的令牌（推导步靠 `hold` 控制节奏，
不靠入场提前量），但保留兼容。
