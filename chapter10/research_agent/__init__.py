"""
自动化研究助手 - 一个简易版的Deep Research智能体

这个包实现了一个完整的多智能体研究系统,包括:
- 研究员: 负责信息收集
- 分析师: 负责数据分析
- 报告员: 负责生成报告
"""

from .agent import create_research_agent

__all__ = ["create_research_agent"]

