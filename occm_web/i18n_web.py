from __future__ import annotations

import json
import locale
from pathlib import Path
from typing import Any, Callable


CONFIG_PATH = Path.home() / ".config" / "opencode" / "occm-ui.json"
LOCALES_PATH = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("zh_CN", "en_US")


class WebI18N:
    def __init__(self) -> None:
        self._translations: dict[str, dict[str, Any]] = {}
        self._listeners: list[Callable[[str], None]] = []
        self._language = "zh_CN"
        self._load_translations()
        self._language = self._load_saved_language()

    def _load_translations(self) -> None:
        for lang in SUPPORTED_LANGUAGES:
            file_path = LOCALES_PATH / f"{lang}.json"
            if not file_path.exists():
                self._translations[lang] = {}
                continue
            try:
                self._translations[lang] = json.loads(
                    file_path.read_text(encoding="utf-8")
                )
            except Exception:
                self._translations[lang] = {}

    def _load_config(self) -> dict[str, Any]:
        if not CONFIG_PATH.exists():
            return {}
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_config(self, config: dict[str, Any]) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _detect_system_language(self) -> str:
        sys_lang = (locale.getdefaultlocale()[0] or "").lower()
        if sys_lang.startswith("zh"):
            return "zh_CN"
        return "en_US"

    def _load_saved_language(self) -> str:
        saved = self._load_config().get("language")
        if saved in SUPPORTED_LANGUAGES:
            return saved
        return self._detect_system_language()

    def get_language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        config = self._load_config()
        config["language"] = language
        self._save_config(config)
        for callback in list(self._listeners):
            try:
                callback(language)
            except Exception:
                continue

    def toggle_language(self) -> str:
        target = "en_US" if self._language == "zh_CN" else "zh_CN"
        self.set_language(target)
        return target

    def on_change(self, callback: Callable[[str], None]) -> None:
        self._listeners.append(callback)

    @staticmethod
    def _walk_nested(data: dict[str, Any], key: str) -> Any:
        current: Any = data
        for part in key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def tr(self, key: str, **kwargs: Any) -> str:
        value = self._walk_nested(self._translations.get(self._language, {}), key)
        if value is None:
            fallback_lang = "en_US" if self._language == "zh_CN" else "zh_CN"
            value = self._walk_nested(self._translations.get(fallback_lang, {}), key)
        if value is None:
            return key
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except Exception:
                return value
        return str(value)

    def bind_text(self, element: Any, key: str, **kwargs: Any) -> None:
        def _update(_: str | None = None) -> None:
            text = self.tr(key, **kwargs)
            try:
                if hasattr(element, "set_text"):
                    element.set_text(text)
                elif hasattr(element, "text"):
                    element.text = text
                if hasattr(element, "update"):
                    element.update()
            except Exception:
                pass

        _update()
        self.on_change(lambda _: _update())


_I18N = WebI18N()


def tr(key: str, **kwargs: Any) -> str:
    return _I18N.tr(key, **kwargs)


def get_i18n() -> WebI18N:
    return _I18N
