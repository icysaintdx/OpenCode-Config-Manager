#!/usr/bin/env python3
"""
验证所有 FEATURED_SKILLS 的分支和路径
"""

import requests
import time

# 从 opencode_config_manager_fluent.py 复制的 FEATURED_SKILLS 列表
FEATURED_SKILLS = [
    # UI/UX 和设计类
    {
        "name": "ui-ux-pro-max",
        "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
        "path": ".opencode/skills/ui-ux-pro-max",
        "expected_branch": "main",
    },
    {
        "name": "canvas-design",
        "repo": "anthropics/skills",
        "path": "skills/canvas-design",
        "expected_branch": "main",
    },
    {
        "name": "theme-factory",
        "repo": "anthropics/skills",
        "path": "skills/theme-factory",
        "expected_branch": "main",
    },
    {
        "name": "web-artifacts-builder",
        "repo": "anthropics/skills",
        "path": "skills/web-artifacts-builder",
        "expected_branch": "main",
    },
    # 开发工具类
    {
        "name": "mcp-builder",
        "repo": "anthropics/skills",
        "path": "skills/mcp-builder",
        "expected_branch": "main",
    },
    {
        "name": "webapp-testing",
        "repo": "anthropics/skills",
        "path": "skills/webapp-testing",
        "expected_branch": "main",
    },
    {
        "name": "skill-creator",
        "repo": "anthropics/skills",
        "path": "skills/skill-creator",
        "expected_branch": "main",
    },
    {
        "name": "changelog-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "changelog-generator",
        "expected_branch": "master",
    },
    # 创意和媒体类
    {
        "name": "algorithmic-art",
        "repo": "anthropics/skills",
        "path": "skills/algorithmic-art",
        "expected_branch": "main",
    },
    {
        "name": "slack-gif-creator",
        "repo": "anthropics/skills",
        "path": "skills/slack-gif-creator",
        "expected_branch": "main",
    },
    {
        "name": "image-enhancer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "image-enhancer",
        "expected_branch": "master",
    },
    {
        "name": "video-downloader",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "video-downloader",
        "expected_branch": "master",
    },
    # 文档和沟通类
    {
        "name": "doc-coauthoring",
        "repo": "anthropics/skills",
        "path": "skills/doc-coauthoring",
        "expected_branch": "main",
    },
    {
        "name": "brand-guidelines",
        "repo": "anthropics/skills",
        "path": "skills/brand-guidelines",
        "expected_branch": "main",
    },
    {
        "name": "internal-comms",
        "repo": "anthropics/skills",
        "path": "skills/internal-comms",
        "expected_branch": "main",
    },
    {
        "name": "content-research-writer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "content-research-writer",
        "expected_branch": "master",
    },
    {
        "name": "meeting-insights-analyzer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "meeting-insights-analyzer",
        "expected_branch": "master",
    },
    {
        "name": "twitter-algorithm-optimizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "twitter-algorithm-optimizer",
        "expected_branch": "master",
    },
    # 商业和营销类
    {
        "name": "competitive-ads-extractor",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "competitive-ads-extractor",
        "expected_branch": "master",
    },
    {
        "name": "domain-name-brainstormer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "domain-name-brainstormer",
        "expected_branch": "master",
    },
    # 生产力和组织类
    {
        "name": "file-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "file-organizer",
        "expected_branch": "master",
    },
    {
        "name": "invoice-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "invoice-organizer",
        "expected_branch": "master",
    },
    {
        "name": "raffle-winner-picker",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "raffle-winner-picker",
        "expected_branch": "master",
    },
    # 职业发展类
    {
        "name": "tailored-resume-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "tailored-resume-generator",
        "expected_branch": "master",
    },
    # 集成和连接类
    {
        "name": "connect-apps",
        "repo": "ComposioHQ/awesome-claude-skills",
        "path": "connect-apps",
        "expected_branch": "master",
    },
]


def verify_skill(skill):
    """验证单个 skill"""
    name = skill["name"]
    repo = skill["repo"]
    path = skill["path"]
    expected_branch = skill["expected_branch"]

    owner, repo_name = repo.split("/")

    # 尝试 SKILL.md
    url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{expected_branch}/{path}/SKILL.md"
    try:
        r = requests.head(url, timeout=10)
        if r.status_code == 200:
            return True, f"OK ({expected_branch})"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

    # 尝试 SKILL.txt
    url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{expected_branch}/{path}/SKILL.txt"
    try:
        r = requests.head(url, timeout=10)
        if r.status_code == 200:
            return True, f"OK ({expected_branch}, SKILL.txt)"
    except Exception as e:
        pass

    return False, f"FAIL: 404 on {expected_branch}"


def main():
    """主函数"""
    print("=" * 80)
    print("验证所有 FEATURED_SKILLS")
    print("=" * 80)
    print()

    results = []

    for skill in FEATURED_SKILLS:
        success, message = verify_skill(skill)
        results.append((skill["name"], success, message))

        status_icon = "✓" if success else "✗"
        print(f"{status_icon} {skill['name']:35} {message}")

        time.sleep(0.3)  # 避免 API 限流

    # 统计
    print()
    print("=" * 80)
    print("统计结果")
    print("=" * 80)

    total = len(results)
    success_count = sum(1 for _, success, _ in results if success)
    fail_count = total - success_count

    print(f"总计: {total}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")

    if fail_count > 0:
        print()
        print("失败的 skills:")
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
