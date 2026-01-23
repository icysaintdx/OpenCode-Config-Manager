#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新帮助页面翻译"""

import json
from pathlib import Path

# 英文翻译
en_help_additions = {
    "priority_content": "1. Remote Configuration\n   Configuration obtained through API or remote server\n   Highest priority, overrides all local configurations\n\n2. Global Configuration\n   Location: ~/.config/opencode/opencode.json\n   Default configuration affecting all projects\n\n3. Custom Configuration\n   Configuration file specified via --config parameter\n   Used for specific scenario configuration overrides\n\n4. Project Configuration\n   Location: <project root>/opencode.json\n   Project-level configuration, affects current project only\n\n5. .opencode Directory Configuration\n   Location: <project root>/.opencode/config.json\n   Hidden configuration directory within project\n\n6. Inline Configuration\n   Configuration specified directly via command line parameters\n   Lowest priority, but most flexible\n\nConfiguration Merge Rules:\n- Higher priority configurations override lower priority ones with the same name\n- Unspecified configuration items inherit values from lower priorities\n- Provider and Model configurations are deeply merged",
    "usage_content": "1. Provider Management\n   Add custom API providers\n   Configure API addresses and keys\n   Support multiple SDKs: @ai-sdk/anthropic, @ai-sdk/openai, etc.\n\n2. Model Management\n   Add models under Provider\n   Support quick selection of preset common models\n   Configure model parameters (context limits, output limits, etc.)\n\n3. Agent Management (Oh My OpenCode)\n   Configure Agents for different purposes\n   Bind configured Provider/Model\n   Support preset Agent templates\n\n4. Category Management (Oh My OpenCode)\n   Configure task categories\n   Set Temperature for different categories\n   Bind corresponding models\n\n5. Permission Management\n   Configure tool usage permissions\n   allow: Allow usage\n   ask: Ask each time\n   deny: Deny usage\n\n6. External Import\n   Detect configurations from Claude Code and other tools\n   One-click import of existing configurations\n\nNotes:\n- Please click Save button after modifications\n- Recommend regular backup of configuration files\n- Agent/Category models must be configured Provider/Model",
    "options_content": 'According to OpenCode official documentation:\n\n【Options】Default configuration parameters for models\n- These configurations are used every time the model is called\n- Suitable for common fixed configurations\n- Example: thinking.type, thinking.budgetTokens\n\n【Variants】Switchable variant configurations\n- Users can switch via variant_cycle shortcut\n- Suitable for different scenario configuration combinations\n- Example: high/medium/low different budgetTokens\n\n═══════════════════════════════════════════════════════════════\nThinking Mode Configuration Examples\n═══════════════════════════════════════════════════════════════\n\n【Claude】\n  options:\n    thinking:\n      type: "enabled"\n      budgetTokens: 16000\n  variants:\n    high:\n      thinking:\n        budgetTokens: 32000\n    max:\n      thinking:\n        budgetTokens: 64000\n\n【OpenAI】\n  options:\n    reasoningEffort: "high"\n  variants:\n    medium:\n      reasoningEffort: "medium"\n    low:\n      reasoningEffort: "low"\n\n【Gemini】\n  options:\n    thinkingConfig:\n      thinkingBudget: 8000\n  variants:\n    high:\n      thinkingConfig:\n        thinkingBudget: 16000',
}

# 中文翻译
zh_help_additions = {
    "priority_content": "1. 远程配置 (Remote)\n   通过 API 或远程服务器获取的配置\n   优先级最高，会覆盖所有本地配置\n\n2. 全局配置 (Global)\n   位置: ~/.config/opencode/opencode.json\n   影响所有项目的默认配置\n\n3. 自定义配置 (Custom)\n   通过 --config 参数指定的配置文件\n   用于特定场景的配置覆盖\n\n4. 项目配置 (Project)\n   位置: <项目根目录>/opencode.json\n   项目级别的配置，仅影响当前项目\n\n5. .opencode 目录配置\n   位置: <项目根目录>/.opencode/config.json\n   项目内的隐藏配置目录\n\n6. 内联配置 (Inline)\n   通过命令行参数直接指定的配置\n   优先级最低，但最灵活\n\n配置合并规则:\n- 高优先级配置会覆盖低优先级的同名配置项\n- 未指定的配置项会继承低优先级的值\n- Provider 和 Model 配置会进行深度合并",
    "usage_content": "一、Provider 管理\n   添加自定义 API 提供商\n   配置 API 地址和密钥\n   支持多种 SDK: @ai-sdk/anthropic, @ai-sdk/openai 等\n\n二、Model 管理\n   在 Provider 下添加模型\n   支持预设常用模型快速选择\n   配置模型参数（上下文限制、输出限制等）\n\n三、Agent 管理 (Oh My OpenCode)\n   配置不同用途的 Agent\n   绑定已配置的 Provider/Model\n   支持预设 Agent 模板\n\n四、Category 管理 (Oh My OpenCode)\n   配置任务分类\n   设置不同分类的 Temperature\n   绑定对应的模型\n\n五、权限管理\n   配置工具的使用权限\n   allow: 允许使用\n   ask: 每次询问\n   deny: 禁止使用\n\n六、外部导入\n   检测 Claude Code 等工具的配置\n   一键导入已有配置\n\n注意事项:\n- 修改后请点击保存按钮\n- 建议定期备份配置文件\n- Agent/Category 的模型必须是已配置的 Provider/Model",
    "options_content": '根据 OpenCode 官方文档:\n\n【Options】模型的默认配置参数\n- 每次调用模型时都会使用这些配置\n- 适合放置常用的固定配置\n- 例如: thinking.type, thinking.budgetTokens\n\n【Variants】可切换的变体配置\n- 用户可通过 variant_cycle 快捷键切换\n- 适合放置不同场景的配置组合\n- 例如: high/medium/low 不同的 budgetTokens\n\n═══════════════════════════════════════════════════════════════\nThinking 模式配置示例\n═══════════════════════════════════════════════════════════════\n\n【Claude】\n  options:\n    thinking:\n      type: "enabled"\n      budgetTokens: 16000\n  variants:\n    high:\n      thinking:\n        budgetTokens: 32000\n    max:\n      thinking:\n        budgetTokens: 64000\n\n【OpenAI】\n  options:\n    reasoningEffort: "high"\n  variants:\n    medium:\n      reasoningEffort: "medium"\n    low:\n      reasoningEffort: "low"\n\n【Gemini】\n  options:\n    thinkingConfig:\n      thinkingBudget: 8000\n  variants:\n    high:\n      thinkingConfig:\n        thinkingBudget: 16000',
}


def update_translations():
    """更新翻译文件"""
    locales_dir = Path("locales")

    # 更新英文翻译
    en_file = locales_dir / "en_US.json"
    with open(en_file, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    en_data["help"].update(en_help_additions)

    with open(en_file, "w", encoding="utf-8") as f:
        json.dump(en_data, f, indent=2, ensure_ascii=False)

    print(f"Updated {en_file}")

    # 更新中文翻译
    zh_file = locales_dir / "zh_CN.json"
    with open(zh_file, "r", encoding="utf-8") as f:
        zh_data = json.load(f)

    zh_data["help"].update(zh_help_additions)

    with open(zh_file, "w", encoding="utf-8") as f:
        json.dump(zh_data, f, indent=2, ensure_ascii=False)

    print(f"Updated {zh_file}")
    print("\nAll translations updated successfully!")


if __name__ == "__main__":
    update_translations()
