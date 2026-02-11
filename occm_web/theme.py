from __future__ import annotations

# pyright: reportMissingImports=false

import json
from pathlib import Path
from typing import Literal, cast

from nicegui import ui


ThemeMode = Literal["dark", "light", "auto"]
CONFIG_PATH = Path.home() / ".config" / "opencode" / "occm-ui.json"


class ThemeManager:
    def __init__(self) -> None:
        self._mode: ThemeMode = "auto"
        self._mode = self._load_mode()

    def _load_config(self) -> dict[str, str]:
        if not CONFIG_PATH.exists():
            return {}
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_config(self, config: dict[str, str]) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_mode(self) -> ThemeMode:
        mode = self._load_config().get("theme", "auto")
        if mode in {"dark", "light", "auto"}:
            return cast(ThemeMode, mode)
        return "auto"

    def get_mode(self) -> ThemeMode:
        return self._mode

    def set_mode(self, mode: ThemeMode) -> None:
        self._mode = mode
        config = self._load_config()
        config["theme"] = mode
        self._save_config(config)

    def cycle_mode(self) -> ThemeMode:
        order: tuple[ThemeMode, ...] = ("light", "dark", "auto")
        idx = order.index(self._mode) if self._mode in order else 0
        next_mode = order[(idx + 1) % len(order)]
        self.set_mode(next_mode)
        return next_mode

    def apply(self) -> None:
        dark = ui.dark_mode()
        if self._mode == "dark":
            dark.enable()
            return
        if self._mode == "light":
            dark.disable()
            return

        # 跟随系统：优先使用 NiceGUI dark_mode 的 auto 能力；
        # 若当前版本无 auto 方法，则退化为前端检测后刷新。
        if hasattr(dark, "auto"):
            dark.auto()  # type: ignore[attr-defined]
            return

        ui.run_javascript(
            """
            const media = window.matchMedia('(prefers-color-scheme: dark)');
            const isDark = media.matches;
            document.body.classList.toggle('body--dark', isDark);
            document.body.classList.toggle('body--light', !isDark);
            """
        )


_THEME = ThemeManager()


def get_theme_manager() -> ThemeManager:
    return _THEME
