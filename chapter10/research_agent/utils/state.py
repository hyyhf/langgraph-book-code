"""
状态定义模块
定义研究助手的状态结构
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    """
    研究助手的状态定义
    
    这个状态会在整个研究流程中传递和更新
    """
    # 消息历史 - 使用add_messages reducer自动管理消息列表
    messages: Annotated[list, add_messages]
    
    # 研究主题
    topic: str
    
    # 研究员收集的数据
    research_data: str
    
    # 分析师的分析结果
    analysis_result: str
    
    # 报告员生成的最终报告
    final_report: str
    
    # 当前执行阶段
    current_stage: Literal["init", "research", "review", "analysis", "report", "complete"]
    
    # 人工审核标志
    human_approved: bool

