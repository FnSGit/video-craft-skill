#!/bin/zsh
# 整片渲染：VER=v1 scripts/render.sh
#   → renders/<slug>_v1.mp4 + fin_frames/（供 core/motion_check.py、core/frame_metrics.py 读）
# 每个 DPxx 场景单独渲染，再按 timeline.json 的顺序拼接——manim 的多场景拼接没有
# remotion 的 Video 合成那么直接，这里用 ffmpeg concat，帧号连续由 timeline.json 保证。
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
source "$ROOT/scripts/env.sh"          # cairo + texlive + TEXMFROOT/TEXMFCNF（见该文件注释）
# 画幅权威来源：-qm = 1280x720@30fps（manim 0.22 的 -q 会覆盖 manim.cfg）
Q=${Q:-qm}

V=${VER:-v1}
SLUG=$(python3 -c "import json;print(json.load(open('config.json'))['slug'])")
mkdir -p renders

# ⚠ zsh 不会像 bash 那样把 "$(cmd)" 按换行分词成多个词——
#   for S in $SCENES 会拿到单个含 \n 的字符串，导致 manim 收到
#   'scenes/DP01\nDP02.py' 这种坏路径。用 ${(f)...} 显式按行拆成数组。
SCENES=(${(f)"$(ls scenes/DP*.py 2>/dev/null | sed 's|scenes/||; s|\.py$||' | sort)"})
[ -n "$SCENES" ] || { echo "scenes/ 下没有 DP*.py"; exit 1; }

# ---- frame_offset 注入：多 Scene 拼接时字幕对齐的关键 ----
# 每个 Scene 的 self.frame 原本从 1 开始，拼接后字幕会按场景内相对帧号查
# timeline.json → 全片字幕错位。这里从分镜表.md 读每个 DPxx 的帧区间，
# 生成 .frame_offsets.json，由 common/timed_scene.py 在渲染时读取。
#
# 分镜表格式（manim 端）：| DP01 | <起始帧>-<结束帧> | ...  或  ## 推导步 DP01  …  帧区间：{S01.from}-{S03.to}
.venv/bin/python scripts/gen_frame_offsets.py 2>/dev/null || true

rm -rf renders/parts_$V && mkdir -p renders/parts_$V
for S in $SCENES; do
  echo "render $S ..."
  # 不吞输出：manim 的报错要能看到（V1 曾被 set -e + >/dev/null 吞掉真实错误）
  .venv/bin/manim render -$Q "scenes/$S.py" "$S" --media_dir media >/dev/null 2>&1 || {
    echo "RENDER FAILED: $S —— 重跑一次看详细错误："
    echo "  .venv/bin/manim render -$Q scenes/$S.py $S --media_dir media"
    exit 1
  }
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
