"""
节点定义模块
定义研究助手的各个节点函数
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from .state import ResearchState
from .tools import search_web, analyze_text

# 加载环境变量
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# 创建LLM实例
def get_llm(streaming: bool = True, temperature: float = 0.7):
    """获取LLM实例"""
    return ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=os.getenv('OPENAI_MODEL_NAME', 'deepseek-chat'),
        temperature=temperature,
        streaming=streaming
    )

# 创建工具节点
tools = [search_web, analyze_text]
tool_node = ToolNode(tools)


def researcher_node(state: ResearchState) -> dict:
    """
    研究员节点 - 负责信息收集

    使用工具搜索和收集相关信息,并使用流式输出展示过程
    """
    topic = state["topic"]
    messages = state["messages"]

    # 检查是否已经有工具调用的结果
    has_tool_result = any(
        hasattr(msg, 'type') and msg.type == 'tool'
        for msg in messages
    )

    if has_tool_result:
        # 如果已经有工具结果,整理信息并结束
        print("\n" + "="*80)
        print("【研究员】整理收集到的信息...")
        print("="*80)

        # 从消息历史中提取工具返回的内容(纯文本)
        tool_results = []
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'tool':
                tool_results.append(msg.content)

        collected_info = "\n\n".join(tool_results)
        print(f"工具调用结果: {collected_info}")

        system_prompt = """你是一位专业的研究员。
请整理和归纳以下收集到的信息,以结构化的方式呈现。"""

        llm = get_llm(streaming=True)

        # 只传入干净的文本,避免传入含tool_calls的消息历史
        final_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"请整理以下关于'{topic}'的研究资料:\n\n{collected_info}")
        ]

        print("\n正在整理信息...\n")
        print("-"*80)

        research_data = ""
        for chunk in llm.stream(final_messages):
            content = chunk.content
            print(content, end="", flush=True)
            research_data += content

        print("\n" + "-"*80)
        print("\n信息整理完成!\n")

        return {
            "research_data": research_data,
            "messages": [AIMessage(content=research_data)],
            "current_stage": "research"
        }
    else:
        # 首次调用,使用工具收集信息
        print("\n" + "="*80)
        print("【研究员】开始收集信息...")
        print("="*80)

        system_prompt = """你是一位专业的研究员,擅长信息收集和资料整理。

你的任务:
1. 使用search_web工具搜索相关信息
2. 只调用一次工具即可

请使用工具收集信息。"""

        # 创建带工具的LLM
        llm = get_llm(streaming=False)  # 工具调用不需要流式
        llm_with_tools = llm.bind_tools(tools)

        # 构建消息
        call_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"请使用search_web工具收集关于'{topic}'的详细信息。")
        ]

        # 调用LLM(会产生工具调用)
        print("\n正在调用搜索工具...\n")
        response = llm_with_tools.invoke(call_messages)

        # 返回响应,包含工具调用
        return {
            "messages": [response],
            "current_stage": "research"
        }


def human_review_node(state: ResearchState) -> dict:
    """
    人工审核节点 - 在分析前进行人工审核
    
    使用interrupt()暂停执行,等待人工确认
    """
    research_data = state["research_data"]
    
    print("\n" + "="*80)
    print("【人工审核】请审核研究数据")
    print("="*80)
    print(f"\n数据预览:\n{research_data[:500]}...\n")
    
    # 使用interrupt暂停执行,等待人工输入
    # 在实际应用中,这里会真正暂停图的执行
    human_response = interrupt({
        "type": "human_review",
        "question": "研究数据是否准确完整?",
        "data_preview": research_data[:500],
        "options": ["approved", "rejected", "needs_revision"]
    })
    
    # 处理人工反馈
    approved = human_response.get("status") == "approved"
    
    if approved:
        print("\n✓ 审核通过,继续执行分析...\n")
    else:
        print("\n✗ 审核未通过,需要重新收集信息...\n")
    
    return {
        "human_approved": approved,
        "current_stage": "review",
        "messages": [AIMessage(content=f"人工审核: {'通过' if approved else '未通过'}")]
    }


def analyst_node(state: ResearchState) -> dict:
    """
    分析师节点 - 负责数据分析
    
    使用流式输出展示分析过程
    """
    topic = state["topic"]
    research_data = state["research_data"]
    
    print("\n" + "="*80)
    print("【分析师】开始分析数据...")
    print("="*80)
    
    # 构建分析师的系统提示
    system_prompt = """你是一位资深的数据分析师,擅长从信息中提取关键洞察。

你的任务:
1. 分析研究员收集的信息
2. 提取核心发现和关键点
3. 进行趋势和模式分析
4. 评估重要性和影响

请提供深入、有见地的分析。"""
    
    # 创建LLM
    llm = get_llm(streaming=True)
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""研究主题: {topic}

研究数据:
{research_data}

请对以上信息进行深入分析,提供有价值的洞察。""")
    ]
    
    # 使用流式输出
    print("\n分析结果:\n")
    print("-"*80)
    
    analysis_result = ""
    for chunk in llm.stream(messages):
        content = chunk.content
        print(content, end="", flush=True)
        analysis_result += content
    
    print("\n" + "-"*80)
    print("\n分析完成!\n")
    
    return {
        "analysis_result": analysis_result,
        "current_stage": "analysis",
        "messages": [AIMessage(content="分析师: 已完成数据分析")]
    }


def reporter_node(state: ResearchState) -> dict:
    """
    报告员节点 - 负责生成最终报告
    
    使用流式输出展示报告生成过程
    """
    topic = state["topic"]
    research_data = state["research_data"]
    analysis_result = state["analysis_result"]
    
    print("\n" + "="*80)
    print("【报告员】开始撰写报告...")
    print("="*80)
    
    # 构建报告员的系统提示
    system_prompt = """你是一位专业的报告撰写专家,擅长将研究成果整理成清晰、专业的报告。

你的任务:
1. 基于研究数据和分析结果撰写完整报告
2. 报告应包括: 摘要、背景介绍、主要发现、深入分析、结论
3. 语言要专业、清晰、易于理解
4. 结构要完整、逻辑要严谨

请撰写一份高质量的研究报告。"""
    
    # 创建LLM
    llm = get_llm(streaming=True)
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""研究主题: {topic}

研究数据:
{research_data}

分析结果:
{analysis_result}

请基于以上内容撰写一份完整的研究报告。""")
    ]
    
    # 使用流式输出
    print("\n研究报告:\n")
    print("="*80)
    
    final_report = ""
    for chunk in llm.stream(messages):
        content = chunk.content
        print(content, end="", flush=True)
        final_report += content
    
    print("\n" + "="*80)
    print("\n报告撰写完成!\n")
    
    return {
        "final_report": final_report,
        "current_stage": "complete",
        "messages": [AIMessage(content="报告员: 已完成报告撰写")]
    }

