"""
第6章示例3: 流式输出模式演示
演示values、updates、messages、custom等多种流式模式
"""

import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


# 定义状态
class State(TypedDict):
    topic: str
    refined_topic: str
    joke: str
    analysis: str


# 定义节点
def refine_topic(state: State) -> dict:
    """节点1: 优化主题"""
    print("  [节点执行] refine_topic 正在执行...")
    refined = state["topic"] + " 和猫"
    return {"refined_topic": refined}


def generate_joke(state: State) -> dict:
    """节点2: 生成笑话"""
    print("  [节点执行] generate_joke 正在执行...")
    joke = f"这是一个关于{state['refined_topic']}的笑话"
    return {"joke": joke}


def analyze_joke(state: State) -> dict:
    """节点3: 分析笑话"""
    print("  [节点执行] analyze_joke 正在执行...")
    analysis = f"笑话分析: 主题是'{state['refined_topic']}', 内容是'{state['joke']}'"
    return {"analysis": analysis}


async def demo_values_mode():
    """演示1: values模式 - 输出完整状态"""
    print("=" * 60)
    print("演示1: values模式 - 输出完整状态")
    print("=" * 60)
    
    # 构建图
    builder = StateGraph(State)
    builder.add_node("refine_topic", refine_topic)
    builder.add_node("generate_joke", generate_joke)
    builder.add_node("analyze_joke", analyze_joke)
    builder.add_edge(START, "refine_topic")
    builder.add_edge("refine_topic", "generate_joke")
    builder.add_edge("generate_joke", "analyze_joke")
    builder.add_edge("analyze_joke", END)
    graph = builder.compile()
    
    print("\n使用stream方法,stream_mode='values':")
    print("-" * 60)
    
    step = 0
    async for chunk in graph.astream(
        {"topic": "冰淇淋"},
        stream_mode="values"
    ):
        step += 1
        print(f"\n步骤 {step}:")
        print(f"  完整状态: {chunk}")
    
    print("\n" + "=" * 60)
    print("values模式特点:")
    print("  - 每次输出完整的状态快照")
    print("  - 适合UI渲染,可以直接使用状态更新界面")
    print("  - 数据量较大,包含所有字段")
    print("=" * 60)


async def demo_updates_mode():
    """演示2: updates模式 - 只输出状态变化"""
    print("\n" + "=" * 60)
    print("演示2: updates模式 - 只输出状态变化")
    print("=" * 60)
    
    # 使用相同的图
    builder = StateGraph(State)
    builder.add_node("refine_topic", refine_topic)
    builder.add_node("generate_joke", generate_joke)
    builder.add_node("analyze_joke", analyze_joke)
    builder.add_edge(START, "refine_topic")
    builder.add_edge("refine_topic", "generate_joke")
    builder.add_edge("generate_joke", "analyze_joke")
    builder.add_edge("analyze_joke", END)
    graph = builder.compile()
    
    print("\n使用stream方法,stream_mode='updates':")
    print("-" * 60)
    
    # 手动维护状态(演示如何使用updates模式)
    current_state = {"topic": "冰淇淋"}
    
    async for chunk in graph.astream(
        {"topic": "冰淇淋"},
        stream_mode="updates"
    ):
        print(f"\n收到更新: {chunk}")
        # 手动合并更新到当前状态
        for node_name, node_update in chunk.items():
            print(f"  节点 '{node_name}' 的更新: {node_update}")
            current_state.update(node_update)
    
    print(f"\n最终状态(手动合并): {current_state}")
    
    print("\n" + "=" * 60)
    print("updates模式特点:")
    print("  - 只输出状态的变化部分")
    print("  - 网络传输效率高,数据量小")
    print("  - 需要接收方手动维护和合并状态")
    print("  - 适合性能敏感的场景")
    print("=" * 60)


