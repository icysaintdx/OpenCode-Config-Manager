from __future__ import annotations

import base64
import json
import platform
import shlex
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

# paramiko 为可选依赖：如果未安装，远程功能将不可用
try:
    import paramiko  # pyright: ignore[reportMissingModuleSource]
except Exception:  # pragma: no cover - 可选依赖导入失败时兜底
    paramiko = None


ConfigType = Literal["opencode", "oh-my-opencode", "auth"]


@dataclass
class RemoteServer:
    """远程服务器连接信息。

    字段说明：
    - host: 服务器地址
    - port: SSH 端口，默认 22
    - username: 登录用户名
    - auth_type: 鉴权方式，password 或 key
    - password: 密码（仅在内存中明文，持久化时建议编码）
    - key_path: 私钥路径（本地路径）
    - nickname: 服务器昵称（用于 UI 展示）
    - custom_config_path: 远程配置目录自定义路径（可选）
    """

    host: str
    port: int = 22
    username: str = ""
    auth_type: Literal["password", "key"] = "password"
    password: Optional[str] = None
    key_path: Optional[str] = None
    nickname: str = ""
    custom_config_path: Optional[str] = None

    def unique_id(self) -> str:
        """返回服务器唯一标识，用于连接池索引。"""
        return f"{self.username}@{self.host}:{self.port}"

    def to_dict(self, encode_password: bool = True) -> Dict[str, Any]:
        """序列化为 dict，可选对密码进行 base64 编码存储。"""
        data = asdict(self)
        if encode_password and data.get("password"):
            raw = data["password"].encode("utf-8")
            data["password"] = base64.b64encode(raw).decode("utf-8")
            data["password_encoded"] = True
        else:
            data["password_encoded"] = False
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any], decode_password: bool = True) -> "RemoteServer":
        """从 dict 反序列化为 RemoteServer。"""
        parsed = dict(data or {})
        encoded = bool(parsed.pop("password_encoded", False))

        if decode_password and encoded and parsed.get("password"):
            try:
                parsed["password"] = base64.b64decode(parsed["password"]).decode(
                    "utf-8"
                )
            except Exception:
                # 解码失败不抛错，保留原始值，避免因历史数据导致整个列表不可用
                pass

        return RemoteServer(
            host=parsed.get("host", ""),
            port=int(parsed.get("port", 22) or 22),
            username=parsed.get("username", ""),
            auth_type=parsed.get("auth_type", "password"),
            password=parsed.get("password"),
            key_path=parsed.get("key_path"),
            nickname=parsed.get("nickname", ""),
            custom_config_path=parsed.get("custom_config_path"),
        )


