#!/usr/bin/env python3
"""从分镜表.md 解析每个 DPxx 推导步的帧区间，生成 .frame_offsets.json。

为什么需要：manim 多 Scene 拼接时，每个 Scene 的 self.frame 都从 1 开始。
TimedScene 的 frame_offset 属性告诉它「本场景在全片中的起始帧」，
字幕 updater 才能按全片绝对帧号查 timeline.json。
不设这个 → 拼接后全片字幕错位。

输入（按优先级找第一个存在的）：
  1. 分镜表.md            —— render_storyboard.py 的产物，形如：
                            | DP01 | 1-75 | ...
                            或「帧区间：1-75」
  2. .frame_offsets.json  —— 已存在则不动（允许手工指定）

输出：.frame_offsets.json
  {"DP01": {"start": 1, "end": 75}, "DP02": {"start": 76, "end": 150}, ...}

分镜表里没提到的 DPxx 不给 offset（保持 0，即单场景模式）。
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.environ.get("VIDEO_CRAFT_ROOT", os.getcwd()))
OUT = os.path.join(ROOT, ".frame_offsets.json")
SB = os.path.join(ROOT, "分镜表.md")


def parse_storyboard(text: str) -> dict:
    """两种格式都认：
    A. 表格行：  | DP01 | 1-75 | ...
    B. 小节：    ## 推导步 DP01  ...  帧区间：1-75（或 帧区间：{S01.from}-{S03.to} 已替换后的数字）
    """
    out = {}
    # 格式 A：表格行
    for m in re.finditer(r"^\|\s*(DP\d+)\s*\|[^|]*?\b(\d+)\s*[-–]\s*(\d+)\b", text, re.M):
        out[m.group(1)] = {"start": int(m.group(2)), "end": int(m.group(3))}
    if out:
        return out
    # 格式 B：小节 + 帧区间行
    blocks = re.split(r"^##\s+", text, flags=re.M)
    for b in blocks:
        hm = re.match(r"推导步\s+(DP\d+)", b)
        if not hm:
            continue
        sid = hm.group(1)
        rm = re.search(r"帧区间[：:]\s*(\d+)\s*[-–]\s*(\d+)", b)
        if rm:
            out[sid] = {"start": int(rm.group(1)), "end": int(rm.group(2))}
    return out


def main():
    if os.path.exists(OUT):
        print(f"frame_offsets: 已存在 {OUT}，不覆盖（删掉它可从分镜表重新生成）")
        return
    if not os.path.exists(SB):
        print(f"frame_offsets: 没有 {SB} —— 跳过多 Scene 字幕对齐（单场景模式不受影响）")
        return
    text = open(SB, encoding="utf-8").read()
    offsets = parse_storyboard(text)
    if not offsets:
        print(f"frame_offsets: {SB} 里没解析出 DPxx 帧区间 —— 跳过多 Scene 字幕对齐")
        return
    # 校验：区间应首尾相接（或至少不重叠）
    items = sorted(offsets.items(), key=lambda kv: kv[1]["start"])
    for i in range(len(items) - 1):
        a, b = items[i][1], items[i + 1][1]
        if b["start"] <= a["end"]:
            print(f"⚠ frame_offsets: {items[i][0]}({a['start']}-{a['end']}) 与 "
                  f"{items[i+1][0]}({b['start']}-{b['end']}) 重叠——检查分镜表")
    json.dump(offsets, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"frame_offsets: {len(offsets)} 个场景 → {OUT}")
    for k, v in items:
        print(f"  {k}: f{v['start']}-f{v['end']} ({v['end'] - v['start'] + 1} 帧)")


if __name__ == "__main__":
    main()
