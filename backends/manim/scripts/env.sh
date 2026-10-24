#!/bin/zsh
# manim 后端的环境注入——被 render.sh / still.sh / preview.sh / test_render.sh source。
# 独立成一个文件是因为这套环境变量有四个坑，每个都必须设对（详见 backends/manim/README.md 零节）：
#
#   1. cairo/pango  —— pycairo 编译必需，缺了 manim 装不上
#   2. texlive PATH —— basictex 装在 /usr/local/texlive，不在默认 PATH
#   3. TEXINPUTS    —— standalone / preview 宏包 basictex 没带，手工解到 ~/.local/texlive-extra
#   4. TEXMFROOT/TEXMFCNF —— ⚠ 最关键的坑：
#        只设 TEXINPUTS 会污染 kpathsea 搜索起点，dvisvgm 报
#        "configuration file texmf.cnf not found" → 字体 map 加载失败 →
#        SVG 的 glyph 引用悬空（use=5 defs=0）→ 公式字符全不可见。
#        必须把 TEXMFROOT 与 TEXMFCNF 显式钉死，latex 和 dvisvgm 才都正常。
#
# 可调：TEXLIVE_ROOT / TEXLIVE_EXTRA 指向别处（如另一台机器的 texlive 布局）。

export PATH="/opt/homebrew/bin:$PATH"
[ -n "$PKG_CONFIG_PATH" ] || export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"

TEXLIVE_BIN=${TEXLIVE_ROOT:-/usr/local/texlive/2026basic}/bin/universal-darwin
TEXLIVE_ROOT=${TEXLIVE_ROOT:-/usr/local/texlive/2026basic}
TEXLIVE_EXTRA=${TEXLIVE_EXTRA:-$HOME/.local/texlive-extra}

[ -d "$TEXLIVE_BIN" ] && export PATH="$TEXLIVE_BIN:$PATH"
[ -d "$HOME/.local/bin" ] && export PATH="$HOME/.local/bin:$PATH"   # dvisvgm 二进制在这
[ -d "$TEXLIVE_EXTRA/tex" ] && export TEXINPUTS="$TEXLIVE_EXTRA/tex//:"

export TEXMFROOT="$TEXLIVE_ROOT"
export TEXMFCNF="$TEXLIVE_ROOT/texmf-dist/web2c"

# 真公式（latex）vs ASCII 近似（text）；缺 texlive 时 common/formula.py 自动降级并警告
export MANIM_TEX=${MANIM_TEX:-latex}

# 自检：把当前 manim 渲染链路的关键依赖状态打出来（V1 排查用，V2 可加 --quiet 关掉）
if [ "${VC_ENV_VERBOSE:-1}" = 1 ] && [ -t 2 ]; then
  _miss=()
  command -v latex >/dev/null 2>&1 || _miss+=(latex)
  command -v dvisvgm >/dev/null 2>&1 || _miss+=(dvisvgm)
  if [ ${#_miss} -gt 0 ]; then
    echo "⚠ manim 环境缺: ${_miss[*]} —— 详见 backends/manim/README.md 零节" >&2
    echo "  （公式将退化成 ASCII 近似；推导片必须补全）" >&2
  fi
fi