async def demo_custom_mode():
    """演示3: custom模式 - 自定义流式数据"""
    print("\n" + "=" * 60)
    print("演示3: custom模式 - 自定义流式数据")
    print("=" * 60)
    
    # 定义带有自定义流式输出的节点
    def search_node(state: State) -> dict:
        """搜索节点:发送自定义进度信息"""
        writer = get_stream_writer()
        
        # 发送进度信息
        writer({"type": "progress", "message": "开始搜索文献..."})
        
        # 模拟搜索过程
        import time
        time.sleep(0.5)
        writer({"type": "progress", "message": "找到 10 篇相关文献"})
        
        time.sleep(0.5)
        writer({"type": "progress", "message": "搜索完成"})
        
        return {"refined_topic": state["topic"] + " 研究"}
    
    def analyze_node(state: State) -> dict:
        """分析节点:发送自定义进度信息"""
        writer = get_stream_writer()
        
        for i in range(1, 4):
            import time
            time.sleep(0.3)
            writer({
                "type": "progress",
                "message": f"正在分析第 {i}/3 篇文献...",
                "progress": i / 3
            })
        
        return {"analysis": "分析完成"}
    
    # 构建图
    builder = StateGraph(State)
    builder.add_node("search", search_node)
    builder.add_node("analyze", analyze_node)
    builder.add_edge(START, "search")
    builder.add_edge("search", "analyze")
    builder.add_edge("analyze", END)
    graph = builder.compile()
    
    print("\n使用stream方法,stream_mode='custom':")
    print("-" * 60)
    
    async for chunk in graph.astream(
        {"topic": "人工智能"},
        stream_mode="custom"
    ):
        print(f"  自定义数据: {chunk}")
    
    print("\n" + "=" * 60)
    print("custom模式特点:")
    print("  - 可以发送任意自定义数据")
    print("  - 适合发送进度信息、日志、调试信息")
    print("  - 使用get_stream_writer()发送数据")
    print("  - 提供最大的灵活性")
    print("=" * 60)


async def demo_multiple_modes():
    """演示4: 同时使用多种流式模式"""
    print("\n" + "=" * 60)
    print("演示4: 同时使用多种流式模式")
    print("=" * 60)
    
    # 定义带有自定义输出的节点
    def process_node(state: State) -> dict:
        """处理节点"""
        writer = get_stream_writer()
        writer({"custom_info": "处理开始"})
        
        result = state["topic"] + " 已处理"
        
        writer({"custom_info": "处理完成"})
        return {"refined_topic": result}
    
    # 构建图
    builder = StateGraph(State)
    builder.add_node("process", process_node)
    builder.add_edge(START, "process")
    builder.add_edge("process", END)
    graph = builder.compile()
    
    print("\n使用stream方法,stream_mode=['updates', 'custom']:")
    print("-" * 60)
    
    async for mode, chunk in graph.astream(
        {"topic": "测试"},
        stream_mode=["updates", "custom"]
    ):
        print(f"\n模式: {mode}")
        print(f"  数据: {chunk}")
    
    print("\n" + "=" * 60)
    print("多模式特点:")
    print("  - 可以同时接收多种类型的数据")
    print("  - 返回(模式, 数据)元组")
    print("  - 适合需要多种信息的复杂场景")
    print("=" * 60)


async def demo_comparison():
    """演示5: 对比不同模式的输出"""
    print("\n" + "=" * 60)
    print("演示5: 对比不同模式的输出")
    print("=" * 60)
    
    # 构建简单的图
    builder = StateGraph(State)
    builder.add_node("refine", refine_topic)
    builder.add_node("joke", generate_joke)
    builder.add_edge(START, "refine")
    builder.add_edge("refine", "joke")
    builder.add_edge("joke", END)
    graph = builder.compile()
    
    input_data = {"topic": "编程"}
    
    # values模式
    print("\nvalues模式输出:")
    print("-" * 60)
    async for chunk in graph.astream(input_data, stream_mode="values"):
        print(f"  {chunk}")
    
    # updates模式
    print("\nupdates模式输出:")
    print("-" * 60)
    async for chunk in graph.astream(input_data, stream_mode="updates"):
        print(f"  {chunk}")
    
    print("\n" + "=" * 60)
    print("模式选择建议:")
    print("  - values: UI渲染、需要完整状态")
    print("  - updates: 性能优化、增量更新")
    print("  - custom: 进度反馈、调试信息")
    print("  - 多模式: 复杂场景、需要多种信息")
    print("=" * 60)


async def main():
    """主函数"""
    await demo_values_mode()
    await demo_updates_mode()
    await demo_custom_mode()
    await demo_multiple_modes()
    await demo_comparison()


if __name__ == "__main__":
    asyncio.run(main())

