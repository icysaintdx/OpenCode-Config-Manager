from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Deque, Dict, List, Optional
from urllib.parse import urlparse

from .native_providers import _resolve_env_value, _safe_base_url


MONITOR_POLL_INTERVAL_MS = 60000
MONITOR_HISTORY_LIMIT = 60
DEGRADED_THRESHOLD_MS = 6000


def _build_chat_url(base_url: str) -> str:
    """根据 baseURL 生成 chat/completions 地址"""
    value = (base_url or "").strip()
    if not value:
        return ""
    if value.endswith("/v1") or value.endswith("/v1/"):
        return value.rstrip("/") + "/chat/completions"
    if value.endswith("/"):
        return value + "v1/chat/completions"
    return value + "/v1/chat/completions"


def _extract_origin(base_url: str) -> str:
    """从 baseURL 提取可用于 Ping 的源站"""
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return base_url


def _measure_ping(origin: str, timeout_sec: float = 3.0) -> Optional[int]:
    if not origin:
        return None
    parsed = urlparse(origin)
    host = parsed.hostname
    if not host:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout_sec)
        sock.close()
    except Exception:
        return None
    return int((time.time() - start) * 1000)


@dataclass
class MonitorTarget:
    provider_key: str
    provider_name: str
    base_url: str
    api_key: str
    model_id: str
    model_name: str

    @property
    def target_id(self) -> str:
        return f"{self.provider_key}/{self.model_id}"


@dataclass
class MonitorResult:
    target_id: str
    status: str
    latency_ms: Optional[int]
    ping_ms: Optional[int]
    checked_at: datetime
    message: str


