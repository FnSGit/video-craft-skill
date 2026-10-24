#!/bin/zsh
# 前 N 秒样片（确认点 4 用）：preview.sh [秒数=30] [起始秒=0]
# 做法：按 timeline.json 找出覆盖该时间段的推导步，只渲这些再拼接。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export PATH="/opt/homebrew/bin:$PATH"
[ -n "$PKG_CONFIG_PATH" ] || export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
SEC=${1:-30}; FROM=${2:-0}
SLUG=$(python3 -c "import json;print(json.load(open('config.json'))['slug'])")
A=$((FROM * 30)); B=$((A + SEC * 30 - 1))
mkdir -p renders
OUTF="renders/${SLUG}_preview_${FROM}-$((FROM + SEC))s.mp4"

# 从 timeline.json 找时间段内的句子 → 但推导步与句子的映射在分镜表里，这里简化为
# 渲染全部场景后按帧区间裁切（manim 场景通常不长，成本可接受）
SCENES=$(ls scenes/DP*.py 2>/dev/null | sed 's|scenes/||; s|\.py$||' | sort)
[ -n "$SCENES" ] || { echo "scenes/ 下没有 DP*.py"; exit 1; }
rm -rf renders/parts_prev && mkdir -p renders/parts_prev
for S in $SCENES; do
  .venv/bin/manim render -ql "scenes/$S.py" "$S" --media_dir media >/dev/null 2>&1
  SRC=$(find media/videos -name "$S.mp4" | head -1)
  [ -n "$SRC" ] && cp "$SRC" "renders/parts_prev/$S.mp4"
done
LIST=renders/parts_prev/list.txt
: > "$LIST"
for S in $SCENES; do [ -f "renders/parts_prev/$S.mp4" ] && echo "file '$S.mp4'" >> "$LIST"; done
ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy renders/_all_prev.mp4
ffmpeg -v error -y -i renders/_all_prev.mp4 -vf "select='between(n\,$A\,$B)',setpts=N/30/TB" -frames:v $((B - A + 1)) -c:v libx264 -pix_fmt yuv420p "$OUTF"
[ -s "$OUTF" ] || { echo "PREVIEW FAILED"; exit 1; }
echo "$OUTF"
