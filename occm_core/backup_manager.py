from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config_paths import ConfigPaths


class BackupManager:
    """备份管理器"""

    def __init__(self):
        self.backup_dir = ConfigPaths.get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path: Path, tag: str = "auto") -> Optional[Path]:
        """创建配置文件备份，支持自定义标签"""
        try:
            if not config_path.exists():
                return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_path.stem}.{timestamp}.{tag}.bak"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(config_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def create_backup(self) -> Optional[Path]:
        """创建 OpenCode 主配置备份（页面调用入口）"""
        return self.backup(ConfigPaths.get_opencode_config(), tag="manual")

    def backup_data(
        self, config_path: Path, data: Dict, tag: str = "memory"
    ) -> Optional[Path]:
        """备份当前内存态配置（不依赖磁盘内容）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_path.stem}.{timestamp}.{tag}.bak"
            backup_path = self.backup_dir / backup_name
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return backup_path
        except Exception as e:
            print(f"Backup data failed: {e}")
            return None

    @staticmethod
    def file_hash(path: Path) -> Optional[str]:
        """计算文件哈希，用于检测外部修改"""
        try:
            if not path.exists():
                return None
            with open(path, "rb") as f:
                data = f.read()
            return hashlib.md5(data).hexdigest()
        except Exception as e:
            print(f"Hash failed: {e}")
            return None

    def list_backups(self, config_name: Optional[str] = None) -> List[Dict]:
        """列出所有备份文件，按时间倒序"""
        try:
            backups = []
            for f in self.backup_dir.glob("*.bak"):
                parts = f.stem.split(".")
                if len(parts) >= 3:
                    name = parts[0]
                    timestamp = parts[1]
                    tag = parts[2] if len(parts) > 2 else "auto"
                    if config_name is None or name == config_name:
                        backups.append(
                            {
                                "path": f,
                                "name": name,
                                "timestamp": timestamp,
                                "tag": tag,
                                "display": f"{name} - {timestamp} ({tag})",
                            }
                        )
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
        except Exception as e:
            print(f"List backups failed: {e}")
            return []

    def restore(self, backup_path: Path, target_path: Path) -> bool:
        """从备份恢复配置"""
        try:
            if not backup_path.exists():
                return False
            self.backup(target_path, tag="before_restore")
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def delete_backup(self, backup_path: Path) -> bool:
        """删除指定备份"""
        try:
            if backup_path.exists():
                backup_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Delete backup failed: {e}")
            return False
