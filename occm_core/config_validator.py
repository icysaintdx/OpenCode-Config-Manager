from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .i18n import tr


class ConfigValidator:
    """配置文件验证器 - 检查 OpenCode 配置格式是否正确"""

    @staticmethod
    def _is_blank(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False

    PROVIDER_REQUIRED_FIELDS = ["npm", "options"]
    PROVIDER_OPTIONS_REQUIRED = ["baseURL", "apiKey"]
    MODEL_RECOMMENDED_FIELDS = ["name", "limit"]
    OHMY_AGENT_REQUIRED_FIELDS = ["model"]
    OHMY_CATEGORY_REQUIRED_FIELDS = ["model"]
    VALID_NPM_PACKAGES = [
        "@ai-sdk/anthropic",
        "@ai-sdk/openai",
        "@ai-sdk/openai-compatible",
        "@ai-sdk/google",
        "@ai-sdk/azure",
        "@ai-sdk/amazon-bedrock",
        "@ai-sdk/google-vertex",
        "@ai-sdk/mistral",
        "@ai-sdk/xai",
        "@ai-sdk/togetherai",
        "@ai-sdk/cohere",
        "@ai-sdk/deepseek",
    ]

    @staticmethod
    def validate_opencode_config(config: Dict) -> List[Dict]:
        issues = []

        if config is None:
            issues.append(
                {
                    "level": "error",
                    "path": "root",
                    "message": tr("validator.config_parse_failed"),
                }
            )
            return issues

        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": tr("validator.root_must_be_object")}
            )
            return issues

        if not config or config == {}:
            issues.append(
                {
                    "level": "warning",
                    "path": "root",
                    "message": tr("validator.config_empty"),
                }
            )
            return issues

        schema = config.get("$schema")
        if schema != "https://opencode.ai/config.json":
            issues.append(
                {
                    "level": "warning",
                    "path": "$schema",
                    "message": tr("validator.schema_recommend"),
                }
            )

        providers = config.get("provider", {})
        if not providers:
            issues.append(
                {
                    "level": "warning",
                    "path": "provider",
                    "message": tr("validator.no_providers"),
                }
            )
        if not isinstance(providers, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "provider",
                    "message": tr("validator.provider_must_be_object"),
                }
            )
            return issues

        for provider_name, provider_data in providers.items():
            provider_path = f"provider.{provider_name}"

            if not isinstance(provider_data, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": provider_path,
                        "message": tr("validator.provider_value_not_object", name=provider_name, type=type(provider_data).__name__),
                    }
                )
                continue

            for field in ConfigValidator.PROVIDER_REQUIRED_FIELDS:
                if field not in provider_data:
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": tr("validator.provider_missing_field", name=provider_name, field=field),
                        }
                    )
                elif ConfigValidator._is_blank(provider_data.get(field)):
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": tr("validator.provider_field_empty", name=provider_name, field=field),
                        }
                    )

            npm = provider_data.get("npm", "")
            if npm and npm not in ConfigValidator.VALID_NPM_PACKAGES:
                issues.append(
                    {
                        "level": "warning",
                        "path": f"{provider_path}.npm",
                        "message": tr("validator.provider_unknown_npm", name=provider_name, npm=npm),
                    }
                )

            options = provider_data.get("options", {})
            if not isinstance(options, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.options",
                        "message": tr("validator.provider_options_not_object", name=provider_name),
                    }
                )
            else:
                for opt_field in ConfigValidator.PROVIDER_OPTIONS_REQUIRED:
                    if opt_field not in options:
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": tr("validator.provider_options_missing", name=provider_name, field=opt_field),
                            }
                        )
                    elif ConfigValidator._is_blank(options.get(opt_field)):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": tr("validator.provider_options_empty", name=provider_name, field=opt_field),
                            }
                        )

            models = provider_data.get("models", {})
            if not isinstance(models, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.models",
                        "message": tr("validator.provider_models_not_object", name=provider_name),
                    }
                )
            else:
                if not models:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{provider_path}.models",
                            "message": tr("validator.provider_no_models", name=provider_name),
                        }
                    )
                for model_id, model_data in models.items():
                    model_path = f"{provider_path}.models.{model_id}"
                    if ConfigValidator._is_blank(model_id):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": tr("validator.provider_empty_model_id", name=provider_name),
                            }
                        )
                        continue
                    if not isinstance(model_data, dict):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": tr("validator.model_value_not_object", model=model_id),
                            }
                        )
                        continue

                    limit = model_data.get("limit", {})
                    if not isinstance(limit, dict):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{model_path}.limit",
                                "message": tr("validator.model_limit_should_be_object", model=model_id),
                            }
                        )
                    elif limit:
                        context = limit.get("context")
                        output = limit.get("output")
                        if context is not None and not isinstance(context, int):
                            issues.append(
                                {
                                    "level": "warning",
                                    "path": f"{model_path}.limit.context",
                                    "message": tr("validator.model_context_should_be_int", model=model_id),
                                }
                            )
                        if output is not None and not isinstance(output, int):
                            issues.append(
                                {
                                    "level": "warning",
                                    "path": f"{model_path}.limit.output",
                                    "message": tr("validator.model_output_should_be_int", model=model_id),
                                }
                            )

        mcp = config.get("mcp", {})
        if mcp and not isinstance(mcp, dict):
            issues.append(
                {"level": "error", "path": "mcp", "message": tr("validator.mcp_must_be_object")}
            )
        elif isinstance(mcp, dict):
            for mcp_name, mcp_data in mcp.items():
                mcp_path = f"mcp.{mcp_name}"
                if not isinstance(mcp_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": mcp_path,
                            "message": tr("validator.mcp_value_not_object", name=mcp_name),
                        }
                    )
                    continue

                mcp_type = mcp_data.get("type")
                if mcp_type == "local" and "command" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.command",
                            "message": tr("validator.mcp_local_missing_command", name=mcp_name),
                        }
                    )
                elif mcp_type == "remote" and "url" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.url",
                            "message": tr("validator.mcp_remote_missing_url", name=mcp_name),
                        }
                    )

        agent = config.get("agent", {})
        if agent and not isinstance(agent, dict):
            issues.append(
                {"level": "error", "path": "agent", "message": tr("validator.agent_must_be_object")}
            )

        return issues

    @staticmethod
    def validate_ohmyopencode_config(config: Dict) -> List[Dict]:
        issues = []
        if not config:
            issues.append(
                {"level": "error", "path": "root", "message": tr("validator.config_empty_or_invalid")}
            )
            return issues
        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": tr("validator.root_must_be_object")}
            )
            return issues

        agents = config.get("agents", {})
        if not agents:
            issues.append(
                {"level": "warning", "path": "agents", "message": tr("validator.no_agents")}
            )
        if agents and not isinstance(agents, dict):
            issues.append(
                {"level": "error", "path": "agents", "message": tr("validator.agents_must_be_object")}
            )
            return issues

        if isinstance(agents, dict):
            for agent_name, agent_data in agents.items():
                agent_path = f"agents.{agent_name}"
                if ConfigValidator._is_blank(agent_name):
                    issues.append(
                        {
                            "level": "error",
                            "path": agent_path,
                            "message": tr("validator.agent_name_empty"),
                        }
                    )
                    continue
                if not isinstance(agent_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": agent_path,
                            "message": tr("validator.agent_value_not_object", name=agent_name),
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_AGENT_REQUIRED_FIELDS:
                    if field not in agent_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": tr("validator.agent_missing_field", name=agent_name, field=field),
                            }
                        )
                    elif ConfigValidator._is_blank(agent_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": tr("validator.agent_field_empty", name=agent_name, field=field),
                            }
                        )
                if "description" in agent_data and ConfigValidator._is_blank(
                    agent_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{agent_path}.description",
                            "message": tr("validator.agent_description_empty", name=agent_name),
                        }
                    )

        categories = config.get("categories", {})
        if not categories:
            issues.append(
                {
                    "level": "warning",
                    "path": "categories",
                    "message": tr("validator.no_categories"),
                }
            )
        if categories and not isinstance(categories, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "categories",
                    "message": tr("validator.categories_must_be_object"),
                }
            )
            return issues

        if isinstance(categories, dict):
            for category_name, category_data in categories.items():
                category_path = f"categories.{category_name}"
                if ConfigValidator._is_blank(category_name):
                    issues.append(
                        {
                            "level": "error",
                            "path": category_path,
                            "message": tr("validator.category_name_empty"),
                        }
                    )
                    continue
                if not isinstance(category_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": category_path,
                            "message": tr("validator.category_value_not_object", name=category_name),
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_CATEGORY_REQUIRED_FIELDS:
                    if field not in category_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": tr("validator.category_missing_field", name=category_name, field=field),
                            }
                        )
                    elif ConfigValidator._is_blank(category_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": tr("validator.category_field_empty", name=category_name, field=field),
                            }
                        )

                temperature = category_data.get("temperature")
                if temperature is not None and not isinstance(
                    temperature, (int, float)
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{category_path}.temperature",
                            "message": tr("validator.category_temperature_should_be_number", name=category_name),
                        }
                    )
                if "description" in category_data and ConfigValidator._is_blank(
                    category_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{category_path}.description",
                            "message": tr("validator.category_description_empty", name=category_name),
                        }
                    )

        return issues

    @staticmethod
    def fix_provider_structure(config: Dict) -> Tuple[Dict, List[str]]:
        fixes = []
        if not config:
            return config, fixes

        providers = config.get("provider", {})
        if not isinstance(providers, dict):
            return config, fixes

        fixed_providers = {}
        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                fixes.append(tr("validator.fix_skip_invalid_provider", name=provider_name))
                continue

            fixed_provider = dict(provider_data)

            if "npm" not in fixed_provider:
                fixed_provider["npm"] = "@ai-sdk/openai"
                fixes.append(tr("validator.fix_add_default_npm", name=provider_name))

            if "options" not in fixed_provider or not isinstance(
                fixed_provider.get("options"), dict
            ):
                fixed_provider["options"] = fixed_provider.get("options", {})
                if not isinstance(fixed_provider["options"], dict):
                    fixed_provider["options"] = {}
                fixes.append(tr("validator.fix_options_field", name=provider_name))

            if "baseURL" not in fixed_provider["options"]:
                fixed_provider["options"]["baseURL"] = ""
                fixes.append(tr("validator.fix_add_empty_baseurl", name=provider_name))
            if "apiKey" not in fixed_provider["options"]:
                fixed_provider["options"]["apiKey"] = ""
                fixes.append(tr("validator.fix_add_empty_apikey", name=provider_name))

            if "models" not in fixed_provider:
                fixed_provider["models"] = {}
                fixes.append(tr("validator.fix_add_empty_models", name=provider_name))
            elif not isinstance(fixed_provider.get("models"), dict):
                fixed_provider["models"] = {}
                fixes.append(tr("validator.fix_models_to_object", name=provider_name))

            for model_id, model_cfg in list(fixed_provider.get("models", {}).items()):
                if not isinstance(model_cfg, dict):
                    continue
                if "limit" not in model_cfg:
                    continue

                limit = model_cfg.get("limit")
                if not isinstance(limit, dict):
                    model_cfg.pop("limit", None)
                    fixes.append(
                        tr("validator.fix_remove_invalid_limit", name=provider_name, model=model_id)
                    )
                    continue

                normalized_limit = {}
                if isinstance(limit.get("context"), int):
                    normalized_limit["context"] = limit["context"]
                if isinstance(limit.get("output"), int):
                    normalized_limit["output"] = limit["output"]

                if normalized_limit:
                    model_cfg["limit"] = normalized_limit
                else:
                    model_cfg.pop("limit", None)
                    fixes.append(
                        tr("validator.fix_remove_empty_limit", name=provider_name, model=model_id)
                    )

            ordered_provider = {}
            if "npm" in fixed_provider:
                ordered_provider["npm"] = fixed_provider["npm"]
            if "name" in fixed_provider:
                ordered_provider["name"] = fixed_provider["name"]
            if "options" in fixed_provider:
                ordered_provider["options"] = fixed_provider["options"]
            if "models" in fixed_provider:
                ordered_provider["models"] = fixed_provider["models"]
            for k, v in fixed_provider.items():
                if k not in ordered_provider:
                    ordered_provider[k] = v

            fixed_providers[provider_name] = ordered_provider

        config["provider"] = fixed_providers
        return config, fixes

    @staticmethod
    def get_issues_summary(issues: List[Dict]) -> str:
        """生成问题摘要"""
        errors = [i for i in issues if i["level"] == "error"]
        warnings = [i for i in issues if i["level"] == "warning"]

        lines = []
        if errors:
            lines.append(tr("validator.error_count", count=len(errors)))
            for e in errors[:5]:
                lines.append(f"  • {e['message']}")
            if len(errors) > 5:
                lines.append(tr("validator.error_more", count=len(errors) - 5))

        if warnings:
            lines.append(tr("validator.warning_count", count=len(warnings)))
            for w in warnings[:5]:
                lines.append(f"  • {w['message']}")
            if len(warnings) > 5:
                lines.append(tr("validator.warning_more", count=len(warnings) - 5))

        return "\n".join(lines) if lines else tr("validator.config_valid")
