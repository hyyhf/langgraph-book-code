"""
配置文件 - 加载环境变量和创建LLM实例
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载.env文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 获取环境变量
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME')


def get_llm(temperature: float = 0) -> ChatOpenAI:
    """
    创建LLM实例
    
    Args:
        temperature: 温度参数,控制输出的随机性
        
    Returns:
        ChatOpenAI实例
    """
    return ChatOpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL_NAME,
        temperature=temperature
    )

