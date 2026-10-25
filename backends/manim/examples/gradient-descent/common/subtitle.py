"""字幕 mobject——读 core/tts_build.py 产出的 script/timeline.json。

与 remotion 后端的字幕规范对齐：44px 白字黑边，位于画面底部 y637–690
（remotion 左上原点）→ manim 坐标 y ∈ [-330, -277]。

用法：
    sub = SubtitleTrack("script/timeline.json")
    # 在 Scene 里：sub.add_to(self)  然后 self.add(sub.mob)
    # 或按帧取当前字幕：sub.at(frame) → Mobject | None
"""
import json
import os

from manim import Text, VGroup

from . import style


class SubtitleTrack:
    def __init__(self, timeline_path: str = "script/timeline.json", font_size: int = style.FONT_SUBTITLE):
        if not os.path.exists(timeline_path):
            raise FileNotFoundError(f"{timeline_path} 不存在——先跑 core/tts_build.py 生成时间轴")
        tl = json.load(open(timeline_path, encoding="utf-8"))
        self.fps = tl.get("fps", style.FPS)
        self.total = tl.get("total_frames", 0)
        # 字幕块（一句可切多个块，用 | 分隔）
        self.blocks = []
        for s in tl["sentences"]:
            for sb in s["subs"]:
                self.blocks.append(
                    {"from": sb["from"], "to": sb["to"], "text": sb["text"], "sentence": s["id"]}
                )
        self.font_size = font_size
        self._cache = {}

    def at(self, frame: int):
        """返回该帧对应的字幕文本；没有则 None。frame 从 1 起（与 timeline.json 一致）。"""
        for b in self.blocks:
            if b["from"] <= frame <= b["to"]:
                return b["text"]
        return None

    def mob_at(self, frame: int):
        """返回该帧的字幕 Mobject（带缓存）。"""
        text = self.at(frame)
        if text is None:
            return None
        if text not in self._cache:
            m = Text(text, font_size=self.font_size, color=style.WHITE, font=style.FONT_CN)
            # 黑边：manim 用 stroke_width 描边
            m.set_stroke(color=style.BLACK, width=6)
            # 位置：字幕带中心。remotion y637-690 中心 ≈ 663 → manim y = 360-663 = -303
            m.move_to([0, -303, 0])
            self._cache[text] = m
        return self._cache[text]


def add_subtitle(scene, track: SubtitleTrack, frame: int):
    """把当前帧的字幕加进 scene（每帧调用；manim 的 updater 模式见下）。"""
    mob = track.mob_at(frame)
    if mob is not None and mob not in scene.mobjects:
        scene.add(mob)
    return mob
