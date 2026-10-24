"""TimedScene —— 帧级驱动的 Scene 基类。

为什么需要它：core/tts_build.py 产出的 timeline.json 是**帧号**体系
（每句/每字幕块的 from/to 都是帧）。而 manim 原生的 self.wait(秒) 是秒级，
且 manim 内部按「animation 的 run_time」推帧，很难精确对上 timeline.json 的帧号。

做法：用一个「帧预算」机制——每个 self.play()/self.hold() 都指定占用多少帧，
scene 累计帧数；字幕 updater 每帧按累计帧数查 timeline.json。
这样镜头/推导步的帧号与 remotion 后端同源，core/motion_check.py 也能直接读。

用法：
    class DP01(TimedScene):
        def construct(self):
            a = Formula(r"a = b + c")
            self.show(a, 45)            # 写入场，占 45 帧
            self.hold(60)               # 静止 60 帧（推导片常用：让观众看清）
            b = Formula(r"b = a - c")
            self.play(Transform(a, b), frames=30)
"""
from manim import Scene

from . import style
from .subtitle import SubtitleTrack


class TimedScene(Scene):
    """帧级计时的 Scene。self.frame 是当前帧号（1 起，与 timeline.json 一致）。"""

    timeline_path = "script/timeline.json"
    show_subtitle = True

    def setup(self):
        super().setup()
        self.frame = 0
        self.track = None
        if self.show_subtitle:
            try:
                self.track = SubtitleTrack(self.timeline_path)
            except FileNotFoundError:
                self.track = None
        self._sub_mob = None
        if self.track is not None:
            # 每帧刷新字幕
            self.add_updater(self._update_subtitle)

    def _update_subtitle(self, dt):
        """每帧调用。注意 scene 级 updater 签名是 func(dt) 单参数
        （mobject 级才是 func(mob, dt)）——用错会 TypeError。

        用 self.time（秒）反推帧号，比「每帧 +1」更可靠：updater 频率虽与
        渲染帧率一致，但 dt 累计有浮点误差。
        """
        if self.track is None:
            return
        # self.time 是 scene 已播放的秒数；+0.5 取整到最近帧
        self.frame = int(self.time * style.FPS + 0.5) + 1
        cur = self.track.mob_at(self.frame)
        if cur is not self._sub_mob:
            if self._sub_mob is not None and self._sub_mob in self.mobjects:
                self.remove(self._sub_mob)
            if cur is not None:
                self.add(cur)
            self._sub_mob = cur

    def _frames_to_run_time(self, frames: float) -> float:
        return frames / style.FPS

    def show(self, *mobjects, frames: int = 30, **kw):
        """入场：写入场动画并占用 frames 帧。"""
        from manim import FadeIn

        self.play(*[FadeIn(m, **kw) for m in mobjects], run_time=self._frames_to_run_time(frames))

    def hold(self, frames: int):
        """静止停留 frames 帧——推导片的核心节奏：让观众看清当前式子。"""
        self.wait(self._frames_to_run_time(frames))

    def play_for(self, *animations, frames: int):
        """指定帧数的 play。"""
        self.play(*animations, run_time=self._frames_to_run_time(frames))

    def total_frames(self) -> int:
        if self.track is not None:
            return self.track.total
        return self.frame
