from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


class ConfigManager:
    """配置文件读写管理 - 支持 JSON 和 JSONC (带注释的JSON)"""

    @staticmethod
    def strip_jsonc_comments(content: str) -> str:
        """移除 JSONC 中的注释，支持 // 单行注释和 /* */ 多行注释"""
        result = []
        i = 0
        in_string = False
        escape_next = False

        while i < len(content):
            char = content[i]

            # 处理字符串内的转义
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue

            # 检测转义字符
            if char == "\\" and in_string:
                result.append(char)
                escape_next = True
                i += 1
                continue

            # 检测字符串边界
            if char == '"' and not escape_next:
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            # 不在字符串内时处理注释
            if not in_string:
                # 检测单行注释 //
                if char == "/" and i + 1 < len(content) and content[i + 1] == "/":
                    # 跳过到行尾
                    while i < len(content) and content[i] != "\n":
                        i += 1
                    # 保留换行符（如果存在）
                    if i < len(content) and content[i] == "\n":
                        result.append("\n")
                        i += 1
                    continue

                # 检测多行注释 /* */
                if char == "/" and i + 1 < len(content) and content[i + 1] == "*":
                    i += 2  # 跳过 /*
                    # 查找 */
                    while i < len(content):
                        if (
                            content[i] == "*"
                            and i + 1 < len(content)
                            and content[i + 1] == "/"
                        ):
                            i += 2  # 跳过 */
                            break
                        i += 1
                    continue

            result.append(char)
            i += 1

        return "".join(result)

    @staticmethod
    def load_json(path: Path) -> Optional[Dict]:
        """加载 JSON/JSONC 文件"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 尝试直接解析 JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e1:
                    # 如果失败，尝试移除注释后再解析 (JSONC)
                    try:
                        stripped_content = ConfigManager.strip_jsonc_comments(content)
                        return json.loads(stripped_content)
                    except json.JSONDecodeError as e2:
                        # 详细记录解析失败原因
                        print(f"Load failed {path}:")
                        print(f"  - 标准JSON解析失败: {e1}")
                        print(f"  - JSONC解析失败: {e2}")
                        print(f"  - 文件大小: {len(content)} 字节")
                        # 打印前200个字符用于调试
                        preview = content[:200].replace("\n", "\\n")
                        print(f"  - 文件预览: {preview}...")
                        return None
        except Exception as e:
            print(f"Load failed {path}: {e}")
        return None

    @staticmethod
    def is_jsonc_file(path: Path) -> bool:
        """检查文件是否为 JSONC 格式（包含注释）"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 尝试直接解析，如果失败说明可能有注释
                try:
                    json.loads(content)
                    return False  # 标准 JSON
                except json.JSONDecodeError:
                    return True  # 可能是 JSONC
        except Exception:
            pass
        return False

    @staticmethod
    def has_jsonc_comments(path: Path) -> bool:
        """检查文件是否包含 JSONC 注释（// 或 /* */）"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 检查是否包含注释标记（简单检测）
                # 需要排除字符串内的 // 和 /*
                in_string = False
                escape_next = False
                i = 0
                while i < len(content):
                    char = content[i]
                    if escape_next:
                        escape_next = False
                        i += 1
                        continue
                    if char == "\\" and in_string:
                        escape_next = True
                        i += 1
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        i += 1
                        continue
                    if not in_string:
                        # 检测 // 或 /*
                        if char == "/" and i + 1 < len(content):
                            next_char = content[i + 1]
                            if next_char == "/" or next_char == "*":
                                return True
                    i += 1
        except Exception:
            pass
        return False

    @staticmethod
    def save_json(path: Path, data: Dict, backup_manager=None) -> Tuple[bool, bool]:
        """
        保存为标准 JSON 格式

        注意：如果原文件是 JSONC 格式（带注释），保存后注释会丢失。
        会自动检测并备份 JSONC 文件。

        Args:
            path: 保存路径
            data: 要保存的数据
            backup_manager: 备份管理器实例（用于自动备份 JSONC 文件）

        Returns:
            Tuple[bool, bool]: (保存是否成功, 是否为 JSONC 文件且注释已丢失)
        """
        jsonc_warning = False
        try:
            # 保存前自动备份当前文件
            if backup_manager and path.exists():
                backup_manager.backup(path, tag="before-save")

            # 检测是否为 JSONC 文件（包含注释）
            if path.exists() and ConfigManager.has_jsonc_comments(path):
                jsonc_warning = True
                # 自动备份 JSONC 文件
                if backup_manager:
                    backup_manager.backup(path, tag="jsonc-auto")

            # 如果是 oh-my-opencode 配置文件，自动添加 $schema 字段
            if "oh-my-opencode" in str(path):
                # 创建新的数据副本，避免修改原始数据
                data_to_save = data.copy()
                # 添加 $schema 字段到最前面
                schema_url = "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json"
                # 使用 OrderedDict 确保 $schema 在最前面
                from collections import OrderedDict

                ordered_data = OrderedDict()
                ordered_data["$schema"] = schema_url
                # 添加其他字段
                for key, value in data_to_save.items():
                    if key != "$schema":  # 避免重复
                        ordered_data[key] = value
                data_to_save = ordered_data
            else:
                data_to_save = data

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            return True, jsonc_warning
        except Exception as e:
            print(f"Save failed {path}: {e}")
            return False, jsonc_warning
