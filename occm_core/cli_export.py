from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .data_types import (
    BackupInfo,
    BatchExportResult,
    CLIToolStatus,
    ExportResult,
    ValidationResult,
)


# ==================== CLI 导出模块异常类 ====================
class CLIExportError(Exception):
    """CLI 导出错误基类"""

    pass


class ProviderValidationError(CLIExportError):
    """Provider 配置验证错误"""

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Provider 配置不完整: 缺少 {', '.join(missing_fields)}")


class ConfigWriteError(CLIExportError):
    """配置写入错误"""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"写入配置失败 ({path}): {reason}")


class ConfigParseError(CLIExportError):
    """配置解析错误"""

    def __init__(self, path: Path, format_type: str, reason: str):
        self.path = path
        self.format_type = format_type
        self.reason = reason
        super().__init__(f"解析 {format_type} 配置失败 ({path}): {reason}")


class BackupError(CLIExportError):
    """备份操作错误"""

    def __init__(self, cli_type: str, reason: str):
        self.cli_type = cli_type
        self.reason = reason
        super().__init__(f"备份 {cli_type} 配置失败: {reason}")


class RestoreError(CLIExportError):
    """恢复操作错误"""

    def __init__(self, backup_path: Path, reason: str):
        self.backup_path = backup_path
        self.reason = reason
        super().__init__(f"恢复备份失败 ({backup_path}): {reason}")


class CLIConfigWriter:
    """CLI 配置写入器 - 原子写入配置文件"""

    @staticmethod
    def get_claude_dir() -> Path:
        """获取 Claude 配置目录 (~/.claude/)"""
        return Path.home() / ".claude"

    @staticmethod
    def get_codex_dir() -> Path:
        """获取 Codex 配置目录 (~/.codex/)"""
        return Path.home() / ".codex"

    @staticmethod
    def get_gemini_dir() -> Path:
        """获取 Gemini 配置目录 (~/.gemini/)"""
        return Path.home() / ".gemini"

    @staticmethod
    def get_cli_dir(cli_type: str) -> Path:
        """根据 CLI 类型获取配置目录"""
        if cli_type == "claude":
            return CLIConfigWriter.get_claude_dir()
        elif cli_type == "codex":
            return CLIConfigWriter.get_codex_dir()
        elif cli_type == "gemini":
            return CLIConfigWriter.get_gemini_dir()
        else:
            raise ValueError(f"Unknown CLI type: {cli_type}")

    def atomic_write_json(self, path: Path, data: Dict) -> None:
        """原子写入 JSON 文件

        1. 写入临时文件 (path.tmp.timestamp)
        2. 验证 JSON 格式
        3. 重命名替换原文件

        Raises:
            ConfigWriteError: 写入失败时抛出
        """
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = path.parent / f"{path.name}.tmp.{timestamp}"

        try:
            # 写入临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 验证写入的 JSON 格式
            with open(temp_path, "r", encoding="utf-8") as f:
                json.load(f)

            # 原子替换（Windows 需要先删除目标文件）
            if sys.platform == "win32" and path.exists():
                path.unlink()
            temp_path.rename(path)

        except json.JSONDecodeError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, f"JSON 格式验证失败: {e}")
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, str(e))

    def atomic_write_text(self, path: Path, content: str) -> None:
        """原子写入文本文件 (用于 TOML/.env)

        Raises:
            ConfigWriteError: 写入失败时抛出
        """
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = path.parent / f"{path.name}.tmp.{timestamp}"

        try:
            # 写入临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 原子替换
            if sys.platform == "win32" and path.exists():
                path.unlink()
            temp_path.rename(path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, str(e))

    def set_file_permissions(self, path: Path, mode: int = 0o600) -> None:
        """设置文件权限 (Unix only)

        Args:
            path: 文件路径
            mode: 权限模式，默认 600 (仅所有者可读写)
        """
        if sys.platform != "win32" and path.exists():
            try:
                path.chmod(mode)
            except Exception as e:
                print(f"设置文件权限失败 ({path}): {e}")

    def write_claude_settings(self, config: Dict, merge: bool = True) -> None:
        """写入 Claude settings.json

        Args:
            config: 要写入的配置（包含 env 字段）
            merge: 是否与现有配置合并 (保留非 env 字段)
        """
        settings_path = self.get_claude_dir() / "settings.json"

        if merge and settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # 合并配置：保留现有字段，更新 env
                existing["env"] = config.get("env", {})
                config = existing
            except (json.JSONDecodeError, Exception):
                # 现有文件无效，直接覆盖
                pass

        self.atomic_write_json(settings_path, config)

    def write_codex_auth(self, auth: Dict) -> None:
        """写入 Codex auth.json"""
        auth_path = self.get_codex_dir() / "auth.json"
        self.atomic_write_json(auth_path, auth)

    def write_codex_config(self, config_toml: str, merge: bool = True) -> None:
        """写入 Codex config.toml

        Args:
            config_toml: TOML 格式配置字符串
            merge: 是否保留现有的 MCP 配置等
        """
        config_path = self.get_codex_dir() / "config.toml"

        if merge and config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                # 简单合并：保留 [mcp] 段
                mcp_section = self._extract_toml_section(existing_content, "mcp")
                if mcp_section:
                    config_toml = config_toml.rstrip() + "\n\n" + mcp_section
            except Exception:
                pass

        self.atomic_write_text(config_path, config_toml)

    def _extract_toml_section(self, content: str, section_name: str) -> Optional[str]:
        """从 TOML 内容中提取指定段落"""
        lines = content.split("\n")
        result = []
        in_section = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"[{section_name}"):
                in_section = True
                result.append(line)
            elif in_section:
                if stripped.startswith("[") and not stripped.startswith(
                    f"[{section_name}"
                ):
                    break
                result.append(line)

        return "\n".join(result) if result else None

    def write_gemini_env(self, env_map: Dict[str, str]) -> None:
        """写入 Gemini .env 文件

        格式: KEY=VALUE (每行一个)
        """
        env_path = self.get_gemini_dir() / ".env"

        # 生成 .env 内容
        lines = [f"{key}={value}" for key, value in env_map.items()]
        content = "\n".join(lines) + "\n"

        self.atomic_write_text(env_path, content)

        # 设置文件权限 (Unix: 600)
        self.set_file_permissions(env_path, 0o600)

    def write_gemini_settings(self, security_config: Dict, merge: bool = True) -> None:
        """写入 Gemini settings.json

        Args:
            security_config: security.auth.selectedType 配置
            merge: 是否保留现有的 mcpServers 等字段
        """
        settings_path = self.get_gemini_dir() / "settings.json"

        config = {"security": security_config.get("security", security_config)}

        if merge and settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # 合并配置：保留 mcpServers 等字段
                for key, value in existing.items():
                    if key != "security":
                        config[key] = value
                # 深度合并 security 字段
                if "security" in existing:
                    existing_security = existing["security"]
                    new_security = config.get("security", {})
                    for key, value in existing_security.items():
                        if key not in new_security:
                            new_security[key] = value
                    config["security"] = new_security
            except (json.JSONDecodeError, Exception):
                pass

        self.atomic_write_json(settings_path, config)


