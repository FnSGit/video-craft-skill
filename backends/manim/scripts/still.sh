#!/bin/zsh
# 单帧静图：still.sh <Scene: DP01> [帧号 1 起,仅用于命名] [输出目录]
# ⚠ manim 0.22 没有「按帧号出静图」的参数：-t 是 --transparent（透明背景）不是动画进度。
#   这里用 --format=png 存最后一帧（fast-forward 所有动画），帧号只进文件名。
#   要中间态就临时改场景的动画时长，或先用 test_render.sh 渲片段再 ffmpeg 抽帧。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
source "$ROOT/scripts/env.sh"

S=$1; N=${2:-99}; OUT=${3:-stills}
[ -n "$S" ] || { echo "usage: still.sh <Scene> [frame_label] [out_dir]"; exit 1; }
mkdir -p "$OUT"
.venv/bin/manim render -s --format=png -qm "scenes/$S.py" "$S" --media_dir media >/dev/null 2>&1
SRC=$(find media/images -name "$S*.png" | head -1)
[ -n "$SRC" ] || { echo "STILL FAILED: $S"; exit 1; }
cp "$SRC" "$OUT/f_$(printf %04d $N).png"
echo "$OUT/f_$(printf %04d $N).png"
