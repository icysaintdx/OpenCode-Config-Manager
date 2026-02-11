from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PluginConfig:
    """插件配置数据类"""

    name: str
    version: str
    type: str
    source: str
    enabled: bool
    description: str
    homepage: str
    installed_at: str


class PluginManager:
    """插件管理器"""

    @staticmethod
    def get_installed_plugins(config: Dict[str, Any]) -> List[PluginConfig]:
        """获取已安装的插件列表"""
        plugins: List[PluginConfig] = []

        plugin_list = config.get("plugin", [])
        if isinstance(plugin_list, list):
            for plugin_entry in plugin_list:
                if isinstance(plugin_entry, str):
                    if "@" in plugin_entry and not plugin_entry.startswith("@"):
                        parts = plugin_entry.rsplit("@", 1)
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else "latest"
                    elif plugin_entry.startswith("@") and plugin_entry.count("@") > 1:
                        parts = plugin_entry.rsplit("@", 1)
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else "latest"
                    else:
                        name = plugin_entry
                        version = "latest"

                    plugins.append(
                        PluginConfig(
                            name=name,
                            version=version,
                            type="npm",
                            source=plugin_entry,
                            enabled=True,
                            description="",
                            homepage="",
                            installed_at="",
                        )
                    )

        return plugins

    @staticmethod
    def install_npm_plugin(
        config: Dict[str, Any], package_name: str, version: str = ""
    ) -> bool:
        """安装npm插件"""
        try:
            if version and version != "latest":
                full_name = f"{package_name}@{version}"
            else:
                full_name = package_name

            if "plugin" not in config:
                config["plugin"] = []

            plugin_list = config["plugin"]
            if not isinstance(plugin_list, list):
                plugin_list = []
                config["plugin"] = plugin_list

            base_name = package_name.split("@")[0]
            for i, existing in enumerate(plugin_list):
                if isinstance(existing, str):
                    existing_base = existing.split("@")[0]
                    if existing_base == base_name:
                        plugin_list[i] = full_name
                        return True

            plugin_list.append(full_name)
            return True

        except Exception as e:
            print(f"安装插件失败: {e}")
            return False

    @staticmethod
    def uninstall_plugin(config: Dict[str, Any], plugin: PluginConfig) -> bool:
        """卸载插件"""
        try:
            if plugin.type == "npm":
                plugin_list = config.get("plugin", [])
                if isinstance(plugin_list, list):
                    base_name = plugin.name.split("@")[0]
                    config["plugin"] = [
                        p
                        for p in plugin_list
                        if not (isinstance(p, str) and p.split("@")[0] == base_name)
                    ]
                    return True
            elif plugin.type == "local":
                pass

            return False

        except Exception as e:
            print(f"卸载插件失败: {e}")
            return False

    @staticmethod
    def check_npm_version(package_name: str) -> str:
        """检查npm包的最新版本"""
        try:
            import requests

            url = f"https://registry.npmjs.org/{package_name}/latest"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("version", "")
        except Exception as e:
            print(f"检查版本失败: {e}")

        return ""
