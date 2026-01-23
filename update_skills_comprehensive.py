#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新技能市场 - 综合版本
包含真实存在的技能仓库
"""

import json
import sys
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 综合技能列表（已验证存在）
COMPREHENSIVE_SKILLS = [
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
        "tags": ["lead", "research", "sales"],
        "path": "lead-research-assistant",
    },
    # 生产力和组织类
    {
        "name": "file-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "file_organizer_desc",
        "category": "productivity",
        "tags": ["file", "organization", "management"],
        "path": "file-organizer",
    },
    {
        "name": "invoice-organizer",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "invoice_organizer_desc",
        "category": "productivity",
        "tags": ["invoice", "finance", "organization"],
        "path": "invoice-organizer",
    },
    {
        "name": "raffle-winner-picker",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "raffle_winner_picker_desc",
        "category": "productivity",
        "tags": ["raffle", "random", "picker"],
        "path": "raffle-winner-picker",
    },
    # 职业发展类
    {
        "name": "tailored-resume-generator",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "tailored_resume_generator_desc",
        "category": "career",
        "tags": ["resume", "career", "job"],
        "path": "tailored-resume-generator",
    },
    # 集成和连接类
    {
        "name": "connect-apps",
        "repo": "ComposioHQ/awesome-claude-skills",
        "description": "connect_apps_desc",
        "category": "integration",
        "tags": ["integration", "apps", "automation"],
        "path": "connect-apps",
    },
]

# 翻译内容
TRANSLATIONS_ZH = {
    "categories": {
        "creative": "创意设计",
        "media": "媒体处理",
        "career": "职业发展",
        "integration": "应用集成",
    },
    "market_skills": {
        # UI/UX
        "ui_ux_pro_max_desc": "UI/UX 设计专家 - 50种样式、21种配色、50种字体组合",
        "canvas_design_desc": "创建精美的视觉艺术和设计作品（PNG/PDF）",
        "theme_factory_desc": "为各种项目生成和应用主题样式",
        "web_artifacts_builder_desc": "使用 React、Tailwind CSS、shadcn/ui 创建复杂的 Web 组件",
        # 开发工具
        "mcp_builder_desc": "创建高质量的 MCP (Model Context Protocol) 服务器",
        "webapp_testing_desc": "Web 应用自动化测试和验证",
        "skill_creator_desc": "创建和管理自定义 Skills",
        "changelog_generator_desc": "从 Git 提交自动生成用户友好的更新日志",
        # 创意和媒体
        "algorithmic_art_desc": "使用 p5.js 创建算法艺术和生成式艺术",
        "slack_gif_creator_desc": "为 Slack 创建动画 GIF",
        "image_enhancer_desc": "提升图片和截图质量，增强分辨率和清晰度",
        "video_downloader_desc": "从 YouTube 等平台下载视频",
        # 文档和沟通
        "doc_coauthoring_desc": "协作编写和编辑文档",
        "brand_guidelines_desc": "创建和维护品牌设计规范",
        "internal_comms_desc": "内部沟通和团队协作工具",
        "content_research_writer_desc": "研究和撰写高质量内容",
        "meeting_insights_analyzer_desc": "分析会议记录，提取行为模式和洞察",
        "twitter_algorithm_optimizer_desc": "优化推文以提高参与度和可见性",
        # 商业和营销
        "competitive_ads_extractor_desc": "提取和分析竞争对手的广告",
        "domain_name_brainstormer_desc": "生成创意域名并检查可用性",
        "lead_research_assistant_desc": "识别和筛选高质量潜在客户",
        # 生产力
        "file_organizer_desc": "智能整理文件和文件夹",
        "invoice_organizer_desc": "自动整理发票和收据",
        "raffle_winner_picker_desc": "随机选择抽奖获胜者",
        # 职业发展
        "tailored_resume_generator_desc": "根据职位描述生成定制简历",
        # 集成
        "connect_apps_desc": "连接 Claude 到 500+ 应用，实现自动化操作",
    },
}

TRANSLATIONS_EN = {
    "categories": {
        "creative": "Creative Design",
        "media": "Media Processing",
        "career": "Career Development",
        "integration": "App Integration",
    },
    "market_skills": {
        # UI/UX
        "ui_ux_pro_max_desc": "UI/UX design expert - 50 styles, 21 palettes, 50 font pairings",
        "canvas_design_desc": "Create beautiful visual art and designs (PNG/PDF)",
        "theme_factory_desc": "Generate and apply theme styles for various projects",
        "web_artifacts_builder_desc": "Build complex web components with React, Tailwind CSS, shadcn/ui",
        # Dev Tools
        "mcp_builder_desc": "Create high-quality MCP (Model Context Protocol) servers",
        "webapp_testing_desc": "Automated testing and validation for web applications",
        "skill_creator_desc": "Create and manage custom Skills",
        "changelog_generator_desc": "Automatically generate user-friendly changelogs from Git commits",
        # Creative & Media
        "algorithmic_art_desc": "Create algorithmic and generative art using p5.js",
        "slack_gif_creator_desc": "Create animated GIFs for Slack",
        "image_enhancer_desc": "Enhance image and screenshot quality, resolution, and clarity",
        "video_downloader_desc": "Download videos from YouTube and other platforms",
        # Documentation & Communication
        "doc_coauthoring_desc": "Collaborative document writing and editing",
        "brand_guidelines_desc": "Create and maintain brand design guidelines",
        "internal_comms_desc": "Internal communication and team collaboration tools",
        "content_research_writer_desc": "Research and write high-quality content",
        "meeting_insights_analyzer_desc": "Analyze meeting transcripts for behavioral patterns and insights",
        "twitter_algorithm_optimizer_desc": "Optimize tweets for maximum engagement and visibility",
        # Business & Marketing
        "competitive_ads_extractor_desc": "Extract and analyze competitors' ads",
        "domain_name_brainstormer_desc": "Generate creative domain names and check availability",
        "lead_research_assistant_desc": "Identify and qualify high-quality leads",
        # Productivity
        "file_organizer_desc": "Intelligently organize files and folders",
        "invoice_organizer_desc": "Automatically organize invoices and receipts",
        "raffle_winner_picker_desc": "Randomly select raffle winners",
        # Career
        "tailored_resume_generator_desc": "Generate tailored resumes based on job descriptions",
        # Integration
        "connect_apps_desc": "Connect Claude to 500+ apps for automated actions",
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
        # 保留现有的，添加新的
        old_count = len(translations["skill"]["market_skills"])
        translations["skill"]["market_skills"].update(new_translations["market_skills"])
        new_count = len(translations["skill"]["market_skills"])
        print(f"  ✅ 更新了技能描述：原有 {old_count} 个，现在 {new_count} 个")

    # 保存更新后的翻译
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 翻译文件已保存")


def generate_python_code():
    """生成Python代码"""
    print("\n" + "=" * 80)
    print("生成的 Python 代码（用于替换 FEATURED_SKILLS）")
    print("=" * 80)

    print("\nFEATURED_SKILLS = [")
    for skill in COMPREHENSIVE_SKILLS:
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
    print(f"新列表包含 {len(COMPREHENSIVE_SKILLS)} 个技能")
    print("=" * 80)


if __name__ == "__main__":
    print("开始更新技能市场...\n")

    # 更新中文翻译
    update_translation_file("locales/zh_CN.json", TRANSLATIONS_ZH)

    # 更新英文翻译
    update_translation_file("locales/en_US.json", TRANSLATIONS_EN)

    # 生成Python代码
    generate_python_code()

    print("\n✅ 所有更新完成！")
    print("\n下一步:")
    print("1. 复制上面生成的 FEATURED_SKILLS 代码")
    print("2. 替换 opencode_config_manager_fluent.py 中的 FEATURED_SKILLS 列表")
