"""
第5章高级示例: 带质量检查和迭代改进的问答助手

这个示例展示了LangGraph的高级特性:
1. 条件边 - 根据答案质量决定下一步
2. 循环迭代 - 如果质量不够就改进答案
3. 最大迭代次数限制 - 避免无限循环
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END


# ============================================================================
# 定义State
# ============================================================================

class AdvancedQAState(TypedDict):
    """带质量检查的问答助手状态"""
    question: str
    documents: List[str]
    answer: str
    quality_score: float  # 答案质量评分 (0-1)
    iteration: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    feedback: str  # 改进建议


# ============================================================================
# Node函数
# ============================================================================

def retrieve_documents(state: AdvancedQAState) -> dict:
    """检索文档"""
    print(f"\n[检索] 正在检索文档...")

    mock_documents = [
        "LangGraph是一个用于构建智能体应用的框架,采用图结构来组织执行流程。",
        "LangGraph的核心组件包括State(状态)、Node(节点)和Edge(边)。",
        "使用LangGraph可以实现条件分支、循环迭代等复杂控制流。"
    ]

    print(f"[检索] 检索到 {len(mock_documents)} 个文档")

    return {"documents": mock_documents}


def generate_answer(state: AdvancedQAState) -> dict:
    """生成答案"""
    iteration = state.get("iteration", 0)
    feedback = state.get("feedback", "")

    print(f"\n[生成] 正在生成答案 (第 {iteration + 1} 次)...")

    if feedback:
        print(f"   改进建议: {feedback}")
    
    # 模拟答案生成,迭代次数越多,答案越详细
    if iteration == 0:
        # 第一次生成 - 简单答案
        answer = "LangGraph是一个智能体框架。"
    elif iteration == 1:
        # 第二次生成 - 加入更多细节
        answer = "LangGraph是一个用于构建智能体应用的框架,它使用图结构来组织执行流程,包括State、Node和Edge三个核心组件。"
    else:
        # 第三次及以后 - 完整详细的答案
        answer = """LangGraph是一个专门用于构建智能体应用的强大框架。

核心特点:
- 采用图结构来组织和管理智能体的执行流程
- 提供清晰的状态管理机制
- 支持复杂的控制流,如条件分支和循环迭代

三大核心组件:
1. State: 定义智能体需要维护的数据结构
2. Node: 代表具体的计算步骤
3. Edge: 定义节点之间的转移关系

通过这种设计,LangGraph能够轻松实现复杂的多步骤工作流。"""

    print(f"[生成] 答案生成完成 (长度: {len(answer)} 字符)")

    return {
        "answer": answer,
        "iteration": iteration + 1
    }


def evaluate_quality(state: AdvancedQAState) -> dict:
    """评估答案质量"""
    answer = state["answer"]
    iteration = state["iteration"]

    print(f"\n[评估] 正在评估答案质量...")

    # 模拟质量评估 - 基于答案长度和迭代次数
    # 实际应用中,这里会使用LLM来评估答案质量
    if len(answer) < 50:
        score = 0.3
        feedback = "答案过于简短,需要提供更多细节和解释"
    elif len(answer) < 150:
        score = 0.6
        feedback = "答案基本完整,但可以更详细地说明核心组件和特点"
    else:
        score = 0.9
        feedback = "答案质量良好"

    # 随着迭代次数增加,适当提高评分(避免无限循环)
    score = min(1.0, score + iteration * 0.1)

    print(f"[评估] 质量评分: {score:.2f}")
    print(f"   反馈: {feedback}")

    return {
        "quality_score": score,
        "feedback": feedback
    }


def format_final_response(state: AdvancedQAState) -> dict:
    """格式化最终响应"""
    print(f"\n[格式化] 正在格式化最终响应...")

    response = f"""{'='*60}
最终答案 (经过 {state['iteration']} 次迭代优化)
{'='*60}

{state['answer']}

