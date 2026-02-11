from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .i18n import tr


@dataclass
class DiscoveredSkill:
    """发现的 Skill 信息"""

    name: str
    description: str
    path: Path
    source: str
    license_info: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    content: str = ""


class SkillDiscovery:
    """Skill 发现器 - 扫描所有路径发现已有的 Skill"""

    SKILL_PATHS = {
        "opencode-global": Path.home() / ".config" / "opencode" / "skills",
        "claude-global": Path.home() / ".claude" / "skills",
    }

    @staticmethod
    def get_project_paths() -> Dict[str, Path]:
        cwd = Path.cwd()
        return {
            "opencode-project": cwd / ".opencode" / "skills",
            "claude-project": cwd / ".claude" / "skills",
        }

    @staticmethod
    def validate_skill_name(name: str) -> Tuple[bool, str]:
        if not name:
            return False, "名称不能为空"
        if len(name) > 64:
            return False, "名称不能超过 64 字符"
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            return False, "名称格式错误：只能使用小写字母、数字、单连字符分隔"
        return True, ""

    @staticmethod
    def validate_description(desc: str) -> Tuple[bool, str]:
        if not desc:
            return False, "描述不能为空"
        if len(desc) > 1024:
            return False, "描述不能超过 1024 字符"
        return True, ""

    @staticmethod
    def parse_skill_file(skill_path: Path) -> Optional[DiscoveredSkill]:
        if not skill_path.exists():
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            return None

        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    yaml_content = parts[1].strip()
                    for line in yaml_content.split("\n"):
                        line = line.strip()
                        if ":" in line and not line.startswith("#"):
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "metadata":
                                frontmatter["metadata"] = {}
                            elif key.startswith("  ") and "metadata" in frontmatter:
                                sub_key = key.strip()
                                frontmatter["metadata"][sub_key] = value
                            else:
                                frontmatter[key] = value
                    body = parts[2].strip()
                except Exception:
                    pass

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        if not name or not description:
            return None

        skill_dir = skill_path.parent
        source = "unknown"
        for src, base_path in SkillDiscovery.SKILL_PATHS.items():
            try:
                if skill_dir.is_relative_to(base_path):
                    source = src
                    break
            except (ValueError, TypeError):
                pass

        if source == "unknown":
            for src, base_path in SkillDiscovery.get_project_paths().items():
                try:
                    if skill_dir.is_relative_to(base_path):
                        source = src
                        break
                except (ValueError, TypeError):
                    pass

        return DiscoveredSkill(
            name=name,
            description=description,
            path=skill_path,
            source=source,
            license_info=frontmatter.get("license"),
            compatibility=frontmatter.get("compatibility"),
            metadata=frontmatter.get("metadata")
            if isinstance(frontmatter.get("metadata"), dict)
            else None,
            content=body,
        )

    @classmethod
    def discover_all(cls) -> List[DiscoveredSkill]:
        skills = []
        seen_names = set()

        all_paths = {**cls.SKILL_PATHS, **cls.get_project_paths()}

        for _, base_path in all_paths.items():
            if not base_path.exists():
                continue

            try:
                for skill_dir in base_path.iterdir():
                    if not skill_dir.is_dir():
                        continue

                    skill_file = None
                    for filename in ["SKILL.md", "SKILL.txt"]:
                        potential_file = skill_dir / filename
                        if potential_file.exists():
                            skill_file = potential_file
                            break

                    if not skill_file:
                        continue

                    try:
                        skill = cls.parse_skill_file(skill_file)
                        if skill and skill.name not in seen_names:
                            skills.append(skill)
                            seen_names.add(skill.name)
                    except Exception as e:
                        print(f"解析 skill 失败 {skill_dir.name}: {e}")
                        continue
            except Exception as e:
                print(f"遍历目录失败 {base_path}: {e}")
                continue

        return skills

    @classmethod
    def get_skill_by_name(cls, name: str) -> Optional[DiscoveredSkill]:
        for skill in cls.discover_all():
            if skill.name == name:
                return skill
        return None


