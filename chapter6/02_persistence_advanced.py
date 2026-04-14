"""
第6章示例2: 持久化进阶示例
演示如何使用文件数据库和PostgreSQL进行持久化
"""

import asyncio
import os
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # 需要安装: pip install langgraph-checkpoint-postgres


async def chatbot_node(state: MessagesState) -> dict:
    """聊天节点:模拟LLM生成回复"""
    last_message = state["messages"][-1]
    response_text = f"收到消息: '{last_message.content}'"
    return {"messages": [AIMessage(content=response_text)]}


async def demo_sqlite_file():
    """演示1: 使用SQLite文件数据库"""
    print("=" * 60)
    print("演示1: 使用SQLite文件数据库")
    print("=" * 60)
    
    # 数据库文件路径
    db_path = "chapter6_checkpoints.db"
    
    # 创建AsyncSqliteSaver实例,使用文件数据库
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        
        # 构建图
        builder = StateGraph(MessagesState)
        builder.add_node("chatbot", chatbot_node)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "session_001"}}
        
        # 第一次运行:创建新对话
        print("\n第一次运行:创建新对话")
        print("-" * 60)
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="第一条消息")]},
            config=config
        )
        print(f"消息数量: {len(result['messages'])}")
        
        # 第二次运行:继续对话
        print("\n第二次运行:继续对话")
        print("-" * 60)
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="第二条消息")]},
            config=config
        )
        print(f"消息数量: {len(result['messages'])}")
        
    print(f"\n数据库文件已创建: {db_path}")
    print(f"文件大小: {os.path.getsize(db_path)} 字节")
    
    # 演示程序重启后恢复对话
    print("\n" + "=" * 60)
    print("演示2: 程序重启后恢复对话")
    print("=" * 60)
    
    # 重新打开数据库(模拟程序重启)
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        builder = StateGraph(MessagesState)
        builder.add_node("chatbot", chatbot_node)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "session_001"}}
        
        # 获取之前的状态
        print("\n恢复之前的对话状态:")
        print("-" * 60)
        state = await graph.aget_state(config)
        print(f"恢复的消息数量: {len(state.values['messages'])}")
        for i, msg in enumerate(state.values["messages"], 1):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"{i}. {role}: {msg.content}")
        
        # 继续对话
        print("\n继续对话:")
        print("-" * 60)
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="第三条消息(重启后)")]},
            config=config
        )
        print(f"当前消息数量: {len(result['messages'])}")
    
    # 清理数据库文件
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"\n已清理数据库文件: {db_path}")


async def demo_postgres():
    """演示3: 使用PostgreSQL数据库(需要PostgreSQL服务)"""
    print("\n" + "=" * 60)
    print("演示3: 使用PostgreSQL数据库")
    print("=" * 60)
    
    print("""
注意:此示例需要PostgreSQL数据库服务。

安装依赖:
    pip install langgraph-checkpoint-postgres psycopg

配置数据库:
    1. 安装PostgreSQL数据库
    2. 创建数据库: CREATE DATABASE langgraph_checkpoints;
    3. 配置连接字符串

示例代码:
    
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    
    # PostgreSQL连接字符串
    DB_URI = "postgresql://username:password@localhost:5432/langgraph_checkpoints"
    
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 首次使用时需要初始化数据库表
        # await checkpointer.setup()
        
        # 构建图
        builder = StateGraph(MessagesState)
        builder.add_node("chatbot", chatbot_node)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "user_001"}}
        
        # 使用图
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="你好")]},
            config=config
        )

PostgreSQL的优势:
    - 支持高并发访问
    - 提供ACID事务保证
    - 支持复杂查询和索引
    - 适合生产环境部署
    - 支持水平扩展

适用场景:
    - 生产环境部署
    - 多用户并发访问
    - 需要复杂查询的场景
    - 需要高可用性的系统
    """)


async def demo_thread_management():
    """演示4: 线程管理和配置"""
    print("\n" + "=" * 60)
    print("演示4: 线程管理和配置")
    print("=" * 60)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        builder = StateGraph(MessagesState)
        builder.add_node("chatbot", chatbot_node)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        # 策略1: 基于用户ID的线程管理
        print("\n策略1: 基于用户ID")
        print("-" * 60)
        user_id = "alice"
        config = {"configurable": {"thread_id": f"user_{user_id}"}}
        await graph.ainvoke(
            {"messages": [HumanMessage(content="我是Alice")]},
            config=config
        )
        print(f"为用户 {user_id} 创建线程: user_{user_id}")
        
        # 策略2: 基于会话ID的线程管理
        print("\n策略2: 基于会话ID")
        print("-" * 60)
        import uuid
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}
        await graph.ainvoke(
            {"messages": [HumanMessage(content="新会话")]},
            config=config
        )
        print(f"创建新会话线程: {session_id[:20]}...")
        
        # 策略3: 基于用户+会话的组合线程管理
        print("\n策略3: 用户+会话组合")
        print("-" * 60)
        user_id = "bob"
        session_num = 1
        config = {"configurable": {"thread_id": f"{user_id}_session_{session_num}"}}
        await graph.ainvoke(
            {"messages": [HumanMessage(content="Bob的第一个会话")]},
            config=config
        )
        print(f"创建组合线程: {user_id}_session_{session_num}")
        
        # 策略4: 基于时间的线程管理
        print("\n策略4: 基于时间")
        print("-" * 60)
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        config = {"configurable": {"thread_id": f"daily_{date_str}"}}
        await graph.ainvoke(
            {"messages": [HumanMessage(content="今天的对话")]},
            config=config
        )
        print(f"创建日期线程: daily_{date_str}")
        
        # 查看所有线程
        print("\n所有线程:")
        print("-" * 60)
        all_threads = set()
        async for checkpoint in checkpointer.alist(None):
            thread_id = checkpoint.config["configurable"]["thread_id"]
            all_threads.add(thread_id)
        
        for i, thread_id in enumerate(sorted(all_threads), 1):
            print(f"{i}. {thread_id}")


async def main():
    """主函数"""
    # 演示1: SQLite文件数据库
    await demo_sqlite_file()
    
    # 演示2: PostgreSQL(仅显示说明)
    await demo_postgres()
    
    # 演示3: 线程管理
    await demo_thread_management()


if __name__ == "__main__":
    asyncio.run(main())

