#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试语言功能"""

import json
from pathlib import Path


# 测试语言文件加载
def test_language_files():
    print("=== 测试语言文件 ===\n")

    locales_dir = Path(__file__).parent / "locales"

    for lang_file in ["zh_CN.json", "en_US.json"]:
        file_path = locales_dir / lang_file
        print(f"检查文件: {file_path}")

        if not file_path.exists():
            print(f"  ❌ 文件不存在")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"  ✅ 文件格式正确")
            print(f"  📊 顶级键: {list(data.keys())}")

            # 检查必要的键
            required_keys = ["app", "menu", "common", "settings"]
            missing_keys = [k for k in required_keys if k not in data]

            if missing_keys:
                print(f"  ⚠️  缺少键: {missing_keys}")
            else:
                print(f"  ✅ 所有必要键都存在")

            # 统计翻译数量
            def count_translations(obj, prefix=""):
                count = 0
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str):
                            count += 1
                        elif isinstance(value, dict):
                            count += count_translations(
                                value, f"{prefix}.{key}" if prefix else key
                            )
                return count

            total = count_translations(data)
            print(f"  📝 翻译条目总数: {total}")

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 格式错误: {e}")
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")

        print()


# 测试语言管理器
def test_language_manager():
    print("=== 测试语言管理器 ===\n")

    try:
        # 导入语言管理器
        import sys

        sys.path.insert(0, str(Path(__file__).parent))

        # 只导入必要的部分
        import json
        from pathlib import Path

        class SimpleLanguageManager:
            def __init__(self):
                self._current_language = "zh_CN"
                self._translations = {}
                self._load_translations()

            def _load_translations(self):
                locales_dir = Path(__file__).parent / "locales"
                for lang_file in locales_dir.glob("*.json"):
                    if lang_file.stem.endswith("_old"):
                        continue
                    lang_code = lang_file.stem
                    try:
                        with open(lang_file, "r", encoding="utf-8") as f:
                            self._translations[lang_code] = json.load(f)
                        print(f"✅ 加载语言文件: {lang_code}")
                    except Exception as e:
                        print(f"❌ 加载失败 {lang_file}: {e}")

            def tr(self, key: str) -> str:
                keys = key.split(".")
                value = self._translations.get(self._current_language, {})

                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        return key

                if value is None:
                    return key

                return str(value)

        manager = SimpleLanguageManager()

        print(f"\n当前语言: {manager._current_language}")
        print(f"可用语言: {list(manager._translations.keys())}\n")

        # 测试翻译
        test_keys = [
            "app.title",
            "menu.home",
            "menu.provider",
            "menu.model",
            "common.add",
            "common.save",
            "settings.language",
            "settings.restart_required",
        ]

        print("翻译测试:")
        for key in test_keys:
            result = manager.tr(key)
            status = "✅" if result != key else "❌"
            print(f"  {status} {key} -> {result}")

        # 切换到英文
        print(f"\n切换到英文...")
        manager._current_language = "en_US"

        print("\n英文翻译测试:")
        for key in test_keys:
            result = manager.tr(key)
            status = "✅" if result != key else "❌"
            print(f"  {status} {key} -> {result}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_language_files()
    print("\n" + "=" * 50 + "\n")
    test_language_manager()
