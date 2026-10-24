#!/bin/zsh
# 从模板创建新项目：new_project.sh <目标目录> <slug>
# 项目根 = <dest>/，含 src/（remotion 工程）、script/、research/、qc/、public/assets/<slug>/
# core/ 的中性脚本（tts_build / render_storyboard / motion_check / frame_metrics / sheet）
# 不复制进项目——它们由 skill 提供，用 --root 或 VIDEO_CRAFT_ROOT 指向本目录即可。
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)      # backends/remotion/
TEMPLATE=$HERE/template
DEST=$1; SLUG=${2:-video}
[ -n "$DEST" ] || { echo "usage: new_project.sh <dest_dir> <slug>"; exit 1; }
# 本脚本必须留在 backends/remotion/scripts/ 里：$HERE 是下面 rsync 的源，脚本被单独拷到别处时
# $HERE 会指向无关目录（最坏是 /），rsync 就会去复制那整棵目录树
[ -f "$TEMPLATE/src/config.ts" ] && [ -d "$TEMPLATE/src/common" ] || { echo "找不到模板（$TEMPLATE 不像 template/），请从 backends/remotion/scripts/ 里运行本脚本"; exit 1; }
# slug 会进文件名、sed 表达式与渲染命令行，只允许安全字符
case "$SLUG" in
  ''|*[!A-Za-z0-9_-]*) echo "slug 只能用字母/数字/-/_，收到：$SLUG"; exit 1;;
esac
mkdir -p "$DEST"
rsync -a --exclude node_modules --exclude 'build*' --exclude renders --exclude fin_frames --exclude stills --exclude 'audio/cache' "$TEMPLATE/" "$DEST/"
# portable in-place edit: `-i.bak` + rm works on both BSD/macOS and GNU/Linux sed
# (BSD `sed -i ''` breaks on GNU sed, which reads '' as the script and config.ts as a file)
sed -i.bak "s/slug: 'demo'/slug: '$SLUG'/" "$DEST/src/config.ts" && rm -f "$DEST/src/config.ts.bak"
mkdir -p "$DEST/public/assets/$SLUG" "$DEST/script" "$DEST/research" "$DEST/qc" "$DEST/stills" "$DEST/renders"
# 后端脚本复制进项目：这些脚本用 dirname($0)/.. 定位项目根，必须待在项目根的 scripts/ 下
mkdir -p "$DEST/scripts"
for s in render.sh preview.sh still.sh test_render.sh selfcheck.py; do
  cp "$HERE/scripts/$s" "$DEST/scripts/"
done
# core/ 的中性脚本也复制进项目（它们在 skill 里，但项目内调用更直接，且 motion_check 等
# 需要读项目文件；core 版已参数化项目根，复制过去后用 cwd 即可正确解析）
CORE=${VIDEO_CRAFT_CORE:-$(cd "$HERE/../.." && pwd)/core}
if [ -d "$CORE" ]; then
  for s in tts_build.py render_storyboard.py motion_check.py frame_metrics.py sheet.py; do
    [ -f "$CORE/$s" ] && cp "$CORE/$s" "$DEST/scripts/"
  done
else
  echo "⚠ 找不到 core/（$CORE）——中性脚本未复制，请手动拷贝 core/*.py 到 $DEST/scripts/"
fi
# 后端标识：写进项目根 config.json，供 core/ 脚本识别项目根与后端类型
cat > "$DEST/config.json" <<EOF
{"slug": "$SLUG", "lang": "zh", "backend": "remotion"}
EOF
cd "$DEST" && npm install --silent && npx tsc --noEmit && echo "project ready: $DEST (slug=$SLUG, backend=remotion)"
