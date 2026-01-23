#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新验证技能仓库并构建新的技能列表
"""

import sys
import io
import requests
import json
from typing import Dict, List, Tuple

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 需要验证的技能仓库列表
SKILLS_TO_VERIFY = [
    # 用户提到的仓库
    {"name": "ui-ux-pro-max", "repo": "nextlevelbuilder/ui-ux-pro-max-skill"},
    # ComposioHQ的技能（直接从仓库根目录）
    {
        "name": "connect-apps",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "connect-apps",
    },
    {
        "name": "changelog-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "changelog-generator",
    },
    {
        "name": "competitive-ads-extractor",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "competitive-ads-extractor",
    },
    {
        "name": "content-research-writer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "content-research-writer",
    },
    {
        "name": "domain-name-brainstormer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "domain-name-brainstormer",
    },
    {
        "name": "file-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "file-organizer",
    },
    {
        "name": "image-enhancer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "image-enhancer",
    },
    {
        "name": "invoice-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "invoice-organizer",
    },
    {
        "name": "lead-research-assistant",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "lead-research-assistant",
    },
    {
        "name": "meeting-insights-analyzer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "meeting-insights-analyzer",
    },
    {
        "name": "raffle-winner-picker",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "raffle-winner-picker",
    },
    {
        "name": "tailored-resume-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "tailored-resume-generator",
    },
    {
        "name": "twitter-algorithm-optimizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "twitter-algorithm-optimizer",
    },
    {
        "name": "video-downloader",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "video-downloader",
    },
    # Anthropic官方技能（保留一些核心的）
    {"name": "mcp-builder", "repo": "anthropics/skills", "path": "skills/mcp-builder"},
    {
        "name": "web-artifacts-builder",
        "repo": "anthropics/skills",
        "path": "skills/web-artifacts-builder",
    },
    {
        "name": "canvas-design",
        "repo": "anthropics/skills",
        "path": "skills/canvas-design",
    },
    {
        "name": "theme-factory",
        "repo": "anthropics/skills",
        "path": "skills/theme-factory",
    },
    {
        "name": "algorithmic-art",
        "repo": "anthropics/skills",
        "path": "skills/algorithmic-art",
    },
    {
        "name": "webapp-testing",
        "repo": "anthropics/skills",
        "path": "skills/webapp-testing",
    },
]


def check_repo_exists(repo: str) -> Tuple[bool, str]:
    """检查GitHub仓库是否存在"""
    url = f"https://api.github.com/repos/{repo}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return True, "✅ 存在"
        elif response.status_code == 404:
            return False, "❌ 404 不存在"
        else:
            return False, f"⚠️ HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"⚠️ 网络错误: {str(e)}"


def categorize_skill(name: str) -> str:
    """根据技能名称自动分类"""
    name_lower = name.lower()

    if any(
        k in name_lower
        for k in ["ui", "ux", "design", "canvas", "theme", "art", "visual"]
    ):
        return "ui_ux"
    elif any(k in name_lower for k in ["mcp", "builder", "webapp", "test", "code"]):
        return "dev_tools"
    elif any(k in name_lower for k in ["file", "organizer", "invoice", "raffle"]):
        return "productivity"
    elif any(
        k in name_lower
        for k in ["content", "writer", "twitter", "meeting", "changelog"]
    ):
        return "communication"
    elif any(k in name_lower for k in ["lead", "research", "competitive", "domain"]):
        return "business"
    elif any(k in name_lower for k in ["image", "video", "enhancer", "downloader"]):
        return "media"
    elif any(k in name_lower for k in ["resume", "tailored"]):
        return "career"
    elif any(k in name_lower for k in ["connect", "apps"]):
        return "integration"
    else:
        return "dev_tools"


def verify_and_build_list():
    """验证所有技能并构建新列表"""
    print("=" * 80)
    print("验证技能仓库")
    print("=" * 80)

    valid_skills = []
    invalid_skills = []

    for skill in SKILLS_TO_VERIFY:
        name = skill["name"]
        repo = skill["repo"]
        exists, status = check_repo_exists(repo)

        if exists:
            valid_skills.append(skill)
            print(f"{status} {name:35s} {repo}")
        else:
            invalid_skills.append(skill)
            print(f"{status} {name:35s} {repo}")

    print("\n" + "=" * 80)
    print(f"统计: 有效 {len(valid_skills)} 个, 无效 {len(invalid_skills)} 个")
    print("=" * 80)

    # 生成Python代码
    print("\n" + "=" * 80)
    print("生成的 FEATURED_SKILLS 列表")
    print("=" * 80)

    print("\nFEATURED_SKILLS = [")
    for skill in valid_skills:
        name = skill["name"]
        repo = skill["repo"]
        category = categorize_skill(name)
        desc_key = name.replace("-", "_") + "_desc"

        print("    {")
        print(f'        "name": "{name}",')
        print(f'        "repo": "{repo}",')
        print(f'        "description": "{desc_key}",')
        print(f'        "category": "{category}",')
        print(f'        "tags": ["{name.split("-")[0]}", "skill"],')

        if "path" in skill:
            print(f'        "path": "{skill["path"]}",')

        print("    },")

    print("]")

    print("\n" + "=" * 80)
    print(f"新列表包含 {len(valid_skills)} 个技能")
    print("=" * 80)

    # 生成翻译键
    print("\n" + "=" * 80)
    print("需要添加的翻译键（中文）")
    print("=" * 80)

    for skill in valid_skills:
        name = skill["name"]
        desc_key = name.replace("-", "_") + "_desc"
        # 生成简单的描述（需要后续手动完善）
        desc = f"{name.replace('-', ' ').title()} 技能"
        print(f'"{desc_key}": "{desc}",')


if __name__ == "__main__":
    print("开始验证技能仓库...\n")
    verify_and_build_list()
    print("\n✅ 验证完成！")
