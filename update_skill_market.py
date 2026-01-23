#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新技能市场列表和翻译文件
"""

import json
import sys
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 新的技能列表（全部来自Anthropic官方仓库）
NEW_FEATURED_SKILLS = [
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
    {
        "name": "frontend-design",
        "repo": "anthropics/skills",
        "description": "frontend_design_desc",
        "category": "ui_ux",
        "tags": ["frontend", "design", "ui"],
        "path": "skills/frontend-design",
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
        "name": "slack-gif-creator",
        "repo": "anthropics/skills",
        "description": "slack_gif_creator_desc",
        "category": "creative",
        "tags": ["slack", "gif", "creative"],
        "path": "skills/slack-gif-creator",
    },
]

# 新的翻译条目
NEW_TRANSLATIONS_ZH = {
    "categories": {"creative": "创意设计"},
    "market_skills": {
        "mcp_builder_desc": "创建高质量的 MCP (Model Context Protocol) 服务器",
        "web_artifacts_builder_desc": "使用 React、Tailwind CSS、shadcn/ui 创建复杂的 Web 组件",
        "canvas_design_desc": "创建精美的视觉艺术和设计作品（PNG/PDF）",
        "theme_factory_desc": "为各种项目生成和应用主题样式",
        "algorithmic_art_desc": "使用 p5.js 创建算法艺术和生成式艺术",
        "frontend_design_desc": "前端设计和 UI 组件开发",
        "webapp_testing_desc": "Web 应用自动化测试和验证",
        "skill_creator_desc": "创建和管理自定义 Skills",
        "doc_coauthoring_desc": "协作编写和编辑文档",
        "brand_guidelines_desc": "创建和维护品牌设计规范",
        "internal_comms_desc": "内部沟通和团队协作工具",
        "slack_gif_creator_desc": "为 Slack 创建动画 GIF",
    },
}

NEW_TRANSLATIONS_EN = {
    "categories": {"creative": "Creative Design"},
    "market_skills": {
        "mcp_builder_desc": "Create high-quality MCP (Model Context Protocol) servers",
        "web_artifacts_builder_desc": "Build complex web components with React, Tailwind CSS, shadcn/ui",
        "canvas_design_desc": "Create beautiful visual art and designs (PNG/PDF)",
        "theme_factory_desc": "Generate and apply theme styles for various projects",
        "algorithmic_art_desc": "Create algorithmic and generative art using p5.js",
        "frontend_design_desc": "Frontend design and UI component development",
        "webapp_testing_desc": "Automated testing and validation for web applications",
        "skill_creator_desc": "Create and manage custom Skills",
        "doc_coauthoring_desc": "Collaborative document writing and editing",
        "brand_guidelines_desc": "Create and maintain brand design guidelines",
        "internal_comms_desc": "Internal communication and team collaboration tools",
        "slack_gif_creator_desc": "Create animated GIFs for Slack",
    },
}


def update_translation_file(file_path: str, new_translations: dict):
    """更新翻译文件"""
    print(f"\n正在更新翻译文件: {file_path}")

    # 读取现有翻译
    with open(file_path, "r", encoding="utf-8") as f:
        translations = json.load(f)

    # 更新 categories
    if "skill" in translations and "categories" in translations["skill"]:
        translations["skill"]["categories"].update(new_translations["categories"])
        print(f"  ✅ 更新了 {len(new_translations['categories'])} 个分类")

    # 更新 market_skills
    if "skill" in translations and "market_skills" in translations["skill"]:
        # 清空旧的技能描述
        old_count = len(translations["skill"]["market_skills"])
        translations["skill"]["market_skills"] = new_translations["market_skills"]
        print(
            f"  ✅ 替换了 {old_count} 个旧技能描述，添加了 {len(new_translations['market_skills'])} 个新技能描述"
        )

    # 保存更新后的翻译
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 翻译文件已保存")


def generate_python_code():
    """生成Python代码"""
    print("\n" + "=" * 80)
    print(
        "生成的 Python 代码（用于替换 opencode_config_manager_fluent.py 中的 FEATURED_SKILLS）"
    )
    print("=" * 80)

    print("\nFEATURED_SKILLS = [")
    for skill in NEW_FEATURED_SKILLS:
        print("    {")
        print(f'        "name": "{skill["name"]}",')
        print(f'        "repo": "{skill["repo"]}",')
        print(f'        "description": "{skill["description"]}",')
        print(f'        "category": "{skill["category"]}",')
        print(f'        "tags": {skill["tags"]},')
        if "path" in skill:
            print(f'        "path": "{skill["path"]}",')
        print("    },")
    print("]")

    print("\n" + "=" * 80)
    print(f"新列表包含 {len(NEW_FEATURED_SKILLS)} 个技能")
    print("=" * 80)


if __name__ == "__main__":
    print("开始更新技能市场列表和翻译文件...\n")

    # 更新中文翻译
    update_translation_file("locales/zh_CN.json", NEW_TRANSLATIONS_ZH)

    # 更新英文翻译
    update_translation_file("locales/en_US.json", NEW_TRANSLATIONS_EN)

    # 生成Python代码
    generate_python_code()

    print("\n✅ 所有更新完成！")
    print("\n下一步:")
    print("1. 复制上面生成的 FEATURED_SKILLS 代码")
    print(
        "2. 替换 opencode_config_manager_fluent.py 中的 FEATURED_SKILLS 列表（约第 13057 行）"
    )
    print("3. 修改技能安装逻辑，支持从 anthropics/skills 仓库的子目录安装")
