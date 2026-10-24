"""示例推导步：从 a = b + c 推出 b = a - c。

用途：V1 最小闭环的验证场景——证明 manim 后端能
  1. 用 TimedScene 帧级计时
  2. 从 script/timeline.json 上字幕
  3. 用 Formula 排公式（text 模式下 ASCII 近似，latex 模式下真公式）
  4. 产出可被 core/motion_check.py 读的帧
"""
from manim import Transform, VGroup

from common import Formula, TimedScene
from common import style


class DP01(TimedScene):
    """推导步 01：移项。"""

    timeline_path = "script/timeline.json"

    def construct(self):
        # 起点式
        a = Formula(r"a = b + c")
        a.move_to([0, 1.2, 0])
        self.show(a, frames=45)
        self.hold(30)

        # 高亮要操作的项：b + c
        box = a.box_around(2, 5)  # 'b + c' 的字符区间（latex 模式按字符切）
        self.show(box, frames=20)
        self.hold(30)

        # 变换到 b = a - c
        b = Formula(r"b = a - c")
        b.move_to([0, 1.2, 0])
        self.play_for(Transform(a, b), frames=45)
        self.hold(45)
