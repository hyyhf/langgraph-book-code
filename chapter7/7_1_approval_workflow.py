"""
7.1节 人在环路 - 审批工作流示例
场景:武汉黄鹤楼景区门票预订系统

这个示例展示了一个完整的审批工作流,包括:
1. 自动检查预订信息
2. 价格计算
3. AI风险评估(使用LLM)
4. 人工审批(团体票需要审批)
5. 支付处理
6. 生成门票
"""

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import uuid
from datetime import datetime
import os

# 加载环境变量
load_dotenv()

# 初始化LLM
llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL_NAME"),
    temperature=0.7
)


class TicketBookingState(TypedDict):
    """门票预订状态"""
    visitor_name: str  # 游客姓名
    visitor_phone: str  # 联系电话
    visit_date: str  # 参观日期
    ticket_type: str  # 票种类型: "adult"成人票, "student"学生票, "group"团体票
    quantity: int  # 数量
    total_price: float  # 总价
    risk_assessment: Optional[str]  # AI风险评估
    approved: Optional[bool]  # 是否批准
    approval_reason: Optional[str]  # 审批原因
    ticket_code: Optional[str]  # 门票编号
    status: str  # 状态


def validate_booking(state: TicketBookingState) -> dict:
    """验证预订信息"""
    print(f"\n 验证预订信息...")
    print(f"游客: {state['visitor_name']}")
    print(f"电话: {state['visitor_phone']}")
    print(f"参观日期: {state['visit_date']}")
    print(f"票种: {state['ticket_type']}, 数量: {state['quantity']}")
    
    # 简单验证
    if not state["visitor_name"] or not state["visitor_phone"]:
        return {"status": "validation_failed"}
    
    if state["quantity"] <= 0:
        return {"status": "validation_failed"}
    
    print(" 信息验证通过")
    return {"status": "validated"}


def calculate_price(state: TicketBookingState) -> dict:
    """计算价格"""
    print(f"\n 计算价格...")

    # 黄鹤楼门票价格表(单位:元)
    prices = {
        "adult": 70,  # 成人票
        "student": 35,  # 学生票(半价)
        "group": 60  # 团体票(10人以上,8.5折)
    }

    unit_price = prices.get(state["ticket_type"], 70)
    total = unit_price * state["quantity"]

    print(f"单价: {unit_price}元 × {state['quantity']}张 = {total}元")

    return {"total_price": total}


def ai_risk_assessment(state: TicketBookingState) -> dict:
    """AI风险评估 - 使用LLM分析预订风险"""
    print(f"\n AI风险评估...")

    # 构建提示词
    prompt = f"""你是黄鹤楼景区的智能风险评估系统。请分析以下团体票预订的风险:

预订信息:
- 预订人: {state['visitor_name']}
- 联系电话: {state['visitor_phone']}
- 参观日期: {state['visit_date']}
- 票种: {state['ticket_type']}
- 数量: {state['quantity']}张
- 总金额: {state['total_price']}元

请从以下几个维度评估风险:
1. 预订规模是否合理
2. 预订时间是否合适
3. 是否存在异常模式

请给出简短的风险评估(50字以内),格式为: "风险等级: [低/中/高], 原因: [具体原因]"
"""

    try:
        response = llm.invoke(prompt)
        assessment = response.content.strip()
        print(f"   评估结果: {assessment}")
        return {"risk_assessment": assessment}
    except Exception as e:
        print(f"   AI评估失败: {e}")
        return {"risk_assessment": "AI评估暂时不可用,建议人工审核"}



def approval_check(state: TicketBookingState) -> Command[Literal["payment", "rejected"]]:
    """审批检查 - 团体票需要人工审批"""

    # 团体票(10张以上)需要人工审批
    if state["ticket_type"] == "group" or state["quantity"] >= 10:
        print(f"\n⏸️  团体预订需要审批!")
        print(f"预订人: {state['visitor_name']}")
        print(f"数量: {state['quantity']}张")
        print(f"金额: {state['total_price']}元")
        print(f"AI风险评估: {state.get('risk_assessment', '无')}")

        # 中断并等待审批
        approval_result = interrupt({
            "type": "group_booking_approval",
            "visitor": state["visitor_name"],
            "phone": state["visitor_phone"],
            "date": state["visit_date"],
            "quantity": state["quantity"],
            "amount": state["total_price"],
            "risk_assessment": state.get("risk_assessment", "无"),
            "message": "请审批团体票预订"
        })
        
        # approval_result应该是一个字典,包含approved和reason
        if approval_result.get("approved"):
            print(f" 审批通过: {approval_result.get('reason', '无')}")
            return Command(
                goto="payment",
                update={
                    "approved": True,
                    "approval_reason": approval_result.get("reason", "审批通过")
                }
            )
        else:
            print(f" 审批拒绝: {approval_result.get('reason', '无')}")
            return Command(
                goto="rejected",
                update={
                    "approved": False,
                    "approval_reason": approval_result.get("reason", "审批拒绝")
                }
            )
    else:
        # 普通票自动批准
        print("\n 普通票自动批准")
        return Command(
            goto="payment",
            update={"approved": True, "approval_reason": "自动批准"}
        )


