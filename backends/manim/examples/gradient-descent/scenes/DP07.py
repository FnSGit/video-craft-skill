"""DP07 更新规则（全片第一个高光时刻）。

θ_new = θ_old - η∇f(θ_old) —— 全片的主角公式，登场要给足排面。
"""
from common import Formula, TimedScene, plain
from common import style


class DP07(TimedScene):
    def construct(self):
        # 前面的公式退场，清屏给主角
        hero = Formula(r"\theta_{\text{new}} = \theta_{\text{old}} - \eta\,\nabla f(\theta_{\text{old}})")
        hero.move_to([0, 0.4, 0])
        self.show(hero, frames=55)

        # 逐项注解（中文走 Text）
        sign = plain("减号：往下走")
        sign.move_to([-2.7, -1.4, 0])
        eta = plain("η：步长")
        eta.move_to([0.5, -1.4, 0])
        self.show(sign, eta, frames=35)
        self.hold(183)
