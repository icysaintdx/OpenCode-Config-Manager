#!/usr/bin/env python3
"""测试 FEATURED_SKILLS 列表中的每个 skill 是否真实存在"""

import requests
import time
from typing import Dict, List, Tuple

# 从 opencode_config_manager_fluent.py 复制的 FEATURED_SKILLS 列表
FEATURED_SKILLS = [
    # UI/UX 和设计类
    {
        "name": "ui-ux-pro-max",
        "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
        "description": "ui_ux_pro_max_desc",
        "category": "ui_ux",
        "tags": ["ui", "ux", "design", "frontend"],
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
        "name": "web-artifacts-builder",
        "repo": "anthropics/skills",
        "description": "web_artifacts_builder_desc",
        "category": "ui_ux",
        "tags": ["web", "react", "frontend"],
        "path": "skills/web-artifacts-builder",
    },
    # 开发工具类
    {
        "name": "mcp-builder",
        "repo": "anthropics/skills",
        "description": "mcp_builder_desc",
        "category": "dev_tools",
        "tags": ["mcp", "server", "protocol"],
        "path": "skills/mcp-builder",
    },
    {
        "name": "webapp-testing",
        "repo": "anthropics/skills",
        "description": "webapp_testing_desc",
        "category": "testing",
        "tags": ["testing", "webapp", "automation"],
        "path": "skills/webapp-testing",
    },
    {
        "name": "skill-creator",
        "repo": "anthropics/skills",
        "description": "skill_creator_desc",
        "category": "dev_tools",
        "tags": ["skill", "creator", "development"],
        "path": "skills/skill-creator",
    },
    {
        "name": "changelog-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "changelog_generator_desc",
        "category": "dev_tools",
        "tags": ["changelog", "git", "automation"],
        "path": "changelog-generator",
    },
    # 创意和媒体类
    {
        "name": "algorithmic-art",
        "repo": "anthropics/skills",
        "description": "algorithmic_art_desc",
        "category": "creative",
        "tags": ["art", "generative", "creative"],
        "path": "skills/algorithmic-art",
    },
    {
        "name": "slack-gif-creator",
        "repo": "anthropics/skills",
        "description": "slack_gif_creator_desc",
        "category": "creative",
        "tags": ["slack", "gif", "creative"],
        "path": "skills/slack-gif-creator",
    },
    {
        "name": "image-enhancer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "image_enhancer_desc",
        "category": "media",
        "tags": ["image", "enhancement", "quality"],
        "path": "image-enhancer",
    },
    {
        "name": "video-downloader",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "video_downloader_desc",
        "category": "media",
        "tags": ["video", "download", "youtube"],
        "path": "video-downloader",
    },
    # 文档和沟通类
    {
        "name": "doc-coauthoring",
        "repo": "anthropics/skills",
        "description": "doc_coauthoring_desc",
        "category": "documentation",
        "tags": ["documentation", "collaboration", "writing"],
        "path": "skills/doc-coauthoring",
    },
    {
        "name": "brand-guidelines",
        "repo": "anthropics/skills",
        "description": "brand_guidelines_desc",
        "category": "documentation",
        "tags": ["brand", "guidelines", "design"],
        "path": "skills/brand-guidelines",
    },
    {
        "name": "internal-comms",
        "repo": "anthropics/skills",
        "description": "internal_comms_desc",
        "category": "documentation",
        "tags": ["communication", "internal", "team"],
        "path": "skills/internal-comms",
    },
    {
        "name": "content-research-writer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "content_research_writer_desc",
        "category": "communication",
        "tags": ["content", "research", "writing"],
        "path": "content-research-writer",
    },
    {
        "name": "meeting-insights-analyzer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "meeting_insights_analyzer_desc",
        "category": "communication",
        "tags": ["meeting", "insights", "analysis"],
        "path": "meeting-insights-analyzer",
    },
    {
        "name": "twitter-algorithm-optimizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "twitter_algorithm_optimizer_desc",
        "category": "communication",
        "tags": ["twitter", "social", "optimization"],
        "path": "twitter-algorithm-optimizer",
    },
    # 商业和营销类
    {
        "name": "competitive-ads-extractor",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "competitive_ads_extractor_desc",
        "category": "business",
        "tags": ["competitive", "ads", "marketing"],
        "path": "competitive-ads-extractor",
    },
    {
        "name": "domain-name-brainstormer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "domain_name_brainstormer_desc",
        "category": "business",
        "tags": ["domain", "naming", "brainstorm"],
        "path": "domain-name-brainstormer",
    },
    {
        "name": "lead-research-assistant",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "lead_research_assistant_desc",
        "category": "business",
        "tags": ["lead", "research", "assistant"],
        "path": "lead-research-assistant",
    },
    # 生产力类
    {
        "name": "email-assistant",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "email_assistant_desc",
        "category": "productivity",
        "tags": ["email", "assistant", "automation"],
        "path": "email-assistant",
    },
    {
        "name": "calendar-scheduler",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "calendar_scheduler_desc",
        "category": "productivity",
        "tags": ["calendar", "scheduling", "automation"],
        "path": "calendar-scheduler",
    },
    {
        "name": "task-manager",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "task_manager_desc",
        "category": "productivity",
        "tags": ["task", "management", "productivity"],
        "path": "task-manager",
    },
    # 职业发展类
    {
        "name": "resume-builder",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "resume_builder_desc",
        "category": "career",
        "tags": ["resume", "career", "job"],
        "path": "resume-builder",
    },
    # 应用集成类
    {
        "name": "connect-apps",
        "repo": "ComposioHQ/connect-apps",
        "description": "connect_apps_desc",
        "category": "integration",
        "tags": ["integration", "apps", "automation"],
    },
]


