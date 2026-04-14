"""
武汉旅行规划助手 - 主程序

这是一个完整的实战案例,展示如何使用LangGraph构建一个多角色智能体系统。

功能特点:
1. 多角色协作: 规划助手、工具调用、HTML生成助手
2. 工具集成: 高德地图API(天气、POI、路线规划)
3. Human-in-the-loop: 用户可以审核和修改旅行计划
4. 流式输出: 实时展示智能体的思考过程
5. 精美输出: 生成HTML格式的旅行计划文档
"""

import os
import asyncio
from dotenv import load_dotenv

# 加载环境变量 
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from wuhan_travel_agent import create_travel_agent


async def run_travel_planner():
    """
    运行旅行规划助手的主函数
    """
    print("=" * 80)
    print("欢迎使用武汉旅行规划助手!")
    print("=" * 80)
    print()
    
    # 创建智能体
    print("正在初始化智能体...")
    agent = create_travel_agent()
    print("智能体初始化完成!")
    print()
    
    # 配置线程ID(用于状态持久化)
    config = {
        "configurable": {
            "thread_id": "travel_plan_001"
        }
    }
    
    # 用户输入
    user_request = input("请描述您的旅行需求(例如: 我想在武汉玩3天,喜欢历史文化和美食): ")
    print()
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content=user_request)],
        "user_request": user_request,
        "destination": "武汉",
        "travel_days": 3,
        "weather_info": "",
        "poi_info": "",
        "route_info": "",
        "travel_plan": "",
        "user_feedback": "",
        "final_plan": "",
        "html_path": "",
        "current_stage": "collect_info",
        "need_replan": False
    }
    
    print("开始规划您的旅行...")
    print("-" * 80)
    print()
    
    # 第一阶段: 运行直到人工审核节点
    print("阶段1: 收集信息并生成初步计划")
    print("=" * 80)
    
    async for event in agent.astream(initial_state, config, stream_mode="values"):
        # 获取最后一条消息
        messages = event.get("messages", [])
        if messages:
            last_message = messages[-1]
            
            # 打印AI消息
            if hasattr(last_message, 'content') and last_message.content:
                print(f"\n[智能体]: {last_message.content}")
            
            # 打印工具调用
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    print(f"\n[工具调用]: {tool_call['name']}")
                    print(f"  参数: {tool_call['args']}")
            
            # 打印工具结果
            if hasattr(last_message, 'name') and last_message.name:
                print(f"\n[工具结果 - {last_message.name}]:")
                print(f"  {last_message.content}...")  # 只显示前200字符
        
        print("-" * 80)
    
    # 检查是否到达中断点(人工审核)
    state_snapshot = agent.get_state(config)

    # 可能存在多轮人工审核: 直到不再中断为止
    round_idx = 1
    while state_snapshot.next:
        print("\n" + "=" * 80)
        title = "阶段2: 人工审核" if round_idx == 1 else f"阶段2: 人工审核(第{round_idx}轮)"
        print(title)
        print("=" * 80)

        # 显示当前生成的计划(若有)
        current_state = state_snapshot.values
        travel_plan = current_state.get("travel_plan", "")
        if travel_plan:
            print("\n生成的旅行计划:")
            print("-" * 80)
            print(travel_plan)
            print("-" * 80)

        # 获取用户反馈
        print("\n请审核以上旅行计划:")
        print("1. 输入'确认'接受计划")
        print("2. 输入具体的修改建议")
        user_feedback = input("\n您的反馈: ")
        print()

        # 使用Command恢复执行(本轮处理)
        print("阶段3: 处理反馈(本轮)")
        print("=" * 80)
        async for event in agent.astream(
            Command(resume=user_feedback),
            config,
            stream_mode="values"
        ):
            messages = event.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content') and last_message.content:
                    print(f"\n[智能体]: {last_message.content}")
            print("-" * 80)

        # 本轮结束后,检查是否还需要继续人工审核
        state_snapshot = agent.get_state(config)
        round_idx += 1

    # 获取最终状态
    final_state = agent.get_state(config)
    final_values = final_state.values
    
    print("\n" + "=" * 80)
    print("旅行规划完成!")
    print("=" * 80)
    
    html_path = final_values.get("html_path", "")
    if html_path:
        print(f"\nHTML文档已生成: {html_path}")
        print("您可以在浏览器中打开查看完整的旅行计划。")
    
    print("\n感谢使用武汉旅行规划助手!")
    print("=" * 80)


def run_simple_example():
    """
    运行一个简单的示例(不需要用户交互)
    """
    print("=" * 80)
    print("运行简单示例(自动确认计划)")
    print("=" * 80)
    print()
    
    # 创建智能体
    agent = create_travel_agent()
    
    # 配置
    config = {
        "configurable": {
            "thread_id": "simple_example_001"
        }
    }
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content="我想在武汉玩2天,喜欢历史文化景点")],
        "user_request": "我想在武汉玩2天,喜欢历史文化景点",
        "destination": "武汉",
        "travel_days": 2,
        "weather_info": "",
        "poi_info": "",
        "route_info": "",
        "travel_plan": "",
        "user_feedback": "",
        "final_plan": "",
        "html_path": "",
        "current_stage": "collect_info",
        "need_replan": False
    }
    
    print("开始规划...")
    
    # 运行到中断点
    for event in agent.stream(initial_state, config, stream_mode="values"):
        pass
    
    # 自动确认
    print("自动确认计划...")
    for event in agent.stream(Command(resume="确认"), config, stream_mode="values"):
        pass
    
    # 获取结果
    final_state = agent.get_state(config)
    html_path = final_state.values.get("html_path", "")
    
    print(f"\n完成! HTML文档: {html_path}")


if __name__ == "__main__":
    # 运行交互式版本
    asyncio.run(run_travel_planner())
    
    # 或者运行简单示例
    # run_simple_example()