class CLIBackupManager:
    """CLI 配置备份管理器"""

    BACKUP_DIR = Path.home() / ".opencode-backup"
    MAX_BACKUPS = 5

    def __init__(self):
        self.backup_dir = self.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, cli_type: str) -> Optional[Path]:
        """创建指定 CLI 工具的配置备份"""
        try:
            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            if not cli_dir.exists():
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{cli_type}_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)

            files_backed_up = []
            for item in cli_dir.iterdir():
                if item.is_file():
                    dest = backup_path / item.name
                    shutil.copy2(item, dest)
                    files_backed_up.append(item.name)

            if not files_backed_up:
                backup_path.rmdir()
                return None

            self.cleanup_old_backups(cli_type)
            return backup_path

        except Exception as e:
            raise BackupError(cli_type, str(e))

    def restore_backup(self, backup_path: Path, cli_type: str) -> bool:
        """从备份恢复配置"""
        try:
            if not backup_path.exists():
                raise RestoreError(backup_path, "备份目录不存在")

            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            cli_dir.mkdir(parents=True, exist_ok=True)

            self.create_backup(cli_type)

            for item in backup_path.iterdir():
                if item.is_file():
                    dest = cli_dir / item.name
                    shutil.copy2(item, dest)

            return True

        except RestoreError:
            raise
        except Exception as e:
            raise RestoreError(backup_path, str(e))

    def list_backups(self, cli_type: str) -> List[BackupInfo]:
        """列出指定 CLI 工具的所有备份"""
        backups = []
        prefix = f"{cli_type}_"

        try:
            for item in self.backup_dir.iterdir():
                if item.is_dir() and item.name.startswith(prefix):
                    timestamp_str = item.name[len(prefix) :]
                    try:
                        created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        continue

                    files = [f.name for f in item.iterdir() if f.is_file()]

                    backups.append(
                        BackupInfo(
                            path=item,
                            cli_type=cli_type,
                            created_at=created_at,
                            files=files,
                        )
                    )

            backups.sort(key=lambda x: x.created_at, reverse=True)

        except Exception as e:
            print(f"列出备份失败: {e}")

        return backups

    def cleanup_old_backups(self, cli_type: str) -> None:
        """清理旧备份，保留最近 MAX_BACKUPS 个"""
        backups = self.list_backups(cli_type)
        for backup in backups[self.MAX_BACKUPS :]:
            try:
                shutil.rmtree(backup.path)
            except Exception as e:
                print(f"删除旧备份失败 ({backup.path}): {e}")


