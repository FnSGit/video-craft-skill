"""公式 mobject 封装——按 MANIM_TEX 环境变量在 LaTeX 与纯文本间切换。

背景：manim 的 MathTex 需要系统有 `latex` 可执行文件。本机（2026-10-24 实测）没有，
直接装 manim 只能跑 Text()。所以这里做一层封装：

  MANIM_TEX=latex（默认）  → MathTex，公式排版正确，**需先 brew install --cask basictex**
  MANIM_TEX=text           → Text()，零依赖，但公式只能用 ASCII 近似（如 \\frac{a}{b} → a/b）

推导片对公式排版质量要求极高，**正式做片必须用 latex 模式**。
text 模式只用于：无 LaTeX 环境下验证流程、或公式极简单不值得上 LaTeX。
"""
import os
import shutil

from manim import MathTex, Text, VGroup

from . import style


def latex_available() -> bool:
    return shutil.which("latex") is not None


def tex_mode() -> str:
    """返回 'latex' 或 'text'。默认 latex；显式 MANIM_TEX=text 或缺少 latex 时退回 text。"""
    want = os.environ.get("MANIM_TEX", "latex").strip().lower()
    if want == "text":
        return "text"
    if want == "latex" and not latex_available():
        import sys
        print(
            "⚠ 找不到 `latex` 可执行文件，退回 MANIM_TEX=text。\n"
            "  推导片需要正确公式排版，请先装：brew install --cask basictex\n"
            "  （详见 backends/manim/README.md 零节）",
            file=sys.stderr,
        )
        return "text"
    return "latex"


_MODE = None


def mode() -> str:
    global _MODE
    if _MODE is None:
        _MODE = tex_mode()
    return _MODE


class Formula(VGroup):
    """一个公式。latex 模式下就是 MathTex；text 模式下是等宽 Text。

    注意：不再覆写 submobjects property——VGroup.__init__ 内部要给
    self.submobjects 赋值，覆写成 property 会 AttributeError。
    这里只是包一层，保留 VGroup 原本的 submobjects 行为。

    用法：
        f = Formula(r"\\frac{a}{b} = c")
        f.mob[0]        # 访问内部 MathTex/Text 的 submobject（按字符切，可逐个高亮）
        f.highlight(0, 3)   # 高亮第 0..3 个字符
    """

    def __init__(self, tex: str, font_size: int = style.FONT_FORMULA, **kwargs):
        super().__init__()
        self.tex = tex
        self._mode = mode()
        if self._mode == "latex":
            self.mob = MathTex(tex, font_size=font_size, **kwargs)
        else:
            # text 模式：把常见 LaTeX 记法降级成 ASCII
            self.mob = Text(_ascii_fold(tex), font_size=font_size, font=style.FONT_MONO, **kwargs)
        self.add(self.mob)

    def __getitem__(self, i):
        return self.mob[i]

    def __len__(self):
        return len(self.mob)

    def highlight(self, start: int, end: int, color=None):
        """高亮 [start, end) 个字符/子式。end 为 None 表示到末尾。

        ⚠ text 模式下 self.mob 是单个 Text 对象，没有按字符切分的 submobject，
        高亮会退化为「整体变色」；latex 模式下才逐字符精确高亮。
        """
        color = color or style.PURPLE
        end = len(self.mob) if end is None else end
        subs = getattr(self.mob, "submobjects", None)
        if not subs:
            # text 模式：没有子结构可逐段高亮，整体变色
            self.mob.set_color(color)
            return self
        for i in range(start, min(end, len(subs))):
            subs[i].set_color(color)
        return self

    def box_around(self, start: int, end: int):
        """给 [start, end) 个子式加框（SurroundingRectangle），返回框本身。

        ⚠ text 模式下 self.mob 没有子结构，box_around 退化为框住整个公式。
        """
        from manim import SurroundingRectangle

        end = len(self.mob) if end is None else end
        subs = getattr(self.mob, "submobjects", None)
        if not subs:
            return SurroundingRectangle(self.mob, color=style.PURPLE, buff=0.12)
        n = len(subs)
        start = max(0, min(start, n - 1))
        end = max(start + 1, min(end, n))
        grp = VGroup(*[subs[i] for i in range(start, end)])
        return SurroundingRectangle(grp, color=style.PURPLE, buff=0.12)

    def underline(self, start: int, end: int):
        from manim import Underline

        end = len(self.mob) if end is None else end
        subs = getattr(self.mob, "submobjects", None)
        if not subs:
            return Underline(self.mob, color=style.PURPLE)
        n = len(subs)
        start = max(0, min(start, n - 1))
        end = max(start + 1, min(end, n))
        grp = VGroup(*[subs[i] for i in range(start, end)])
        return Underline(grp, color=style.PURPLE)


def _ascii_fold(tex: str) -> str:
    """把 LaTeX 记法降级为 ASCII 近似（text 模式用）。质量有限，仅兜底。"""
    t = tex
    # \frac{a}{b} → (a)/(b)
    while "\\frac{" in t:
        i = t.index("\\frac{")
        j = i + len("\\frac{")
        depth, k = 1, j
        while depth and k < len(t):
            if t[k] == "{":
                depth += 1
            elif t[k] == "}":
                depth -= 1
            k += 1
        num = t[j : k - 1]
        rest = t[k:]
        if rest.startswith("{"):
            depth, m = 1, 1
            while depth and m < len(rest):
                if rest[m] == "{":
                    depth += 1
                elif rest[m] == "}":
                    depth -= 1
                m += 1
            den = rest[1 : m - 1]
            t = t[:i] + f"({num})/({den})" + rest[m:]
        else:
            t = t[:i] + f"({num})/" + rest
    for a, b in [
        ("\\cdot", "*"),
        ("\\times", "x"),
        ("\\left(", "("),
        ("\\right)", ")"),
        ("\\sum", "SUM"),
        ("\\int", "INT"),
        ("\\infty", "inf"),
        ("\\pi", "pi"),
        ("\\theta", "theta"),
        ("\\alpha", "alpha"),
        ("\\beta", "beta"),
        ("\\lambda", "lambda"),
        ("\\mu", "mu"),
        ("\\sigma", "sigma"),
        ("\\partial", "d"),
        ("\\nabla", "grad"),
        ("^2", "^2"),
        ("\\,", " "),
        ("\\ ", " "),
        ("~", " "),
    ]:
        t = t.replace(a, b)
    return t


def formula(tex: str, **kw) -> Formula:
    """快捷构造。"""
    return Formula(tex, **kw)


def plain(text: str, **kw):
    """中文/纯文本标注——**不要走 LaTeX**。

    LaTeX 的 \\text{} 不支持 Unicode 中文（报 `Unicode character 步 (U+6B65)`），
    需要 ctex/xeCJK 那一套。推导片里的中文说明一律用这个工厂走 Text()。

    用法：
        note = plain("减号：往下走")
    """
    from manim import Text

    return Text(text, font_size=kw.pop("font_size", style.FONT_SMALL), font=style.FONT_CN, **kw)