class SkillMarket:
    """Skill 市场 - 内置常用 Skills 列表"""

    FEATURED_SKILLS = [
        {
            "name": "ui-ux-pro-max",
            "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
            "description": "ui_ux_pro_max_desc",
            "category": "ui_ux",
            "tags": ["ui", "ux", "design", "frontend"],
            "subdir": ".claude/skills/ui-ux-pro-max",
        },
        {
            "name": "canvas-design",
            "repo": "anthropics/skills",
            "description": "canvas_design_desc",
            "category": "ui_ux",
            "tags": ["design", "canvas", "art"],
            "subdir": "skills/canvas-design",
        },
        {
            "name": "theme-factory",
            "repo": "anthropics/skills",
            "description": "theme_factory_desc",
            "category": "ui_ux",
            "tags": ["theme", "styling", "design"],
            "subdir": "skills/theme-factory",
        },
        {
            "name": "web-artifacts-builder",
            "repo": "anthropics/skills",
            "description": "web_artifacts_builder_desc",
            "category": "ui_ux",
            "tags": ["web", "react", "frontend"],
            "subdir": "skills/web-artifacts-builder",
        },
        {
            "name": "mcp-builder",
            "repo": "anthropics/skills",
            "description": "mcp_builder_desc",
            "category": "dev_tools",
            "tags": ["mcp", "server", "protocol"],
            "subdir": "skills/mcp-builder",
        },
        {
            "name": "webapp-testing",
            "repo": "anthropics/skills",
            "description": "webapp_testing_desc",
            "category": "testing",
            "tags": ["testing", "webapp", "automation"],
            "subdir": "skills/webapp-testing",
        },
        {
            "name": "skill-creator",
            "repo": "anthropics/skills",
            "description": "skill_creator_desc",
            "category": "dev_tools",
            "tags": ["skill", "creator", "development"],
            "subdir": "skills/skill-creator",
        },
        {
            "name": "algorithmic-art",
            "repo": "anthropics/skills",
            "description": "algorithmic_art_desc",
            "category": "creative",
            "tags": ["art", "generative", "creative"],
            "subdir": "skills/algorithmic-art",
        },
        {
            "name": "slack-gif-creator",
            "repo": "anthropics/skills",
            "description": "slack_gif_creator_desc",
            "category": "creative",
            "tags": ["slack", "gif", "creative"],
            "subdir": "skills/slack-gif-creator",
        },
        {
            "name": "doc-coauthoring",
            "repo": "anthropics/skills",
            "description": "doc_coauthoring_desc",
            "category": "documentation",
            "tags": ["documentation", "collaboration", "writing"],
            "subdir": "skills/doc-coauthoring",
        },
        {
            "name": "brand-guidelines",
            "repo": "anthropics/skills",
            "description": "brand_guidelines_desc",
            "category": "documentation",
            "tags": ["brand", "guidelines", "design"],
            "subdir": "skills/brand-guidelines",
        },
        {
            "name": "internal-comms",
            "repo": "anthropics/skills",
            "description": "internal_comms_desc",
            "category": "documentation",
            "tags": ["communication", "internal", "team"],
            "subdir": "skills/internal-comms",
        },
    ]

    @classmethod
    def get_all_skills(cls) -> List[Dict[str, Any]]:
        return [cls._translate_skill(s) for s in cls.FEATURED_SKILLS]

    @classmethod
    def _translate_skill(cls, skill: Dict[str, Any]) -> Dict[str, Any]:
        translated = skill.copy()
        translated["description"] = tr(f"skill.market_skills.{skill['description']}")
        translated["category"] = tr(f"skill.categories.{skill['category']}")
        return translated

    @classmethod
    def search_skills(cls, query: str) -> List[Dict[str, Any]]:
        query = query.lower()
        results = []
        for skill in cls.FEATURED_SKILLS:
            translated = cls._translate_skill(skill)
            if (
                query in skill["name"].lower()
                or query in translated["description"].lower()
                or any(query in tag for tag in skill["tags"])
            ):
                results.append(translated)
        return results

    @classmethod
    def get_by_category(cls, category: str) -> List[Dict[str, Any]]:
        all_skills = cls.get_all_skills()
        return [s for s in all_skills if s["category"] == category]

    @classmethod
    def get_categories(cls) -> List[str]:
        category_keys = set(s["category"] for s in cls.FEATURED_SKILLS)
        translated_categories = [tr(f"skill.categories.{key}") for key in category_keys]
        return sorted(translated_categories)


