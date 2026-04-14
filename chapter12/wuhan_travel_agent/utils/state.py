"""
状态定义模块
定义武汉旅行规划助手的状态结构
"""

from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph.message import add_messages


class TravelPlanState(TypedDict):
    """
    旅行规划助手的状态定义
    
    这个状态会在整个规划流程中传递和更新
    """
    # 消息历史 - 使用add_messages reducer自动管理消息列表
    messages: Annotated[list, add_messages]
    
    # 用户的旅行需求
    user_request: str
    
    # 旅行目的地(默认武汉)
    destination: str
    
    # 旅行天数
    travel_days: int
    
    # 收集的天气信息
    weather_info: str
    
    # 收集的景点信息
    poi_info: str
    
    # 收集的路线信息
    route_info: str
    
    # 规划助手生成的初步旅行计划
    travel_plan: str
    
    # 用户对计划的反馈
    user_feedback: str
    
    # 最终确认的旅行计划
    final_plan: str
    
    # 生成的HTML文档路径
    html_path: str
    
    # 当前执行阶段
    current_stage: Literal[
        "init",           # 初始化
        "collect_info",   # 收集信息
        "replan",         # 重新规划(用户反馈后)
        "plan_ready",     # 计划就绪(等待审核)
        "generate_html",  # 生成HTML
        "complete"        # 完成
    ]
    
    # 是否需要重新规划
    need_replan: bool

