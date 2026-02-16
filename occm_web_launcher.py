#!/usr/bin/env python3
"""OCCM Web 启动器 — PyInstaller 打包入口"""

import sys
import os

# PyInstaller 打包后的路径修正
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS  # type: ignore[attr-defined]
    os.chdir(_base)
    sys.path.insert(0, _base)

# 启动 occm_web 包
from occm_web.__main__ import *  # noqa: F401,F403
