"""DP04 一阶泰勒展开（全片第一个核心公式）。

f(x+h) ≈ f(x) + f'(x)h —— 这是整个推导的地基。
进入纯公式段，此处清屏。
"""
from common import Formula, TimedScene, plain
from common import style


class DP04(TimedScene):
    def construct(self):
        f = Formula(r"f(x+h) \approx f(x) + f'(x)\,h")
        f.move_to([0, 0.9, 0])
        self.show(f, frames=50)

        # 中文说明走 Text
        note = plain("局部看，任何光滑函数都像一条直线")
        note.move_to([0, -0.5, 0])
        self.show(note, frames=30)
        self.hold(101)
