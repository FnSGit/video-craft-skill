#!/bin/zsh
# 整片渲染：VER=v1 scripts/render.sh
#   → renders/<slug>_v1.mp4 + fin_frames/（供 core/motion_check.py、core/frame_metrics.py 读）
# 每个 DPxx 场景单独渲染，再按 timeline.json 的顺序拼接——manim 的多场景拼接没有
# remotion 的 Video 合成那么直接，这里用 ffmpeg concat，帧号连续由 timeline.json 保证。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
export PATH="/opt/homebrew/bin:$PATH"          # manim 需要 pkg-config/cairo/ffmpeg
[ -n "$PKG_CONFIG_PATH" ] || export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
V=${VER:-v1}
SLUG=$(python3 -c "import json;print(json.load(open('config.json'))['slug'])")
Q=${Q:-qm}                                     # 默认中等画质；终稿用 -qh（--quality high）
mkdir -p renders

SCENES=$(ls scenes/DP*.py 2>/dev/null | sed 's|scenes/||; s|\.py$||' | sort)
[ -n "$SCENES" ] || { echo "scenes/ 下没有 DP*.py"; exit 1; }

rm -rf renders/parts_$V && mkdir -p renders/parts_$V
for S in $SCENES; do
  echo "render $S ..."
  .venv/bin/manim render -$Q "scenes/$S.py" "$S" --media_dir media >/dev/null 2>&1
  # manim 输出到 media/videos/<Scene>.mp4（-ql/-qm/-qh 决定子目录）
  SRC=$(find media/videos -name "$S.mp4" | head -1)
  [ -n "$SRC" ] || { echo "RENDER FAILED: $S 没找到输出"; exit 1; }
  cp "$SRC" "renders/parts_$V/$S.mp4"
done

# 拼接
LIST=renders/parts_$V/list.txt
: > "$LIST"
for S in $SCENES; do echo "file '$S.mp4'" >> "$LIST"; done
ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy "renders/${SLUG}_${V}.mp4"
[ -s "renders/${SLUG}_${V}.mp4" ] || { echo "RENDER FAILED"; exit 1; }

# 抽帧供 core QC 脚本读
rm -rf fin_frames && mkdir -p fin_frames
ffmpeg -v error -y -i "renders/${SLUG}_${V}.mp4" -q:v 4 fin_frames/f_%04d.jpg
ls fin_frames | wc -l > fin_count.txt
python3 scripts/sheet.py fin_frames "renders/sheet_${V}.html" 60 || true
echo "done: renders/${SLUG}_${V}.mp4 ($(ls fin_frames | wc -l) frames)"
