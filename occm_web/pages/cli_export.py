"""CLI 工具导出页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

import json
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import CLIConfigGenerator, CLIExportManager, ConfigManager, ConfigPaths

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/cli-export")
    @dec
    async def cli_export_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        if not isinstance(config, dict):
            config = {}

        providers = config.get("provider", {})
        if not isinstance(providers, dict):
            providers = {}

        manager = CLIExportManager()
        generator = CLIConfigGenerator()

        def content():
            provider_keys = sorted(list(providers.keys()))
            if not provider_keys:
                ui.label(tr("web.no_provider_detected")).classes("text-negative")
                return

            with ui.tabs().classes("w-full occm-tabs") as tabs:
                t_claude = ui.tab("Claude Code")
                t_codex = ui.tab("Codex")
                t_gemini = ui.tab("Gemini")

            with ui.tab_panels(tabs, value=t_claude).classes("w-full"):
                for panel, cli_type in [
                    (t_claude, "claude"),
                    (t_codex, "codex"),
                    (t_gemini, "gemini"),
                ]:
                    with ui.tab_panel(panel):
                        provider_select = ui.select(
                            label=tr("web.select_provider"),
                            options=provider_keys,
                            value=provider_keys[0],
                        ).classes("w-full")

                        model_select = ui.select(
                            label=tr("web.select_model"),
                            options=[],
                            value=None,
                            with_input=True,
                        ).classes("w-full")

                        preview_title = ui.label(tr("web.export_preview")).classes(
                            "text-base font-medium"
                        )
                        preview_code = ui.code("{}", language="json").classes("w-full")

                        def get_selected_provider() -> dict[str, Any] | None:
                            key = str(provider_select.value or "")
                            provider = providers.get(key)
                            if not isinstance(provider, dict):
                                return None
                            return provider

                        def get_selected_model() -> str:
                            return str(model_select.value or "").strip()

                        def refresh_models() -> None:
                            provider = get_selected_provider() or {}
                            model_map = provider.get("models", {})
                            model_options = (
                                sorted(list(model_map.keys()))
                                if isinstance(model_map, dict)
                                else []
                            )
                            model_select.options = model_options
                            if model_options:
                                model_select.value = model_options[0]
                            else:
                                model_select.value = ""
                            model_select.update()
                            refresh_preview()

                        def build_preview_text() -> str:
                            provider = get_selected_provider()
                            model = get_selected_model()
                            if not provider:
                                return "{}"
                            if cli_type == "claude":
                                data = generator.generate_claude_config(
                                    provider, model or None
                                )
                                return json.dumps(data, ensure_ascii=False, indent=2)
                            if cli_type == "codex":
                                auth_json = generator.generate_codex_auth(provider)
                                config_toml = generator.generate_codex_config(
                                    provider, model
                                )
                                return (
                                    "# auth.json\n"
                                    + json.dumps(
                                        auth_json, ensure_ascii=False, indent=2
                                    )
                                    + "\n\n# config.toml\n"
                                    + config_toml
                                )
                            env_map = generator.generate_gemini_env(provider, model)
                            settings_json = generator.generate_gemini_settings()
                            env_text = "\n".join(
                                [f"{k}={v}" for k, v in env_map.items()]
                            )
                            return (
                                "# .env\n"
                                + env_text
                                + "\n\n# settings.json\n"
                                + json.dumps(
                                    settings_json, ensure_ascii=False, indent=2
                                )
                            )

                        def refresh_preview() -> None:
                            preview_text = build_preview_text()
                            preview_code.set_content(preview_text)
                            preview_title.set_text(
                                f"{cli_type.upper()} {tr('web.export_preview')}"
                            )

                        def do_export() -> None:
                            provider = get_selected_provider()
                            model = get_selected_model()
                            if not provider:
                                ui.notify(
                                    tr("web.please_select_valid_provider"),
                                    type="warning",
                                )
                                return
                            if not model:
                                ui.notify(tr("web.please_select_model"), type="warning")
                                return

                            if cli_type == "claude":
                                result = manager.export_to_claude(provider, model)
                            elif cli_type == "codex":
                                result = manager.export_to_codex(provider, model)
                            else:
                                result = manager.export_to_gemini(provider, model)

                            if not result.success:
                                ui.notify(
                                    result.error_message
                                    or tr("cli_export.export_failed"),
                                    type="negative",
                                )
                                return

                            files = ", ".join(str(p) for p in result.files_written)
                            ui.notify(
                                f"{tr('cli_export.export_success')}: {files}",
                                type="positive",
                            )

                        async def copy_preview() -> None:
                            preview_text = build_preview_text()
                            js = f"""
                            try {{
                              await navigator.clipboard.writeText({json.dumps(preview_text)});
                              return true;
                            }} catch (e) {{
                              return false;
                            }}
                            """
                            ok = await ui.run_javascript(js)
                            if ok:
                                ui.notify(
                                    tr("web.copied_to_clipboard"), type="positive"
                                )
                            else:
                                ui.notify(tr("web.copy_failed"), type="negative")

                        provider_select.on(
                            "update:model-value", lambda _: refresh_models()
                        )
                        model_select.on(
                            "update:model-value", lambda _: refresh_preview()
                        )

                        with ui.row().classes("mt-2 gap-2"):
                            ui.button(
                                tr("web.refresh_preview"),
                                icon="refresh",
                                on_click=refresh_preview,
                            ).props("outline")
                            ui.button(
                                tr("web.copy_preview"),
                                icon="content_copy",
                                on_click=copy_preview,
                            ).props("outline")
                            ui.button(
                                tr("web.do_export"), icon="download", on_click=do_export
                            ).props("unelevated")

                        refresh_models()

        render_layout(
            request=request,
            page_key="menu.export",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
