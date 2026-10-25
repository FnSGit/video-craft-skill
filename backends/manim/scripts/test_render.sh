#!/bin/zsh
# 低画质快渲单个推导步：test_render.sh <Scene: DP01>
# 验证场景能跑、语法没错、动画播得完，几秒完成。
# ⚠ 用 -qm（30fps）而非 -ql：-ql 是 15fps，会让 frames= 参数换算错帧数，
   帧预算校验失真（V2 样片实测踩过）。降画质用 -r 指定低分辨率，帧率保持 30。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
source "$ROOT/scripts/env.sh"

S=$1
[ -n "$S" ] || { echo "usage: test_render.sh <Scene>"; exit 1; }
time .venv/bin/manim render -qm -r 480,270 "scenes/$S.py" "$S" --media_dir media 2>&1 | tail -6
SRC=$(find media/videos -name "$S.mp4" | head -1)
[ -n "$SRC" ] && echo "OK: $SRC" || echo "FAILED"
