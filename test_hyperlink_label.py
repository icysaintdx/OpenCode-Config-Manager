#!/usr/bin/env python3
"""
快速测试 HyperlinkLabel 修复
"""

import sys
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import HyperlinkLabel


def test_hyperlink_label():
    """测试 HyperlinkLabel 的正确用法"""
    app = QApplication(sys.argv)

    # 正确的用法
    label = HyperlinkLabel()
    label.setUrl("https://skillsmp.com/")
    label.setText("🌐 浏览更多社区技能 (SkillsMP.com)")
    label.setToolTip("访问 SkillsMP.com 浏览更多社区技能")

    print("✓ HyperlinkLabel 创建成功")
    print(f"  URL: {label.url()}")
    print(f"  Text: {label.text()}")
    print(f"  Tooltip: {label.toolTip()}")

    label.show()

    return 0


if __name__ == "__main__":
    sys.exit(test_hyperlink_label())
