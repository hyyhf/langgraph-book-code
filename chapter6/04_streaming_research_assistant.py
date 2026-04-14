"""
第6章示例4: 流式输出实战 - 智能研究助手
演示如何在实际应用中使用流式输出提供实时反馈
"""

import asyncio
import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


# 定义状态
class ResearchState(TypedDict):
    topic: str  # 研究主题
    papers: List[dict]  # 找到的文献列表
    analysis: str  # 分析结果
    summary: str  # 研究摘要


# 节点1: 搜索文献
def search_papers(state: ResearchState) -> dict:
    """搜索相关文献"""
    writer = get_stream_writer()
    topic = state["topic"]
    
    # 发送开始搜索的消息
    writer({
        "type": "status",
        "stage": "search",
        "message": f"开始搜索关于'{topic}'的文献..."
    })
    
    # 模拟搜索多个数据库
    databases = ["arXiv", "Google Scholar", "IEEE Xplore"]
    all_papers = []
    
    for i, db in enumerate(databases, 1):
        time.sleep(0.5)  # 模拟搜索延迟
        
        # 发送搜索进度
        writer({
            "type": "progress",
            "stage": "search",
            "message": f"正在搜索 {db}...",
            "progress": i / len(databases),
            "current": i,
            "total": len(databases)
        })
        
        # 模拟找到一些文献
        papers_found = [
            {"title": f"{topic} 研究论文 {j} (来自{db})", "source": db}
            for j in range(1, 4)
        ]
        all_papers.extend(papers_found)
        
        # 发送找到的文献数量
        writer({
            "type": "result",
            "stage": "search",
            "message": f"在 {db} 找到 {len(papers_found)} 篇文献"
        })
    
    # 发送搜索完成消息
    writer({
        "type": "status",
        "stage": "search",
        "message": f"搜索完成!共找到 {len(all_papers)} 篇文献"
    })
    
    return {"papers": all_papers}


# 节点2: 分析文献
def analyze_papers(state: ResearchState) -> dict:
    """分析文献内容"""
    writer = get_stream_writer()
    papers = state["papers"]
    
    writer({
        "type": "status",
        "stage": "analyze",
        "message": f"开始分析 {len(papers)} 篇文献..."
    })
    
    analysis_results = []
    
    for i, paper in enumerate(papers[:5], 1):  # 只分析前5篇
        time.sleep(0.3)  # 模拟分析延迟
        
        # 发送分析进度
        writer({
            "type": "progress",
            "stage": "analyze",
            "message": f"正在分析: {paper['title']}",
            "progress": i / min(5, len(papers)),
            "current": i,
            "total": min(5, len(papers))
        })
        
        # 模拟分析结果
        analysis = f"文献{i}的关键发现: {paper['title']}提出了创新方法"
        analysis_results.append(analysis)
        
        # 发送分析结果
        writer({
            "type": "result",
            "stage": "analyze",
            "message": f"完成分析: {paper['title'][:30]}..."
        })
    
    writer({
        "type": "status",
        "stage": "analyze",
        "message": "文献分析完成!"
    })
    
    return {"analysis": "\n".join(analysis_results)}


# 节点3: 生成摘要
def generate_summary(state: ResearchState) -> dict:
    """生成研究摘要"""
    writer = get_stream_writer()
    
    writer({
        "type": "status",
        "stage": "summary",
        "message": "开始生成研究摘要..."
    })
    
    # 模拟逐步生成摘要
    summary_parts = [
        f"关于'{state['topic']}'的研究综述:\n",
        f"1. 共检索到 {len(state['papers'])} 篇相关文献\n",
        f"2. 主要研究方向包括...\n",
        f"3. 关键发现: {state['analysis'][:50]}...\n",
        f"4. 未来研究方向建议..."
    ]
    
    full_summary = ""
    for i, part in enumerate(summary_parts, 1):
        time.sleep(0.4)  # 模拟生成延迟
        full_summary += part
        
        # 发送生成进度
        writer({
            "type": "progress",
            "stage": "summary",
            "message": "正在生成摘要...",
            "progress": i / len(summary_parts),
            "current": i,
            "total": len(summary_parts),
            "partial_content": full_summary  # 发送部分内容
        })
    
    writer({
        "type": "status",
        "stage": "summary",
        "message": "研究摘要生成完成!"
    })
    
    return {"summary": full_summary}


async def main():
    """主函数:演示流式研究助手"""
    print("=" * 70)
    print("智能研究助手 - 流式输出演示")
    print("=" * 70)
    
    # 构建图
    builder = StateGraph(ResearchState)
    builder.add_node("search", search_papers)
    builder.add_node("analyze", analyze_papers)
    builder.add_node("summary", generate_summary)
    builder.add_edge(START, "search")
    builder.add_edge("search", "analyze")
    builder.add_edge("analyze", "summary")
    builder.add_edge("summary", END)
    graph = builder.compile()
    
    # 研究主题
    topic = "大语言模型在代码生成中的应用"
    print(f"\n研究主题: {topic}")
    print("=" * 70)
    
    # 使用多种流式模式
    print("\n开始研究(使用custom模式获取实时进度):")
    print("-" * 70)
    
    start_time = time.time()
    final_state = None
    
    async for chunk in graph.astream(
        {"topic": topic},
        stream_mode="custom"
    ):
        # 解析自定义数据
        msg_type = chunk.get("type", "unknown")
        stage = chunk.get("stage", "")
        message = chunk.get("message", "")
        
        if msg_type == "status":
            print(f"\n[{stage.upper()}] {message}")
        elif msg_type == "progress":
            progress = chunk.get("progress", 0)
            current = chunk.get("current", 0)
            total = chunk.get("total", 0)
            bar_length = 30
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  [{bar}] {current}/{total} - {message}")
        elif msg_type == "result":
            print(f"  ✓ {message}")
    
    # 获取最终状态
    print("\n" + "=" * 70)
    print("研究完成!")
    print("=" * 70)
    
    # 使用values模式获取最终状态
    async for state in graph.astream(
        {"topic": topic},
        stream_mode="values"
    ):
        final_state = state
    
    if final_state:
        print(f"\n找到文献数量: {len(final_state.get('papers', []))}")
        print(f"\n研究摘要:\n{final_state.get('summary', '')}")
    
    elapsed_time = time.time() - start_time
    print(f"\n总耗时: {elapsed_time:.2f} 秒")
    
    # 演示对比:不使用流式输出
    print("\n" + "=" * 70)
    print("对比:不使用流式输出(用户体验较差)")
    print("=" * 70)
    print("\n开始研究...")
    print("(用户只能看到这个消息,然后等待...)")
    
    start_time = time.time()
    result = await graph.ainvoke({"topic": topic})
    elapsed_time = time.time() - start_time
    
    print(f"\n研究完成!(等待了 {elapsed_time:.2f} 秒)")
    print(f"找到文献数量: {len(result.get('papers', []))}")
    
    print("\n" + "=" * 70)
    print("流式输出的优势:")
    print("  ✓ 实时反馈,用户知道系统正在工作")
    print("  ✓ 进度可见,减少用户焦虑")
    print("  ✓ 可以提前发现问题并中断")
    print("  ✓ 更好的用户体验")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