def detect_default_branch(owner: str, repo: str) -> Tuple[str, str]:
    """检测GitHub仓库的默认分支

    Returns:
        (branch_name, status_message)
    """
    try:
        # 尝试通过 GitHub API 获取仓库信息
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            branch = data.get("default_branch", "main")
            return branch, f"✓ API检测: {branch}"
        elif response.status_code == 404:
            return "", "✗ 仓库不存在 (404)"
        else:
            return "", f"✗ API错误: {response.status_code}"
    except Exception as e:
        return "", f"✗ 网络错误: {str(e)}"


def check_skill_file(
    owner: str, repo: str, branch: str, subdir: str = None
) -> Tuple[bool, str]:
    """检查 SKILL.md 或 SKILL.txt 是否存在

    Returns:
        (exists, status_message)
    """
    base_path = f"{subdir}/" if subdir else ""

    # 尝试 SKILL.md
    for filename in ["SKILL.md", "SKILL.txt"]:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{base_path}{filename}"
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                return True, f"✓ 找到 {filename}"
        except Exception:
            pass

    return False, "✗ 未找到 SKILL.md 或 SKILL.txt"


def test_skill(skill: Dict) -> Dict:
    """测试单个 skill

    Returns:
        测试结果字典
    """
    name = skill["name"]
    repo = skill["repo"]
    subdir = skill.get("path", None)

    print(f"\n{'=' * 80}")
    print(f"测试: {name}")
    print(f"仓库: {repo}")
    if subdir:
        print(f"子目录: {subdir}")

    owner, repo_name = repo.split("/")

    # 1. 检测分支
    branch, branch_msg = detect_default_branch(owner, repo_name)
    print(f"  分支检测: {branch_msg}")

    if not branch:
        return {
            "name": name,
            "repo": repo,
            "subdir": subdir,
            "status": "FAIL",
            "reason": branch_msg,
        }

    # 2. 检查 SKILL 文件
    has_skill, skill_msg = check_skill_file(owner, repo_name, branch, subdir)
    print(f"  SKILL文件: {skill_msg}")

    if not has_skill:
        return {
            "name": name,
            "repo": repo,
            "subdir": subdir,
            "branch": branch,
            "status": "FAIL",
            "reason": skill_msg,
        }

    return {
        "name": name,
        "repo": repo,
        "subdir": subdir,
        "branch": branch,
        "status": "OK",
        "reason": "所有检查通过",
    }


def main():
    """主函数"""
    print("开始测试 FEATURED_SKILLS 列表...")
    print(f"总共 {len(FEATURED_SKILLS)} 个 skills")

    results = []
    for i, skill in enumerate(FEATURED_SKILLS, 1):
        print(f"\n[{i}/{len(FEATURED_SKILLS)}]", end=" ")
        result = test_skill(skill)
        results.append(result)
        time.sleep(0.5)  # 避免 GitHub API 限流

    # 统计结果
    print(f"\n\n{'=' * 80}")
    print("测试结果汇总:")
    print(f"{'=' * 80}\n")

    ok_count = sum(1 for r in results if r["status"] == "OK")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    print(f"✓ 成功: {ok_count}/{len(results)}")
    print(f"✗ 失败: {fail_count}/{len(results)}")

    if fail_count > 0:
        print(f"\n失败的 skills:")
        print(f"{'-' * 80}")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ✗ {r['name']}")
                print(f"    仓库: {r['repo']}")
                if r.get("subdir"):
                    print(f"    子目录: {r['subdir']}")
                print(f"    原因: {r['reason']}")
                print()

    # 生成修复后的列表
    print(f"\n{'=' * 80}")
    print("修复建议:")
    print(f"{'=' * 80}\n")

    valid_skills = [r for r in results if r["status"] == "OK"]
    print(f"保留 {len(valid_skills)} 个有效的 skills")
    print(f"移除 {fail_count} 个无效的 skills")

    # 保存结果到文件
    with open("D:\\opcdcfg\\skill_test_results.txt", "w", encoding="utf-8") as f:
        f.write("FEATURED_SKILLS 测试结果\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"总计: {len(results)} 个 skills\n")
        f.write(f"成功: {ok_count} 个\n")
        f.write(f"失败: {fail_count} 个\n\n")

        f.write("详细结果:\n")
        f.write("-" * 80 + "\n\n")

        for r in results:
            f.write(f"名称: {r['name']}\n")
            f.write(f"仓库: {r['repo']}\n")
            if r.get("subdir"):
                f.write(f"子目录: {r['subdir']}\n")
            if r.get("branch"):
                f.write(f"分支: {r['branch']}\n")
            f.write(f"状态: {r['status']}\n")
            f.write(f"原因: {r['reason']}\n")
            f.write("\n")

    print(f"\n详细结果已保存到: D:\\opcdcfg\\skill_test_results.txt")


if __name__ == "__main__":
    main()
