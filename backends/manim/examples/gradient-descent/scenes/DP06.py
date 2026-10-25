"""DP06 梯度即最陡上升。

把一元导数推广到多元梯度，指出 ∇f 指向增长最快的方向。
帧预算 186（f1316-f1501）：一阶式静态 + 梯度式 45 + 说明 30 + 向量示意 60 + 停留 50。
「向量随位置改变方向」的示意把死寂变成持续运动。
"""
import numpy as np
from manim import Arrow, ParametricFunction, Transform

from common import Formula, TimedScene, plain
from common import style


def bowl(t):
    """一个碗形曲面的一维切片（用于展示梯度方向随位置变化）。"""
    x = (t - 0.5) * 6
    y = 0.9 * (t - 0.5) ** 2 * 4 - 0.8
    return np.array([x, y, 0])


class DP06(TimedScene):
    def construct(self):
        # 一阶泰勒式退到上方当配角
        f = Formula(r"f(x+h) \approx f(x) + f'(x)\,h", font_size=style.FONT_SMALL)
        f.move_to([0, 2.4, 0])
        self.add(f)

        # 主公式：梯度定义
        g = Formula(
            r"\nabla f(\theta) = \begin{pmatrix} \partial f/\partial \theta_1 \\ \vdots \\ \partial f/\partial \theta_n \end{pmatrix}"
        )
        g.move_to([0, 1.0, 0])
        self.show(g, frames=45)

        note = plain("∇f 指向函数值增长最快的方向")
        note.move_to([0, -0.3, 0])
        self.show(note, frames=30)

        # 梯度向量示意：碗形曲线上一个点，箭头始终垂直于曲线（= 最陡上升方向）
        curve = ParametricFunction(bowl, t_range=[0, 1, 0.01], color=style.GREY)
        curve.scale_to_fit_width(4.2)
        curve.move_to([0, -1.5, 0])

        def arrow_at(t):
            p = curve.point_from_proportion(t)
            # 碗形 y = 0.9*(x)^2*4 - 0.8，导数 dy/dx ∝ x；法线方向取 (-dy, dx) 归一化
            q = curve.point_from_proportion(min(1.0, t + 0.02))
            d = q - p
            d = d / (np.linalg.norm(d) + 1e-9)
            normal = np.array([-d[1], d[0], 0])
            if normal[1] < 0:
                normal = -normal
            start = p + normal * 0.12
            end = p + normal * 0.85
            return Arrow(start, end, color=style.PURPLE, buff=0, stroke_width=5, max_tip_length_to_length_ratio=0.25)

        arrow = arrow_at(0.5)
        self.add(arrow)
        # 箭头沿曲线连续移动，方向始终跟着法线变（80 帧持续运动，覆盖解说时长）
        t_vals = [0.5, 0.62, 0.5, 0.38, 0.5, 0.68, 0.5, 0.32]
        for t in t_vals:
            self.play_for(Transform(arrow, arrow_at(t)), frames=10)
        self.hold(30)
