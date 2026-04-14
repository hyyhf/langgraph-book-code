"""
第6章示例6: 记忆管理 - 消息删除和摘要
演示如何删除特定消息和生成对话摘要
"""

import asyncio
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# 定义状态
class State(MessagesState):
    """聊天状态"""
    summary: str = ""  # 对话摘要


async def demo_remove_messages():
    """演示1: 删除特定消息"""
    print("=" * 60)
    print("演示1: 删除特定消息")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        # 定义简单的聊天节点
        async def chatbot(state: State) -> dict:
            last_message = state["messages"][-1]
            response = f"收到: {last_message.content}"
            return {"messages": [AIMessage(content=response)]}
        
        # 构建图
        builder = StateGraph(State)
        builder.add_node("chatbot", chatbot)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "test_remove"}}
        
        # 创建一些对话
        print("\n创建对话:")
        print("-" * 60)
        messages_to_add = [
            "你好",
            "我叫Alice",
            "我喜欢编程",
            "今天天气不错"
        ]
        
        for msg in messages_to_add:
            await graph.ainvoke(
                {"messages": [HumanMessage(content=msg)]},
                config=config
            )
            print(f"  添加: {msg}")
        
        # 查看当前消息
        state = await graph.aget_state(config)
        print(f"\n当前消息数量: {len(state.values['messages'])}")
        for i, msg in enumerate(state.values['messages']):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"  {i+1}. [{msg.id[:8]}] {role}: {msg.content}")
        
        # 删除特定消息(删除第2条用户消息)
        print("\n删除第2条用户消息('我叫Alice'):")
        print("-" * 60)
        
        # 找到要删除的消息
        messages = state.values['messages']
        user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        message_to_delete = user_messages[1]  # 第2条用户消息
        
        # 使用update_state删除消息
        await graph.aupdate_state(
            config,
            {"messages": [RemoveMessage(id=message_to_delete.id)]}
        )
        
        # 查看删除后的消息
        state = await graph.aget_state(config)
        print(f"删除后消息数量: {len(state.values['messages'])}")
        for i, msg in enumerate(state.values['messages']):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"  {i+1}. {role}: {msg.content}")
        
        # 删除最早的2条消息
        print("\n删除最早的2条消息:")
        print("-" * 60)
        messages = state.values['messages']
        messages_to_remove = messages[:2]
        
        await graph.aupdate_state(
            config,
            {"messages": [RemoveMessage(id=msg.id) for msg in messages_to_remove]}
        )
        
        state = await graph.aget_state(config)
        print(f"删除后消息数量: {len(state.values['messages'])}")
        for i, msg in enumerate(state.values['messages']):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"  {i+1}. {role}: {msg.content}")


async def demo_remove_all():
    """演示2: 删除所有消息"""
    print("\n" + "=" * 60)
    print("演示2: 删除所有消息")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        async def chatbot(state: State) -> dict:
            return {"messages": [AIMessage(content="回复")]}
        
        builder = StateGraph(State)
        builder.add_node("chatbot", chatbot)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "test_remove_all"}}
        
        # 创建一些消息
        for i in range(3):
            await graph.ainvoke(
                {"messages": [HumanMessage(content=f"消息{i+1}")]},
                config=config
            )
        
        state = await graph.aget_state(config)
        print(f"\n删除前消息数量: {len(state.values['messages'])}")
        
        # 删除所有消息
        await graph.aupdate_state(
            config,
            {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}
        )
        
        state = await graph.aget_state(config)
        print(f"删除后消息数量: {len(state.values['messages'])}")


async def demo_undo_last_message():
    """演示3: 撤回最后一条消息"""
    print("\n" + "=" * 60)
    print("演示3: 实现'撤回'功能")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        async def chatbot(state: State) -> dict:
            last_message = state["messages"][-1]
            return {"messages": [AIMessage(content=f"回复: {last_message.content}")]}
        
        builder = StateGraph(State)
        builder.add_node("chatbot", chatbot)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "test_undo"}}
        
        # 用户发送消息
        print("\n用户发送消息:")
        await graph.ainvoke(
            {"messages": [HumanMessage(content="这是一条错误的消息")]},
            config=config
        )
        
        state = await graph.aget_state(config)
        for msg in state.values['messages']:
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"  {role}: {msg.content}")
        
        # 用户想要撤回(删除最后一条用户消息和对应的AI回复)
        print("\n用户撤回消息:")
        print("-" * 60)
        messages = state.values['messages']
        # 删除最后2条消息(用户消息 + AI回复)
        to_remove = messages[-2:]
        
        await graph.aupdate_state(
            config,
            {"messages": [RemoveMessage(id=msg.id) for msg in to_remove]}
        )
        
        state = await graph.aget_state(config)
        print(f"撤回后消息数量: {len(state.values['messages'])}")


