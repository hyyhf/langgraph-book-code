"""
第6章示例5: 记忆管理 - 消息裁剪
演示如何使用trim_messages管理对话历史
"""

import asyncio
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# 定义状态
class State(MessagesState):
    """聊天状态"""
    pass


# 定义聊天节点(不使用裁剪)
async def chatbot_no_trim(state: State) -> dict:
    """不使用消息裁剪的聊天节点"""
    # 模拟LLM调用
    last_message = state["messages"][-1]
    response = f"收到消息: '{last_message.content}' (当前共{len(state['messages'])}条消息)"
    return {"messages": [AIMessage(content=response)]}


# 定义聊天节点(使用裁剪)
async def chatbot_with_trim(state: State) -> dict:
    """使用消息裁剪的聊天节点"""
    # 裁剪消息:只保留最近5条消息
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",  # 保留最后N条
        max_tokens=100,  # 最大token数
        token_counter=count_tokens_approximately,  # token计数器
        start_on="human",  # 从人类消息开始
        end_on=("human", "tool"),  # 在人类或工具消息结束
        include_system=True,  # 始终包含系统消息
    )
    
    # 模拟LLM调用(使用裁剪后的消息)
    response = f"收到消息(裁剪后{len(trimmed_messages)}条,原始{len(state['messages'])}条)"
    return {"messages": [AIMessage(content=response)]}


async def demo_basic_trim():
    """演示1: 基础消息裁剪"""
    print("=" * 60)
    print("演示1: 基础消息裁剪")
    print("=" * 60)
    
    # 创建一些测试消息
    messages = [
        SystemMessage(content="你是一个有帮助的助手"),
        HumanMessage(content="消息1"),
        AIMessage(content="回复1"),
        HumanMessage(content="消息2"),
        AIMessage(content="回复2"),
        HumanMessage(content="消息3"),
        AIMessage(content="回复3"),
        HumanMessage(content="消息4"),
        AIMessage(content="回复4"),
        HumanMessage(content="消息5"),
    ]
    
    print(f"\n原始消息数量: {len(messages)}")
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        print(f"  {i+1}. {msg_type}: {msg.content}")
    
    # 策略1: 按消息数量裁剪
    print("\n策略1: 保留最后3条消息")
    print("-" * 60)
    trimmed = trim_messages(
        messages,
        strategy="last",
        max_tokens=3,  # 这里max_tokens实际上控制消息数量
        token_counter=len,  # 使用简单的长度计数
    )
    print(f"裁剪后消息数量: {len(trimmed)}")
    for i, msg in enumerate(trimmed):
        msg_type = type(msg).__name__
        print(f"  {i+1}. {msg_type}: {msg.content}")
    
    # 策略2: 保留系统消息
    print("\n策略2: 保留系统消息 + 最后2条消息")
    print("-" * 60)
    trimmed = trim_messages(
        messages,
        strategy="last",
        max_tokens=2,
        token_counter=len,
        include_system=True,  # 始终包含系统消息
    )
    print(f"裁剪后消息数量: {len(trimmed)}")
    for i, msg in enumerate(trimmed):
        msg_type = type(msg).__name__
        print(f"  {i+1}. {msg_type}: {msg.content}")
    
    # 策略3: 按token数量裁剪
    print("\n策略3: 按token数量裁剪(约50 tokens)")
    print("-" * 60)
    trimmed = trim_messages(
        messages,
        strategy="last",
        max_tokens=50,
        token_counter=count_tokens_approximately,
        include_system=True,
    )
    print(f"裁剪后消息数量: {len(trimmed)}")
    total_tokens = count_tokens_approximately(trimmed)
    print(f"总token数(约): {total_tokens}")
    for i, msg in enumerate(trimmed):
        msg_type = type(msg).__name__
        tokens = count_tokens_approximately([msg])
        print(f"  {i+1}. {msg_type} ({tokens} tokens): {msg.content}")


