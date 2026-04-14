"""
自动运行示例
演示智能体的完整工作流程(自动确认计划)
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from wuhan_travel_agent import create_travel_agent


def run_auto_example():
    """
    自动运行示例
    
    这个示例会:
    1. 创建智能体
    2. 输入旅行需求
    3. 自动收集信息并生成计划
    4. 自动确认计划
    5. 生成HTML文档
    """
    print("=" * 80)
    print("武汉旅行规划助手 - 自动运行示例")
    print("=" * 80)
    print()
    
    # 创建智能体
    print("步骤1: 创建智能体")
    print("-" * 80)
    agent = create_travel_agent()
    print("智能体创建成功!")
    print()
    
    # 配置
    config = {
        "configurable": {
            "thread_id": "auto_example_001"
        }
    }
    
    # 初始状态
    user_request = "我想在武汉玩2天,第一天去历史文化景点,第二天品尝当地美食"
    
    print("步骤2: 输入旅行需求")
    print("-" * 80)
    print(f"需求: {user_request}")
    print()
    
    initial_state = {
        "messages": [HumanMessage(content=user_request)],
        "user_request": user_request,
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
    
    # 第一阶段: 运行到中断点
    print("步骤3: 收集信息并生成计划")
    print("-" * 80)
    
    step_count = 0
    for event in agent.stream(initial_state, config, stream_mode="values"):
        step_count += 1
        messages = event.get("messages", [])
        
        if messages:
            last_message = messages[-1]
            
            # 打印AI消息
            if hasattr(last_message, 'content') and last_message.content:
                content = last_message.content
                if len(content) > 200:
                    content = content[:200] + "..."
                print(f"\n[步骤 {step_count}] AI: {content}")
            
            # 打印工具调用
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    print(f"\n[步骤 {step_count}] 工具调用: {tool_call['name']}")
                    print(f"  参数: {tool_call['args']}")
    
    print()
    print(f"完成! 共执行了 {step_count} 步")
    print()
    
    # 获取当前状态
    state_snapshot = agent.get_state(config)
    current_state = state_snapshot.values
    travel_plan = current_state.get("travel_plan", "")
    
    if travel_plan:
        print("步骤4: 生成的旅行计划")
        print("-" * 80)
        print(travel_plan[:500] + "..." if len(travel_plan) > 500 else travel_plan)
        print()
    
    # 自动确认
    print("步骤5: 自动确认计划")
    print("-" * 80)
    print("发送确认信号...")
    print()
    
    # 第二阶段: 恢复执行
    print("步骤6: 生成HTML文档")
    print("-" * 80)
    
    for event in agent.stream(Command(resume="确认"), config, stream_mode="values"):
        messages = event.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content') and last_message.content:
                print(f"\n{last_message.content}")
    
    print()
    
    # 获取最终状态
    final_state = agent.get_state(config)
    final_values = final_state.values
    
    print("步骤7: 完成")
    print("-" * 80)
    
    html_path = final_values.get("html_path", "")
    if html_path:
        print(f"HTML文档已生成: {html_path}")
        print(f"文件大小: {os.path.getsize(html_path)} 字节")
        print()
        print("您可以在浏览器中打开查看完整的旅行计划。")
    else:
        print("未生成HTML文档")
    
    print()
    print("=" * 80)
    print("示例运行完成!")
    print("=" * 80)


if __name__ == "__main__":
    run_auto_example()

