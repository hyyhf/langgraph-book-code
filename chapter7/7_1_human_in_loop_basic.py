"""
7.1节 人在环路(Human-in-the-Loop)示例代码
场景:武汉热干面店订单审批系统

这个示例展示了如何使用LangGraph的中断机制实现人在环路功能。
场景设定:一个武汉热干面店的智能订单系统,需要人工审批大额订单。
"""

from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
import uuid


# ============================================================================
# 示例1: 基本的中断机制
# ============================================================================

class OrderState(TypedDict):
    """订单状态"""
    customer_name: str  # 顾客姓名
    items: list[str]  # 订单项目
    total_amount: float  # 总金额
    approved: Optional[bool]  # 是否批准
    status: Optional[str]  # 订单状态


def check_order(state: OrderState) -> dict:
    """检查订单,计算总金额"""
    # 热干面价格表(单位:元)
    prices = {
        "热干面": 6.0,
        "豆皮": 8.0,
        "蛋酒": 5.0,
        "面窝": 3.0,
        "糊汤粉": 7.0
    }
    
    total = sum(prices.get(item, 0) for item in state["items"])
    print(f" 订单检查: {state['customer_name']} 点了 {', '.join(state['items'])}")
    print(f" 总金额: {total}元")
    
    return {"total_amount": total}


def approval_node(state: OrderState) -> Command[Literal["process", "cancel"]]:
    """审批节点 - 大额订单需要人工审批"""
    # 如果订单金额超过50元,需要人工审批
    if state["total_amount"] > 50:
        print(f"\n  大额订单需要审批!")
        print(f"顾客: {state['customer_name']}")
        print(f"金额: {state['total_amount']}元")
        
        # 中断执行,等待人工审批
        approved = interrupt({
            "type": "approval_required",
            "customer": state["customer_name"],
            "amount": state["total_amount"],
            "items": state["items"],
            "message": "请审批此订单"
        })
        
        # 根据审批结果路由
        if approved:
            print(" 订单已批准")
            return Command(goto="process", update={"approved": True})
        else:
            print(" 订单被拒绝")
            return Command(goto="cancel", update={"approved": False})
    else:
        # 小额订单自动批准
        print(" 小额订单自动批准")
        return Command(goto="process", update={"approved": True})


def process_order(state: OrderState) -> dict:
    """处理订单"""
    print(f"\n 开始制作订单...")
    print(f"为 {state['customer_name']} 准备: {', '.join(state['items'])}")
    return {"status": "completed"}


def cancel_order(state: OrderState) -> dict:
    """取消订单"""
    print(f"\n 订单已取消")
    return {"status": "cancelled"}


# 构建图
def build_order_approval_graph():
    """构建订单审批图"""
    builder = StateGraph(OrderState)
    
    # 添加节点
    builder.add_node("check", check_order)
    builder.add_node("approval", approval_node)
    builder.add_node("process", process_order)
    builder.add_node("cancel", cancel_order)
    
    # 添加边
    builder.add_edge(START, "check")
    builder.add_edge("check", "approval")
    builder.add_edge("process", END)
    builder.add_edge("cancel", END)
    
    # 使用内存检查点器(生产环境应使用持久化检查点器)
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


# ============================================================================
# 示例2: 信息传递与恢复执行
# ============================================================================

def demo_basic_interrupt():
    """演示基本的中断和恢复"""
    print("=" * 60)
    print("示例1: 基本的中断机制")
    print("=" * 60)
    
    graph = build_order_approval_graph()
    
    # 创建一个大额订单
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = {
        "customer_name": "张三",
        "items": ["热干面", "热干面", "热干面", "豆皮", "豆皮", "蛋酒", "面窝"],
        "total_amount": 0.0,
        "approved": None,
        "status": None
    }
    
    print("\n 创建订单...")
    # 运行图直到遇到中断
    result = graph.invoke(initial_state, config)
    
    # 检查是否有中断
    if "__interrupt__" in result:
        print("\n 执行已暂停,等待审批")
        interrupt_info = result["__interrupt__"][0]
        print(f"中断信息: {interrupt_info.value}")
        
        # 模拟人工审批 - 批准订单
        print("\n 店长审批: 批准")
        resumed_result = graph.invoke(
            Command(resume=True),  # True表示批准
            config
        )
        print(f"\n最终状态: {resumed_result['status']}")
    
    print("\n" + "=" * 60)


def demo_rejection():
    """演示拒绝订单的情况"""
    print("\n示例2: 拒绝订单")
    print("=" * 60)
    
    graph = build_order_approval_graph()
    
    # 创建另一个大额订单
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = {
        "customer_name": "李四",
        "items": ["热干面"] * 10,  # 10碗热干面
        "total_amount": 0.0,
        "approved": None,
        "status": None
    }
    
    print("\n 创建订单...")
    result = graph.invoke(initial_state, config)
    
    if "__interrupt__" in result:
        print("\n  执行已暂停,等待审批")
        
        # 模拟人工审批 - 拒绝订单
        print("\n 店长审批: 拒绝(数量过多)")
        resumed_result = graph.invoke(
            Command(resume=False),  # False表示拒绝
            config
        )
        print(f"\n最终状态: {resumed_result['status']}")
    
    print("\n" + "=" * 60)


def demo_small_order():
    """演示小额订单自动批准"""
    print("\n示例3: 小额订单自动批准")
    print("=" * 60)
    
    graph = build_order_approval_graph()
    
    # 创建一个小额订单
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = {
        "customer_name": "王五",
        "items": ["热干面", "蛋酒"],
        "total_amount": 0.0,
        "approved": None,
        "status": None
    }
    
    print("\n 创建订单...")
    result = graph.invoke(initial_state, config)
    
    # 小额订单不会中断,直接完成
    print(f"\n最终状态: {result['status']}")
    print("(小额订单无需审批,自动完成)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 运行所有示例
    demo_basic_interrupt()
    demo_rejection()
    demo_small_order()
    
    print("\n 所有示例运行完成!")