async def demo_trim_in_graph():
    """演示2: 在图中使用消息裁剪"""
    print("\n" + "=" * 60)
    print("演示2: 在图中使用消息裁剪")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        # 构建不使用裁剪的图
        builder_no_trim = StateGraph(State)
        builder_no_trim.add_node("chatbot", chatbot_no_trim)
        builder_no_trim.add_edge(START, "chatbot")
        builder_no_trim.add_edge("chatbot", END)
        graph_no_trim = builder_no_trim.compile(checkpointer=checkpointer)
        
        # 构建使用裁剪的图
        builder_with_trim = StateGraph(State)
        builder_with_trim.add_node("chatbot", chatbot_with_trim)
        builder_with_trim.add_edge(START, "chatbot")
        builder_with_trim.add_edge("chatbot", END)
        graph_with_trim = builder_with_trim.compile(checkpointer=checkpointer)
        
        # 测试不使用裁剪
        print("\n不使用裁剪:")
        print("-" * 60)
        config_no_trim = {"configurable": {"thread_id": "no_trim"}}
        
        for i in range(1, 6):
            result = await graph_no_trim.ainvoke(
                {"messages": [HumanMessage(content=f"消息{i}")]},
                config=config_no_trim
            )
            print(f"  轮次{i}: {result['messages'][-1].content}")
        
        # 查看最终状态
        state = await graph_no_trim.aget_state(config_no_trim)
        print(f"\n最终消息数量: {len(state.values['messages'])}")
        
        # 测试使用裁剪
        print("\n使用裁剪:")
        print("-" * 60)
        config_with_trim = {"configurable": {"thread_id": "with_trim"}}
        
        for i in range(1, 6):
            result = await graph_with_trim.ainvoke(
                {"messages": [HumanMessage(content=f"消息{i}")]},
                config=config_with_trim
            )
            print(f"  轮次{i}: {result['messages'][-1].content}")
        
        # 查看最终状态
        state = await graph_with_trim.aget_state(config_with_trim)
        print(f"\n最终消息数量: {len(state.values['messages'])}")
        
        print("\n" + "=" * 60)
        print("对比:")
        print("  不使用裁剪: 消息数量持续增长,可能超出LLM上下文窗口")
        print("  使用裁剪: 消息数量受控,始终在限制范围内")
        print("=" * 60)


async def demo_advanced_trim():
    """演示3: 高级裁剪策略"""
    print("\n" + "=" * 60)
    print("演示3: 高级裁剪策略")
    print("=" * 60)
    
    # 创建包含不同类型消息的列表
    messages = [
        SystemMessage(content="你是一个专业的AI助手"),
        HumanMessage(content="第一个问题"),
        AIMessage(content="第一个回答"),
        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个回答"),
        SystemMessage(content="重要提示:请保持专业"),
        HumanMessage(content="第三个问题"),
        AIMessage(content="第三个回答"),
    ]
    
    print(f"\n原始消息:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. {type(msg).__name__}: {msg.content}")
    
    # 策略1: 保留所有系统消息
    print("\n策略1: 保留所有系统消息 + 最后2条对话")
    print("-" * 60)
    trimmed = trim_messages(
        messages,
        strategy="last",
        max_tokens=2,
        token_counter=len,
        include_system=True,
    )
    for i, msg in enumerate(trimmed):
        print(f"  {i+1}. {type(msg).__name__}: {msg.content}")
    
    # 策略2: 从人类消息开始
    print("\n策略2: 从人类消息开始,保留完整的对话对")
    print("-" * 60)
    trimmed = trim_messages(
        messages,
        strategy="last",
        max_tokens=4,
        token_counter=len,
        start_on="human",  # 确保从人类消息开始
        end_on=("human", "ai"),  # 在完整的对话对结束
    )
    for i, msg in enumerate(trimmed):
        print(f"  {i+1}. {type(msg).__name__}: {msg.content}")
    
    print("\n" + "=" * 60)
    print("裁剪策略总结:")
    print("  - strategy='last': 保留最后N条消息")
    print("  - max_tokens: 控制保留的消息数量或token数")
    print("  - include_system=True: 始终保留系统消息")
    print("  - start_on='human': 确保从人类消息开始")
    print("  - end_on=('human','ai'): 确保在完整对话对结束")
    print("=" * 60)


async def main():
    """主函数"""
    await demo_basic_trim()
    await demo_trim_in_graph()
    await demo_advanced_trim()


if __name__ == "__main__":
    asyncio.run(main())