def process_payment(state: TicketBookingState) -> dict:
    """处理支付"""
    print(f"\n 处理支付...")
    print(f"金额: {state['total_price']}元")
    print(" 支付成功")
    return {}


def generate_ticket(state: TicketBookingState) -> dict:
    """生成门票"""
    print(f"\n 生成门票...")
    
    # 生成门票编号
    ticket_code = f"YHC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
    
    print(f"门票编号: {ticket_code}")
    print(f"游客: {state['visitor_name']}")
    print(f"参观日期: {state['visit_date']}")
    print(f"数量: {state['quantity']}张")
    print("门票生成成功")
    
    return {"ticket_code": ticket_code, "status": "completed"}


def handle_rejection(state: TicketBookingState) -> dict:
    """处理拒绝"""
    print(f"\n 预订被拒绝")
    print(f"原因: {state.get('approval_reason', '未知')}")
    return {"status": "rejected"}


def build_ticket_booking_graph():
    """构建门票预订图"""
    builder = StateGraph(TicketBookingState)

    # 添加节点
    builder.add_node("validate", validate_booking)
    builder.add_node("calculate", calculate_price)
    builder.add_node("ai_assess", ai_risk_assessment)  # 新增AI评估节点
    builder.add_node("approval", approval_check)
    builder.add_node("payment", process_payment)
    builder.add_node("generate", generate_ticket)
    builder.add_node("rejected", handle_rejection)

    # 添加边
    builder.add_edge(START, "validate")
    builder.add_edge("validate", "calculate")
    builder.add_edge("calculate", "ai_assess")  # 计算价格后进行AI评估
    builder.add_edge("ai_assess", "approval")  # AI评估后进入审批
    builder.add_edge("payment", "generate")
    builder.add_edge("generate", END)
    builder.add_edge("rejected", END)

    # 使用检查点器
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


def demo_group_booking_approved():
    """演示团体票预订 - 批准"""
    print("=" * 70)
    print("示例1: 团体票预订 - 批准")
    print("=" * 70)
    
    graph = build_ticket_booking_graph()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    booking = {
        "visitor_name": "武汉大学历史系",
        "visitor_phone": "027-68752000",
        "visit_date": "2024-05-01",
        "ticket_type": "group",
        "quantity": 30,
        "total_price": 0.0,
        "risk_assessment": None,
        "approved": None,
        "approval_reason": None,
        "ticket_code": None,
        "status": "pending"
    }
    
    print("\n 提交团体票预订...")
    result = graph.invoke(booking, config)
    
    if "__interrupt__" in result:
        print("\n 等待审批...")
        
        # 模拟景区管理员审批 - 批准
        print("\n👤 景区管理员审批:")
        approval_decision = {
            "approved": True,
            "reason": "武汉大学师生参观,批准优惠"
        }
        
        final_result = graph.invoke(Command(resume=approval_decision), config)
        print(f"\n 最终状态: {final_result['status']}")
        if final_result['status'] == 'completed':
            print(f"门票编号: {final_result['ticket_code']}")


def demo_group_booking_rejected():
    """演示团体票预订 - 拒绝"""
    print("\n\n" + "=" * 70)
    print("示例2: 团体票预订 - 拒绝")
    print("=" * 70)
    
    graph = build_ticket_booking_graph()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    booking = {
        "visitor_name": "某旅行社",
        "visitor_phone": "138-0000-0000",
        "visit_date": "2024-05-01",  # 假设是节假日
        "ticket_type": "group",
        "quantity": 100,
        "total_price": 0.0,
        "risk_assessment": None,
        "approved": None,
        "approval_reason": None,
        "ticket_code": None,
        "status": "pending"
    }
    
    print("\n 提交团体票预订...")
    result = graph.invoke(booking, config)
    
    if "__interrupt__" in result:
        print("\n  等待审批...")
        
        # 模拟景区管理员审批 - 拒绝
        print("\n 景区管理员审批:")
        approval_decision = {
            "approved": False,
            "reason": "五一假期游客量已达上限,无法接待大型团体"
        }
        
        final_result = graph.invoke(Command(resume=approval_decision), config)
        print(f"\n 最终状态: {final_result['status']}")


def demo_individual_booking():
    """演示个人票预订 - 自动批准"""
    print("\n\n" + "=" * 70)
    print("示例3: 个人票预订 - 自动批准")
    print("=" * 70)
    
    graph = build_ticket_booking_graph()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    booking = {
        "visitor_name": "张三",
        "visitor_phone": "138-2711-8888",
        "visit_date": "2024-04-15",
        "ticket_type": "adult",
        "quantity": 2,
        "total_price": 0.0,
        "risk_assessment": None,
        "approved": None,
        "approval_reason": None,
        "ticket_code": None,
        "status": "pending"
    }
    
    print("\n 提交个人票预订...")
    result = graph.invoke(booking, config)
    
    # 个人票不会中断,直接完成
    print(f"\n 最终状态: {result['status']}")
    if result['status'] == 'completed':
        print(f"门票编号: {result['ticket_code']}")
    print("(个人票无需审批,自动完成)")


if __name__ == "__main__":
    demo_group_booking_approved()
    demo_group_booking_rejected()
    demo_individual_booking()
    
    print("\n\n 所有示例运行完成!")

