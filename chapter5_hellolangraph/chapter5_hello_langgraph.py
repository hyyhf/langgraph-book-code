"""
第5章示例代码: Hello LangGraph
一个简单但完整的智能问答助手示例

功能:
1. 接收用户问题
2. 检索相关文档
3. 基于文档生成答案
4. 格式化并返回结果
"""

from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END


# ============================================================================
# 第一步: 定义State
# ============================================================================

class QAState(TypedDict):
    """问答助手的状态定义
    
    这个State包含了整个问答流程中需要维护的所有信息:
    - question: 用户的问题(输入)
    - documents: 检索到的相关文档(中间状态)
    - answer: 生成的答案(中间状态)
    - formatted_response: 格式化后的最终响应(输出)
    - retrieval_count: 检索次数,用于演示状态更新
    """
    question: str
    documents: List[str]
    answer: str
    formatted_response: str
    retrieval_count: int


# ============================================================================
# 第二步: 实现Node函数
# ============================================================================

def retrieve_documents(state: QAState) -> dict:
    """文档检索节点
    
    模拟从知识库中检索相关文档的过程。
    在实际应用中,这里会调用向量数据库或搜索引擎。
    
    Args:
        state: 当前状态,包含用户问题
        
    Returns:
        包含检索到的文档列表的字典
    """
    question = state["question"]
    
    # 模拟文档检索过程
    # 实际应用中,这里会调用向量数据库、Elasticsearch等
    print(f"[检索] 正在检索关于 '{question}' 的文档...")

    # 模拟检索结果
    mock_documents = [
        f"文档1: LangGraph是一个用于构建智能体应用的框架,采用图结构来组织执行流程。",
        f"文档2: LangGraph的核心组件包括State(状态)、Node(节点)和Edge(边)。",
        f"文档3: 使用LangGraph可以轻松实现复杂的多步骤智能体工作流。"
    ]

    print(f"[检索] 检索到 {len(mock_documents)} 个相关文档")
    
    return {
        "documents": mock_documents,
        "retrieval_count": state.get("retrieval_count", 0) + 1
    }


def generate_answer(state: QAState) -> dict:
    """答案生成节点
    
    基于检索到的文档和用户问题生成答案。
    在实际应用中,这里会调用LLM(如OpenAI、Claude等)。
    
    Args:
        state: 当前状态,包含问题和文档
        
    Returns:
        包含生成答案的字典
    """
    question = state["question"]
    documents = state["documents"]

    print(f"[生成] 正在基于 {len(documents)} 个文档生成答案...")

    # 模拟LLM调用
    # 实际应用中,这里会调用OpenAI API、Claude API等
    context = "\n".join(documents)

    # 模拟生成的答案
    mock_answer = f"""基于检索到的文档,我可以回答您的问题:

{question}

LangGraph是一个专门用于构建智能体应用的框架。它的核心特点是采用图结构来组织和管理智能体的执行流程。

主要组成部分包括:
1. State(状态): 定义智能体需要维护的数据结构
2. Node(节点): 代表具体的计算步骤,如调用LLM、查询数据库等
3. Edge(边): 定义节点之间的转移关系和执行顺序

通过这种图结构,LangGraph能够轻松实现复杂的多步骤工作流,包括条件分支、循环迭代等高级控制流。"""

    print("[生成] 答案生成完成")
    
    return {
        "answer": mock_answer
    }


def format_response(state: QAState) -> dict:
    """响应格式化节点
    
    将生成的答案格式化为用户友好的形式,添加引用来源等信息。
    
    Args:
        state: 当前状态,包含答案和文档
        
    Returns:
        包含格式化响应的字典
    """
    answer = state["answer"]
    documents = state["documents"]
    retrieval_count = state["retrieval_count"]

    print("[格式化] 正在格式化响应...")

    # 格式化最终响应
    formatted = f"""{answer}

---
参考文档 ({len(documents)} 个):
"""

    for i, doc in enumerate(documents, 1):
        formatted += f"\n{i}. {doc}"

    formatted += f"\n\n检索次数: {retrieval_count}"

    print("[格式化] 响应格式化完成")
    
    return {
        "formatted_response": formatted
    }


# ============================================================================
# 第三步: 构建图结构
# ============================================================================

def build_qa_graph():
    """构建问答助手的状态图

    Returns:
        编译后的可执行图
    """
    print("\n[构建] 正在构建状态图...")

    # 创建StateGraph实例
    builder = StateGraph(QAState)

    # 添加节点
    builder.add_node("retrieve", retrieve_documents)
    builder.add_node("generate", generate_answer)
    builder.add_node("format", format_response)

    # 添加边 - 定义执行流程
    # START -> retrieve -> generate -> format -> END
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "format")
    builder.add_edge("format", END)

    # 编译图
    graph = builder.compile()

    print("[构建] 状态图构建完成\n")

    return graph


# ============================================================================
# 第四步: 可视化图结构
# ============================================================================

def visualize_graph(graph):
    """可视化图结构

    将图结构保存为PNG图片,方便理解执行流程。

    Args:
        graph: 编译后的图
    """
    try:
        # 生成Mermaid图
        png_data = graph.get_graph().draw_mermaid_png()

        # 保存为文件
        with open("qa_graph.png", "wb") as f:
            f.write(png_data)

        print("[可视化] 图结构已保存到 qa_graph.png")

        # 如果在Jupyter环境中,尝试直接显示
        try:
            from IPython.display import Image, display  # type: ignore
            display(Image(png_data))
        except ImportError:
            # 不在Jupyter环境中,跳过显示
            pass

    except Exception as e:
        print(f"[警告] 可视化失败: {e}")
        print("提示: 需要安装 pygraphviz 或 graphviz 库")


# ============================================================================
# 第五步: 执行与验证
# ============================================================================

def run_qa_example():
    """运行问答示例"""
    print("=" * 70)
    print("Hello LangGraph - 智能问答助手示例")
    print("=" * 70)

    # 构建图
    graph = build_qa_graph()

    # 可视化图结构
    visualize_graph(graph)

    # 准备初始状态
    initial_state = {
        "question": "什么是LangGraph?",
        "documents": [],
        "answer": "",
        "formatted_response": "",
        "retrieval_count": 0
    }

    print("\n" + "=" * 70)
    print("[输入] 问题:", initial_state["question"])
    print("=" * 70 + "\n")

    # 执行图
    print("[执行] 开始执行图...\n")
    result = graph.invoke(initial_state)

    # 显示结果
    print("\n" + "=" * 70)
    print("[输出] 最终结果:")
    print("=" * 70)
    print(result["formatted_response"])
    print("\n" + "=" * 70)
    
    return result


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    result = run_qa_example()

    print("\n[完成] 示例执行完成!")
    print("\n[要点] 关键要点:")
    print("  1. State定义了整个流程需要维护的数据")
    print("  2. 每个Node是一个纯函数,接收State并返回更新")
    print("  3. Edge定义了Node之间的执行顺序")
    print("  4. 图的执行是自动的,我们只需要提供初始状态")

