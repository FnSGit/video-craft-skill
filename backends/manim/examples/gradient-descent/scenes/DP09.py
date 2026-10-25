"""DP09 学习率的两难。

用 U 形曲线 + 会动的小球展示「太小慢 / 太大冲过头」。
帧预算 292（f2076-f2367）：曲线 40 + 三球 75 + 小球演示 130 + 停留 47。
核心是把静态的「两种失败」变成真会动的小球：一个挪一点点，一个直接冲出曲线。
"""
import numpy as np
from manim import ArcBetweenPoints, Dot, MoveAlongPath, ParametricFunction, Text

from common import TimedScene, plain
from common import style


def ucurve(t):
    """U 形曲线：y = 0.55*(x)^2，x ∈ [-3, 3]。"""
    x = (t - 0.5) * 6
    y = 0.55 * (x / 3.0) ** 2 * 1.6 - 1.2
    return np.array([x, y, 0])


class DP09(TimedScene):
    def construct(self):
        curve = ParametricFunction(ucurve, t_range=[0, 1, 0.01], color=style.DIM)
        curve.scale_to_fit_width(6.0)
        curve.move_to([0, 0.4, 0])
        self.show(curve, frames=40)

        # 三个标注球
        slow = Dot(curve.point_from_proportion(0.08), radius=0.13, color=style.DIM)
        slow_lab = plain("太小：慢")
        slow_lab.font_size = style.FONT_SMALL
        slow_lab.move_to([-2.9, 1.5, 0])
        fast = Dot(curve.point_from_proportion(0.94), radius=0.13, color=style.PURPLE)
        fast_lab = plain("太大：冲过头")
        fast_lab.font_size = style.FONT_SMALL
        fast_lab.move_to([2.4, 1.8, 0])
        ok = Dot(curve.point_from_proportion(0.5), radius=0.13, color=style.WHITE)
        ok_lab = plain("合适")
        ok_lab.font_size = style.FONT_SMALL
        ok_lab.move_to([0, -0.9, 0])
        self.show(slow, fast, ok, slow_lab, fast_lab, ok_lab, frames=75)

        # 演示 1：学习率太小——小球只挪一小段就停（标注「太小」强调它没走远）
        demo_slow = Dot(curve.point_from_proportion(0.30), radius=0.12, color=style.GREY)
        self.add(demo_slow)
        self.play_for(
            MoveAlongPath(demo_slow, curve),
            frames=65,
            rate_func=lambda t: min(1.0, t * 0.55),   # 走 55% 路程，看得出在动但没到头
        )

        # 演示 2：学习率太大——小球高速冲过去（65 帧）
        demo_fast = Dot(curve.point_from_proportion(0.30), radius=0.12, color=style.PURPLE)
        self.add(demo_fast)
        self.play_for(
            MoveAlongPath(demo_fast, curve),
            frames=65,
            rate_func=lambda t: min(1.0, t * 2.2),    # 2.2 倍速冲过去
        )

        self.hold(47)
