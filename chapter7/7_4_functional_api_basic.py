"""
7.4节 函数API(Functional API)示例代码
场景:武汉户部巷美食推荐系统

这个示例展示了如何使用LangGraph的函数API:
1. @entrypoint和@task装饰器的基本使用
2. 确定性执行
3. 人在环路支持
4. 使用LLM生成美食描述
"""

from typing import TypedDict, Optional
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import time
import uuid
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


# ============================================================================
# 示例1: 基本的@task和@entrypoint使用
# ============================================================================

# 武汉户部巷美食数据
HUBU_LANE_FOODS = {
    "热干面": {"price": 6, "rating": 4.8, "category": "面食"},
    "豆皮": {"price": 8, "rating": 4.7, "category": "小吃"},
    "糊汤粉": {"price": 7, "rating": 4.6, "category": "汤粉"},
    "面窝": {"price": 3, "rating": 4.5, "category": "油炸"},
    "欢喜坨": {"price": 4, "rating": 4.4, "category": "甜品"},
    "汤包": {"price": 10, "rating": 4.9, "category": "包点"},
    "烧麦": {"price": 8, "rating": 4.6, "category": "包点"},
    "蛋酒": {"price": 5, "rating": 4.3, "category": "饮品"}
}


@task
def fetch_food_data(category: Optional[str] = None) -> dict:
    """获取美食数据(模拟API调用)"""
    print(f"\n 获取美食数据...")
    time.sleep(0.5)  # 模拟网络延迟
    
    if category:
        foods = {k: v for k, v in HUBU_LANE_FOODS.items() if v["category"] == category}
        print(f"   找到 {len(foods)} 个 {category} 类美食")
    else:
        foods = HUBU_LANE_FOODS
        print(f"   找到 {len(foods)} 个美食")
    
    return foods


@task
def filter_by_price(foods: dict, max_price: float) -> dict:
    """按价格筛选"""
    print(f"\n 筛选价格 ≤ {max_price}元的美食...")
    filtered = {k: v for k, v in foods.items() if v["price"] <= max_price}
    print(f"   筛选后剩余 {len(filtered)} 个")
    return filtered


@task
def sort_by_rating(foods: dict) -> list:
    """按评分排序"""
    print(f"\n 按评分排序...")
    sorted_foods = sorted(foods.items(), key=lambda x: x[1]["rating"], reverse=True)
    return sorted_foods


@entrypoint(checkpointer=MemorySaver())
def recommend_foods(inputs: dict) -> dict:
    """推荐美食的工作流"""
    category = inputs.get("category")
    max_price = inputs.get("max_price", 10.0)

    print(f"\n{'='*60}")
    print(f"开始推荐美食")
    print(f"类别: {category or '全部'}, 最高价格: {max_price}元")
    print(f"{'='*60}")
    
    # 使用task获取数据
    foods = fetch_food_data(category).result()
    
    # 筛选价格
    filtered_foods = filter_by_price(foods, max_price).result()
    
    # 排序
    sorted_foods = sort_by_rating(filtered_foods).result()
    
    # 返回推荐结果
    recommendations = [
        {
            "name": name,
            "price": info["price"],
            "rating": info["rating"],
            "category": info["category"]
        }
        for name, info in sorted_foods[:3]  # 只返回前3个
    ]
    
    print(f"\n 推荐结果:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec['name']} - {rec['price']}元 ({rec['rating']})")
    
    return {"recommendations": recommendations}


# ============================================================================
# 示例2: 人在环路支持
# ============================================================================

@task
def generate_food_description(food_name: str) -> str:
    """生成美食描述 - 使用LLM"""
    print(f"\n AI生成 {food_name} 的描述...")

    prompt = f"""请用一句话(30字以内)描述武汉特色美食"{food_name}"的特点和口感。
要求:
1. 突出美食的特色
2. 描述口感和味道
3. 语言生动形象
4. 不要使用"是"、"为"等系动词开头

例如: 芝麻酱香浓,面条劲道,武汉人的早餐灵魂
"""

    try:
        response = llm.invoke(prompt)
        desc = response.content.strip()
        print(f"  AI描述: {desc}")
        return desc
    except Exception as e:
        print(f"  AI生成失败: {e}")
        # 降级方案
        fallback_descriptions = {
            "热干面": "芝麻酱香浓,面条劲道,武汉人的早餐灵魂",
            "豆皮": "外酥里嫩,糯米香软,配料丰富",
            "糊汤粉": "汤汁浓郁,米粉滑嫩,鲜香可口",
            "面窝": "外酥内软,葱香四溢,武汉早餐经典",
            "汤包": "皮薄馅大,汤汁鲜美,一口满足"
        }
        desc = fallback_descriptions.get(food_name, f"{food_name}是武汉特色美食")
        print(f"   默认描述: {desc}")
        return desc


