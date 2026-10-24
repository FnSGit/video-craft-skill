"""让 `common` 包可被 scenes/ 下的场景文件导入。

manim CLI 渲染时不改 sys.path，scenes/DPxx.py 里 `from common import ...` 会失败。
Python 启动时会自动 import sitecustomize（只要它在 sys.path 上）——把模板根放进
PYTHONPATH 即可让本文件被找到，从而把模板根也加进 sys.path。

用法：在项目根（manim.cfg 同级）执行
    PYTHONPATH=. .venv/bin/manim render -ql scenes/DP01.py DP01

脚本里已统一带 PYTHONPATH=.，无需手动加。
"""
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)