{'='*60}
质量评分: {state['quality_score']:.2f} / 1.00
{'='*60}"""

    print("[格式化] 格式化完成")

    return {"answer": response}


# ============================================================================
# 条件边路由函数
# ============================================================================

def should_continue(state: AdvancedQAState) -> Literal["improve", "format"]:
    """决定是否需要继续改进答案

    这是一个条件边的路由函数,它会根据当前状态决定下一步:
    - 如果质量足够好,或者达到最大迭代次数,就进入格式化阶段
    - 否则,继续改进答案

    Returns:
        "improve": 继续改进答案
        "format": 进入格式化阶段
    """
    quality_score = state["quality_score"]
    iteration = state["iteration"]
    max_iterations = state["max_iterations"]

    print(f"\n[决策] 当前质量: {quality_score:.2f}, 迭代次数: {iteration}/{max_iterations}")

    # 判断是否需要继续改进
    if quality_score >= 0.8:
        print("   -> 质量达标,进入格式化阶段")
        return "format"
    elif iteration >= max_iterations:
        print("   -> 达到最大迭代次数,进入格式化阶段")
        return "format"
    else:
        print("   -> 质量不足,继续改进")
        return "improve"


# ============================================================================
# 构建图
# ============================================================================

def build_advanced_graph():
    """构建带质量检查和迭代改进的问答图"""
    print("\n[构建] 正在构建高级状态图...")

    builder = StateGraph(AdvancedQAState)

    # 添加节点
    builder.add_node("retrieve", retrieve_documents)
    builder.add_node("generate", generate_answer)
    builder.add_node("evaluate", evaluate_quality)
    builder.add_node("format", format_final_response)

    # 添加边
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "evaluate")

    # 添加条件边 - 这是关键!
    # 根据质量评估结果,决定是继续改进还是格式化输出
    builder.add_conditional_edges(
        "evaluate",  # 从evaluate节点出发
        should_continue,  # 使用should_continue函数决定路由
        {
            "improve": "generate",  # 如果返回"improve",回到generate节点
            "format": "format"  # 如果返回"format",进入format节点
        }
    )

    builder.add_edge("format", END)

    graph = builder.compile()

    print("[构建] 高级状态图构建完成")
    print("\n图结构:")
    print("  START -> retrieve -> generate -> evaluate")
    print("                        ^          |")
    print("                        +- improve-+ (条件边)")
    print("                                   |")
    print("                                format -> END")

    return graph


# ============================================================================
# 可视化
# ============================================================================

def visualize_graph(graph):
    """可视化图结构"""
    try:
        png_data = graph.get_graph().draw_mermaid_png()

        with open("advanced_qa_graph.png", "wb") as f:
            f.write(png_data)

        print("\n[可视化] 图结构已保存到 advanced_qa_graph.png")

    except Exception as e:
        print(f"\n[警告] 可视化失败: {e}")


# ============================================================================
# 执行示例
# ============================================================================

def run_advanced_example():
    """运行高级示例"""
    print("=" * 70)
    print("LangGraph高级示例 - 带质量检查和迭代改进的问答助手")
    print("=" * 70)

    # 构建图
    graph = build_advanced_graph()

    # 可视化
    visualize_graph(graph)

    # 准备初始状态
    initial_state = {
        "question": "什么是LangGraph?",
        "documents": [],
        "answer": "",
        "quality_score": 0.0,
        "iteration": 0,
        "max_iterations": 3,  # 最多迭代3次
        "feedback": ""
    }

    print("\n" + "=" * 70)
    print(f"[输入] 问题: {initial_state['question']}")
    print(f"[配置] 最大迭代次数: {initial_state['max_iterations']}")
    print("=" * 70)

    # 执行图
    print("\n[执行] 开始执行图...\n")
    result = graph.invoke(initial_state)

    # 显示结果
    print("\n" + "=" * 70)
    print("[输出] 执行完成!")
    print("=" * 70)
    print(result["answer"])

    return result


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    result = run_advanced_example()

    print("\n[完成] 高级示例执行完成!")
    print("\n[要点] 关键要点:")
    print("  1. 条件边可以根据状态动态决定下一步执行哪个节点")
    print("  2. 通过条件边可以实现循环迭代,不断改进结果")
    print("  3. 必须设置退出条件(如最大迭代次数),避免无限循环")
    print("  4. 这种模式在很多场景下都很有用,如代码生成与调试、文本优化等")