@entrypoint(checkpointer=MemorySaver())
def interactive_recommendation(budget: float) -> dict:
    """交互式美食推荐"""
    print(f"\n{'='*60}")
    print(f"交互式美食推荐")
    print(f"预算: {budget}元")
    print(f"{'='*60}")
    
    # 获取美食数据
    foods = fetch_food_data().result()
    filtered = filter_by_price(foods, budget).result()
    sorted_foods = sort_by_rating(filtered).result()
    
    if not sorted_foods:
        return {"message": "没有符合预算的美食"}
    
    # 推荐第一个
    top_food = sorted_foods[0]
    food_name = top_food[0]
    food_info = top_food[1]
    
    # 生成描述
    description = generate_food_description(food_name).result()
    
    # 询问用户是否接受推荐
    print(f"\n 推荐: {food_name}")
    print(f"   价格: {food_info['price']}元")
    print(f"   评分: {food_info['rating']}")
    print(f"   描述: {description}")
    
    user_choice = interrupt({
        "food": food_name,
        "price": food_info["price"],
        "rating": food_info["rating"],
        "description": description,
        "question": "您是否接受这个推荐?"
    })
    
    if user_choice:
        print(f"\n 用户接受推荐: {food_name}")
        return {
            "accepted": True,
            "food": food_name,
            "price": food_info["price"]
        }
    else:
        print(f"\n 用户拒绝推荐,尝试下一个...")
        
        # 推荐第二个
        if len(sorted_foods) > 1:
            second_food = sorted_foods[1]
            food_name = second_food[0]
            food_info = second_food[1]
            
            description = generate_food_description(food_name).result()
            
            print(f"\n 备选推荐: {food_name}")
            print(f"   价格: {food_info['price']}元")
            print(f"   评分: {food_info['rating']}")
            
            return {
                "accepted": False,
                "alternative": food_name,
                "price": food_info["price"]
            }
        else:
            return {"accepted": False, "message": "没有更多推荐"}


# ============================================================================
# 示例3: 短期记忆(previous参数)
# ============================================================================

@entrypoint(checkpointer=MemorySaver())
def accumulate_orders(
    new_item: str,
    *,
    previous: Optional[dict] = None
) -> entrypoint.final[dict, dict]:
    """累积订单(使用短期记忆)"""
    
    # 从previous获取历史订单
    if previous is None:
        orders = []
        total = 0.0
    else:
        orders = previous.get("orders", [])
        total = previous.get("total", 0.0)
    
    # 添加新订单
    if new_item in HUBU_LANE_FOODS:
        item_info = HUBU_LANE_FOODS[new_item]
        orders.append({
            "name": new_item,
            "price": item_info["price"]
        })
        total += item_info["price"]
        
        print(f"\n 添加: {new_item} ({item_info['price']}元)")
    else:
        print(f"\n 未找到: {new_item}")
    
    print(f" 当前订单:")
    for order in orders:
        print(f"   • {order['name']} - {order['price']}元")
    print(f" 总计: {total}元")
    
    # 保存状态到checkpoint
    saved_state = {
        "orders": orders,
        "total": total
    }
    
    # 返回当前订单信息,同时保存状态
    return entrypoint.final(
        value={"orders": orders, "total": total, "count": len(orders)},
        save=saved_state
    )


# ============================================================================
# 演示函数
# ============================================================================

def demo_basic_usage():
    """演示基本使用"""
    print("\n" + "="*70)
    print("示例1: 基本的@task和@entrypoint使用")
    print("="*70)
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # 推荐面食,预算8元
    result = recommend_foods.invoke(
        {"category": "面食", "max_price": 8.0},
        config
    )


def demo_human_in_loop():
    """演示人在环路"""
    print("\n\n" + "="*70)
    print("示例2: 人在环路支持")
    print("="*70)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 第一次调用,会在interrupt处暂停
    print("\n第一次调用(会暂停):")
    result = interactive_recommendation.invoke(15.0, config)
    
    if "__interrupt__" in result:
        print(f"\n  工作流已暂停,等待用户决策...")
        
        # 模拟用户接受推荐
        print("\n 用户决策: 接受推荐")
        from langgraph.types import Command
        final_result = interactive_recommendation.invoke(
            Command(resume=True),
            config
        )
        print(f"\n最终结果: {final_result}")


def demo_short_term_memory():
    """演示短期记忆"""
    print("\n\n" + "="*70)
    print("示例3: 短期记忆(累积订单)")
    print("="*70)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 连续添加订单
    items = ["热干面", "豆皮", "蛋酒"]
    
    for item in items:
        print(f"\n--- 添加 {item} ---")
        result = accumulate_orders.invoke(item, config)
        print(f"订单数量: {result['count']}")


if __name__ == "__main__":
    demo_basic_usage()
    demo_human_in_loop()
    demo_short_term_memory()
    
    print("\n\n 所有示例运行完成!")

