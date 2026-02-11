from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


# ==================== CLI 导出模块数据类 ====================
@dataclass
class CLIToolStatus:
    """CLI 工具安装状态"""

    cli_type: str  # "claude" | "codex" | "gemini"
    installed: bool  # 是否已安装（配置目录存在）
    config_dir: Optional[Path]  # 配置目录路径
    has_config: bool  # 是否已有配置文件
    version: Optional[str] = None  # CLI 版本（如果可检测）


@dataclass
class ValidationResult:
    """Provider 配置验证结果"""

    valid: bool
    errors: List[str]  # 错误信息列表
    warnings: List[str]  # 警告信息列表

    @staticmethod
    def success() -> "ValidationResult":
        """创建成功的验证结果"""
        return ValidationResult(valid=True, errors=[], warnings=[])

    @staticmethod
    def failure(
        errors: List[str], warnings: Optional[List[str]] = None
    ) -> "ValidationResult":
        """创建失败的验证结果"""
        return ValidationResult(valid=False, errors=errors, warnings=warnings or [])


@dataclass
class ExportResult:
    """单个 CLI 工具导出结果"""

    success: bool
    cli_type: str
    backup_path: Optional[Path]
    error_message: Optional[str]
    files_written: List[Path]

    @staticmethod
    def ok(
        cli_type: str, files_written: List[Path], backup_path: Optional[Path] = None
    ) -> "ExportResult":
        """创建成功的导出结果"""
        return ExportResult(
            success=True,
            cli_type=cli_type,
            backup_path=backup_path,
            error_message=None,
            files_written=files_written,
        )

    @staticmethod
    def fail(
        cli_type: str, error_message: str, backup_path: Optional[Path] = None
    ) -> "ExportResult":
        """创建失败的导出结果"""
        return ExportResult(
            success=False,
            cli_type=cli_type,
            backup_path=backup_path,
            error_message=error_message,
            files_written=[],
        )


@dataclass
class BatchExportResult:
    """批量导出结果"""

    total: int
    successful: int
    failed: int
    results: List[ExportResult]

    @property
    def all_success(self) -> bool:
        """是否全部成功"""
        return self.failed == 0

    @property
    def partial_success(self) -> bool:
        """是否部分成功"""
        return self.successful > 0 and self.failed > 0


@dataclass
class BackupInfo:
    """备份信息"""

    path: Path
    cli_type: str
    created_at: datetime
    files: List[str]
