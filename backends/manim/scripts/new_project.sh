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
for s in render.sh preview.sh still.sh test_render.sh env.sh; do
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
# LaTeX 检查——MathTeX 必需。basictex 装在 /usr/local/texlive，不在默认 PATH，
# 所以这里显式把 texlive bin 加进来再检测（否则明明装了也报缺失）。
TEXLIVE_BIN=/usr/local/texlive/2026basic/bin/universal-darwin
TEXLIVE_EXTRA=${TEXLIVE_EXTRA:-$HOME/.local/texlive-extra}
PATH_HAVE_LATEX=0
if command -v latex >/dev/null 2>&1; then
  PATH_HAVE_LATEX=1
elif [ -x "$TEXLIVE_BIN/latex" ]; then
  PATH_HAVE_LATEX=1
fi
if [ "$PATH_HAVE_LATEX" = 0 ]; then
  echo "⚠ 找不到 latex —— 将用 MANIM_TEX=text（ASCII 近似公式）。"
  echo "   推导片需要正确公式排版，请先装：brew install --cask basictex"
  echo "   然后补两个包：sudo tlmgr install standalone dvisvgm preview"
  echo "   详见 backends/manim/README.md 零节。"
fi
uv venv --python 3.14 .venv >/dev/null 2>&1
uv pip install --python .venv/bin/python manim numpy pillow >/dev/null 2>&1
# 把本机的 texlive-extra 路径写进 .envrc：standalone/preview 宏包与 dvisvgm 二进制
# 是用户态装的（sudo tlmgr 装不了时的手工方案），render.sh 读这个变量。
if [ -d "$TEXLIVE_EXTRA" ]; then
  echo "TEXLIVE_EXTRA=$TEXLIVE_EXTRA" > "$DEST/.envrc"
fi
# 冒烟测试：模板自带的 DP01 场景能渲出非空画面才算项目可用
if [ -f "$DEST/scenes/DP01.py" ] && [ -x "$DEST/.venv/bin/manim" ]; then
  SMOKE=$(cd "$DEST" && zsh scripts/test_render.sh DP01 2>&1 | tail -1)
  case "$SMOKE" in
    OK:*) echo "  冒烟测试通过：$(basename $SMOKE)" ;;
    *)    echo "  ⚠ 冒烟测试未通过（$SMOKE）——检查上面 backends/manim/README.md 零节的环境依赖" ;;
  esac
fi
echo "project ready: $DEST (slug=$SLUG, backend=manim)"
echo "  venv: .venv  |  建场景: scenes/DPxx.py  |  渲染: scripts/render.sh"
