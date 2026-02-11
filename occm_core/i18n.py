from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Callable, Dict, List


class LanguageManager:
    """多语言管理器（纯 Python 版本）"""

    _instance = None
    _current_language = "zh_CN"
    _translations: Dict[str, Dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._callbacks: List[Callable[[str], None]] = []
        return cls._instance

    def __init__(self):
        if not self._translations:
            self._load_translations()
            self._current_language = self._load_language_preference()

    def _load_translations(self):
        """加载所有语言文件"""
        # 优先兼容原项目目录结构：D:/opcdcfg/locales
        base = Path(__file__).resolve().parent.parent
        locales_dir = base / "locales"
        if not locales_dir.exists():
            locales_dir = Path(__file__).resolve().parent / "locales"
        if not locales_dir.exists():
            return

        for lang_file in locales_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Failed to load language file {lang_file}: {e}")

    def add_callback(self, fn: Callable[[str], None]) -> None:
        """添加语言切换回调"""
        if fn not in self._callbacks:
            self._callbacks.append(fn)

    def remove_callback(self, fn: Callable[[str], None]) -> None:
        """移除语言切换回调"""
        if fn in self._callbacks:
            self._callbacks.remove(fn)

    def notify(self) -> None:
        """通知所有回调"""
        for cb in list(self._callbacks):
            try:
                cb(self._current_language)
            except Exception:
                pass

    def set_language(self, lang_code: str):
        """设置当前语言"""
        if lang_code in self._translations:
            self._current_language = lang_code
            self._save_language_preference(lang_code)
            self.notify()

    def get_current_language(self) -> str:
        """获取当前语言"""
        return self._current_language

    def get_available_languages(self) -> List[str]:
        """获取可用语言列表"""
        return list(self._translations.keys())

    def tr(self, key: str, **kwargs) -> str:
        """翻译文本"""
        keys = key.split(".")
        value = self._translations.get(self._current_language, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return key

        if value is None:
            return key

        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value)

    def _save_language_preference(self, lang_code: str):
        """保存语言偏好到配置文件"""
        config_file = Path.home() / ".config" / "opencode" / "ui_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        config["language"] = lang_code

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save language preference: {e}")

    def _load_language_preference(self) -> str:
        """从配置文件加载语言偏好，如果没有则自动识别系统语言"""
        config_file = Path.home() / ".config" / "opencode" / "ui_config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_lang = config.get("language")
                    if saved_lang:
                        return saved_lang
            except Exception:
                pass
        return self._detect_system_language()

    def _detect_system_language(self) -> str:
        """自动识别系统语言"""
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith("zh"):
                return "zh_CN"
            else:
                return "en_US"
        except Exception:
            pass
        return "zh_CN"


_lang_manager = LanguageManager()


def tr(key: str, **kwargs) -> str:
    """全局翻译函数"""
    return _lang_manager.tr(key, **kwargs)
