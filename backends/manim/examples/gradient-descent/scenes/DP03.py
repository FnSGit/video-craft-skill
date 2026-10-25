"""DP03 步长的两个因素。

写 `步长 = η × 坡度`——把「这一步迈多大」拆成两个可控量。
中文不进 LaTeX（\\text{} 不支持 Unicode），公式与说明分开排。
"""
from manim import Text

from common import TimedScene, formula, plain
from common import style


class DP03(TimedScene):
    def construct(self):
        # 公式（纯符号）
        f = formula(r"\Delta\theta = \eta \times g")
        f.move_to([0, 0.5, 0])
        self.show(f, frames=40)

        # 中文说明（走 Text，不走 LaTeX）
        lr = Text("学习率 η：你胆有多大", font_size=style.FONT_SMALL, color=style.DIM, font=style.FONT_CN)
        lr.move_to([0, -0.5, 0])
        slope = Text("坡度 g：坡有多陡", font_size=style.FONT_SMALL, color=style.DIM, font=style.FONT_CN)
        slope.move_to([0, -1.1, 0])
        self.show(lr, slope, frames=30)
        self.hold(178)
