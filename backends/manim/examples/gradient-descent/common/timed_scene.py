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
import json
import os
import sys

from manim import Scene

from . import style
from .subtitle import SubtitleTrack


class TimedScene(Scene):
    """帧级计时的 Scene。self.frame 是当前帧号（1 起，与 timeline.json 一致）。

    frame_offset：本场景在全片中的起始帧（1 起）。多 Scene 拼接时必须设，
    否则每个 Scene 的 self.frame 都从 1 开始，字幕会按场景内相对帧号查
    timeline.json → 拼接后全片字幕错位。

    两种设法：
      · 每个 Scene 类上写死 `frame_offset = 151`（简单，但换配音后要手动改）
      · 由 render.sh 从分镜表自动注入（推荐，见 render.sh 的 --frame-offset 逻辑）
    """

    timeline_path = "script/timeline.json"
    show_subtitle = True
    frame_offset = 0          # 全片起始帧偏移；0 = 单场景独立渲染（不拼接）
    frame_span = None         # (start, end) 声明区间，供 check_frame_budget 核对

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_frame_offset()

    def _apply_frame_offset(self):
        """从 .frame_offsets.json 读本场景的全片起始帧（render.sh 生成）。

        类上手写的 frame_offset 优先（临时调试用）；文件里有就用文件的。
        """
        if self.frame_offset:
            return
        p = os.path.join(os.getcwd(), ".frame_offsets.json")
        if not os.path.exists(p):
            return
        try:
            data = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            return
        me = data.get(type(self).__name__)
        if me:
            self.frame_offset = int(me.get("start", 0)) - 1   # 转成偏移量（起始帧减 1）
            self.frame_span = (int(me["start"]), int(me["end"]))

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

    def render(self, preview: bool = False) -> bool:
        """包一层 render：construct 结束后自动核对帧预算。

        为什么自动：手写 check_frame_budget() 调用一定会忘（V2 样片实测：
        12 个场景全部没调，导致每个场景帧数比声明区间少 56–463 帧，
        成片 1585 帧 vs 预期 3962 帧，字幕与画面整体错位）。
        """
        ok = super().render(preview)
        self.check_frame_budget()
        return ok

    def _update_subtitle(self, dt):
        """每帧调用。注意 scene 级 updater 签名是 func(dt) 单参数
        （mobject 级才是 func(mob, dt)）——用错会 TypeError。

        用 self.time（秒）反推帧号，比「每帧 +1」更可靠：updater 频率虽与
        渲染帧率一致，但 dt 累计有浮点误差。
        """
        if self.track is None:
            return
        from manim import config

        fps = config.frame_rate or style.FPS
        # self.time 是场景内已播放秒数；加上 frame_offset 得到全片绝对帧号
        self.frame = int(self.time * fps + 0.5) + 1 + self.frame_offset
        cur = self.track.mob_at(self.frame)
        if cur is not self._sub_mob:
            if self._sub_mob is not None and self._sub_mob in self.mobjects:
                self.remove(self._sub_mob)
            if cur is not None:
                self.add(cur)
            self._sub_mob = cur

    def check_frame_budget(self):
        """ construct 结束时调用：检查本场景实际帧数与 frame_offset 声明的区间是否吻合。

        render.sh 会在每个 Scene 渲染前注入 frame_offset（从分镜表读），
        这里在渲染后核对实际产出帧数，防止「声明 151 帧但实际渲了 160 帧」
        导致后续 Scene 的字幕整体偏移。
        """
        if self.frame_offset <= 0:
            return
        declared = getattr(self, "frame_span", None)
        if declared is None:
            return
        start, end = declared
        actual_end = self.frame
        if abs(actual_end - end) > 2:
            print(
                f"⚠ {type(self).__name__}: frame_offset={self.frame_offset} "
                f"声明区间 {start}-{end}，实际结束于 f{actual_end}（差 {actual_end - end:+d} 帧）。"
                f"后续 Scene 的字幕会偏移——改场景的 frames= 参数，或更新分镜表。",
                file=sys.stderr,
            )

    def _frames_to_run_time(self, frames: float) -> float:
        """帧数 → manim 的 run_time（秒）。

        ⚠ 必须读 manim 的实际 config.frame_rate，不能用硬编码 30：
        -ql 是 15fps、-qm 是 30fps、-qh 是 60fps。硬编码 30 时，
        在 -ql 下 frames=70 会被算成 70/30=2.33s=35 帧（15fps），
        导致测渲与正式渲染的帧数不一致（V2 样片实测：DP01 在 -ql 下
        出了 674 帧而非声明的 300 帧）。
        """
        from manim import config

        fps = config.frame_rate or style.FPS
        return frames / fps

    def show(self, *mobjects, frames: int = 30, rate_func=None, **kw):
        """入场：写入场动画并占用 frames 帧。"""
        from manim import FadeIn

        # rate_func 只在非 None 时注入：manim 的 Animation.rate_func 需要 callable，
        # 显式传 None 会 TypeError（"'NoneType' object is not callable"）。
        if rate_func is not None:
            kw["rate_func"] = rate_func
        self.play(*[FadeIn(m, **kw) for m in mobjects], run_time=self._frames_to_run_time(frames))

    def hold(self, frames: int):
        """静止停留 frames 帧——推导片的核心节奏：让观众看清当前式子。"""
        self.wait(self._frames_to_run_time(frames))

    def play_for(self, *animations, frames: int, rate_func=None):
        """指定帧数的 play。

        rate_func 透传给 manim（如 lambda t: t*0.12 表示只走 12% 路程），
        用来做「学习率太小只挪一点点」这类演示。None 时不给 manim 传
        （manim 的 rate_func 默认是 smooth，传 None 会 TypeError）。
        """
        if rate_func is None:
            self.play(*animations, run_time=self._frames_to_run_time(frames))
        else:
            self.play(*animations, run_time=self._frames_to_run_time(frames), rate_func=rate_func)

    def total_frames(self) -> int:
        if self.track is not None:
            return self.track.total
        return self.frame
