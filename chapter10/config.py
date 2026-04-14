"""
配置文件

集中管理所有配置项
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LLM配置
LLM_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "api_key": os.getenv("OPENAI_API_KEY"),
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
}

# 研究助手配置
RESEARCH_CONFIG = {
    # 是否启用人工审核
    "enable_human_review": False,

    # 默认研究主题
    "default_topics": [
        "武汉热干面的历史与文化",
        "武汉长江大桥的建设历程",
        "武汉黄鹤楼的诗词文化",
        "武汉东湖的生态保护",
    ],

    # 输出配置
    "output_dir": "outputs",
    "report_format": "markdown",  # markdown, txt, html
}

# 流式输出配置
STREAMING_CONFIG = {
    "enable_streaming": True,
    "show_progress": True,
    "verbose": True,
}

# 工具配置
TOOLS_CONFIG = {
    # 搜索工具配置
    "search": {
        "max_results": 5,
        "use_mock_data": True,  # 是否使用模拟数据
    },

    # 分析工具配置
    "analysis": {
        "max_length": 1000,
    },
}


def get_llm_config():
    """获取LLM配置"""
    return LLM_CONFIG.copy()


def get_research_config():
    """获取研究助手配置"""
    return RESEARCH_CONFIG.copy()


def get_streaming_config():
    """获取流式输出配置"""
    return STREAMING_CONFIG.copy()


def get_tools_config():
    """获取工具配置"""
    return TOOLS_CONFIG.copy()
