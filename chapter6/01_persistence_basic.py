"""
第6章示例1: 持久化基础示例
演示如何使用AsyncSqliteSaver实现对话历史的持久化
"""

import asyncio
import os
import sys
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

# 设置输出编码为UTF-8,避免emoji显示问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# 加载环境变量
load_dotenv()


# 定义状态Schema
# 使用MessagesState作为基类,它已经包含了messages字段和add_messages reducer
class State(MessagesState):
    """聊天机器人的状态,包含对话历史"""
    pass


# 定义聊天节点
async def chatbot_node(state: State) -> dict:
    """
    聊天节点:调用DeepSeek LLM生成回复
    """
    # 初始化DeepSeek模型
    llm = ChatOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME"),
        temperature=0.7
    )

    # 调用LLM生成回复
    response = await llm.ainvoke(state["messages"])

    # 返回AI消息
    return {"messages": [response]}


async def main():
    """主函数:演示持久化功能"""
    
    print("=" * 60)
    print("示例1: 基础持久化功能演示")
    print("=" * 60)
    
    # 创建AsyncSqliteSaver实例
    # 使用":memory:"创建内存数据库(仅用于演示)
    # 在实际应用中,应该使用文件路径,如: "checkpoints.db"
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        
        # 构建图
        builder = StateGraph(State)
        builder.add_node("chatbot", chatbot_node)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        
        # 编译图,指定checkpointer
        graph = builder.compile(checkpointer=checkpointer)
        
        # 配置对象,指定thread_id
        # thread_id用于标识不同的对话会话
        config = {"configurable": {"thread_id": "user_001"}}
        
        print("\n第一轮对话:")
        print("-" * 60)
        
        # 第一次调用:用户说"你好"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="你好")]},
            config=config
        )
        print(f"用户: 你好")
        print(f"助手: {result['messages'][-1].content}")
        
        print("\n第二轮对话:")
        print("-" * 60)
        
        # 第二次调用:用户说"我叫Alice"
        # 注意:这里我们使用相同的thread_id,所以图会自动加载之前的对话历史
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我叫Alice")]},
            config=config
        )
        print(f"用户: 我叫Alice")
        print(f"助手: {result['messages'][-1].content}")
        
        print("\n第三轮对话:")
        print("-" * 60)
        
        # 第三次调用:用户问"我刚才说了什么?"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我刚才说了什么?")]},
            config=config
        )
        print(f"用户: 我刚才说了什么?")
        print(f"助手: {result['messages'][-1].content}")
        
        # 查看完整的对话历史
        print("\n完整对话历史:")
        print("-" * 60)
        state = await graph.aget_state(config)
        for i, msg in enumerate(state.values["messages"], 1):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"{i}. {role}: {msg.content}")
        
        # 查看检查点历史
        print("\n检查点历史:")
        print("-" * 60)
        checkpoint_history = []
        async for checkpoint in checkpointer.alist(config):
            checkpoint_history.append(checkpoint)
        
        print(f"共有 {len(checkpoint_history)} 个检查点")
        for i, cp in enumerate(checkpoint_history[:3], 1):  # 只显示前3个
            print(f"\n检查点 {i}:")
            print(f"  - ID: {cp.checkpoint['id'][:20]}...")
            print(f"  - 消息数量: {len(cp.checkpoint['channel_values'].get('messages', []))}")
        
        # 演示多用户场景
        print("\n" + "=" * 60)
        print("示例2: 多用户并发场景")
        print("=" * 60)
        
        # 用户2的对话
        config_user2 = {"configurable": {"thread_id": "user_002"}}
        
        print("\n用户2的对话:")
        print("-" * 60)
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我是Bob")]},
            config=config_user2
        )
        print(f"用户2: 我是Bob")
        print(f"助手: {result['messages'][-1].content}")
        
        # 验证用户1的对话历史没有被影响
        print("\n验证用户1的对话历史:")
        print("-" * 60)
        state_user1 = await graph.aget_state(config)
        print(f"用户1的消息数量: {len(state_user1.values['messages'])}")
        print(f"用户1的最后一条消息: {state_user1.values['messages'][-1].content}")
        
        # 验证用户2的对话历史是独立的
        print("\n验证用户2的对话历史:")
        print("-" * 60)
        state_user2 = await graph.aget_state(config_user2)
        print(f"用户2的消息数量: {len(state_user2.values['messages'])}")
        print(f"用户2的最后一条消息: {state_user2.values['messages'][-1].content}")


if __name__ == "__main__":
    asyncio.run(main())

