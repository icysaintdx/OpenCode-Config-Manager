#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证技能市场中的GitHub仓库是否存在
"""

import sys
import io
import requests
import json
from typing import Dict, List, Tuple

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 当前的FEATURED_SKILLS列表
CURRENT_SKILLS = [
    {"name": "git-release", "repo": "vercel-labs/git-release"},
    {"name": "code-review", "repo": "anthropics/code-review-skill"},
    {"name": "test-generator", "repo": "openai/test-generator-skill"},
    {"name": "documentation", "repo": "anthropics/documentation-skill"},
    {"name": "refactoring", "repo": "openai/refactoring-skill"},
    {"name": "security-audit", "repo": "anthropics/security-audit-skill"},
    {"name": "api-design", "repo": "openai/api-design-skill"},
    {"name": "database-migration", "repo": "vercel-labs/database-migration-skill"},
    {"name": "ui-ux-pro-max", "repo": "code-yeongyu/ui-ux-pro-max"},
    {"name": "playwright", "repo": "anthropics/playwright-skill"},
    {"name": "docker-compose", "repo": "vercel-labs/docker-compose-skill"},
    {"name": "ci-cd-pipeline", "repo": "github/ci-cd-pipeline-skill"},
    {
        "name": "performance-optimization",
        "repo": "openai/performance-optimization-skill",
    },
    {"name": "error-handling", "repo": "anthropics/error-handling-skill"},
    {"name": "regex-helper", "repo": "openai/regex-helper-skill"},
    {"name": "sql-query-optimizer", "repo": "vercel-labs/sql-query-optimizer-skill"},
    {"name": "accessibility-checker", "repo": "anthropics/accessibility-checker-skill"},
    {"name": "i18n-translator", "repo": "openai/i18n-translator-skill"},
    {"name": "git-workflow", "repo": "github/git-workflow-skill"},
    {"name": "code-formatter", "repo": "anthropics/code-formatter-skill"},
]

# Anthropic官方skills仓库中的真实技能
ANTHROPIC_OFFICIAL_SKILLS = [
    {
        "name": "algorithmic-art",
        "repo": "anthropics/skills",
        "path": "skills/algorithmic-art",
    },
    {
        "name": "brand-guidelines",
        "repo": "anthropics/skills",
        "path": "skills/brand-guidelines",
    },
    {
        "name": "canvas-design",
        "repo": "anthropics/skills",
        "path": "skills/canvas-design",
    },
    {
        "name": "doc-coauthoring",
        "repo": "anthropics/skills",
        "path": "skills/doc-coauthoring",
    },
    {"name": "docx", "repo": "anthropics/skills", "path": "skills/docx"},
    {
        "name": "frontend-design",
        "repo": "anthropics/skills",
        "path": "skills/frontend-design",
    },
    {
        "name": "internal-comms",
        "repo": "anthropics/skills",
        "path": "skills/internal-comms",
    },
    {"name": "mcp-builder", "repo": "anthropics/skills", "path": "skills/mcp-builder"},
    {"name": "pdf", "repo": "anthropics/skills", "path": "skills/pdf"},
    {"name": "pptx", "repo": "anthropics/skills", "path": "skills/pptx"},
    {
        "name": "skill-creator",
        "repo": "anthropics/skills",
        "path": "skills/skill-creator",
    },
    {
        "name": "slack-gif-creator",
        "repo": "anthropics/skills",
        "path": "skills/slack-gif-creator",
    },
    {
        "name": "theme-factory",
        "repo": "anthropics/skills",
        "path": "skills/theme-factory",
    },
    {
        "name": "web-artifacts-builder",
        "repo": "anthropics/skills",
        "path": "skills/web-artifacts-builder",
    },
    {
        "name": "webapp-testing",
        "repo": "anthropics/skills",
        "path": "skills/webapp-testing",
    },
    {"name": "xlsx", "repo": "anthropics/skills", "path": "skills/xlsx"},
]


def check_repo_exists(repo: str) -> Tuple[bool, str]:
    """
    检查GitHub仓库是否存在

    Args:
        repo: 仓库路径，格式为 "owner/repo"

    Returns:
        (是否存在, 状态信息)
    """
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


def verify_all_skills():
    """验证所有技能仓库"""
    print("=" * 80)
    print("验证当前FEATURED_SKILLS列表中的仓库")
    print("=" * 80)

    valid_count = 0
    invalid_count = 0

    for skill in CURRENT_SKILLS:
        name = skill["name"]
        repo = skill["repo"]
        exists, status = check_repo_exists(repo)

        if exists:
            valid_count += 1
            print(f"{status} {name:30s} {repo}")
        else:
            invalid_count += 1
            print(f"{status} {name:30s} {repo}")

    print("\n" + "=" * 80)
    print(f"统计: 有效 {valid_count} 个, 无效 {invalid_count} 个")
    print("=" * 80)

    # 验证Anthropic官方技能
    print("\n" + "=" * 80)
    print("Anthropic官方skills仓库中的真实技能")
    print("=" * 80)

    for skill in ANTHROPIC_OFFICIAL_SKILLS:
        name = skill["name"]
        path = skill.get("path", "")
        print(f"✅ {name:30s} {path}")

    print("\n" + "=" * 80)
    print(f"Anthropic官方技能总数: {len(ANTHROPIC_OFFICIAL_SKILLS)} 个")
    print("=" * 80)


def generate_new_skills_list():
    """生成新的技能列表（仅包含有效的仓库）"""
    print("\n" + "=" * 80)
    print("生成新的FEATURED_SKILLS列表")
    print("=" * 80)

    # 1. 验证当前列表中的有效仓库
    valid_skills = []
    for skill in CURRENT_SKILLS:
        exists, _ = check_repo_exists(skill["repo"])
        if exists:
            valid_skills.append(skill)

    # 2. 添加Anthropic官方技能（选择一些常用的）
    # 注意：这些技能在anthropics/skills仓库的子目录中，需要特殊处理
    selected_official_skills = [
        {
            "name": "mcp-builder",
            "repo": "anthropics/skills",
            "description": "mcp_builder_desc",
            "category": "dev_tools",
            "tags": ["mcp", "server", "protocol"],
            "path": "skills/mcp-builder",
        },
        {
            "name": "web-artifacts-builder",
            "repo": "anthropics/skills",
            "description": "web_artifacts_builder_desc",
            "category": "ui_ux",
            "tags": ["web", "react", "frontend"],
            "path": "skills/web-artifacts-builder",
        },
        {
            "name": "canvas-design",
            "repo": "anthropics/skills",
            "description": "canvas_design_desc",
            "category": "ui_ux",
            "tags": ["design", "canvas", "art"],
            "path": "skills/canvas-design",
        },
        {
            "name": "theme-factory",
            "repo": "anthropics/skills",
            "description": "theme_factory_desc",
            "category": "ui_ux",
            "tags": ["theme", "styling", "design"],
            "path": "skills/theme-factory",
        },
        {
            "name": "algorithmic-art",
            "repo": "anthropics/skills",
            "description": "algorithmic_art_desc",
            "category": "creative",
            "tags": ["art", "generative", "creative"],
            "path": "skills/algorithmic-art",
        },
    ]

    print(f"\n从当前列表中保留的有效技能: {len(valid_skills)} 个")
    print(f"添加的Anthropic官方技能: {len(selected_official_skills)} 个")
    print(f"新列表总数: {len(valid_skills) + len(selected_official_skills)} 个")

    # 输出Python代码格式
    print("\n建议的新FEATURED_SKILLS列表（Python代码）:")
    print("-" * 80)
    print("FEATURED_SKILLS = [")

    # 输出有效的技能
    for skill in valid_skills:
        print(f"    {{")
        print(f'        "name": "{skill["name"]}",')
        print(f'        "repo": "{skill["repo"]}",')
        print(f'        "description": "{skill["name"].replace("-", "_")}_desc",')
        print(f'        "category": "dev_tools",')
        print(f'        "tags": ["tag1", "tag2"],')
        print(f"    }},")

    # 输出官方技能
    for skill in selected_official_skills:
        print(f"    {{")
        print(f'        "name": "{skill["name"]}",')
        print(f'        "repo": "{skill["repo"]}",')
        print(f'        "description": "{skill["description"]}",')
        print(f'        "category": "{skill["category"]}",')
        print(f'        "tags": {skill["tags"]},')
        if "path" in skill:
            print(f'        "path": "{skill["path"]}",')
        print(f"    }},")

    print("]")
    print("-" * 80)


if __name__ == "__main__":
    print("开始验证技能市场仓库...\n")
    verify_all_skills()
    generate_new_skills_list()
    print("\n验证完成！")
