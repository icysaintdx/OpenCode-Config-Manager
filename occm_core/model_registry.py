from __future__ import annotations

from typing import Dict, List, Optional

from .auth_manager import AuthManager


class ModelRegistry:
    """模型注册表 - 管理所有已配置的模型"""

    def __init__(
        self,
        opencode_config: Optional[Dict],
        auth_manager: Optional[AuthManager] = None,
    ):
        self.config = opencode_config or {}
        self.auth_manager = auth_manager or AuthManager()
        self.models: Dict[str, bool] = {}
        self.native_providers: Dict[str, bool] = {}  # 已配置的原生 Provider
        self.refresh()

    def refresh(self):
        self.models = {}
        self.native_providers = {}

        providers = self.config.get("provider", {})
        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                continue
            models = provider_data.get("models", {})
            for model_id in models.keys():
                full_ref = f"{provider_name}/{model_id}"
                self.models[full_ref] = True

        try:
            auth_data = self.auth_manager.read_auth()
            for provider_id in auth_data:
                if auth_data[provider_id]:
                    self.native_providers[provider_id] = True
        except Exception:
            pass

    def get_all_models(self) -> List[str]:
        return list(self.models.keys())

    def get_configured_native_providers(self) -> List[str]:
        """获取已配置的原生 Provider ID 列表"""
        return list(self.native_providers.keys())

    def is_native_provider_configured(self, provider_id: str) -> bool:
        """检查原生 Provider 是否已配置"""
        return provider_id in self.native_providers
