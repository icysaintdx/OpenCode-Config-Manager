from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_manager import ConfigManager
from .config_paths import ConfigPaths


class ImportService:
    """外部配置导入服务 - 支持Claude Code、Codex、Gemini、cc-switch等配置格式"""

    @staticmethod
    def _first_existing_path(paths: List[Path]) -> Path:
        for path in paths:
            if path.exists():
                return path
        return paths[0]

    @staticmethod
    def _parse_toml_value(value: str):
        lower_value = value.lower()
        if lower_value in {"true", "false"}:
            return lower_value == "true"
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _parse_toml_string(self, content: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        current_section: Dict[str, Any] = result
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                current_section = result
                for part in section.split("."):
                    current_section = current_section.setdefault(part, {})
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = self._parse_toml_value(value.strip())
                current_section[key] = value
        return result

    @staticmethod
    def _normalize_base_url(base_url: str, require_v1: bool) -> str:
        if not base_url:
            return ""
        trimmed = base_url.rstrip("/")
        if require_v1 and not trimmed.endswith("/v1"):
            trimmed = f"{trimmed}/v1"
        return trimmed

    @staticmethod
    def _sanitize_provider_key(name: str) -> str:
        cleaned = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower())
        return cleaned.strip("-") or "provider"

    @staticmethod
    def _unique_provider_key(base: str, used_keys: set) -> str:
        candidate = base
        index = 2
        while candidate in used_keys:
            candidate = f"{base}-{index}"
            index += 1
        used_keys.add(candidate)
        return candidate

    def scan_external_configs(self) -> Dict:
        """扫描所有支持的外部配置文件"""
        results = {}
        test_root = Path(__file__).parent / "test"

        claude_settings = ConfigPaths.get_import_path("claude")
        if claude_settings is None:
            claude_settings = ConfigPaths.get_claude_settings()
            if not claude_settings.exists() and test_root.exists():
                test_path = test_root / ".claude" / "settings.json"
                if test_path.exists():
                    claude_settings = test_path
        results["Claude Code Settings"] = {
            "path": str(claude_settings),
            "exists": claude_settings.exists(),
            "data": ConfigManager.load_json(claude_settings)
            if claude_settings.exists()
            else None,
            "type": "claude",
        }

        claude_providers = ConfigPaths.get_import_path("claude_providers")
        if claude_providers is None:
            claude_providers = ConfigPaths.get_claude_providers()
            if not claude_providers.exists() and test_root.exists():
                test_path = test_root / ".claude" / "providers.json"
                if test_path.exists():
                    claude_providers = test_path
        results["Claude Providers"] = {
            "path": str(claude_providers),
            "exists": claude_providers.exists(),
            "data": ConfigManager.load_json(claude_providers)
            if claude_providers.exists()
            else None,
            "type": "claude_providers",
        }

        codex_config = ConfigPaths.get_import_path("codex")
        if codex_config is None:
            codex_config = Path.home() / ".codex" / "config.toml"
            if not codex_config.exists() and test_root.exists():
                test_path = test_root / ".codex" / "config.toml"
                if test_path.exists():
                    codex_config = test_path
        results["Codex Config"] = {
            "path": str(codex_config),
            "exists": codex_config.exists(),
            "data": self._parse_toml(codex_config) if codex_config.exists() else None,
            "type": "codex",
        }

        gemini_dir = Path.home() / ".gemini"
        gemini_config = ConfigPaths.get_import_path("gemini")
        if gemini_config is None:
            gemini_config = self._first_existing_path(
                [gemini_dir / "config.json", gemini_dir / "settings.json"]
            )
            if not gemini_config.exists() and test_root.exists():
                test_path = test_root / ".gemini" / "settings.json"
                if test_path.exists():
                    gemini_config = test_path
        results["Gemini Config"] = {
            "path": str(gemini_config),
            "exists": gemini_config.exists(),
            "data": ConfigManager.load_json(gemini_config)
            if gemini_config.exists()
            else None,
            "type": "gemini",
        }

        ccswitch_dir = Path.home() / ".cc-switch"
        ccswitch_config = ConfigPaths.get_import_path("ccswitch")
        if ccswitch_config is None:
            ccswitch_config = self._first_existing_path(
                [
                    ccswitch_dir / "config.json.migrated",
                    ccswitch_dir / "config.json.bak",
                    ccswitch_dir / "config.json",
                ]
            )
            if not ccswitch_config.exists() and test_root.exists():
                test_path = test_root / ".cc-switch" / "config.json.migrated"
                if test_path.exists():
                    ccswitch_config = test_path
        results["CC-Switch Config"] = {
            "path": str(ccswitch_config),
            "exists": ccswitch_config.exists(),
            "data": ConfigManager.load_json(ccswitch_config)
            if ccswitch_config.exists()
            else None,
            "type": "ccswitch",
        }

        return results

    def _parse_toml(self, path: Path) -> Optional[Dict]:
        """简易TOML解析器"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_toml_string(content)
        except Exception as e:
            print(f"TOML parse failed: {e}")
            return None

    @staticmethod
    def _extract_from_env(env: Dict[str, Any]) -> Dict[str, str]:
        if not isinstance(env, dict):
            return {}
        api_key = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_TOKEN")
        base_url = env.get("ANTHROPIC_BASE_URL") or ""
        default_model = env.get("ANTHROPIC_MODEL")
        return {
            "api_key": api_key or "",
            "base_url": base_url or "",
            "default_model": default_model or "",
        }

    @staticmethod
    def _extract_provider_items(source_data: Any) -> List[Dict[str, Any]]:
        if isinstance(source_data, list):
            return [item for item in source_data if isinstance(item, dict)]
        if isinstance(source_data, dict):
            if "providers" in source_data and isinstance(
                source_data["providers"], dict
            ):
                items = []
                for item in source_data["providers"].values():
                    if isinstance(item, dict):
                        items.append(item)
                return items
            return [source_data]
        return []

    @staticmethod
    def _collect_model_ids(*values: Any) -> List[str]:
        model_ids: List[str] = []

        def add_value(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    model_ids.append(cleaned)
                return
            if isinstance(value, list):
                for item in value:
                    add_value(item)
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    key_upper = str(key).upper()
                    if "MODEL" in key_upper:
                        add_value(item)
                for key in (
                    "model",
                    "default_model",
                    "defaultModel",
                    "model_id",
                    "modelId",
                    "id",
                    "name",
                ):
                    if key in value:
                        add_value(value.get(key))
                if "models" in value:
                    add_value(value.get("models"))

        for value in values:
            add_value(value)

        seen = set()
        deduped: List[str] = []
        for item in model_ids:
            lowered = item.lower()
            if lowered in {"opus", "sonnet", "haiku"}:
                continue
            if re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", lowered
            ):
                continue
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    def convert_to_opencode(
        self, source_type: str, source_data: Dict
    ) -> Optional[Dict]:
        """将外部配置转换为OpenCode格式"""
        if not source_data:
            return None

        result = {"provider": {}, "permission": {}}
        used_keys: set = set()

        def add_provider(
            key: str,
            display_name: str,
            npm: str,
            api_key: str,
            base_url: str,
            require_v1: bool = False,
            model_ids: Optional[List[str]] = None,
        ) -> None:
            provider_key = self._unique_provider_key(key, used_keys)
            normalized_url = self._normalize_base_url(base_url, require_v1)
            models: Dict[str, Any] = {}
            if model_ids:
                for model_id in model_ids:
                    if model_id and isinstance(model_id, str):
                        models[model_id] = {"name": model_id}
            result["provider"][provider_key] = {
                "npm": npm,
                "name": display_name,
                "options": {
                    "apiKey": api_key or "",
                    "baseURL": normalized_url,
                },
                "models": models,
            }

        if source_type == "claude":
            env = source_data.get("env", source_data)
            extracted = self._extract_from_env(env)
            model_ids = self._collect_model_ids(
                extracted.get("default_model"),
                source_data.get("model"),
                source_data.get("default_model"),
                source_data.get("defaultModel"),
            )
            if extracted["api_key"] or extracted["base_url"] or model_ids:
                add_provider(
                    "anthropic",
                    "Anthropic (Claude)",
                    "@ai-sdk/anthropic",
                    extracted["api_key"],
                    extracted["base_url"],
                    require_v1=False,
                    model_ids=model_ids or None,
                )
            if "permissions" in source_data:
                for tool, perm in source_data.get("permissions", {}).items():
                    result["permission"][tool] = perm

        elif source_type == "claude_providers":
            for provider_data in self._extract_provider_items(source_data):
                display_name = provider_data.get("name") or provider_data.get("id")
                display_name = display_name or "Anthropic (Claude)"
                provider_key = self._sanitize_provider_key(display_name)
                api_key = provider_data.get("api_key") or provider_data.get(
                    "auth_token"
                )
                base_url = provider_data.get("base_url") or ""
                model_ids = self._collect_model_ids(
                    provider_data.get("models"),
                    provider_data.get("model"),
                    provider_data.get("default_model"),
                    provider_data.get("defaultModel"),
                )
                add_provider(
                    provider_key,
                    display_name,
                    "@ai-sdk/anthropic",
                    api_key or "",
                    base_url,
                    require_v1=False,
                    model_ids=model_ids or None,
                )

        elif source_type == "codex":
            model_providers = source_data.get("model_providers", {})
            provider_name = source_data.get("model_provider")
            provider_config = None
            if provider_name and isinstance(model_providers, dict):
                provider_config = model_providers.get(provider_name)
            if provider_config is None and isinstance(model_providers, dict):
                provider_name = next(iter(model_providers.keys()), None)
                provider_config = (
                    model_providers.get(provider_name) if provider_name else None
                )
            model_ids = self._collect_model_ids(
                source_data.get("model"),
                source_data.get("default_model"),
                source_data.get("defaultModel"),
                provider_config,
            )
            if isinstance(provider_config, dict):
                display_name = provider_config.get("name") or provider_name or "Codex"
                provider_key = self._sanitize_provider_key(
                    provider_name or display_name
                )
                base_url = provider_config.get("base_url", "")
                add_provider(
                    provider_key,
                    display_name,
                    "@ai-sdk/openai",
                    "",
                    base_url,
                    require_v1=True,
                    model_ids=model_ids or None,
                )
            elif model_ids:
                add_provider(
                    "codex",
                    "Codex",
                    "@ai-sdk/openai",
                    "",
                    "",
                    require_v1=True,
                    model_ids=model_ids,
                )

        elif source_type == "gemini":
            env = source_data.get("env", source_data)
            api_key = ""
            if isinstance(env, dict):
                api_key = env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
            api_key = api_key or source_data.get("apiKey") or ""
            base_url = source_data.get("baseURL") or source_data.get("base_url") or ""
            if api_key or base_url:
                add_provider(
                    "google",
                    "Google (Gemini)",
                    "@ai-sdk/google",
                    api_key,
                    base_url,
                    require_v1=False,
                )

        elif source_type == "ccswitch":
            claude = source_data.get("claude", {})
            claude_providers = claude.get("providers", {})
            if isinstance(claude_providers, dict):
                for provider_data in claude_providers.values():
                    if not isinstance(provider_data, dict):
                        continue
                    settings = provider_data.get("settingsConfig", {})
                    extracted = self._extract_from_env(settings.get("env", {}))
                    model_ids = self._collect_model_ids(
                        settings.get("env", {}),
                        settings.get("config", {}),
                        provider_data,
                        claude,
                    )
                    if not (extracted["api_key"] or extracted["base_url"] or model_ids):
                        continue
                    display_name = provider_data.get("name", "Anthropic (Claude)")
                    provider_key = self._sanitize_provider_key(display_name)
                    add_provider(
                        provider_key,
                        display_name,
                        "@ai-sdk/anthropic",
                        extracted["api_key"],
                        extracted["base_url"],
                        require_v1=False,
                        model_ids=model_ids or None,
                    )

            codex = source_data.get("codex", {})
            codex_providers = codex.get("providers", {})
            if isinstance(codex_providers, dict):
                for provider_data in codex_providers.values():
                    if not isinstance(provider_data, dict):
                        continue
                    settings = provider_data.get("settingsConfig", {})
                    auth = settings.get("auth", {})
                    config = settings.get("config", {})
                    if isinstance(config, str):
                        config = self._parse_toml_string(config)
                    api_key = ""
                    if isinstance(auth, dict):
                        api_key = auth.get("OPENAI_API_KEY") or ""
                    base_url = ""
                    if isinstance(config, dict):
                        base_url = config.get("base_url", "")
                    model_ids = self._collect_model_ids(
                        auth,
                        config,
                        settings.get("env", {}),
                        provider_data,
                        codex,
                    )
                    if not (api_key or base_url or model_ids):
                        continue
                    display_name = provider_data.get("name", "Codex")
                    provider_key = self._sanitize_provider_key(display_name)
                    require_v1 = True
                    if "/v1/" in base_url or base_url.rstrip("/").endswith("/v1"):
                        require_v1 = False
                    add_provider(
                        provider_key,
                        display_name,
                        "@ai-sdk/openai",
                        api_key,
                        base_url,
                        require_v1=require_v1,
                        model_ids=model_ids or None,
                    )

        return result
