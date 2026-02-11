from __future__ import annotations

from typing import Any, Dict, List, Tuple


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
                    "message": "配置文件无法解析或读取失败",
                }
            )
            return issues

        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": "配置根必须是对象类型"}
            )
            return issues

        if not config or config == {}:
            issues.append(
                {
                    "level": "warning",
                    "path": "root",
                    "message": "配置为空，尚未添加任何Provider",
                }
            )
            return issues

        schema = config.get("$schema")
        if schema != "https://opencode.ai/config.json":
            issues.append(
                {
                    "level": "warning",
                    "path": "$schema",
                    "message": "建议设置 $schema 为 https://opencode.ai/config.json",
                }
            )

        providers = config.get("provider", {})
        if not providers:
            issues.append(
                {
                    "level": "warning",
                    "path": "provider",
                    "message": "未配置任何 Provider",
                }
            )
        if not isinstance(providers, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "provider",
                    "message": "provider 必须是对象类型",
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
                        "message": f"Provider '{provider_name}' 的值必须是对象，当前是 {type(provider_data).__name__}",
                    }
                )
                continue

            for field in ConfigValidator.PROVIDER_REQUIRED_FIELDS:
                if field not in provider_data:
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": f"Provider '{provider_name}' 缺少必需字段 '{field}'",
                        }
                    )
                elif ConfigValidator._is_blank(provider_data.get(field)):
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": f"Provider '{provider_name}' 的 '{field}' 为空",
                        }
                    )

            npm = provider_data.get("npm", "")
            if npm and npm not in ConfigValidator.VALID_NPM_PACKAGES:
                issues.append(
                    {
                        "level": "warning",
                        "path": f"{provider_path}.npm",
                        "message": f"Provider '{provider_name}' 的 npm 包 '{npm}' 不在已知列表中",
                    }
                )

            options = provider_data.get("options", {})
            if not isinstance(options, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.options",
                        "message": f"Provider '{provider_name}' 的 options 必须是对象",
                    }
                )
            else:
                for opt_field in ConfigValidator.PROVIDER_OPTIONS_REQUIRED:
                    if opt_field not in options:
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": f"Provider '{provider_name}' 的 options 缺少 '{opt_field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(options.get(opt_field)):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": f"Provider '{provider_name}' 的 options.{opt_field} 为空",
                            }
                        )

            models = provider_data.get("models", {})
            if not isinstance(models, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.models",
                        "message": f"Provider '{provider_name}' 的 models 必须是对象",
                    }
                )
            else:
                if not models:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{provider_path}.models",
                            "message": f"Provider '{provider_name}' 没有配置任何模型",
                        }
                    )
                for model_id, model_data in models.items():
                    model_path = f"{provider_path}.models.{model_id}"
                    if ConfigValidator._is_blank(model_id):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": f"Provider '{provider_name}' 存在空模型ID",
                            }
                        )
                        continue
                    if not isinstance(model_data, dict):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": f"Model '{model_id}' 的值必须是对象",
                            }
                        )
                        continue

                    limit = model_data.get("limit", {})
                    if not isinstance(limit, dict):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{model_path}.limit",
                                "message": f"Model '{model_id}' 的 limit 应该是对象",
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
                                    "message": f"Model '{model_id}' 的 context 应该是整数",
                                }
                            )
                        if output is not None and not isinstance(output, int):
                            issues.append(
                                {
                                    "level": "warning",
                                    "path": f"{model_path}.limit.output",
                                    "message": f"Model '{model_id}' 的 output 应该是整数",
                                }
                            )

        mcp = config.get("mcp", {})
        if mcp and not isinstance(mcp, dict):
            issues.append(
                {"level": "error", "path": "mcp", "message": "mcp 必须是对象类型"}
            )
        elif isinstance(mcp, dict):
            for mcp_name, mcp_data in mcp.items():
                mcp_path = f"mcp.{mcp_name}"
                if not isinstance(mcp_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": mcp_path,
                            "message": f"MCP '{mcp_name}' 的值必须是对象",
                        }
                    )
                    continue

                mcp_type = mcp_data.get("type")
                if mcp_type == "local" and "command" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.command",
                            "message": f"Local MCP '{mcp_name}' 缺少 command 字段",
                        }
                    )
                elif mcp_type == "remote" and "url" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.url",
                            "message": f"Remote MCP '{mcp_name}' 缺少 url 字段",
                        }
                    )

        agent = config.get("agent", {})
        if agent and not isinstance(agent, dict):
            issues.append(
                {"level": "error", "path": "agent", "message": "agent 必须是对象类型"}
            )

        return issues

    @staticmethod
    def validate_ohmyopencode_config(config: Dict) -> List[Dict]:
        issues = []
        if not config:
            issues.append(
                {"level": "error", "path": "root", "message": "配置文件为空或无法解析"}
            )
            return issues
        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": "配置根必须是对象类型"}
            )
            return issues

        agents = config.get("agents", {})
        if not agents:
            issues.append(
                {"level": "warning", "path": "agents", "message": "未配置任何 Agent"}
            )
        if agents and not isinstance(agents, dict):
            issues.append(
                {"level": "error", "path": "agents", "message": "agents 必须是对象类型"}
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
                            "message": "Agent 名称为空",
                        }
                    )
                    continue
                if not isinstance(agent_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": agent_path,
                            "message": f"Agent '{agent_name}' 的值必须是对象",
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_AGENT_REQUIRED_FIELDS:
                    if field not in agent_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": f"Agent '{agent_name}' 缺少必需字段 '{field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(agent_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": f"Agent '{agent_name}' 的 '{field}' 为空",
                            }
                        )
                if "description" in agent_data and ConfigValidator._is_blank(
                    agent_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{agent_path}.description",
                            "message": f"Agent '{agent_name}' 的 description 为空",
                        }
                    )

        categories = config.get("categories", {})
        if not categories:
            issues.append(
                {
                    "level": "warning",
                    "path": "categories",
                    "message": "未配置任何 Category",
                }
            )
        if categories and not isinstance(categories, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "categories",
                    "message": "categories 必须是对象类型",
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
                            "message": "Category 名称为空",
                        }
                    )
                    continue
                if not isinstance(category_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": category_path,
                            "message": f"Category '{category_name}' 的值必须是对象",
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_CATEGORY_REQUIRED_FIELDS:
                    if field not in category_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": f"Category '{category_name}' 缺少必需字段 '{field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(category_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": f"Category '{category_name}' 的 '{field}' 为空",
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
                            "message": f"Category '{category_name}' 的 temperature 应该是数字",
                        }
                    )
                if "description" in category_data and ConfigValidator._is_blank(
                    category_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{category_path}.description",
                            "message": f"Category '{category_name}' 的 description 为空",
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
                fixes.append(f"跳过无效 Provider '{provider_name}' (值不是对象)")
                continue

            fixed_provider = dict(provider_data)

            if "npm" not in fixed_provider:
                fixed_provider["npm"] = "@ai-sdk/openai"
                fixes.append(f"Provider '{provider_name}': 添加默认 npm 字段")

            if "options" not in fixed_provider or not isinstance(
                fixed_provider.get("options"), dict
            ):
                fixed_provider["options"] = fixed_provider.get("options", {})
                if not isinstance(fixed_provider["options"], dict):
                    fixed_provider["options"] = {}
                fixes.append(f"Provider '{provider_name}': 修复 options 字段")

            if "baseURL" not in fixed_provider["options"]:
                fixed_provider["options"]["baseURL"] = ""
                fixes.append(f"Provider '{provider_name}': 添加空 baseURL")
            if "apiKey" not in fixed_provider["options"]:
                fixed_provider["options"]["apiKey"] = ""
                fixes.append(f"Provider '{provider_name}': 添加空 apiKey")

            if "models" not in fixed_provider:
                fixed_provider["models"] = {}
                fixes.append(f"Provider '{provider_name}': 添加空 models 字段")
            elif not isinstance(fixed_provider.get("models"), dict):
                fixed_provider["models"] = {}
                fixes.append(f"Provider '{provider_name}': 修复 models 字段为对象")

            for model_id, model_cfg in list(fixed_provider.get("models", {}).items()):
                if not isinstance(model_cfg, dict):
                    continue
                if "limit" not in model_cfg:
                    continue

                limit = model_cfg.get("limit")
                if not isinstance(limit, dict):
                    model_cfg.pop("limit", None)
                    fixes.append(
                        f"Provider '{provider_name}' Model '{model_id}': 移除无效 limit"
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
                        f"Provider '{provider_name}' Model '{model_id}': 移除空 limit"
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
            lines.append(f"❌ {len(errors)} 个错误:")
            for e in errors[:5]:
                lines.append(f"  • {e['message']}")
            if len(errors) > 5:
                lines.append(f"  ... 还有 {len(errors) - 5} 个错误")

        if warnings:
            lines.append(f"⚠️ {len(warnings)} 个警告:")
            for w in warnings[:5]:
                lines.append(f"  • {w['message']}")
            if len(warnings) > 5:
                lines.append(f"  ... 还有 {len(warnings) - 5} 个警告")

        return "\n".join(lines) if lines else "✅ 配置格式正确"
