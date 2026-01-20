#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查脚本 - 验证所有必需的依赖是否已安装
"""

import sys
import io

# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def check_dependencies():
    """检查所有必需的依赖"""
    dependencies = {
        "PyQt5": "PyQt5",
        "qfluentwidgets": "PyQt-Fluent-Widgets",
        "requests": "requests",
    }

    missing = []
    installed = []

    for module, package in dependencies.items():
        try:
            __import__(module)
            installed.append(package)
            print(f"[OK] {package} 已安装")
        except ImportError:
            missing.append(package)
            print(f"[FAIL] {package} 未安装")

    print("\n" + "=" * 50)
    if missing:
        print(f"缺少 {len(missing)} 个依赖:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n请运行以下命令安装缺失的依赖:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print(f"所有 {len(installed)} 个依赖已正确安装")
        return True


if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)