class RemoteManager:
    """远程 OpenCode 配置管理器（基于 SSH/paramiko）。"""

    _CONFIG_FILENAME_MAP: Dict[str, str] = {
        "opencode": "opencode.json",
        "opencode.json": "opencode.json",
        "oh-my-opencode": "oh-my-opencode.json",
        "ohmyopencode": "oh-my-opencode.json",
        "oh-my-opencode.json": "oh-my-opencode.json",
        "auth": "auth.json",
        "auth.json": "auth.json",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._clients: Dict[str, Any] = {}

    @staticmethod
    def _ensure_paramiko() -> None:
        """确保 paramiko 可用。"""
        if paramiko is None:
            raise RuntimeError(
                "未安装 paramiko，无法使用远程管理功能。请先执行: pip install paramiko"
            )

    @staticmethod
    def _normalize_config_type(config_type: str) -> str:
        """规范化配置类型，返回对应文件名。"""
        key = (config_type or "").strip().lower()
        if key not in RemoteManager._CONFIG_FILENAME_MAP:
            raise ValueError(
                f"不支持的配置类型: {config_type}。仅支持 opencode / oh-my-opencode / auth"
            )
        return RemoteManager._CONFIG_FILENAME_MAP[key]

    def _connect_auth(self, client: Any, server: RemoteServer) -> None:
        """按鉴权方式建立 SSH 连接。"""
        if server.auth_type == "key":
            if not server.key_path:
                raise ValueError("使用密钥登录时必须提供 key_path")

            key_path = Path(server.key_path).expanduser()
            if not key_path.exists():
                raise FileNotFoundError(f"私钥文件不存在: {key_path}")

            client.connect(
                hostname=server.host,
                port=server.port,
                username=server.username,
                key_filename=str(key_path),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            return

        if server.auth_type == "password":
            if not server.password:
                raise ValueError("使用密码登录时必须提供 password")

            client.connect(
                hostname=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            return

        raise ValueError(f"不支持的 auth_type: {server.auth_type}")

    def connect(self, server: RemoteServer) -> Tuple[bool, str]:
        """连接远程服务器。"""
        try:
            self._ensure_paramiko()
            key = server.unique_id()

            # 已连接则直接复用
            if key in self._clients:
                transport = self._clients[key].get_transport()
                if transport and transport.is_active():
                    return True, "已连接（复用现有连接）"
                self.disconnect(server)

            pm = paramiko
            if pm is None:
                raise RuntimeError("paramiko 不可用")

            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            self._connect_auth(client, server)
            self._clients[key] = client
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {e}"

    def disconnect(self, server: RemoteServer) -> None:
        """断开单个服务器连接。"""
        key = server.unique_id()
        client = self._clients.pop(key, None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    def disconnect_all(self) -> None:
        """断开全部连接。"""
        for key, client in list(self._clients.items()):
            try:
                client.close()
            except Exception:
                pass
            self._clients.pop(key, None)

    def test_connection(self, server: RemoteServer) -> Tuple[bool, str]:
        """测试远程连接可用性。"""
        ok, msg = self.connect(server)
        if not ok:
            return False, msg

        try:
            code, out, err = self._exec(server, "echo OCCM_REMOTE_OK")
            if code == 0 and out.strip() == "OCCM_REMOTE_OK":
                return True, "连接测试成功"
            return False, f"连接测试失败: {err or out}"
        except Exception as e:
            return False, f"连接测试异常: {e}"

    def _get_client(self, server: RemoteServer) -> Any:
        """获取可用客户端，不可用时自动重连。"""
        self._ensure_paramiko()
        key = server.unique_id()

        client = self._clients.get(key)
        if client:
            transport = client.get_transport()
            if transport and transport.is_active():
                return client

        ok, msg = self.connect(server)
        if not ok:
            raise ConnectionError(msg)

        return self._clients[key]

    def _exec(self, server: RemoteServer, command: str) -> Tuple[int, str, str]:
        """执行远程命令并返回 (exit_code, stdout, stderr)。"""
        client = self._get_client(server)
        stdin, stdout, stderr = client.exec_command(command, timeout=self.timeout)
        # 明确关闭 stdin，避免部分场景下阻塞
        try:
            stdin.close()
        except Exception:
            pass

        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        return code, out, err

    def _expand_remote_path(self, server: RemoteServer, path: str) -> str:
        """展开远程路径中的 ~。"""
        quoted = shlex.quote(path)
        cmd = f'python3 -c "import os; print(os.path.expanduser({quoted}))"'
        code, out, err = self._exec(server, cmd)
        if code == 0 and out.strip():
            return out.strip()

        # python3 不存在时退化使用 shell 方式
        shell_cmd = f"sh -lc 'eval echo {shlex.quote(path)}'"
        code2, out2, err2 = self._exec(server, shell_cmd)
        if code2 == 0 and out2.strip():
            return out2.strip()

        raise RuntimeError(f"远程路径展开失败: {err or err2 or out or out2}")

    def _get_remote_config_dir(self, server: RemoteServer) -> str:
        """获取远程配置目录。

        规则：
        1) 若 server.custom_config_path 存在，优先使用
        2) 否则默认 Linux 路径 ~/.config/opencode
        """
        base = server.custom_config_path or "~/.config/opencode"

        # Linux 是目标主平台，其他系统给出提醒但仍尝试执行
        if platform.system().lower().startswith("win"):
            # 本地是 Windows 不影响远程路径，保留注释用于说明跨平台调用
            pass

        return self._expand_remote_path(server, base)

    def _get_remote_config_path(self, server: RemoteServer, config_type: str) -> str:
        """根据配置类型得到远程配置文件完整路径。"""
        filename = self._normalize_config_type(config_type)
        base_dir = self._get_remote_config_dir(server)
        return f"{base_dir.rstrip('/')}/{filename}"

    def read_remote_config(
        self, server: RemoteServer, config_type: str
    ) -> Dict[str, Any]:
        """读取远程配置文件（opencode/oh-my-opencode/auth）。"""
        try:
            remote_path = self._get_remote_config_path(server, config_type)
            client = self._get_client(server)
            sftp = client.open_sftp()
            try:
                with sftp.open(remote_path, "r") as fp:
                    content = fp.read().decode("utf-8", errors="replace")
            finally:
                sftp.close()

            if not content.strip():
                return {}

            return json.loads(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"远程配置文件不存在: {config_type}")
        except json.JSONDecodeError as e:
            raise ValueError(f"远程配置文件 JSON 解析失败: {e}")
        except Exception as e:
            raise RuntimeError(f"读取远程配置失败: {e}")

    def write_remote_config(
        self, server: RemoteServer, config_type: str, data: Dict[str, Any]
    ) -> bool:
        """写入远程配置文件。"""
        if not isinstance(data, dict):
            raise ValueError("写入失败：data 必须为 dict")

        try:
            remote_path = self._get_remote_config_path(server, config_type)
            remote_dir = str(Path(remote_path).parent).replace("\\", "/")

            # 确保远程目录存在
            mk_cmd = f"mkdir -p {shlex.quote(remote_dir)}"
            code, _, err = self._exec(server, mk_cmd)
            if code != 0:
                raise RuntimeError(f"创建远程目录失败: {err}")

            payload = json.dumps(data, indent=2, ensure_ascii=False)
            client = self._get_client(server)
            sftp = client.open_sftp()
            try:
                with sftp.open(remote_path, "w") as fp:
                    fp.write(payload)
            finally:
                sftp.close()

            return True
        except Exception as e:
            raise RuntimeError(f"写入远程配置失败: {e}")

    def create_remote_backup(self, server: RemoteServer) -> str:
        """创建远程备份（按时间戳打包当前配置文件）。"""
        try:
            config_dir = self._get_remote_config_dir(server)
            backup_dir = f"{config_dir.rstrip('/')}/backups"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 仅备份存在的文件，避免 cp 报错
            cmd = (
                f"mkdir -p {shlex.quote(backup_dir)} && "
                f"for f in opencode.json oh-my-opencode.json auth.json; do "
                f"if [ -f {shlex.quote(config_dir)}/$f ]; then "
                f"cp {shlex.quote(config_dir)}/$f {shlex.quote(backup_dir)}/$f.{timestamp}.bak; "
                f"fi; "
                f"done"
            )
            code, _, err = self._exec(server, cmd)
            if code != 0:
                raise RuntimeError(err or "未知错误")

            return backup_dir
        except Exception as e:
            raise RuntimeError(f"创建远程备份失败: {e}")

    def list_remote_backups(self, server: RemoteServer) -> List[Dict[str, Any]]:
        """列出远程备份文件。"""
        try:
            config_dir = self._get_remote_config_dir(server)
            backup_dir = f"{config_dir.rstrip('/')}/backups"

            client = self._get_client(server)
            sftp = client.open_sftp()
            try:
                try:
                    attrs = sftp.listdir_attr(backup_dir)
                except FileNotFoundError:
                    return []

                items: List[Dict[str, Any]] = []
                for attr in attrs:
                    name = attr.filename
                    if not name.endswith(".bak"):
                        continue
                    items.append(
                        {
                            "name": name,
                            "path": f"{backup_dir}/{name}",
                            "size": attr.st_size,
                            "mtime": datetime.fromtimestamp(attr.st_mtime).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )

                items.sort(key=lambda x: x["mtime"], reverse=True)
                return items
            finally:
                sftp.close()
        except Exception as e:
            raise RuntimeError(f"列出远程备份失败: {e}")

    def get_remote_opencode_status(self, server: RemoteServer) -> Dict[str, Any]:
        """检查远程 OpenCode 运行状态。"""
        result: Dict[str, Any] = {
            "connected": False,
            "opencode_installed": False,
            "version": None,
            "process_running": False,
            "processes": [],
            "config_dir": None,
            "config_dir_exists": False,
            "error": None,
        }

        try:
            ok, msg = self.test_connection(server)
            if not ok:
                result["error"] = msg
                return result

            result["connected"] = True

            config_dir = self._get_remote_config_dir(server)
            result["config_dir"] = config_dir

            # 检测配置目录是否存在
            code, _, _ = self._exec(server, f"test -d {shlex.quote(config_dir)}")
            result["config_dir_exists"] = code == 0

            # 检测 opencode 命令
            cmd_version = (
                "sh -lc 'command -v opencode >/dev/null 2>&1 && opencode --version'"
            )
            code, out, _ = self._exec(server, cmd_version)
            if code == 0 and out.strip():
                result["opencode_installed"] = True
                result["version"] = out.strip().splitlines()[0]

            # 检测进程
            cmd_proc = "sh -lc 'pgrep -fa opencode || true'"
            _, out_proc, _ = self._exec(server, cmd_proc)
            process_lines = [
                line.strip() for line in out_proc.splitlines() if line.strip()
            ]
            result["processes"] = process_lines
            result["process_running"] = len(process_lines) > 0
            return result
        except Exception as e:
            result["error"] = f"检查远程状态失败: {e}"
            return result


class RemoteServerStore:
    """远程服务器列表本地存储。"""

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = (
            store_path
            if store_path is not None
            else Path.home() / ".config" / "opencode" / "occm-servers.json"
        )

    def _load_raw(self) -> List[Dict[str, Any]]:
        """加载原始服务器列表数据。"""
        try:
            if not self.store_path.exists():
                return []
            with open(self.store_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data
            return []
        except Exception:
            # 为保证可用性，读取失败时返回空列表，交由上层决定是否提示
            return []

    def _save_raw(self, items: List[Dict[str, Any]]) -> bool:
        """保存原始服务器列表数据。"""
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def list_servers(self, decode_password: bool = True) -> List[RemoteServer]:
        """列出所有服务器。"""
        servers: List[RemoteServer] = []
        for item in self._load_raw():
            try:
                servers.append(
                    RemoteServer.from_dict(item, decode_password=decode_password)
                )
            except Exception:
                # 单条异常不影响其他条目读取
                continue
        return servers

    def add_server(self, server: RemoteServer) -> bool:
        """新增服务器；若唯一 ID 已存在则拒绝重复。"""
        try:
            items = self._load_raw()
            existing = [RemoteServer.from_dict(i, decode_password=False) for i in items]
            if any(s.unique_id() == server.unique_id() for s in existing):
                return False

            items.append(server.to_dict(encode_password=True))
            return self._save_raw(items)
        except Exception:
            return False

    def remove_server(self, unique_id: str) -> bool:
        """按唯一 ID 删除服务器。"""
        try:
            items = self._load_raw()
            new_items: List[Dict[str, Any]] = []
            removed = False

            for item in items:
                server = RemoteServer.from_dict(item, decode_password=False)
                if server.unique_id() == unique_id:
                    removed = True
                    continue
                new_items.append(item)

            if not removed:
                return False
            return self._save_raw(new_items)
        except Exception:
            return False

    def update_server(self, unique_id: str, server: RemoteServer) -> bool:
        """按唯一 ID 更新服务器。"""
        try:
            items = self._load_raw()
            updated = False
            result_items: List[Dict[str, Any]] = []

            for item in items:
                old = RemoteServer.from_dict(item, decode_password=False)
                if old.unique_id() == unique_id:
                    result_items.append(server.to_dict(encode_password=True))
                    updated = True
                else:
                    result_items.append(item)

            if not updated:
                return False
            return self._save_raw(result_items)
        except Exception:
            return False
