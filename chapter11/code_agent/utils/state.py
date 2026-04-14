"""
状态定义模块
定义智能体系统的状态结构
"""
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict


class PlanExecuteState(TypedDict):
    """Plan-and-Execute 智能体的状态
    
    Attributes:
        input: 用户输入的任务描述
        plan: 当前的执行计划（步骤列表）
        past_steps: 已执行的步骤及其结果
        response: 最终响应给用户的结果
    """
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

