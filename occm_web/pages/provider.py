from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    AuthManager as CoreAuthManager,
    BackupManager,
    ConfigManager,
    ConfigPaths,
    EnvVarDetector,
    NATIVE_PROVIDERS,
)

from ..auth import AuthManager as WebAuth
from ..auth import require_auth
from ..i18n_web import tr
from ..layout import render_layout


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def register_page(auth: WebAuth | None) -> None:
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/provider")
    @dec
    async def provider_page(request: Request) -> None:
        config_path = ConfigPaths.get_opencode_config()
        auth_manager = CoreAuthManager()
        env_detector = EnvVarDetector()
        native_ids = {item.id for item in NATIVE_PROVIDERS}

        def load_config() -> dict[str, Any]:
            cfg = ConfigManager.load_json(config_path) or {}
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["provider"] = _safe_dict(cfg.get("provider"))
            return cfg

        config = load_config()

        def save_config() -> bool:
            ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
            if ok:
                ui.notify(tr("common.success"), type="positive")
                return True
            ui.notify(tr("common.error"), type="negative")
            return False

        def content() -> None:
            selected_key: dict[str, str | None] = {"value": None}

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    tr("provider.add_provider"), on_click=lambda: open_edit_dialog()
                ).props("unelevated")
                ui.button(
                    tr("provider.edit_provider"), on_click=lambda: edit_selected()
                ).props("outline")
                ui.button(
                    tr("provider.delete_provider"), on_click=lambda: delete_selected()
                ).props("outline color=negative")
                ui.button(tr("common.refresh"), on_click=lambda: refresh_all()).props(
                    "outline"
                )

            provider_table = ui.table(
                columns=[
                    {
                        "name": "key",
                        "label": tr("provider.provider_key"),
                        "field": "key",
                    },
                    {
                        "name": "name",
                        "label": tr("provider.provider_name"),
                        "field": "name",
                    },
                    {"name": "sdk", "label": tr("common.sdk"), "field": "sdk"},
                    {
                        "name": "base_url",
                        "label": tr("provider.base_url"),
                        "field": "base_url",
                    },
                    {
                        "name": "model_count",
                        "label": tr("provider.model_count"),
                        "field": "model_count",
                    },
                    {
                        "name": "api_key",
                        "label": tr("provider.api_key"),
                        "field": "api_key",
                    },
                    {
                        "name": "native",
                        "label": tr("provider.native_provider"),
                        "field": "native",
                    },
                ],
                rows=[],
                row_key="key",
                selection="single",
                pagination=10,
            ).classes("w-full")

            def on_select(_: Any) -> None:
                selected = provider_table.selected or []
                selected_key["value"] = selected[0]["key"] if selected else None

            provider_table.on("selection", on_select)

            with ui.card().classes("w-full mt-3"):
                ui.label(tr("provider.native_provider")).classes(
                    "text-base font-semibold"
                )
                native_tags_container = ui.row().classes("w-full gap-2 flex-wrap")

            with ui.card().classes("w-full mt-3"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(tr("native_provider.detected_env_vars")).classes(
                        "text-base font-semibold"
                    )
                    ui.button(
                        tr("native_provider.detect_configured"),
                        on_click=lambda: refresh_env_table(),
                    ).props("outline")

                env_table = ui.table(
                    columns=[
                        {
                            "name": "provider",
                            "label": tr("native_provider.provider"),
                            "field": "provider",
                        },
                        {
                            "name": "sdk",
                            "label": tr("native_provider.sdk"),
                            "field": "sdk",
                        },
                        {
                            "name": "env_vars",
                            "label": tr("native_provider.env_vars"),
                            "field": "env_vars",
                        },
                        {
                            "name": "status",
                            "label": tr("common.status"),
                            "field": "status",
                        },
                    ],
                    rows=[],
                    row_key="provider",
                    pagination=8,
                ).classes("w-full")

            def get_selected_key(require: bool = True) -> str | None:
                key = selected_key.get("value")
                if key:
                    return key
                selected = provider_table.selected or []
                if selected:
                    key = selected[0]["key"]
                    selected_key["value"] = key
                    return key
                if require:
                    ui.notify(tr("provider.select_first"), type="warning")
                return None

            def build_provider_rows() -> list[dict[str, Any]]:
                rows: list[dict[str, Any]] = []
                providers = _safe_dict(config.get("provider"))
                for key, pdata in providers.items():
                    if not isinstance(pdata, dict):
                        continue
                    models = _safe_dict(pdata.get("models"))
                    options = _safe_dict(pdata.get("options"))
                    auth_info = _safe_dict(auth_manager.get_provider_auth(key) or {})
                    api_key = str(auth_info.get("apiKey") or auth_info.get("key") or "")
                    is_native = key in native_ids
                    rows.append(
                        {
                            "key": key,
                            "name": str(pdata.get("name") or key),
                            "sdk": str(pdata.get("sdk") or "-"),
                            "base_url": str(options.get("baseURL") or "-"),
                            "model_count": len(models),
                            "api_key": CoreAuthManager.mask_api_key(api_key)
                            if api_key
                            else "-",
                            "native": tr("common.yes")
                            if is_native
                            else tr("common.no"),
                        }
                    )
                rows.sort(key=lambda item: item["key"])
                return rows

            def refresh_native_tags() -> None:
                native_tags_container.clear()
                providers = _safe_dict(config.get("provider"))
                for item in NATIVE_PROVIDERS:
                    cfg_exists = item.id in providers
                    auth_exists = bool(auth_manager.get_provider_auth(item.id))
                    env_exists = bool(env_detector.detect_env_vars(item.id))
                    label = item.name
                    if auth_exists:
                        label = f"{label} · {tr('native_provider.configured')}"
                    elif env_exists:
                        label = f"{label} · {tr('native_provider.detected_env_vars')}"
                    elif cfg_exists:
                        label = f"{label} · {tr('common.enabled')}"
                    with native_tags_container:
                        color = (
                            "positive"
                            if (auth_exists or env_exists or cfg_exists)
                            else "grey"
                        )
                        ui.chip(label, color=color).props("outline")

            def refresh_env_table() -> None:
                rows: list[dict[str, Any]] = []
                all_detected = env_detector.detect_all_env_vars()
                for item in NATIVE_PROVIDERS:
                    detected = all_detected.get(item.id, {})
                    env_vars = ", ".join(sorted(detected.keys())) if detected else "-"
                    rows.append(
                        {
                            "provider": item.name,
                            "sdk": item.sdk,
                            "env_vars": env_vars,
                            "status": (
                                tr("native_provider.configured")
                                if detected
                                else tr("native_provider.not_configured")
                            ),
                        }
                    )
                env_table.rows = rows
                env_table.update()

            def refresh_all() -> None:
                try:
                    nonlocal config
                    config = load_config()
                    provider_table.rows = build_provider_rows()
                    provider_table.update()
                    refresh_native_tags()
                    refresh_env_table()
                except Exception as exc:
                    ui.notify(f"{tr('common.error')}: {exc}", type="negative")

            def open_edit_dialog(edit_key: str | None = None) -> None:
                providers = _safe_dict(config.get("provider"))
                provider_data = _safe_dict(providers.get(edit_key)) if edit_key else {}
                auth_info = _safe_dict(
                    auth_manager.get_provider_auth(edit_key or "") or {}
                )
                with ui.dialog() as dialog, ui.card().classes("w-[680px] max-w-full"):
                    ui.label(
                        tr("provider.edit_provider")
                        if edit_key
                        else tr("provider.add_provider")
                    ).classes("text-base font-semibold")
                    key_input = ui.input(
                        label=tr("provider.provider_key"),
                        value=edit_key or "",
                    ).classes("w-full")
                    if edit_key:
                        key_input.disable()
                    name_input = ui.input(
                        label=tr("provider.provider_name"),
                        value=str(provider_data.get("name") or edit_key or ""),
                    ).classes("w-full")
                    sdk_input = ui.input(
                        label=tr("provider.sdk_type"),
                        value=str(provider_data.get("sdk") or ""),
                    ).classes("w-full")
                    base_url_input = ui.input(
                        label=tr("provider.base_url"),
                        value=str(
                            _safe_dict(provider_data.get("options")).get("baseURL")
                            or ""
                        ),
                    ).classes("w-full")
                    api_key_input = ui.input(
                        label=tr("provider.api_key"),
                        value=str(auth_info.get("apiKey") or ""),
                        password=True,
                        password_toggle_button=True,
                    ).classes("w-full")

                    def do_save() -> None:
                        try:
                            key = str(key_input.value or "").strip()
                            name = str(name_input.value or "").strip()
                            sdk = str(sdk_input.value or "").strip()
                            base_url = str(base_url_input.value or "").strip()
                            api_key = str(api_key_input.value or "").strip()

                            if not key:
                                ui.notify(tr("provider.enter_name"), type="warning")
                                return
                            providers_map = _safe_dict(config.get("provider"))
                            if not edit_key and key in providers_map:
                                ui.notify(
                                    tr("provider.provider_exists", name=key),
                                    type="warning",
                                )
                                return

                            current = _safe_dict(providers_map.get(key))
                            models = _safe_dict(current.get("models"))
                            options = _safe_dict(current.get("options"))
                            if base_url:
                                options["baseURL"] = base_url
                            else:
                                options.pop("baseURL", None)

                            next_provider: dict[str, Any] = {
                                "name": name or key,
                                "sdk": sdk,
                            }
                            if models:
                                next_provider["models"] = models
                            if options:
                                next_provider["options"] = options

                            providers_map[key] = next_provider
                            config["provider"] = providers_map

                            if api_key:
                                auth_manager.set_provider_auth(key, {"apiKey": api_key})

                            if not save_config():
                                return
                            ui.notify(
                                tr("provider.updated_success")
                                if edit_key
                                else tr("provider.added_success"),
                                type="positive",
                            )
                            dialog.close()
                            refresh_all()
                        except Exception as exc:
                            ui.notify(f"{tr('common.error')}: {exc}", type="negative")

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dialog.close).props(
                            "flat"
                        )
                        ui.button(tr("common.save"), on_click=do_save).props(
                            "unelevated"
                        )
                dialog.open()

            def edit_selected() -> None:
                key = get_selected_key(require=True)
                if key:
                    open_edit_dialog(key)

            def delete_selected() -> None:
                key = get_selected_key(require=True)
                if not key:
                    return

                with ui.dialog() as dialog, ui.card().classes("w-[420px] max-w-full"):
                    ui.label(tr("provider.delete_confirm_title")).classes(
                        "text-base font-semibold"
                    )
                    ui.label(tr("provider.delete_confirm", name=key)).classes(
                        "whitespace-pre-line"
                    )

                    def do_delete() -> None:
                        try:
                            providers_map = _safe_dict(config.get("provider"))
                            if key not in providers_map:
                                ui.notify(
                                    tr("provider.provider_not_exist"), type="warning"
                                )
                                dialog.close()
                                return
                            providers_map.pop(key, None)
                            config["provider"] = providers_map
                            auth_manager.delete_provider_auth(key)
                            if not save_config():
                                return
                            ui.notify(
                                tr("provider.deleted_success", name=key),
                                type="positive",
                            )
                            dialog.close()
                            refresh_all()
                        except Exception as exc:
                            ui.notify(f"{tr('common.error')}: {exc}", type="negative")

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dialog.close).props(
                            "flat"
                        )
                        ui.button(tr("common.delete"), on_click=do_delete).props(
                            "unelevated color=negative"
                        )
                dialog.open()

            refresh_all()

        render_layout(
            request=request,
            page_key="menu.provider",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
