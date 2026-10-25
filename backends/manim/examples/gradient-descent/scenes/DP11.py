"""DP11 步长上限（全片第二个高光时刻）。

η < 2/λ_max(H) —— 从二阶条件整理出的安全步长上限。
帧预算 275（f2830-f3104）：二阶式静态 + 上限式 55 + 说明 30 + 椭圆示意 100 + 停留 90。
椭圆示意：λ_max 是椭圆长轴——长轴越长，安全步长越短。
"""
import numpy as np
from manim import Arrow, Ellipse, Transform, VGroup

from common import Formula, TimedScene, plain
from common import style


class DP11(TimedScene):
    def construct(self):
        # 二阶展开式退到上方
        prev = Formula(
            r"f(\theta - \eta\nabla f) \approx f(\theta) - \eta\|\nabla f\|^2 + \frac{\eta^2}{2}(\nabla f)^{\!T} H (\nabla f)",
            font_size=style.FONT_SMALL,
        )
        prev.move_to([0, 2.6, 0])
        self.add(prev)

        # 主角：上限不等式
        hero = Formula(r"\eta < \frac{2}{\lambda_{\max}(H)}")
        hero.move_to([0, 1.5, 0])
        self.show(hero, frames=55)

        note = plain("超过这条线，每一步都在往上爬")
        note.font_size = style.FONT_SMALL
        note.move_to([0, 0.5, 0])
        self.show(note, frames=30)

        # 椭圆示意：长轴 = λ_max 方向
        ell = Ellipse(width=4.6, height=2.0, color=style.GREY)
        ell.move_to([0, -0.9, 0])
        self.show(ell, frames=35)

        # 长轴箭头（λ_max 方向）
        long_axis = Arrow(
            np.array([-2.3, -0.9, 0]), np.array([2.3, -0.9, 0]),
            color=style.PURPLE, buff=0, stroke_width=5,
        )
        self.show(long_axis, frames=30)

        lam = plain("λ_max：长轴")
        lam.font_size = style.FONT_SMALL
        lam.move_to([0, -2.3, 0])
        self.show(lam, frames=25)

        # 长轴越长 → 上限越低的对照：椭圆与箭头同步拉长（35 帧）
        ell_wider = Ellipse(width=5.8, height=1.4, color=style.GREY)
        ell_wider.move_to([0, -0.9, 0])
        axis_wider = Arrow(
            np.array([-2.9, -0.9, 0]), np.array([2.9, -0.9, 0]),
            color=style.PURPLE, buff=0, stroke_width=5,
        )
        self.play_for(
            Transform(VGroup(ell, long_axis), VGroup(ell_wider, axis_wider)),
            frames=35,
        )

        # 短轴箭头来回扫动：椭圆变形太细微，降采样后看不见
        # V2 QC 实测：只有椭圆变形时 still 9.1s，判 fail
        short_axis = Arrow(
            np.array([0, -1.8, 0]), np.array([0, 0.0, 0]),
            color=style.DIM, buff=0, stroke_width=4,
        )
        self.show(short_axis, frames=20)
        for dy in [-0.45, 0.45]:
            self.play_for(
                Transform(
                    short_axis,
                    Arrow(
                        np.array([0, -1.8 + dy, 0]), np.array([0, 0.0 + dy, 0]),
                        color=style.DIM, buff=0, stroke_width=4,
                    ),
                ),
                frames=20,
            )
        self.hold(4)
