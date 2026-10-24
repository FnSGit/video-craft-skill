#!/bin/zsh
# 低画质快渲单个推导步：test_render.sh <Scene: DP01>
# 验证场景能跑、语法没错、帧数对得上，几秒完成。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export PATH="/opt/homebrew/bin:$PATH"
[ -n "$PKG_CONFIG_PATH" ] || export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
S=$1
[ -n "$S" ] || { echo "usage: test_render.sh <Scene>"; exit 1; }
time .venv/bin/manim render -ql "scenes/$S.py" "$S" --media_dir media 2>&1 | tail -6
SRC=$(find media/videos -name "$S.mp4" | head -1)
[ -n "$SRC" ] && echo "OK: $SRC" || echo "FAILED"
