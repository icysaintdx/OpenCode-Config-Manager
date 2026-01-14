# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 1: 常量定义和预设数据
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# ==================== 版本信息 ====================
VERSION = "0.9.0"
APP_NAME = "OpenCode 配置管理器"
APP_TITLE = f"{APP_NAME} v{VERSION}"

# ==================== 路径常量 ====================
HOME_DIR = Path.home()
OPENCODE_DIR = HOME_DIR / ".opencode"
OPENCODE_JSON = OPENCODE_DIR / "opencode.json"
AGENTS_MD = OPENCODE_DIR / "AGENTS.md"
SKILL_MD = OPENCODE_DIR / "SKILL.md"
BACKUP_DIR = OPENCODE_DIR / "backups"

# ==================== 预设SDK配置 ====================
PRESET_SDKS = {
    "OpenAI": {
        "name": "openai",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o1-preview", "o3-mini"]
    },
    "Anthropic": {
        "name": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]
    },
    "Google": {
        "name": "google",
        "env_key": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"]
    },
    "Azure OpenAI": {
        "name": "azure",
        "env_key": "AZURE_OPENAI_API_KEY",
        "base_url": "",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"]
    },
    "Groq": {
        "name": "groq",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    },
    "OpenRouter": {
        "name": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["anthropic/claude-sonnet-4", "openai/gpt-4o", "google/gemini-2.0-flash-exp:free"]
    },
    "DeepSeek": {
        "name": "deepseek",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"]
    },
    "Mistral": {
        "name": "mistral",
        "env_key": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"]
    },
    "xAI": {
        "name": "xai",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-beta", "grok-2", "grok-2-mini"]
    },
    "Ollama": {
        "name": "ollama",
        "env_key": "",
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3.3", "qwen2.5-coder", "deepseek-r1", "codellama"]
    },
    "硅基流动": {
        "name": "siliconflow",
        "env_key": "SILICONFLOW_API_KEY",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3", "Pro/deepseek-ai/DeepSeek-R1"]
    },
    "阿里云百炼": {
        "name": "dashscope",
        "env_key": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-coder-plus"]
    },
    "火山引擎": {
        "name": "volcengine",
        "env_key": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-pro-32k", "doubao-lite-32k"]
    },
    "智谱AI": {
        "name": "zhipu",
        "env_key": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4", "glm-4-flash"]
    },
    "百度千帆": {
        "name": "qianfan",
        "env_key": "QIANFAN_API_KEY",
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "models": ["ernie-4.0-8k", "ernie-3.5-8k", "ernie-speed-8k"]
    },
    "腾讯混元": {
        "name": "hunyuan",
        "env_key": "HUNYUAN_API_KEY",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "models": ["hunyuan-pro", "hunyuan-standard", "hunyuan-lite"]
    },
    "Moonshot": {
        "name": "moonshot",
        "env_key": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"]
    },
    "零一万物": {
        "name": "lingyiwanwu",
        "env_key": "LINGYIWANWU_API_KEY",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "models": ["yi-large", "yi-medium", "yi-spark"]
    },
    "自定义": {
        "name": "custom",
        "env_key": "",
        "base_url": "",
        "models": []
    }
}

