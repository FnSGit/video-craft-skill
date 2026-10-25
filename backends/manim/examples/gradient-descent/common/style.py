"""manim 后端的视觉基调——与 remotion 后端对齐。

同一系列的不同集可能混用后端，所以配色/字号/安全区必须一致。
注意 manim 的坐标原点是画面中心，remotion 是左上角；用本模块的换算函数转换。
"""
from manim import ManimColor

# ---- 调色板（对齐 remotion src/ui.tsx）----
WHITE = ManimColor("#FFFFFF")
BLACK = ManimColor("#000000")
PURPLE = ManimColor("#A78BFA")     # 强调/当前重点
DIM = ManimColor("#8A8FA3")        # 次要文字
GREY = ManimColor("#3A3F52")       # 结构线

# ---- 画幅（manim.cfg 同步改）----
W, H = 1280, 720
FPS = 30

# ---- 安全区 ----
# remotion 端字幕带是 y637–690（左上原点），内容不得压入。
# 换算到 manim（中心原点，y 向上）：
#   remotion y=637 → manim y = 360 - 637 = -277（字幕带上边界）
#   remotion y=690 → manim y = 360 - 690 = -330（字幕带下边界）
# 字幕带在 manim 的 y ∈ [-330, -277]；内容不得进入该区间
SUBTITLE_BAND = (-330, -277)

# ---- 字号 ----
FONT_FORMULA = 44      # 主公式
FONT_TEXT = 32         # 说明文字
FONT_SUBTITLE = 44     # 字幕（44px 白字黑边，对齐 remotion）
FONT_SMALL = 24        # 标注

# ---- 中文字体 ----
# remotion 端用 public/fonts 下的思源黑体；manim 端依赖系统安装的字体。
# 若中文显示为方框，装：brew install --cask font-noto-sans-sc
FONT_CN = "Noto Sans SC"
FONT_MONO = "Fira Code"


def remotion_y_to_manim(y: float) -> float:
    """remotion（左上原点，y 向下）→ manim（中心原点，y 向上）。"""
    return H / 2 - y


def manim_y_to_remotion(y: float) -> float:
    return H / 2 - y


def to_manim_xy(x: float, y: float) -> tuple[float, float]:
    """remotion 画面坐标 (x, y左上原点) → manim (x, y中心原点)。"""
    return (x - W / 2, H / 2 - y)


def is_in_subtitle_band(mobject) -> bool:
    """mobject 是否压进字幕带。

    字幕带在 manim 坐标的 y ∈ [lo, hi]（lo=-330 是下边，hi=-277 是上边）。
    压入 = mobject 的纵向范围与字幕带有交集，且横向也重叠。
    """
    lo, hi = SUBTITLE_BAND
    top = mobject.get_top()[1]
    bottom = mobject.get_bottom()[1]
    # 纵向有交集
    if bottom > hi or top < lo:
        return False
    # 横向：字幕通常居中，宽度约为画面 60%；这里只判纵向，横向由分镜人工把握
    return True
