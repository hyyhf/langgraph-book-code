"""
智能体构建模块
构建完整的武汉旅行规划助手图
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .utils.state import TravelPlanState
from .utils.nodes import (
    planner_node,
    tool_node,
    human_review_node,
    html_generator_node,
    should_continue_planning,
    should_continue_after_review
)


def create_travel_agent():
    """
    创建武汉旅行规划助手智能体
    
    工作流程:
    1. 用户输入旅行需求
    2. 规划助手理解需求并调用工具收集信息(天气、POI、路线)
    3. 规划助手生成初步旅行计划
    4. 人工审核节点暂停,等待用户反馈
    5. 根据反馈决定是否重新规划
    6. 生成精美的HTML旅行计划文档
    
    Returns:
        编译后的图对象
    """
    # 创建状态图
    workflow = StateGraph(TravelPlanState)
    
    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("review", human_review_node)
    workflow.add_node("html_generator", html_generator_node)
    
    # 定义流程
    # START -> 规划助手
    workflow.add_edge(START, "planner")
    
    # 规划助手 -> 条件边
    workflow.add_conditional_edges(
        "planner",
        should_continue_planning,
        {
            "tools": "tools",        # 需要调用工具
            "review": "review",      # 生成了计划,进入审核
            "continue": "planner"    # 继续规划
        }
    )
    
    # 工具 -> 规划助手(工具执行后返回规划助手继续处理)
    workflow.add_edge("tools", "planner")
    
    # 人工审核 -> 条件边
    workflow.add_conditional_edges(
        "review",
        should_continue_after_review,
        {
            "replan": "planner",           # 需要重新规划
            "generate_html": "html_generator"  # 生成HTML
        }
    )
    
    # HTML生成器 -> END
    workflow.add_edge("html_generator", END)
    
    # 编译图
    # 使用检查点保存器,支持状态持久化和中断恢复
    memory = MemorySaver()
    
    # 在review节点使用interrupt,不需要在这里设置interrupt_before
    return workflow.compile(checkpointer=memory)

