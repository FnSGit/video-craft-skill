"""DP05 下降最快的方向。

在一阶泰勒式上指出：h 取负号时，函数值下降。
"""
from common import Formula, TimedScene, plain
from common import style


class DP05(TimedScene):
    def construct(self):
        f = Formula(r"f(x+h) \approx f(x) + f'(x)\,h")
        f.move_to([0, 1.0, 0])
        self.add(f)

        # 高亮 f'(x)h 项
        box = f.box_around(len(f) - 3, None)
        self.show(box, frames=25)

        # 中文说明走 Text
        note = plain("取 h < 0 且 f'(x) > 0  ⇒  函数值下降")
        note.move_to([0, -0.6, 0])
        self.show(note, frames=35)
        self.hold(57)
