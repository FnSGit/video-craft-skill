"""DP08 局部逼近全局。

「重复足够多次 → 走到平地」——解释为什么这个局部规则能逼近全局最优。
"""
from common import Formula, TimedScene, plain
from common import style


class DP08(TimedScene):
    def construct(self):
        # 更新规则缩小留在屏幕上
        hero = Formula(
            r"\theta_{\text{new}} = \theta_{\text{old}} - \eta\,\nabla f(\theta_{\text{old}})",
            font_size=style.FONT_TEXT,
        )
        hero.move_to([0, 1.7, 0])
        self.add(hero)

        loop = plain("重复 ⇒ 走到平地")
        loop.move_to([0, 0.2, 0])
        self.show(loop, frames=40)

        note = plain("每一步只用局部坡度，不预设知道谷底在哪")
        note.move_to([0, -1.2, 0])
        self.show(note, frames=30)
        self.hold(76)