class CLIConfigGenerator:
    """CLI 配置生成器 - 将 OpenCode 配置转换为各 CLI 工具格式"""

    def generate_claude_config(self, provider: Dict, model: str = None) -> Dict:
        """生成 Claude Code settings.json 配置"""
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )

        env = {
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": api_key,
        }

        if model:
            env["ANTHROPIC_MODEL"] = model

        model_mappings = provider.get("modelMappings", {})
        if model_mappings.get("haiku"):
            env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = model_mappings["haiku"]
        if model_mappings.get("sonnet"):
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model_mappings["sonnet"]
        if model_mappings.get("opus"):
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model_mappings["opus"]

        return {"env": env}

    def generate_codex_auth(self, provider: Dict) -> Dict:
        """生成 Codex auth.json 配置"""
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )
        return {"OPENAI_API_KEY": api_key}

    def generate_codex_config(self, provider: Dict, model: str) -> str:
        """生成 Codex config.toml 配置"""
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )

        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        provider_name = provider.get("name", "newapi")

        lines = [
            f'model_provider = "{provider_name}"',
            f'model = "{model}"',
            'model_reasoning_effort = "high"',
            "disable_response_storage = true",
            "",
            f"[model_providers.{provider_name}]",
            f'name = "{provider_name}"',
            f'base_url = "{base_url}"',
            'wire_api = "responses"',
            "requires_openai_auth = true",
        ]

        return "\n".join(lines) + "\n"

    def generate_gemini_env(self, provider: Dict, model: str) -> Dict[str, str]:
        """生成 Gemini .env 配置"""
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )

        return {
            "GOOGLE_GEMINI_BASE_URL": base_url,
            "GEMINI_API_KEY": api_key,
            "GEMINI_MODEL": model,
        }

    def generate_gemini_settings(self, auth_type: str = "gemini-api-key") -> Dict:
        """生成 Gemini settings.json 中的 security 配置"""
        return {"security": {"auth": {"selectedType": auth_type}}}


class CLIConfigGenerator: ...


