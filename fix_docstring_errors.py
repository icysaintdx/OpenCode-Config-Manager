#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复错误的 docstring 格式"""

import re

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 查找并替换所有 ""tr(...)"" 格式的错误 docstring
# 这些应该是普通的 docstring，不应该包含 tr() 调用
pattern = r'""tr\("([^"]+)"\)""'


def replace_func(match):
    key = match.group(1)
    # 从键名推断中文描述
    key_to_desc = {
        "native_provider.config_provider": "配置 Provider",
        "native_provider.test_connection": "测试连接",
        "native_provider.delete_config": "删除配置",
        "ohmyagent.add_agent": "添加 Agent",
        "skill.save_skill": "保存 Skill",
        "skill.install_skill": "安装 Skill",
        "skill.check_updates": "检查更新",
        "cli_export.edit_common_config": "编辑通用配置",
    }
    desc = key_to_desc.get(key, "")
    return f'"""{desc}"""'


content = re.sub(pattern, replace_func, content)

# 保存文件
with open("opencode_config_manager_fluent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed all docstring errors")