class SkillSecurityScanner:
    """Skill 安全扫描器 - 检测可疑代码模式"""

    DANGEROUS_PATTERNS = [
        {
            "pattern": r"os\.system\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_os_system",
        },
        {
            "pattern": r"subprocess\.(call|run|Popen)",
            "level": "high",
            "description_key": "skill.security_dialog.risk_subprocess",
        },
        {
            "pattern": r"eval\(",
            "level": "critical",
            "description_key": "skill.security_dialog.risk_eval",
        },
        {
            "pattern": r"exec\(",
            "level": "critical",
            "description_key": "skill.security_dialog.risk_exec",
        },
        {
            "pattern": r"__import__\(",
            "level": "medium",
            "description_key": "skill.security_dialog.risk_import",
        },
        {
            "pattern": r"os\.remove\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_remove",
        },
        {
            "pattern": r"shutil\.rmtree\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_rmtree",
        },
        {
            "pattern": r"requests\.(get|post|put|delete)",
            "level": "low",
            "description_key": "skill.security_dialog.risk_requests",
        },
        {
            "pattern": r"socket\.",
            "level": "medium",
            "description_key": "skill.security_dialog.risk_socket",
        },
    ]

    @classmethod
    def scan_skill(cls, skill_path: Path) -> Dict[str, Any]:
        issues = []
        score = 100

        try:
            content = skill_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for pattern_info in cls.DANGEROUS_PATTERNS:
                pattern = pattern_info["pattern"]
                level = pattern_info["level"]
                description_key = pattern_info["description_key"]

                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append(
                            {
                                "line": line_num,
                                "code": line.strip(),
                                "level": level,
                                "description_key": description_key,
                            }
                        )

                        if level == "critical":
                            score -= 30
                        elif level == "high":
                            score -= 20
                        elif level == "medium":
                            score -= 10
                        elif level == "low":
                            score -= 5

            score = max(0, score)

            return {
                "score": score,
                "issues": issues,
                "level": cls._get_risk_level(score),
            }

        except Exception as e:
            return {
                "score": 0,
                "issues": [
                    {
                        "line": 0,
                        "code": "",
                        "level": "critical",
                        "description": f"扫描失败: {str(e)}",
                    }
                ],
                "level": "unknown",
            }

    @staticmethod
    def _get_risk_level(score: int) -> str:
        if score >= 90:
            return "safe"
        elif score >= 70:
            return "low"
        elif score >= 50:
            return "medium"
        elif score >= 30:
            return "high"
        else:
            return "critical"


class SkillInstaller:
    """Skill 安装器 - 支持从 GitHub 和本地安装"""

    @staticmethod
    def detect_default_branch(owner: str, repo: str) -> str:
        import requests

        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")
        except Exception:
            pass

        for branch in ["main", "master"]:
            try:
                test_url = (
                    f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                )
                response = requests.head(test_url, timeout=5)
                if response.status_code == 200:
                    return branch
            except Exception:
                continue

        return "main"

    @staticmethod
    def parse_source(source: str) -> Tuple[str, Dict[str, str]]:
        if re.match(r"^[\w-]+/[\w-]+$", source):
            owner, repo = source.split("/")
            return "github", {
                "owner": owner,
                "repo": repo,
                "branch": "main",
                "url": f"https://github.com/{owner}/{repo}",
            }

        if source.startswith("https://github.com/"):
            match = re.match(r"https://github\.com/([\w-]+)/([\w-]+)", source)
            if match:
                owner, repo = match.groups()
                return "github", {
                    "owner": owner,
                    "repo": repo,
                    "branch": "main",
                    "url": source,
                }

        if os.path.exists(source):
            return "local", {"path": source}

        raise ValueError(f"无法识别的来源格式: {source}")

    @staticmethod
    def install_from_github(
        owner: str,
        repo: str,
        branch: str,
        target_dir: Path,
        subdir: str = None,
        progress_callback=None,
    ) -> Tuple[bool, str]:
        import tempfile
        import zipfile
        from datetime import datetime

        import requests

        try:
            if progress_callback:
                progress_callback("正在下载...")

            zip_url = (
                f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            )
            response = requests.get(zip_url, stream=True, timeout=30)

            if response.status_code == 404:
                if progress_callback:
                    progress_callback("检测分支...")
                detected_branch = SkillInstaller.detect_default_branch(owner, repo)
                if detected_branch != branch:
                    if progress_callback:
                        progress_callback(f"使用分支: {detected_branch}")
                    branch = detected_branch
                    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                    response = requests.get(zip_url, stream=True, timeout=30)

            response.raise_for_status()

            if progress_callback:
                progress_callback("正在解压...")

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "skill.zip"
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                extracted_dir = Path(temp_dir) / f"{repo}-{branch}"

                if subdir:
                    skill_dir = extracted_dir / subdir
                    if not skill_dir.exists():
                        return False, f"子目录不存在: {subdir}"
                else:
                    skill_dir = extracted_dir

                skill_file = None
                for filename in ["SKILL.md", "SKILL.txt"]:
                    potential_file = skill_dir / filename
                    if potential_file.exists():
                        skill_file = potential_file
                        break

                if not skill_file:
                    return (
                        False,
                        f"未找到 SKILL.md 或 SKILL.txt 文件{f' (在 {subdir} 中)' if subdir else ''}",
                    )

                skill = SkillDiscovery.parse_skill_file(skill_file)
                if not skill:
                    return False, "SKILL 文件格式错误"

                if progress_callback:
                    progress_callback("正在安装...")

                skill_target = target_dir / skill.name
                if skill_target.exists():
                    shutil.rmtree(skill_target)

                shutil.copytree(skill_dir, skill_target)

                commit_hash = None
                try:
                    api_url = (
                        f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
                    )
                    commit_response = requests.get(api_url, timeout=10)
                    if commit_response.status_code == 200:
                        commit_hash = commit_response.json()["sha"]
                except Exception:
                    pass

                meta = {
                    "source": "github",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "url": f"https://github.com/{owner}/{repo}",
                    "installed_at": datetime.now().isoformat(),
                    "commit_hash": commit_hash,
                }

                if subdir:
                    meta["subdir"] = subdir

                meta_file = skill_target / ".skill-meta.json"
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)

                if progress_callback:
                    progress_callback("安装完成！")

                return True, f"Skill '{skill.name}' 安装成功"

        except requests.exceptions.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"安装失败: {str(e)}"

    @staticmethod
    def install_from_local(
        source_path: str, target_dir: Path, progress_callback=None
    ) -> Tuple[bool, str]:
        from datetime import datetime

        try:
            source = Path(source_path)
            if not source.exists():
                return False, f"路径不存在: {source_path}"

            skill_md = source / "SKILL.md"
            if not skill_md.exists():
                return False, "未找到 SKILL.md 文件"

            skill = SkillDiscovery.parse_skill_file(skill_md)
            if not skill:
                return False, "SKILL.md 格式错误"

            if progress_callback:
                progress_callback("正在复制...")

            skill_target = target_dir / skill.name
            if skill_target.exists():
                shutil.rmtree(skill_target)

            shutil.copytree(source, skill_target)

            meta = {
                "source": "local",
                "original_path": str(source.absolute()),
                "installed_at": datetime.now().isoformat(),
            }

            meta_file = skill_target / ".skill-meta.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            if progress_callback:
                progress_callback("安装完成！")

            return True, f"Skill '{skill.name}' 安装成功"

        except Exception as e:
            return False, f"安装失败: {str(e)}"