class CLIExportManager:
    """CLI 工具导出管理器"""

    def __init__(self):
        self.config_generator = CLIConfigGenerator()
        self.config_writer = CLIConfigWriter()
        self.backup_manager = CLIBackupManager()

    def detect_cli_tools(self) -> Dict[str, CLIToolStatus]:
        """检测已安装的 CLI 工具"""
        result = {}

        for cli_type in ["claude", "codex", "gemini"]:
            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            installed = cli_dir.exists()

            has_config = False
            if installed:
                if cli_type == "claude":
                    has_config = (cli_dir / "settings.json").exists()
                elif cli_type == "codex":
                    has_config = (cli_dir / "config.toml").exists() or (
                        cli_dir / "auth.json"
                    ).exists()
                elif cli_type == "gemini":
                    has_config = (cli_dir / "settings.json").exists() or (
                        cli_dir / ".env"
                    ).exists()

            result[cli_type] = CLIToolStatus(
                cli_type=cli_type,
                installed=installed,
                config_dir=cli_dir if installed else None,
                has_config=has_config,
                version=None,
            )

        return result

    def validate_provider(self, provider: Dict) -> ValidationResult:
        """验证 Provider 配置完整性"""
        errors = []
        warnings = []

        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        if not base_url or not base_url.strip():
            errors.append("缺少 API 地址 (baseURL)")

        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )
        if not api_key or not api_key.strip():
            errors.append("缺少 API 密钥 (apiKey)")

        models = provider.get("models", {})
        if not models:
            warnings.append("未配置任何模型")

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult(valid=True, errors=[], warnings=warnings)

    def export_to_claude(self, provider: Dict, model: str) -> ExportResult:
        cli_type = "claude"
        backup_path = None

        try:
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            backup_path = self.backup_manager.create_backup(cli_type)
            config = self.config_generator.generate_claude_config(provider, model)
            self.config_writer.write_claude_settings(config)

            settings_path = CLIConfigWriter.get_claude_dir() / "settings.json"
            return ExportResult.ok(cli_type, [settings_path], backup_path)

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def export_to_codex(self, provider: Dict, model: str) -> ExportResult:
        cli_type = "codex"
        backup_path = None

        try:
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            backup_path = self.backup_manager.create_backup(cli_type)

            auth = self.config_generator.generate_codex_auth(provider)
            config_toml = self.config_generator.generate_codex_config(provider, model)

            self.config_writer.write_codex_auth(auth)
            self.config_writer.write_codex_config(config_toml)

            codex_dir = CLIConfigWriter.get_codex_dir()
            return ExportResult.ok(
                cli_type,
                [codex_dir / "auth.json", codex_dir / "config.toml"],
                backup_path,
            )

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def export_to_gemini(self, provider: Dict, model: str) -> ExportResult:
        cli_type = "gemini"
        backup_path = None

        try:
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            backup_path = self.backup_manager.create_backup(cli_type)
            env_map = self.config_generator.generate_gemini_env(provider, model)
            settings = self.config_generator.generate_gemini_settings()

            self.config_writer.write_gemini_env(env_map)
            self.config_writer.write_gemini_settings(settings)

            gemini_dir = CLIConfigWriter.get_gemini_dir()
            return ExportResult.ok(
                cli_type,
                [gemini_dir / ".env", gemini_dir / "settings.json"],
                backup_path,
            )

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def batch_export(
        self, provider: Dict, models: Dict[str, str], targets: List[str]
    ) -> BatchExportResult:
        """批量导出到多个 CLI 工具"""
        results = []

        for cli_type in targets:
            model = models.get(cli_type, "")

            try:
                if cli_type == "claude":
                    result = self.export_to_claude(provider, model)
                elif cli_type == "codex":
                    result = self.export_to_codex(provider, model)
                elif cli_type == "gemini":
                    result = self.export_to_gemini(provider, model)
                else:
                    result = ExportResult.fail(cli_type, f"未知的 CLI 类型: {cli_type}")
            except Exception as e:
                result = ExportResult.fail(cli_type, f"导出异常: {e}")

            results.append(result)

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BatchExportResult(
            total=len(results), successful=successful, failed=failed, results=results
        )

    def validate_exported_config(self, cli_type: str) -> ValidationResult:
        """验证导出后的配置"""
        errors = []
        warnings = []

        cli_dir = CLIConfigWriter.get_cli_dir(cli_type)

        if cli_type == "claude":
            settings_path = cli_dir / "settings.json"
            if not settings_path.exists():
                errors.append("settings.json 文件不存在")
            else:
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    if "env" not in config:
                        errors.append("settings.json 缺少 env 字段")
                    else:
                        env = config["env"]
                        if "ANTHROPIC_BASE_URL" not in env:
                            errors.append("缺少 ANTHROPIC_BASE_URL")
                        if "ANTHROPIC_AUTH_TOKEN" not in env:
                            errors.append("缺少 ANTHROPIC_AUTH_TOKEN")
                except json.JSONDecodeError as e:
                    errors.append(f"settings.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 settings.json 失败: {e}")

        elif cli_type == "codex":
            auth_path = cli_dir / "auth.json"
            config_path = cli_dir / "config.toml"

            if not auth_path.exists():
                errors.append("auth.json 文件不存在")
            else:
                try:
                    with open(auth_path, "r", encoding="utf-8") as f:
                        auth = json.load(f)
                    if "OPENAI_API_KEY" not in auth:
                        errors.append("auth.json 缺少 OPENAI_API_KEY")
                except json.JSONDecodeError as e:
                    errors.append(f"auth.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 auth.json 失败: {e}")

            if not config_path.exists():
                errors.append("config.toml 文件不存在")
            else:
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "model_provider" not in content:
                        errors.append("config.toml 缺少 model_provider")
                    if "model =" not in content:
                        errors.append("config.toml 缺少 model")
                except Exception as e:
                    errors.append(f"读取 config.toml 失败: {e}")

        elif cli_type == "gemini":
            env_path = cli_dir / ".env"
            settings_path = cli_dir / "settings.json"

            if not env_path.exists():
                errors.append(".env 文件不存在")
            else:
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "GEMINI_API_KEY" not in content:
                        errors.append(".env 缺少 GEMINI_API_KEY")
                    if "GOOGLE_GEMINI_BASE_URL" not in content:
                        errors.append(".env 缺少 GOOGLE_GEMINI_BASE_URL")
                except Exception as e:
                    errors.append(f"读取 .env 失败: {e}")

            if not settings_path.exists():
                warnings.append("settings.json 文件不存在")
            else:
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    if "security" not in config:
                        warnings.append("settings.json 缺少 security 字段")
                except json.JSONDecodeError as e:
                    errors.append(f"settings.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 settings.json 失败: {e}")

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult(valid=True, errors=[], warnings=warnings)
