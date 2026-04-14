"""
第6章示例7: 完整的记忆管理聊天机器人
综合演示持久化、流式输出和记忆管理
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

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# 加载环境变量
load_dotenv()


# 定义状态
class ChatState(MessagesState):
    """聊天机器人状态"""
    pass


# 系统消息
SYSTEM_MESSAGE = SystemMessage(content="""你是一个智能聊天助手,具有以下特点:
1. 你能够记住对话历史,提供连贯的对话体验
2. 你会智能地管理记忆,确保不会超出上下文限制
3. 你总是友好、专业、有帮助
4. 你会根据用户的历史对话提供个性化的回复
""")


# 定义聊天节点
async def chat_node(state: ChatState) -> dict:
    """
    聊天节点:处理用户消息并生成回复
    集成了消息裁剪功能
    """
    # 裁剪消息:保留系统消息 + 最近10条消息
    # 这确保传递给LLM的消息始终在合理范围内
    messages_to_process = trim_messages(
        state["messages"],
        strategy="last",
        max_tokens=200,  # 最大token数
        token_counter=count_tokens_approximately,
        include_system=True,  # 始终包含系统消息
        start_on="human",  # 从人类消息开始
        end_on=("human", "ai"),  # 在完整对话对结束
    )

    # 初始化DeepSeek模型
    llm = ChatOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME"),
        temperature=0.7
    )

    # 调用LLM生成回复
    response = await llm.ainvoke(messages_to_process)

    # 返回AI消息
    return {"messages": [response]}


async def demo_basic_chat():
    """演示1: 基础聊天功能"""
    print("=" * 70)
    print("演示1: 基础聊天功能(带记忆)")
    print("=" * 70)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        # 构建图
        builder = StateGraph(ChatState)
        builder.add_node("chat", chat_node)
        builder.add_edge(START, "chat")
        builder.add_edge("chat", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "user_alice"}}
        
        # 初始化对话(添加系统消息)
        await graph.aupdate_state(
            config,
            {"messages": [SYSTEM_MESSAGE]}
        )
        
        # 模拟多轮对话
        conversation = [
            "你好",
            "我叫Alice",
            "我喜欢编程",
            "我之前说了什么?",
            "你记得我的名字吗?"
        ]
        
        print("\n对话过程:")
        print("-" * 70)
        
        for user_input in conversation:
            # 用户输入
            print(f"\n用户: {user_input}")
            
            # 调用图
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config
            )
            
            # 助手回复
            assistant_response = result["messages"][-1].content
            print(f"助手: {assistant_response}")
        
        # 查看完整对话历史
        print("\n" + "=" * 70)
        print("完整对话历史:")
        print("-" * 70)
        state = await graph.aget_state(config)
        for i, msg in enumerate(state.values["messages"], 1):
            if isinstance(msg, SystemMessage):
                role = "系统"
            elif isinstance(msg, HumanMessage):
                role = "用户"
            else:
                role = "助手"
            content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
            print(f"{i}. {role}: {content}")
        
        print(f"\n总消息数: {len(state.values['messages'])}")


async def demo_multi_user():
    """演示2: 多用户场景"""
    print("\n" + "=" * 70)
    print("演示2: 多用户场景(独立记忆)")
    print("=" * 70)
    
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        builder = StateGraph(ChatState)
        builder.add_node("chat", chat_node)
        builder.add_edge(START, "chat")
        builder.add_edge("chat", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        # 用户1的对话
        print("\n用户1 (Alice) 的对话:")
        print("-" * 70)
        config_alice = {"configurable": {"thread_id": "user_alice"}}
        
        await graph.aupdate_state(config_alice, {"messages": [SYSTEM_MESSAGE]})
        
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我叫Alice,我喜欢Python")]},
            config=config_alice
        )
        print(f"Alice: 我叫Alice,我喜欢Python")
        print(f"助手: {result['messages'][-1].content}")
        
        # 用户2的对话
        print("\n用户2 (Bob) 的对话:")
        print("-" * 70)
        config_bob = {"configurable": {"thread_id": "user_bob"}}
        
        await graph.aupdate_state(config_bob, {"messages": [SYSTEM_MESSAGE]})
        
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我叫Bob,我喜欢Java")]},
            config=config_bob
        )
        print(f"Bob: 我叫Bob,我喜欢Java")
        print(f"助手: {result['messages'][-1].content}")
        
        # 验证记忆隔离
        print("\n验证记忆隔离:")
        print("-" * 70)
        
        # Alice询问
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我之前说我喜欢什么?")]},
            config=config_alice
        )
        print(f"Alice: 我之前说我喜欢什么?")
        print(f"助手: {result['messages'][-1].content}")
        
        # Bob询问
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我之前说我喜欢什么?")]},
            config=config_bob
        )
        print(f"Bob: 我之前说我喜欢什么?")
        print(f"助手: {result['messages'][-1].content}")
        
        # 查看各自的消息数量
        state_alice = await graph.aget_state(config_alice)
        state_bob = await graph.aget_state(config_bob)
        
        print(f"\nAlice的消息数: {len(state_alice.values['messages'])}")
        print(f"Bob的消息数: {len(state_bob.values['messages'])}")


async def demo_session_resume():
    """演示3: 会话恢复"""
    print("\n" + "=" * 70)
    print("演示3: 会话恢复(模拟程序重启)")
    print("=" * 70)
    
    # 使用文件数据库
    db_path = "chat_sessions.db"
    
    # 第一次运行:创建对话
    print("\n第一次运行:创建对话")
    print("-" * 70)
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        builder = StateGraph(ChatState)
        builder.add_node("chat", chat_node)
        builder.add_edge(START, "chat")
        builder.add_edge("chat", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "session_001"}}
        
        await graph.aupdate_state(config, {"messages": [SYSTEM_MESSAGE]})
        
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="我叫Charlie")]},
            config=config
        )
        print(f"用户: 我叫Charlie")
        print(f"助手: {result['messages'][-1].content}")
    
    print("\n[模拟程序重启...]")
    
    # 第二次运行:恢复对话
    print("\n第二次运行:恢复对话")
    print("-" * 70)
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        builder = StateGraph(ChatState)
        builder.add_node("chat", chat_node)
        builder.add_edge(START, "chat")
        builder.add_edge("chat", END)
        graph = builder.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "session_001"}}
        
        # 恢复之前的状态
        state = await graph.aget_state(config)
        print(f"恢复的消息数: {len(state.values['messages'])}")
        
        # 继续对话
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="你还记得我的名字吗?")]},
            config=config
        )
        print(f"\n用户: 你还记得我的名字吗?")
        print(f"助手: {result['messages'][-1].content}")
    
    # 清理数据库文件
    import os
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"\n[已清理数据库文件: {db_path}]")


async def main():
    """主函数"""
    await demo_basic_chat()
    await demo_multi_user()
    await demo_session_resume()
    
    print("\n" + "=" * 70)
    print("完整聊天机器人特性总结:")
    print("  ✓ 持久化: 对话历史自动保存,程序重启后可恢复")
    print("  ✓ 记忆管理: 智能裁剪消息,控制上下文大小")
    print("  ✓ 多用户支持: 通过thread_id隔离不同用户的对话")
    print("  ✓ 会话管理: 支持暂停和恢复对话")
    print("  ✓ 可扩展性: 易于切换存储后端(SQLite/PostgreSQL等)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

