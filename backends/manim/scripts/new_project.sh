#!/bin/zsh
# 从模板创建 manim 推导片项目：new_project.sh <目标目录> <slug>
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)      # backends/manim/
TEMPLATE=$HERE/template
DEST=$1; SLUG=${2:-video}
[ -n "$DEST" ] || { echo "usage: new_project.sh <dest_dir> <slug>"; exit 1; }
[ -f "$TEMPLATE/manim.cfg" ] && [ -d "$TEMPLATE/common" ] || { echo "找不到模板（$TEMPLATE 不像 manim template/）"; exit 1; }
case "$SLUG" in
  ''|*[!A-Za-z0-9_-]*) echo "slug 只能用字母/数字/-/_，收到：$SLUG"; exit 1;;
esac
mkdir -p "$DEST"
rsync -a --exclude .venv --exclude media --exclude '__pycache__' --exclude fin_frames "$TEMPLATE/" "$DEST/"

# 后端脚本复制进项目（它们用 dirname($0)/.. 定位项目根）
mkdir -p "$DEST/scripts"
for s in render.sh still.sh preview.sh test_render.sh; do
  cp "$HERE/scripts/$s" "$DEST/scripts/"
done
# core/ 的中性脚本
CORE=${VIDEO_CRAFT_CORE:-$(cd "$HERE/../.." && pwd)/core}
if [ -d "$CORE" ]; then
  for s in tts_build.py render_storyboard.py motion_check.py frame_metrics.py sheet.py; do
    [ -f "$CORE/$s" ] && cp "$CORE/$s" "$DEST/scripts/"
  done
else
  echo "⚠ 找不到 core/（$CORE）——中性脚本未复制，请手动拷贝 core/*.py 到 $DEST/scripts/"
fi

mkdir -p "$DEST/script" "$DEST/research" "$DEST/qc" "$DEST/renders"
cat > "$DEST/config.json" <<EOF
{"slug": "$SLUG", "lang": "zh", "backend": "manim"}
EOF

cd "$DEST"
# manim 需要 cairo/pango（pycairo 编译）；缺了会报 meson build failed
if ! pkg-config --exists cairo 2>/dev/null; then
  echo "⚠ 缺 cairo：请先 brew install pkg-config cairo pango（详见 backends/manim/README.md 零节）"
fi
# LaTeX 检查——MathTex 必需。缺失则退回 text 模式并明确告知
if ! command -v latex >/dev/null 2>&1; then
  echo "⚠ 找不到 latex —— 将用 MANIM_TEX=text（ASCII 近似公式）。"
  echo "   推导片需要正确公式排版，请先：brew install --cask basictex"
  echo "   详见 backends/manim/README.md 零节。"
fi
uv venv --python 3.14 .venv >/dev/null 2>&1
uv pip install --python .venv/bin/python manim numpy pillow >/dev/null 2>&1
echo "project ready: $DEST (slug=$SLUG, backend=manim)"
echo "  venv: .venv  |  建场景: scenes/DPxx.py  |  渲染: scripts/render.sh"