# ==================== 预设模型配置 ====================
PRESET_MODEL_CONFIGS = {
    # OpenAI 系列
    "gpt-4o": {"maxTokens": 16384, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4o-mini": {"maxTokens": 16384, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4-turbo": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4": {"maxTokens": 8192, "contextWindow": 8192, "supportsImages": False, "supportsComputerUse": False},
    "gpt-3.5-turbo": {"maxTokens": 4096, "contextWindow": 16385, "supportsImages": False, "supportsComputerUse": False},
    "o1": {"maxTokens": 100000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False, "reasoning": True},
    "o1-mini": {"maxTokens": 65536, "contextWindow": 128000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},
    "o1-preview": {"maxTokens": 32768, "contextWindow": 128000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},
    "o3-mini": {"maxTokens": 100000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False, "reasoning": True},

    # Anthropic 系列
    "claude-sonnet-4-20250514": {"maxTokens": 16000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-7-sonnet-20250219": {"maxTokens": 16000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-5-sonnet-20241022": {"maxTokens": 8192, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-5-haiku-20241022": {"maxTokens": 8192, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False},
    "claude-3-opus-20240229": {"maxTokens": 4096, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False},

    # Google 系列
    "gemini-2.0-flash": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-2.0-flash-lite": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-1.5-pro": {"maxTokens": 8192, "contextWindow": 2000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-1.5-flash": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},

    # DeepSeek 系列
    "deepseek-chat": {"maxTokens": 8192, "contextWindow": 64000, "supportsImages": False, "supportsComputerUse": False},
    "deepseek-reasoner": {"maxTokens": 8192, "contextWindow": 64000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},

    # 国产模型
    "qwen-max": {"maxTokens": 8192, "contextWindow": 32000, "supportsImages": False, "supportsComputerUse": False},
    "qwen-plus": {"maxTokens": 8192, "contextWindow": 131072, "supportsImages": False, "supportsComputerUse": False},
    "qwen-turbo": {"maxTokens": 8192, "contextWindow": 131072, "supportsImages": False, "supportsComputerUse": False},
    "glm-4-plus": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "glm-4": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "glm-4-flash": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
}

# ==================== 预设Agent配置 ====================
PRESET_AGENTS = {
    "代码助手": {
        "name": "code-assistant",
        "model": "",
        "description": "专注于代码编写、调试和优化的AI助手",
        "instructions": "你是一个专业的代码助手，擅长编写高质量代码、调试问题和优化性能。"
    },
    "文档专家": {
        "name": "doc-expert",
        "model": "",
        "description": "专注于文档编写和技术写作的AI助手",
        "instructions": "你是一个文档专家，擅长编写清晰、准确的技术文档和用户指南。"
    },
    "架构师": {
        "name": "architect",
        "model": "",
        "description": "专注于系统设计和架构规划的AI助手",
        "instructions": "你是一个系统架构师，擅长设计可扩展、高性能的系统架构。"
    },
    "测试工程师": {
        "name": "tester",
        "model": "",
        "description": "专注于测试策略和质量保证的AI助手",
        "instructions": "你是一个测试工程师，擅长编写测试用例、发现bug和确保代码质量。"
    },
    "DevOps专家": {
        "name": "devops",
        "model": "",
        "description": "专注于CI/CD和运维自动化的AI助手",
        "instructions": "你是一个DevOps专家，擅长配置CI/CD流水线、容器化部署和运维自动化。"
    }
}

# ==================== 分类预设 ====================
CATEGORY_PRESETS = {
    "代码生成": {"temperature": 0.3, "description": "适合生成结构化代码，保持一致性"},
    "代码审查": {"temperature": 0.2, "description": "适合严格的代码审查，减少随机性"},
    "创意写作": {"temperature": 0.8, "description": "适合创意内容，增加多样性"},
    "技术文档": {"temperature": 0.4, "description": "适合技术文档，平衡准确性和可读性"},
    "问答对话": {"temperature": 0.5, "description": "适合一般对话，平衡准确性和自然度"},
    "数据分析": {"temperature": 0.1, "description": "适合数据分析，最大化准确性"},
    "头脑风暴": {"temperature": 0.9, "description": "适合创意发散，最大化多样性"},
}

# ==================== 权限预设 ====================
PERMISSION_MODES = {
    "allow": "允许 - 自动执行，无需确认",
    "ask": "询问 - 每次执行前询问用户",
    "deny": "拒绝 - 禁止执行此操作"
}

BASH_COMMAND_MODES = {
    "allow": "允许所有命令",
    "ask": "每次询问",
    "deny": "拒绝所有命令",
    "allowlist": "仅允许白名单命令"
}

# ==================== Tooltip提示 ====================
TOOLTIPS = {
    # Provider相关
    "provider_name": "服务商名称，用于在配置中标识此服务商",
    "provider_api_key": "API密钥，用于身份验证。支持直接填写密钥或使用环境变量格式 ${ENV_VAR}",
    "provider_base_url": "API基础URL，不同服务商有不同的端点地址",
    "provider_disabled": "禁用此服务商，禁用后将不会使用此服务商的模型",

    # Model相关
    "model_id": "模型ID，用于API调用时指定使用的模型",
    "model_max_tokens": "最大输出Token数，限制模型单次回复的最大长度",
    "model_context_window": "上下文窗口大小，模型能处理的最大输入Token数",
    "model_supports_images": "是否支持图像输入，启用后可以处理图片",
    "model_supports_computer_use": "是否支持计算机使用功能（Anthropic特有）",
    "model_reasoning": "是否为推理模型，推理模型会显示思考过程",
    "model_options": "模型选项，如temperature、top_p等参数",
    "model_variants": "模型变体，用于A/B测试或特定场景的模型配置",

    # Thinking相关
    "thinking_enabled": "启用思考模式，模型会显示推理过程",
    "thinking_budget": "思考预算Token数，限制思考过程的长度",
    "thinking_type": "思考类型：enabled(启用)、disabled(禁用)",

    # MCP相关
    "mcp_name": "MCP服务器名称，用于标识此服务器",
    "mcp_type": "服务器类型：local(本地进程)、remote(远程SSE)",
    "mcp_command": "启动命令，用于启动本地MCP服务器",
    "mcp_args": "命令参数，传递给启动命令的参数列表",
    "mcp_url": "远程服务器URL，用于连接远程MCP服务器",
    "mcp_env": "环境变量，传递给MCP服务器的环境变量",
    "mcp_timeout": "超时时间（秒），等待服务器响应的最大时间",

    # Agent相关
    "agent_mode": "Agent模式：auto(自动)、manual(手动)、hybrid(混合)",
    "agent_temperature": "温度参数，控制输出的随机性，0-1之间",
    "agent_max_steps": "最大步骤数，限制Agent执行的最大步骤",
    "agent_tools": "可用工具列表，Agent可以调用的工具",
    "agent_permission": "权限设置，控制Agent的操作权限",

    # Permission相关
    "permission_allow": "允许：自动执行，无需用户确认",
    "permission_ask": "询问：每次执行前询问用户确认",
    "permission_deny": "拒绝：禁止执行此操作",
    "permission_bash": "Bash命令权限，控制命令行操作的权限",

    # Compaction相关
    "compaction_enabled": "启用自动压缩，当上下文过长时自动压缩历史消息",
    "compaction_threshold": "压缩阈值，超过此Token数时触发压缩",
    "compaction_trim_old": "修剪旧输出，移除较早的输出以节省空间",

    # 其他
    "category_temperature": "分类温度，不同任务类型使用不同的温度设置",
    "skill_permission": "技能权限，控制技能的执行权限",
    "rules_instructions": "规则指令，自定义AI的行为规则",
}

# ==================== 默认配置模板 ====================
DEFAULT_CONFIG = {
    "providers": {},
    "models": {},
    "mcpServers": {},
    "agents": {},
    "permissions": {
        "allow": [],
        "ask": [],
        "deny": []
    },
    "compaction": {
        "enabled": False,
        "threshold": 100000,
        "trimOldOutput": False
    }
}
