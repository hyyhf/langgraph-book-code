"""
第9章示例6: Custom Workflow - 定制化的控制流
场景: 武汉外卖订餐系统 - 复杂的订餐流程控制
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 定义订单状态
# ============================================================================

class OrderState(TypedDict):
    """订单状态"""
    messages: Annotated[list, "消息历史"]
    user_location: str  # 用户位置
    restaurant: str  # 选择的餐厅
    dishes: list[str]  # 选择的菜品
    total_price: float  # 总价
    payment_method: str  # 支付方式
    delivery_time: str  # 配送时间
    order_status: str  # 订单状态: selecting/confirming/paying/preparing/delivering/completed


# ============================================================================
# 定义工具
# ============================================================================

@tool
def search_restaurants(location: str, cuisine: str = ""):
    """搜索附近餐厅"""
    restaurants = {
        "光谷": [
            "蔡林记(光谷店) - 热干面、豆皮 - 人均15元",
            "周黑鸭(光谷广场店) - 鸭脖、鸭翅 - 人均30元",
            "老通城(光谷店) - 豆皮、汤包 - 人均25元"
        ],
        "街道口": [
            "蔡林记(街道口店) - 热干面、豆皮 - 人均15元",
            "小蓝鲸(街道口店) - 武昌鱼、排骨藕汤 - 人均80元",
            "靓靓蒸虾(街道口店) - 油焖大虾 - 人均60元"
        ]
    }
    result = restaurants.get(location, ["暂无该区域餐厅"])
    return "\n".join(result)


@tool
def get_menu(restaurant: str):
    """获取餐厅菜单"""
    menus = {
        "蔡林记": "热干面 8元, 豆皮 12元, 糊汤粉 10元, 面窝 5元",
        "周黑鸭": "鸭脖 28元/斤, 鸭翅 32元/斤, 鸭锁骨 30元/斤",
        "老通城": "三鲜豆皮 15元, 汤包 18元, 糊汤粉 12元",
        "小蓝鲸": "清蒸武昌鱼 68元, 排骨藕汤 38元, 糖醋排骨 48元",
        "靓靓蒸虾": "油焖大虾 88元, 蒜蓉虾 78元, 椒盐虾 68元"
    }
    return menus.get(restaurant, "暂无菜单")


@tool
def calculate_price(dishes: list[str]):
    """计算订单总价"""
    prices = {
        "热干面": 8, "豆皮": 12, "糊汤粉": 10, "面窝": 5,
        "鸭脖": 28, "鸭翅": 32, "鸭锁骨": 30,
        "三鲜豆皮": 15, "汤包": 18,
        "清蒸武昌鱼": 68, "排骨藕汤": 38, "糖醋排骨": 48,
        "油焖大虾": 88, "蒜蓉虾": 78, "椒盐虾": 68
    }
    total = sum(prices.get(dish, 0) for dish in dishes)
    delivery_fee = 5  # 配送费
    return total + delivery_fee


@tool
def process_payment(amount: float, method: str):
    """处理支付"""
    return f"已通过{method}支付{amount}元,支付成功"


@tool
def estimate_delivery_time(restaurant: str, location: str):
    """估算配送时间"""
    return "预计30-40分钟送达"


# ============================================================================
# 创建工作流节点
# ============================================================================

def restaurant_selection_node(state: OrderState) -> OrderState:
    """餐厅选择节点"""
    print("\n[餐厅选择] 正在为用户推荐餐厅...")
    
    # 这里简化处理,实际应该调用LLM分析用户需求
    location = state.get("user_location", "光谷")
    restaurants = search_restaurants.invoke({"location": location})
    
    # 模拟用户选择第一家餐厅
    restaurant = "蔡林记"
    
    return {
        **state,
        "restaurant": restaurant,
        "order_status": "selecting"
    }


def dish_selection_node(state: OrderState) -> OrderState:
    """菜品选择节点"""
    print(f"\n[菜品选择] 正在获取{state['restaurant']}的菜单...")
    
    menu = get_menu.invoke({"restaurant": state["restaurant"]})
    print(f"菜单: {menu}")
    
    # 模拟用户选择
    dishes = ["热干面", "豆皮"]
    total_price = calculate_price.invoke({"dishes": dishes})
    
    return {
        **state,
        "dishes": dishes,
        "total_price": total_price,
        "order_status": "confirming"
    }


def order_confirmation_node(state: OrderState) -> OrderState:
    """订单确认节点"""
    print(f"\n[订单确认] 餐厅: {state['restaurant']}")
    print(f"菜品: {', '.join(state['dishes'])}")
    print(f"总价: {state['total_price']}元")
    
    # 模拟用户确认
    return {
        **state,
        "order_status": "paying"
    }


def payment_node(state: OrderState) -> OrderState:
    """支付节点"""
    print(f"\n[支付处理] 金额: {state['total_price']}元")
    
    # 模拟支付
    payment_method = "微信支付"
    result = process_payment.invoke({
        "amount": state["total_price"],
        "method": payment_method
    })
    print(result)
    
    return {
        **state,
        "payment_method": payment_method,
        "order_status": "preparing"
    }


def restaurant_preparation_node(state: OrderState) -> OrderState:
    """餐厅备餐节点"""
    print(f"\n[餐厅备餐] {state['restaurant']}正在准备您的订单...")
    
    # 模拟备餐过程
    import time
    time.sleep(1)  # 模拟备餐时间
    
    return {
        **state,
        "order_status": "delivering"
    }


def delivery_node(state: OrderState) -> OrderState:
    """配送节点"""
    print(f"\n[配送中] 骑手正在配送,预计30-40分钟送达")
    
    delivery_time = estimate_delivery_time.invoke({
        "restaurant": state["restaurant"],
        "location": state["user_location"]
    })
    
    return {
        **state,
        "delivery_time": delivery_time,
        "order_status": "completed"
    }


def quality_check_node(state: OrderState) -> Command:
    """质量检查节点 - 条件分支"""
    print(f"\n[质量检查] 检查订单状态...")
    
    # 模拟质量检查
    # 这里可以检查各种条件,如价格是否合理、配送时间是否可接受等
    if state["total_price"] > 100:
        print("订单金额较大,需要人工审核")
        return Command(goto="manual_review")
    else:
        print("订单正常,继续处理")
        return Command(goto="payment")


def manual_review_node(state: OrderState) -> OrderState:
    """人工审核节点"""
    print(f"\n[人工审核] 订单金额{state['total_price']}元,正在审核...")
    
    # 模拟人工审核
    print("审核通过")
    
    return {
        **state,
        "order_status": "paying"
    }


# ============================================================================
# 构建Custom Workflow
# ============================================================================

def create_custom_workflow():
    """创建定制化的订餐工作流"""
    
    # 创建图
    graph = StateGraph(OrderState)
    
    # 添加节点
    graph.add_node("restaurant_selection", restaurant_selection_node)
    graph.add_node("dish_selection", dish_selection_node)
    graph.add_node("order_confirmation", order_confirmation_node)
    graph.add_node("quality_check", quality_check_node)
    graph.add_node("manual_review", manual_review_node)
    graph.add_node("payment", payment_node)
    graph.add_node("restaurant_preparation", restaurant_preparation_node)
    graph.add_node("delivery", delivery_node)
    
    # 定义流程
    # 1. 顺序执行: 选餐厅 -> 选菜品 -> 确认订单
    graph.add_edge(START, "restaurant_selection")
    graph.add_edge("restaurant_selection", "dish_selection")
    graph.add_edge("dish_selection", "order_confirmation")
    
    # 2. 条件分支: 确认后进行质量检查
    graph.add_edge("order_confirmation", "quality_check")
    # quality_check节点会返回Command,动态决定去payment还是manual_review
    
    # 3. 人工审核后继续支付
    graph.add_edge("manual_review", "payment")
    
    # 4. 顺序执行: 支付 -> 备餐 -> 配送
    graph.add_edge("payment", "restaurant_preparation")
    graph.add_edge("restaurant_preparation", "delivery")
    
    # 5. 配送完成
    graph.add_edge("delivery", END)
    
    return graph.compile()


# ============================================================================
# 测试函数
# ============================================================================

def test_custom_workflow():
    """测试Custom Workflow"""
    
    print("=" * 80)
    print("第9章示例6: Custom Workflow - 武汉外卖订餐系统")
    print("=" * 80)
    print("\n工作流程:")
    print("1. 选择餐厅(顺序)")
    print("2. 选择菜品(顺序)")
    print("3. 确认订单(顺序)")
    print("4. 质量检查(条件分支)")
    print("   ├─ 金额正常 -> 支付")
    print("   └─ 金额较大 -> 人工审核 -> 支付")
    print("5. 餐厅备餐(顺序)")
    print("6. 配送(顺序)")
    print("7. 完成\n")
    
    workflow = create_custom_workflow()
    
    # 测试用例1: 正常订单(金额不大)
    print("\n" + "=" * 80)
    print("测试1: 正常订单(金额25元,不需要人工审核)")
    print("=" * 80)
    
    result1 = workflow.invoke({
        "messages": [],
        "user_location": "光谷",
        "restaurant": "",
        "dishes": [],
        "total_price": 0,
        "payment_method": "",
        "delivery_time": "",
        "order_status": "init"
    })
    
    print(f"\n最终状态: {result1['order_status']}")
    print(f"订单详情: {result1['restaurant']} - {', '.join(result1['dishes'])} - {result1['total_price']}元")
    
    # 测试用例2: 大额订单(需要人工审核)
    print("\n\n" + "=" * 80)
    print("测试2: 大额订单(金额150元,需要人工审核)")
    print("=" * 80)
    
    # 修改dish_selection_node来模拟大额订单
    def dish_selection_node_large(state: OrderState) -> OrderState:
        print(f"\n[菜品选择] 正在获取{state['restaurant']}的菜单...")
        dishes = ["清蒸武昌鱼", "排骨藕汤", "糖醋排骨"]  # 大额菜品
        total_price = 159  # 包含配送费
        return {
            **state,
            "dishes": dishes,
            "total_price": total_price,
            "order_status": "confirming"
        }
    
    # 重新创建工作流(替换节点)
    graph2 = StateGraph(OrderState)
    graph2.add_node("restaurant_selection", restaurant_selection_node)
    graph2.add_node("dish_selection", dish_selection_node_large)
    graph2.add_node("order_confirmation", order_confirmation_node)
    graph2.add_node("quality_check", quality_check_node)
    graph2.add_node("manual_review", manual_review_node)
    graph2.add_node("payment", payment_node)
    graph2.add_node("restaurant_preparation", restaurant_preparation_node)
    graph2.add_node("delivery", delivery_node)
    
    graph2.add_edge(START, "restaurant_selection")
    graph2.add_edge("restaurant_selection", "dish_selection")
    graph2.add_edge("dish_selection", "order_confirmation")
    graph2.add_edge("order_confirmation", "quality_check")
    graph2.add_edge("manual_review", "payment")
    graph2.add_edge("payment", "restaurant_preparation")
    graph2.add_edge("restaurant_preparation", "delivery")
    graph2.add_edge("delivery", END)
    
    workflow2 = graph2.compile()
    
    result2 = workflow2.invoke({
        "messages": [],
        "user_location": "街道口",
        "restaurant": "小蓝鲸",
        "dishes": [],
        "total_price": 0,
        "payment_method": "",
        "delivery_time": "",
        "order_status": "init"
    })
    
    print(f"\n最终状态: {result2['order_status']}")
    print(f"订单详情: {result2['restaurant']} - {', '.join(result2['dishes'])} - {result2['total_price']}元")
    
    print("\n\n" + "=" * 80)
    print("Custom Workflow优势:")
    print("1. 灵活性高 - 可以精确表达复杂的业务逻辑")
    print("2. 支持多种控制流 - 顺序、并行、条件、循环")
    print("3. 业务导向 - 直接映射业务流程")
    print("4. 易于理解 - 流程图清晰可见")
    print("=" * 80)


if __name__ == "__main__":
    test_custom_workflow()