class MonitorService:
    """纯逻辑版本监控服务（回调模式）"""

    def __init__(
        self,
        poll_interval_ms: int = MONITOR_POLL_INTERVAL_MS,
        request_timeout_sec: int = 15,
        max_workers: int = 6,
    ):
        self.poll_interval_ms = poll_interval_ms
        self.request_timeout_sec = request_timeout_sec
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        self._targets: List[MonitorTarget] = []
        self._history: Dict[str, Deque[MonitorResult]] = {}

        self._callbacks: List[Callable[[MonitorResult], None]] = []
        self._poll_done_callbacks: List[Callable[[], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        self._is_polling = False
        self._chat_test_enabled = False
        self._stop_event = threading.Event()
        self._loop_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_result_callback(self, callback: Callable[[MonitorResult], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def add_poll_done_callback(self, callback: Callable[[], None]) -> None:
        if callback not in self._poll_done_callbacks:
            self._poll_done_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        if callback not in self._error_callbacks:
            self._error_callbacks.append(callback)

    def set_chat_test_enabled(self, enabled: bool) -> None:
        self._chat_test_enabled = enabled

    def set_targets(self, targets: List[MonitorTarget]) -> None:
        with self._lock:
            self._targets = list(targets)
            for target in targets:
                if target.target_id not in self._history:
                    self._history[target.target_id] = deque(
                        maxlen=MONITOR_HISTORY_LIMIT
                    )

    def load_targets_from_config(
        self, opencode_config: Optional[Dict]
    ) -> List[MonitorTarget]:
        targets: List[MonitorTarget] = []
        config = opencode_config or {}
        providers = config.get("provider", {})

        for provider_key, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                continue
            provider_name = provider_data.get("name", provider_key)
            options = provider_data.get("options", {})
            base_url = _safe_base_url(
                options.get("baseURL", "") or provider_data.get("baseURL", "")
            )
            api_key_raw = options.get("apiKey", "") or provider_data.get("apiKey", "")
            api_key = _resolve_env_value(api_key_raw) if api_key_raw else ""

            models = provider_data.get("models", {})
            for model_id, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                model_name = model_data.get("name", model_id)
                target = MonitorTarget(
                    provider_key=provider_key,
                    provider_name=provider_name,
                    base_url=base_url,
                    api_key=api_key,
                    model_id=model_id,
                    model_name=model_name,
                )
                targets.append(target)

        self.set_targets(targets)
        return targets

    def start_polling(self) -> None:
        if self._loop_thread and self._loop_thread.is_alive():
            return
        self._stop_event.clear()
        self._loop_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._loop_thread.start()

    def stop_polling(self) -> None:
        self._stop_event.set()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=1.0)

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._do_poll()
            except Exception as e:
                self._notify_error(str(e))
            self._stop_event.wait(self.poll_interval_ms / 1000.0)

    def _do_poll(self) -> None:
        with self._lock:
            if self._is_polling:
                return
            targets = list(self._targets)
            self._is_polling = True

        try:
            if not targets:
                return

            futures = {
                self._executor.submit(self.check_target, t): t.target_id
                for t in targets
            }
            start_at = time.time()

            while futures and (time.time() - start_at) <= 60:
                done_keys = []
                for future, target_id in futures.items():
                    if future.done():
                        try:
                            result = future.result()
                        except Exception as e:
                            result = MonitorResult(
                                target_id=target_id,
                                status="error",
                                latency_ms=None,
                                ping_ms=None,
                                checked_at=datetime.now(),
                                message=str(e)[:50],
                            )
                        self._record_result(result)
                        done_keys.append(future)
                for key in done_keys:
                    futures.pop(key, None)
                if futures:
                    time.sleep(0.05)

            for future, target_id in list(futures.items()):
                future.cancel()
                timeout_result = MonitorResult(
                    target_id=target_id,
                    status="error",
                    latency_ms=None,
                    ping_ms=None,
                    checked_at=datetime.now(),
                    message="请求超时",
                )
                self._record_result(timeout_result)
                futures.pop(future, None)

        finally:
            with self._lock:
                self._is_polling = False
            self._notify_poll_done()

    def check_target(self, target: MonitorTarget) -> MonitorResult:
        """检查单个目标的可用性和延迟"""
        checked_at = datetime.now()
        origin = _extract_origin(target.base_url)

        ping_ms = _measure_ping(origin) if origin else None

        latency_ms: Optional[int] = None
        status = "no_config"
        message = ""

        if not self._chat_test_enabled:
            if not target.base_url:
                message = "未配置 baseURL"
            elif ping_ms is not None:
                status = "operational"
                message = "对话测试已暂停 (Ping 正常)"
            elif origin:
                status = "error"
                message = "Ping 失败"
            else:
                status = "no_config"
                message = "未配置有效的主机"
        elif not target.base_url:
            message = "未配置 baseURL"
        elif not target.api_key:
            message = "未配置 apiKey"
        else:
            try:
                url = _build_chat_url(target.base_url)
                if not url:
                    raise ValueError("baseURL 无效")
                payload = json.dumps(
                    {
                        "model": target.model_id,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    }
                ).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {target.api_key}",
                    },
                    method="POST",
                )
                start = time.time()
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp.read()
                latency_ms = int((time.time() - start) * 1000)
                if latency_ms <= DEGRADED_THRESHOLD_MS:
                    status = "operational"
                    message = "正常"
                else:
                    status = "degraded"
                    message = f"延迟较高 ({latency_ms}ms)"
            except urllib.error.HTTPError as e:
                status = "failed"
                message = "鉴权失败" if e.code in (401, 403) else f"HTTP {e.code}"
            except urllib.error.URLError as e:
                status = "error"
                message = f"连接失败: {e.reason}"
            except Exception as e:
                status = "error"
                message = str(e)[:50]

        return MonitorResult(
            target_id=target.target_id,
            status=status,
            latency_ms=latency_ms,
            ping_ms=ping_ms,
            checked_at=checked_at,
            message=message,
        )

    def _record_result(self, result: MonitorResult) -> None:
        history = self._history.get(result.target_id)
        if history is None:
            history = deque(maxlen=MONITOR_HISTORY_LIMIT)
            self._history[result.target_id] = history
        history.append(result)
        for cb in list(self._callbacks):
            try:
                cb(result)
            except Exception:
                pass

    def _notify_poll_done(self) -> None:
        for cb in list(self._poll_done_callbacks):
            try:
                cb()
            except Exception:
                pass

    def _notify_error(self, message: str) -> None:
        for cb in list(self._error_callbacks):
            try:
                cb(message)
            except Exception:
                pass

    def get_history(self, target_id: str) -> Deque[MonitorResult]:
        return self._history.get(target_id, deque(maxlen=MONITOR_HISTORY_LIMIT))
