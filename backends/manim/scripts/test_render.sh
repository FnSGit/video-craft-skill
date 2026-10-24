#!/bin/zsh
# 低画质快渲单个推导步：test_render.sh <Scene: DP01>
# 验证场景能跑、语法没错、动画播得完，几秒完成。⚠ 画幅用 -ql（854x480@15fps），
# 只用于快速验证；要看真实画幅用 render.sh（-qm = 1280x720@30fps）。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
source "$ROOT/scripts/env.sh"

S=$1
[ -n "$S" ] || { echo "usage: test_render.sh <Scene>"; exit 1; }
time .venv/bin/manim render -ql "scenes/$S.py" "$S" --media_dir media 2>&1 | tail -6
SRC=$(find media/videos -name "$S.mp4" | head -1)
[ -n "$SRC" ] && echo "OK: $SRC" || echo "FAILED"
