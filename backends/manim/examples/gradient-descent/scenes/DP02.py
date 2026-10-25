"""DP02 坡度可感。

在 DP01 的山形曲线上取一点，画切线——把「坡度」这个抽象概念变成一个看得见的线段。
"""
import numpy as np
from manim import Dot, Line, ParametricFunction, Text

from common import TimedScene
from common import style


def hill(t):
    x = (t - 0.5) * 8
    y = 1.2 + 1.6 * (t - 0.5) ** 2 * 4 - 0.4 * np.sin(t * np.pi)
    return np.array([x, y, 0])


class DP02(TimedScene):
    def construct(self):
        curve = ParametricFunction(hill, t_range=[0, 1, 0.01], color=style.DIM)
        curve.scale_to_fit_width(6.5)
        curve.move_to([0, 0.6, 0])
        self.add(curve)

        # P 点：取曲线左侧（t=0.25），这里坡度明显
        p = curve.point_from_proportion(0.25)
        dot = Dot(p, radius=0.09, color=style.PURPLE)
        self.show(dot, frames=25)

        # 切线：用曲线在 P 点附近的两个点近似方向
        p2 = curve.point_from_proportion(0.30)
        direction = p2 - p
        direction = direction / np.linalg.norm(direction)
        tangent = Line(
            p - direction * 1.6, p + direction * 1.6, color=style.PURPLE, stroke_width=4
        )
        self.show(tangent, frames=30)

        # 「坡度」标签
        label = Text("坡度", font_size=style.FONT_TEXT, color=style.WHITE, font=style.FONT_CN)
        label.move_to(p + direction * 2.0 + np.array([0, 0.35, 0]))
        self.show(label, frames=20)
        self.hold(179)
