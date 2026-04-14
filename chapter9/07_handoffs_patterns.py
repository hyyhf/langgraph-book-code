"""
第9章示例7: Handoffs模式详解
场景: 武汉政务服务大厅 - 展示各种交接模式
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 定义工具
# ============================================================================

@tool
def check_id_card_status(id_number: str):
    """查询身份证办理状态"""
    return f"身份证{id_number}正在办理中,预计3个工作日完成"


@tool
def apply_for_passport(name: str, id_number: str):
    """申请护照"""
    return f"已为{name}(身份证{id_number})提交护照申请,需要10个工作日"


@tool
def check_social_security(id_number: str):
    """查询社保信息"""
    return f"身份证{id_number}的社保账户正常,已缴纳120个月"


@tool
def apply_for_business_license(company_name: str):
    """申请营业执照"""
    return f"已为{company_name}提交营业执照申请,需要5个工作日"


@tool
def check_tax_info(tax_number: str):
    """查询税务信息"""
    return f"税号{tax_number}的税务状态正常,无欠税记录"


# ============================================================================
# 模式1: 直接交接(Direct Handoff)
# ============================================================================

def demo_direct_handoff():
    """演示直接交接模式"""
    
    print("\n" + "=" * 80)
    print("模式1: 直接交接(Direct Handoff)")
    print("=" * 80)
    print("场景: 办理护照需要先查询身份证状态,然后直接转到护照办理")
    print("-" * 80)
    
    # 创建智能体
    id_card_agent = create_agent(
        model=get_llm(),
        tools=[check_id_card_status],
        system_prompt="你是身份证办理窗口,查询身份证状态后直接转到护照窗口",
        name="id_card_agent"
    )
    
    passport_agent = create_agent(
        model=get_llm(),
        tools=[apply_for_passport],
        system_prompt="你是护照办理窗口,为用户办理护照",
        name="passport_agent"
    )
    
    # 定义直接交接节点
    def id_card_node_with_handoff(state: MessagesState) -> Command:
        """身份证窗口 - 查询后直接交接给护照窗口"""
        # 调用身份证智能体
        result = id_card_agent.invoke(state)
        
        # 直接交接给护照窗口
        print("→ 身份证状态已查询,直接转到护照窗口")
        return Command(
            goto="passport_agent",
            update={"messages": result["messages"]}
        )
    
    # 构建图
    graph = StateGraph(MessagesState)
    graph.add_node("id_card_agent", id_card_node_with_handoff)
    graph.add_node("passport_agent", passport_agent)
    
    graph.add_edge(START, "id_card_agent")
    graph.add_edge("passport_agent", END)
    
    workflow = graph.compile()
    
    # 测试
    result = workflow.invoke({
        "messages": [HumanMessage(content="我要办护照,身份证号420106199001011234")]
    })
    
    print(f"\n最终结果: {result['messages'][-1].content}")


# ============================================================================
# 模式2: 条件交接(Conditional Handoff)
# ============================================================================

def demo_conditional_handoff():
    """演示条件交接模式"""
    
    print("\n" + "=" * 80)
    print("模式2: 条件交接(Conditional Handoff)")
    print("=" * 80)
    print("场景: 根据用户需求,条件性地转到不同窗口")
    print("-" * 80)
    
    # 创建智能体
    reception_agent = create_agent(
        model=get_llm(),
        tools=[],
        system_prompt="你是接待窗口,根据用户需求引导到相应窗口",
        name="reception_agent"
    )
    
    id_card_agent = create_agent(
        model=get_llm(),
        tools=[check_id_card_status],
        system_prompt="你是身份证窗口",
        name="id_card_agent"
    )
    
    social_security_agent = create_agent(
        model=get_llm(),
        tools=[check_social_security],
        system_prompt="你是社保窗口",
        name="social_security_agent"
    )
    
    business_agent = create_agent(
        model=get_llm(),
        tools=[apply_for_business_license],
        system_prompt="你是工商窗口",
        name="business_agent"
    )
    
    # 定义条件交接节点
    def reception_node_with_routing(state: MessagesState) -> Command:
        """接待窗口 - 根据需求路由到不同窗口"""
        last_message = state["messages"][-1].content
        
        # 条件判断
        if "身份证" in last_message or "护照" in last_message:
            print("→ 识别为身份证业务,转到身份证窗口")
            return Command(goto="id_card_agent")
        elif "社保" in last_message:
            print("→ 识别为社保业务,转到社保窗口")
            return Command(goto="social_security_agent")
        elif "营业执照" in last_message or "公司" in last_message:
            print("→ 识别为工商业务,转到工商窗口")
            return Command(goto="business_agent")
        else:
            print("→ 无法识别业务类型,结束")
            return Command(goto=END)
    
    # 构建图
    graph = StateGraph(MessagesState)
    graph.add_node("reception", reception_node_with_routing)
    graph.add_node("id_card_agent", id_card_agent)
    graph.add_node("social_security_agent", social_security_agent)
    graph.add_node("business_agent", business_agent)
    
    graph.add_edge(START, "reception")
    graph.add_edge("id_card_agent", END)
    graph.add_edge("social_security_agent", END)
    graph.add_edge("business_agent", END)
    
    workflow = graph.compile()
    
    # 测试不同的条件
    test_cases = [
        "我要查询身份证办理进度",
        "我要查询社保缴纳情况",
        "我要注册一家公司"
    ]
    
    for query in test_cases:
        print(f"\n用户: {query}")
        result = workflow.invoke({
            "messages": [HumanMessage(content=query)]
        })
        print(f"结果: {result['messages'][-1].content}")


# ============================================================================
# 模式3: 循环交接(Loop Handoff)
# ============================================================================

def demo_loop_handoff():
    """演示循环交接模式"""
    
    print("\n" + "=" * 80)
    print("模式3: 循环交接(Loop Handoff)")
    print("=" * 80)
    print("场景: 办理业务可能需要多次往返不同窗口")
    print("-" * 80)
    
    class LoopState(TypedDict):
        """带计数器的状态"""
        messages: list
        loop_count: int
        max_loops: int
    
    # 定义循环节点
    def window_a(state: LoopState) -> Command:
        """窗口A - 处理后可能返回窗口B"""
        loop_count = state.get("loop_count", 0) + 1
        print(f"→ 窗口A处理(第{loop_count}次)")
        
        if loop_count < state.get("max_loops", 3):
            print("  需要窗口B补充材料,转到窗口B")
            return Command(
                goto="window_b",
                update={"loop_count": loop_count}
            )
        else:
            print("  材料齐全,办理完成")
            return Command(goto=END)
    
    def window_b(state: LoopState) -> Command:
        """窗口B - 处理后返回窗口A"""
        print(f"→ 窗口B补充材料")
        print("  材料已补充,返回窗口A继续办理")
        return Command(goto="window_a")
    
    # 构建图
    graph = StateGraph(LoopState)
    graph.add_node("window_a", window_a)
    graph.add_node("window_b", window_b)
    
    graph.add_edge(START, "window_a")
    
    workflow = graph.compile()
    
    # 测试
    print("\n开始办理业务...")
    result = workflow.invoke({
        "messages": [],
        "loop_count": 0,
        "max_loops": 3
    })
    
    print(f"\n总共循环{result['loop_count']}次")


# ============================================================================
# 模式4: 终止交接(Terminal Handoff)
# ============================================================================

def demo_terminal_handoff():
    """演示终止交接模式"""
    
    print("\n" + "=" * 80)
    print("模式4: 终止交接(Terminal Handoff)")
    print("=" * 80)
    print("场景: 智能体判断任务完成,返回END信号")
    print("-" * 80)
    
    def final_review_node(state: MessagesState) -> Command:
        """最终审核节点 - 判断是否完成"""
        print("→ 最终审核窗口检查材料...")
        
        # 模拟审核逻辑
        messages = state.get("messages", [])
        if len(messages) > 0:
            print("  材料齐全,审核通过,办理完成")
            return Command(goto=END)
        else:
            print("  材料不全,需要补充")
            return Command(goto="supplement")
    
    def supplement_node(state: MessagesState) -> Command:
        """补充材料节点"""
        print("→ 补充材料窗口")
        print("  材料已补充,返回审核")
        return Command(
            goto="final_review",
            update={"messages": [HumanMessage(content="材料已补充")]}
        )
    
    # 构建图
    graph = StateGraph(MessagesState)
    graph.add_node("final_review", final_review_node)
    graph.add_node("supplement", supplement_node)
    
    graph.add_edge(START, "final_review")
    
    workflow = graph.compile()
    
    # 测试1: 材料齐全
    print("\n测试1: 材料齐全")
    result1 = workflow.invoke({
        "messages": [HumanMessage(content="所有材料")]
    })
    
    # 测试2: 材料不全
    print("\n测试2: 材料不全")
    result2 = workflow.invoke({
        "messages": []
    })


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有Handoff模式演示"""
    
    print("=" * 80)
    print("第9章示例7: Handoffs模式详解 - 武汉政务服务大厅")
    print("=" * 80)
    
    # 演示各种模式
    demo_direct_handoff()
    demo_conditional_handoff()
    demo_loop_handoff()
    demo_terminal_handoff()
    
    print("\n" + "=" * 80)
    print("Handoffs模式总结:")
    print("1. 直接交接 - 固定的顺序流转")
    print("2. 条件交接 - 根据条件动态路由")
    print("3. 循环交接 - 支持往返和迭代")
    print("4. 终止交接 - 判断完成并结束")
    print("=" * 80)


if __name__ == "__main__":
    main()

