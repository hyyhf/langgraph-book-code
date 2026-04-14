"""
智能体图构建模块
使用LangGraph构建Plan-and-Execute智能体
"""
from langgraph.graph import StateGraph, START, END
from .utils import PlanExecuteState, plan_step, execute_step, replan_step


def should_end(state: PlanExecuteState) -> str:
    """判断是否应该结束
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点名称
    """
    if "response" in state and state["response"]:
        return END
    else:
        return "executor"


def create_agent():
    """创建Plan-and-Execute智能体
    
    Returns:
        编译后的智能体图
    """
    # 创建状态图
    workflow = StateGraph(PlanExecuteState)
    
    # 添加节点
    workflow.add_node("planner", plan_step)
    workflow.add_node("executor", execute_step)
    workflow.add_node("replanner", replan_step)
    
    # 添加边
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "replanner")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "replanner",
        should_end,
        ["executor", END]
    )
    
    # 编译图
    app = workflow.compile()
    
    return app


# 创建全局智能体实例
agent = create_agent()