async def demo_summarization():
    """演示4: 对话摘要"""
    print("\n" + "=" * 60)
    print("演示4: 对话摘要")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        # 定义摘要节点
        async def summarize_conversation(state: State) -> dict:
            """生成对话摘要并删除旧消息"""
            messages = state["messages"]
            
            # 如果消息少于6条,不需要摘要
            if len(messages) < 6:
                return {}
            
            # 获取现有摘要
            existing_summary = state.get("summary", "")
            
            # 识别需要摘要的消息(保留最后4条,摘要之前的)
            messages_to_summarize = messages[:-4]
            messages_to_keep = messages[-4:]
            
            # 生成摘要(在实际应用中应该调用LLM)
            if existing_summary:
                new_summary = f"{existing_summary}\n继续讨论了{len(messages_to_summarize)}个话题"
            else:
                topics = [msg.content for msg in messages_to_summarize if isinstance(msg, HumanMessage)]
                new_summary = f"之前讨论的话题包括: {', '.join(topics[:3])}"
            
            # 删除被摘要的消息
            remove_messages = [RemoveMessage(id=msg.id) for msg in messages_to_summarize]
            
            # 添加摘要作为系统消息
            summary_message = SystemMessage(content=f"[对话摘要] {new_summary}")
            
            return {
                "messages": remove_messages + [summary_message],
                "summary": new_summary
            }
        
        # 定义聊天节点
        async def chatbot(state: State) -> dict:
            last_message = state["messages"][-1]
            return {"messages": [AIMessage(content=f"回复: {last_message.content}")]}
        
        # 构建图
        builder = StateGraph(State)
        builder.add_node("chatbot", chatbot)
        builder.add_node("summarize", summarize_conversation)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", "summarize")
        builder.add_edge("summarize", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "test_summary"}}
        
        # 创建多轮对话
        print("\n创建多轮对话:")
        print("-" * 60)
        topics = [
            "Python编程",
            "机器学习",
            "深度学习",
            "自然语言处理",
            "计算机视觉",
            "强化学习",
            "LangGraph框架"
        ]
        
        for i, topic in enumerate(topics, 1):
            await graph.ainvoke(
                {"messages": [HumanMessage(content=f"我想学习{topic}")]},
                config=config
            )
            
            state = await graph.aget_state(config)
            print(f"\n轮次{i}: 消息数量={len(state.values['messages'])}")
            
            # 显示摘要(如果有)
            if state.values.get("summary"):
                print(f"  摘要: {state.values['summary']}")
            
            # 显示最近的消息
            recent_messages = state.values['messages'][-2:]
            for msg in recent_messages:
                role = "用户" if isinstance(msg, HumanMessage) else "助手" if isinstance(msg, AIMessage) else "系统"
                content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                print(f"  {role}: {content}")
        
        # 查看最终状态
        print("\n最终状态:")
        print("-" * 60)
        state = await graph.aget_state(config)
        print(f"总消息数量: {len(state.values['messages'])}")
        print(f"摘要: {state.values.get('summary', '无')}")
        
        print("\n所有消息:")
        for i, msg in enumerate(state.values['messages'], 1):
            role = "用户" if isinstance(msg, HumanMessage) else "助手" if isinstance(msg, AIMessage) else "系统"
            print(f"  {i}. {role}: {msg.content}")


async def main():
    """主函数"""
    await demo_remove_messages()
    await demo_remove_all()
    await demo_undo_last_message()
    await demo_summarization()
    
    print("\n" + "=" * 60)
    print("记忆管理技术总结:")
    print("  1. trim_messages: 裁剪消息,控制数量")
    print("  2. RemoveMessage: 删除特定消息")
    print("  3. 对话摘要: 压缩历史,保留关键信息")
    print("  4. 组合策略: 多层次记忆系统")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