class SkillUpdater:
    """Skill 更新器 - 检查和更新 Skills"""

    @staticmethod
    def check_updates(skills: List[DiscoveredSkill]) -> List[Dict[str, Any]]:
        import requests

        updates = []

        for skill in skills:
            meta_file = skill.path.parent / ".skill-meta.json"

            if not meta_file.exists():
                updates.append(
                    {
                        "skill": skill,
                        "has_update": False,
                        "current_commit": None,
                        "latest_commit": None,
                        "meta": None,
                        "status": "本地",
                    }
                )
                continue

            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                if meta.get("source") != "github":
                    updates.append(
                        {
                            "skill": skill,
                            "has_update": False,
                            "current_commit": None,
                            "latest_commit": None,
                            "meta": meta,
                            "status": "本地",
                        }
                    )
                    continue

                owner = meta["owner"]
                repo = meta["repo"]
                branch = meta.get("branch", "main")

                api_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
                )
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()

                latest_commit = response.json()["sha"]
                current_commit = meta.get("commit_hash")

                has_update = current_commit is None or current_commit != latest_commit

                updates.append(
                    {
                        "skill": skill,
                        "has_update": has_update,
                        "current_commit": current_commit[:7]
                        if current_commit
                        else "未知",
                        "latest_commit": latest_commit[:7],
                        "meta": meta,
                        "status": "有更新" if has_update else "最新",
                    }
                )

            except Exception as e:
                print(f"检查更新失败 {skill.name}: {e}")
                updates.append(
                    {
                        "skill": skill,
                        "has_update": False,
                        "current_commit": None,
                        "latest_commit": None,
                        "meta": meta if "meta" in locals() else None,
                        "status": "检查失败",
                    }
                )

        return updates

    @staticmethod
    def update_skill(
        skill: DiscoveredSkill, meta: dict, progress_callback=None
    ) -> Tuple[bool, str]:
        if meta.get("source") != "github":
            return False, "仅支持更新从 GitHub 安装的 Skills"

        try:
            target_dir = skill.path.parent.parent
            subdir = meta.get("subdir", None)

            success, message = SkillInstaller.install_from_github(
                meta["owner"],
                meta["repo"],
                meta.get("branch", "main"),
                target_dir,
                subdir=subdir,
                progress_callback=progress_callback,
            )

            return success, message

        except Exception as e:
            return False, f"更新失败: {str(e)}"
