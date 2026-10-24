#!/bin/zsh
# 单帧静图：still.sh <Scene: DP01> <帧号 1 起> <输出目录(绝对路径)>
# 用于构建期自检（每推导步至少看一眼公式排版对不对）。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export PATH="/opt/homebrew/bin:$PATH"
[ -n "$PKG_CONFIG_PATH" ] || export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
S=$1; N=${2:-45}; OUT=${3:-stills}
[ -n "$S" ] || { echo "usage: still.sh <Scene> [frame_1based] [out_dir]"; exit 1; }
mkdir -p "$OUT"
# manim 的 still 用 -s（save last frame）；帧号用 -t（动画进度 0..1）
PROG=$(python3 -c "print(f'{$N/120:.4f}')")
.venv/bin/manim render -s -t "$PROG" "scenes/$S.py" "$S" --media_dir media >/dev/null 2>&1
SRC=$(find media/images -name "$S.png" | head -1)
[ -n "$SRC" ] || { echo "STILL FAILED: $S"; exit 1; }
cp "$SRC" "$OUT/f_$(printf %04d $N).png"
echo "$OUT/f_$(printf %04d $N).png"
