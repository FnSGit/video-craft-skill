"""DP12 山顶谷底之异 · 取舍 · 收尾（全片最后一个高光时刻）。

三段：靠近最优点时二阶项相对变大 → 速度 vs 稳定的取舍 → 回到最初的更新规则闭环。
帧预算 708（f3155-f3862）：上限式静态 0 + 观察 45+35 + 取舍 35+30 + 收尾闭环 380 + 停留 55。
收尾段用「小球反复沿曲线下降」把最长的死寂变成可持续观看的迭代运动——
这正是梯度下降本身的动作，也是全片的视觉收束。
"""
import numpy as np
from manim import Dot, MoveAlongPath, ParametricFunction, Transform, VGroup

from common import Formula, TimedScene, plain
from common import style


def bowl(t):
    """碗形曲线：y = 0.5*(x)^2，x ∈ [-3, 3]。"""
    x = (t - 0.5) * 6
    y = 0.5 * (x / 3.0) ** 2 * 1.5 - 1.5
    return np.array([x, y, 0])


class DP12(TimedScene):
    def construct(self):
        # 上限公式留在屏幕上
        hero = Formula(r"\eta < \frac{2}{\lambda_{\max}(H)}", font_size=style.FONT_TEXT)
        hero.move_to([0, 2.4, 0])
        self.add(hero)

        # 第一段：山顶谷底之异
        obs = plain("靠近最点时 ‖∇f‖ 变小 ⇒ 二阶项相对变大")
        obs.font_size = style.FONT_SMALL
        obs.move_to([0, 1.3, 0])
        self.show(obs, frames=45)
        self.hold(35)

        # 第二段：取舍
        tradeoff = plain("速度  ←→  稳定")
        tradeoff.font_size = style.FONT_SMALL
        tradeoff.move_to([0, 0.1, 0])
        self.show(tradeoff, frames=35)
        self.hold(30)

        # 第三段：收尾——碗形曲线 + 小球反复下降（380 帧的主体）
        curve = ParametricFunction(bowl, t_range=[0, 1, 0.01], color=style.GREY)
        curve.scale_to_fit_width(5.6)
        curve.move_to([0, -1.3, 0])
        self.show(curve, frames=40)

        # 更新规则作为主角在场（缩小）
        final = Formula(
            r"\theta_{\text{new}} = \theta_{\text{old}} - \eta\,\nabla f(\theta_{\text{old}})",
            font_size=style.FONT_SMALL,
        )
        final.move_to([0, 1.5, 0])
        self.show(final, frames=40)

        # 小球从左侧高处出发，沿曲线分多步滑向谷底（9 步 × 40 帧 = 360 帧）
        # 步数多一点、每步短一点，视觉上更像「反复迭代」而不是「走一段停一段」
        ball = Dot(curve.point_from_proportion(0.02), radius=0.11, color=style.PURPLE)
        self.add(ball)
        for i in range(9):
            self.play_for(
                MoveAlongPath(ball, curve),
                frames=40,
                rate_func=lambda t, s=(i + 1) / 9: min(1.0, t * (s * 9 / 9)),
            )
        self.hold(123)
