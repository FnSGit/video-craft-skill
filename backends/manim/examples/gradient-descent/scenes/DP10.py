"""DP10 二阶泰勒展开。

把新位置代回函数，看函数值到底升还是降——展开式里多出二阶项。
帧预算 402（f2398-f2799）：主式 55 + 两项说明 40 + 此消彼长演示 250 + 停留 57。
核心演示：随 η 增大，一阶项（下降）线性增长，二阶项（上升）平方增长——后者终将压倒前者。
"""
import numpy as np
from manim import Axes, Dot, Line, MoveAlongPath, VMobject

from common import Formula, TimedScene, plain
from common import style


class DP10(TimedScene):
    def construct(self):
        f = Formula(
            r"f(\theta - \eta\nabla f) \approx f(\theta) - \eta\|\nabla f\|^2 + \frac{\eta^2}{2}(\nabla f)^{\!T} H (\nabla f)"
        )
        f.move_to([0, 2.2, 0])
        self.show(f, frames=55)

        # 一阶项好、二阶项坏
        good = plain("一阶项  −η‖∇f‖² ：使 f 下降")
        good.font_size = style.FONT_SMALL
        good.move_to([0, 1.2, 0])
        bad = plain("二阶项  (η²/2)(∇f)ᵀH(∇f) ：可能使 f 上升")
        bad.font_size = style.FONT_SMALL
        bad.move_to([0, 0.6, 0])
        self.show(good, bad, frames=40)

        # 此消彼长图：x 轴 η，两条曲线一升一降
        axes = Axes(
            x_range=[0, 4, 1], y_range=[-3, 3, 1],
            x_length=6.4, y_length=2.6,
            axis_config={"color": style.GREY, "include_numbers": False},
        )
        axes.move_to([0, -1.0, 0])
        self.show(axes, frames=30)

        # 一阶项：线性下降
        first = axes.plot(lambda x: -1.2 * x + 0.6, color=style.WHITE)
        # 二阶项：平方上升
        second = axes.plot(lambda x: 0.55 * x * x - 1.4, color=style.PURPLE)
        self.show(first, frames=45)
        self.show(second, frames=45)

        # 两条曲线的交点：二阶项开始压倒一阶项的地方（关键帧）
        # -1.2x + 0.6 = 0.55x² - 1.4 → 0.55x² + 1.2x - 2 = 0 → x ≈ 1.18
        x_cross = (-1.2 + np.sqrt(1.44 + 4 * 0.55 * 2)) / (2 * 0.55)
        p_cross = axes.coords_to_point(x_cross, -1.2 * x_cross + 0.6)
        dot_cross = Dot(p_cross, radius=0.10, color=style.WHITE)
        self.show(dot_cross, frames=30)

        # 交点标注
        label = plain(f"η ≈ {x_cross:.2f} 之后开始上升")
        label.font_size = style.FONT_SMALL
        label.move_to([1.8, -2.3, 0])
        self.show(label, frames=30)

        # 动点沿一阶项曲线跑（60 帧）——曲线画完后不能死寂
        # （V2 QC 实测：两条线画完 + hold 126 帧 = 6.2s 静止，判 fail）
        runner = Dot(axes.coords_to_point(0.1, -1.2 * 0.1 + 0.6), radius=0.09, color=style.WHITE)
        self.add(runner)
        self.play_for(
            __import__("manim").MoveAlongPath(runner, first),
            frames=60,
        )
        self.hold(66)
