"""
智能体构建模块
构建完整的研究助手图
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .utils.state import ResearchState
from .utils.nodes import (
    researcher_node,
    tool_node,
    human_review_node,
    analyst_node,
    reporter_node
)


def should_continue_research(state: ResearchState) -> Literal["tools", "human_review", "analyst"]:
    """
    条件边: 判断研究员的下一步行动

    - 如果有工具调用,执行工具
    - 如果有研究数据且需要人工审核,进入审核
    - 如果有研究数据且不需要审核,直接进入分析
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 检查是否有工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # 检查是否已经有研究数据
    if state.get("research_data"):
        # 这里会在create_research_agent中根据with_human_review参数决定
        return "human_review"  # 或 "analyst"

    return "tools"


def should_continue_after_review(state: ResearchState) -> Literal["analyst", "researcher"]:
    """
    条件边: 根据人工审核结果决定下一步
    
    如果审核通过,进入分析阶段
    否则返回研究员重新收集信息
    """
    if state.get("human_approved", False):
        return "analyst"
    else:
        return "researcher"


def create_research_agent(with_human_review: bool = True):
    """
    创建研究助手智能体
    
    Args:
        with_human_review: 是否包含人工审核环节
        
    Returns:
        编译后的图对象
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 添加所有节点
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("reporter", reporter_node)

    # 定义基本流程
    # START -> 研究员
    workflow.add_edge(START, "researcher")

    # 工具 -> 研究员(工具执行后返回研究员继续处理)
    workflow.add_edge("tools", "researcher")

    # 如果包含人工审核
    if with_human_review:
        workflow.add_node("human_review", human_review_node)

        # 研究员 -> 条件边
        workflow.add_conditional_edges(
            "researcher",
            should_continue_research,
            {
                "tools": "tools",
                "human_review": "human_review",
                "analyst": "analyst"
            }
        )

        # 人工审核 -> 条件边(根据审核结果决定)
        workflow.add_conditional_edges(
            "human_review",
            should_continue_after_review,
            {
                "analyst": "analyst",
                "researcher": "researcher"
            }
        )
    else:
        # 不包含人工审核
        workflow.add_conditional_edges(
            "researcher",
            lambda state: "tools" if (
                state["messages"] and
                hasattr(state["messages"][-1], 'tool_calls') and
                state["messages"][-1].tool_calls
            ) else "analyst",
            {
                "tools": "tools",
                "analyst": "analyst"
            }
        )
    
    # 分析师 -> 报告员
    workflow.add_edge("analyst", "reporter")
    
    # 报告员 -> END
    workflow.add_edge("reporter", END)
    
    # 编译图
    # 使用检查点保存器,支持状态持久化和中断恢复
    memory = MemorySaver()
    
    # 如果包含人工审核,在human_review节点前中断
    if with_human_review:
        return workflow.compile(
            checkpointer=memory,
            interrupt_before=["human_review"]
        )
    else:
        return workflow.compile(checkpointer=memory)

