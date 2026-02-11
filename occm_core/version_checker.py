from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, List, Optional


GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class VersionChecker:
    """GitHub 版本检查服务 - 纯 Python 版本（回调替代信号）"""

    def __init__(self, callback: Optional[Callable[[str, str], None]] = None):
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None
        self.checking = False
        self.last_check_time = 0
        self.check_interval = 3600
        self._update_callbacks: List[Callable[[str, str], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
        if callback:
            self._update_callbacks.append(callback)

    def add_update_callback(self, callback: Callable[[str, str], None]) -> None:
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        if callback not in self._error_callbacks:
            self._error_callbacks.append(callback)

    def _notify_update(self, latest_version: str, release_url: str) -> None:
        for cb in list(self._update_callbacks):
            try:
                cb(latest_version, release_url)
            except Exception:
                pass

    def _notify_error(self, error: str) -> None:
        for cb in list(self._error_callbacks):
            try:
                cb(error)
            except Exception:
                pass

    def check_update_async(self):
        """异步检查更新 - 带速率限制保护"""
        if self.checking:
            return

        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            print(
                f"Version check skipped: within cooldown period ({self.check_interval}s)"
            )
            return

        self.checking = True
        thread = threading.Thread(target=self._check_update, daemon=True)
        thread.start()

    def _check_update(self):
        """检查 GitHub 最新版本 - 带错误处理和速率限制"""
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={
                    "User-Agent": "OpenCode-Config-Manager",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    self.latest_version = version_match.group(1)
                    self.release_url = data.get("html_url", GITHUB_URL + "/releases")
                    self.last_check_time = time.time()
                    self._notify_update(self.latest_version, self.release_url)
        except urllib.error.HTTPError as e:
            error_msg = ""
            if e.code == 403:
                error_msg = "GitHub API速率限制（403），将在6小时后重试"
                print(f"Version check failed: {error_msg}")
                self.check_interval = 21600
            else:
                error_msg = f"HTTP {e.code} - {e.reason}"
                print(f"Version check failed: {error_msg}")
            self._notify_error(error_msg)
        except urllib.error.URLError as e:
            error_msg = f"网络错误 - {e.reason}"
            print(f"Version check failed: {error_msg}")
            self._notify_error(error_msg)
        except Exception as e:
            error_msg = str(e)
            print(f"Version check failed: {error_msg}")
            self._notify_error(error_msg)
        finally:
            self.checking = False

    @staticmethod
    def compare_versions(current: str, latest: str) -> bool:
        """比较版本号，返回 True 如果有新版本"""
        try:
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            return latest_parts > current_parts
        except Exception:
            return False
