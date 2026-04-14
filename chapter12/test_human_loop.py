"""
测试Human-in-the-Loop功能
验证用户反馈后能否正确循环
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


def test_human_loop():
    """
    测试人机交互循环
    """
    print("=" * 80)
    print("测试Human-in-the-Loop功能")
    print("=" * 80)
    
    # 创建智能体
    agent = create_travel_agent()
    
    # 配置
    config = {"configurable": {"thread_id": "test_human_loop"}}
    
    # 初始输入
    initial_input = {
        "messages": [HumanMessage(content="我想在武汉玩2天,喜欢历史文化")]
    }
    
    print("\n步骤1: 发送初始请求")
    print("-" * 80)
    
    # 第一次运行,直到中断
    step_count = 0
    for event in agent.stream(initial_input, config, stream_mode="values"):
        step_count += 1
        last_message = event["messages"][-1]
        current_stage = event.get("current_stage", "unknown")
        
        print(f"\n[步骤 {step_count}] 当前阶段: {current_stage}")
        
        if hasattr(last_message, 'content'):
            content = last_message.content
            if len(content) > 200:
                print(f"消息: {content[:200]}...")
            else:
                print(f"消息: {content}")
    
    print("\n" + "=" * 80)
    print("步骤2: 第一次用户反馈 - 要求修改")
    print("=" * 80)
    
    # 第一次反馈 - 要求修改
    feedback1 = Command(
        resume="请增加美食推荐"
    )
    
    step_count = 0
    for event in agent.stream(feedback1, config, stream_mode="values"):
        step_count += 1
        last_message = event["messages"][-1]
        current_stage = event.get("current_stage", "unknown")
        
        print(f"\n[步骤 {step_count}] 当前阶段: {current_stage}")
        
        if hasattr(last_message, 'content'):
            content = last_message.content
            if len(content) > 200:
                print(f"消息: {content[:200]}...")
            else:
                print(f"消息: {content}")
    
    print("\n" + "=" * 80)
    print("步骤3: 第二次用户反馈 - 确认计划")
    print("=" * 80)
    
    # 第二次反馈 - 确认
    feedback2 = Command(
        resume="确认"
    )
    
    step_count = 0
    for event in agent.stream(feedback2, config, stream_mode="values"):
        step_count += 1
        last_message = event["messages"][-1]
        current_stage = event.get("current_stage", "unknown")
        
        print(f"\n[步骤 {step_count}] 当前阶段: {current_stage}")
        
        if hasattr(last_message, 'content'):
            content = last_message.content
            if len(content) > 200:
                print(f"消息: {content[:200]}...")
            else:
                print(f"消息: {content}")
        
        # 检查是否生成了HTML
        if "html_path" in event:
            print(f"\n✅ HTML文件已生成: {event['html_path']}")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)
    
    # 验证结果
    final_state = agent.get_state(config)
    final_stage = final_state.values.get("current_stage", "unknown")
    
    print(f"\n最终阶段: {final_stage}")
    
    if final_stage == "complete":
        print("✅ 测试通过: 完整的人机交互循环工作正常")
        return True
    else:
        print(f"❌ 测试失败: 最终阶段应该是'complete',但实际是'{final_stage}'")
        return False


if __name__ == "__main__":
    try:
        success = test_human_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

