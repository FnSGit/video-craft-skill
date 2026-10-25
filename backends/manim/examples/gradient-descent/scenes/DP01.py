"""DP01 处境：雾里的山。

全片唯一的概念引入段——不涉及公式，只用图形建立「山谷」这个意象，
让后面的推导有地方可站。

帧预算 300（f86-f385）：曲线 60 + 标签 45 + 雾 35 + 走山人 130 + 到达 30。
走山人的移动贯穿 160 帧，覆盖这段解说的主体时长——避免「点停住后死寂」
（V2 QC 实测：只让点动 85 帧，剩下 134 帧全静，被判 still>5s）。
"""
import numpy as np
from manim import Circumscribe, Dot, MoveAlongPath, ParametricFunction, Text, VGroup

from common import TimedScene
from common import style


def hill(t):
    """山形曲线：两侧高中间低（U 形，参数 t ∈ [0,1]）。"""
    x = (t - 0.5) * 8
    y = 1.2 + 1.6 * (t - 0.5) ** 2 * 4 - 0.4 * np.sin(t * np.pi)
    return np.array([x, y, 0])


class DP01(TimedScene):
    def construct(self):
        # 山形曲线
        curve = ParametricFunction(hill, t_range=[0, 1, 0.01], color=style.DIM)
        curve.scale_to_fit_width(6.5)
        curve.move_to([0, 0.6, 0])
        self.show(curve, frames=60)

        # 「山顶」与「谷底」标签
        top = Text("山顶", font_size=style.FONT_TEXT, color=style.WHITE, font=style.FONT_CN)
        top.move_to([-3.2, 2.0, 0])
        valley = Text("谷底", font_size=style.FONT_TEXT, color=style.WHITE, font=style.FONT_CN)
        valley.move_to([0, -1.1, 0])
        self.show(top, valley, frames=45)

        # 雾：几个半透明圆，营造「看不见谷底」的氛围
        fog = VGroup(
            *[
                Dot(np.array([x, y, 0]), radius=r, color=style.GREY, fill_opacity=0.25)
                for x, y, r in [(-2.4, 1.7, 0.5), (-0.8, 2.1, 0.65), (1.2, 1.8, 0.55), (2.8, 1.6, 0.45)]
            ]
        )
        self.show(*fog, frames=35)

        # 走山人：从山顶沿曲线走到谷底（130 帧，覆盖解说主体时长）
        walker = Dot(curve.point_from_proportion(0.06), radius=0.11, color=style.PURPLE)
        self.add(walker)
        self.play_for(MoveAlongPath(walker, curve), frames=130)

        # 到达反馈：谷底标签画个圈，标记「走到了」
        ring = Circumscribe(valley, color=style.PURPLE, fade_out=True)
        self.play_for(ring, frames=30)
