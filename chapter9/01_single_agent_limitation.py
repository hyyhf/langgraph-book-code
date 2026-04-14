"""
第9章示例1: 单智能体的局限性演示
场景: 武汉旅游规划助手 - 展示工具过载和上下文爆炸问题
"""

from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.graph import MessagesState
from config import get_llm


# ============================================================================
# 定义大量工具 - 模拟工具过载
# ============================================================================

@tool
def search_yellow_crane_tower():
    """搜索黄鹤楼的信息"""
    return "黄鹤楼位于武汉市武昌区,是中国四大名楼之一,门票70元,开放时间8:00-18:00"


@tool
def search_east_lake():
    """搜索东湖的信息"""
    return "东湖是中国最大的城中湖,面积33平方公里,有听涛、磨山、落雁等景区"


@tool
def search_wuhan_university():
    """搜索武汉大学的信息"""
    return "武汉大学创建于1893年,以樱花闻名,每年3-4月樱花季吸引大量游客"


@tool
def search_hubei_museum():
    """搜索湖北省博物馆的信息"""
    return "湖北省博物馆收藏曾侯乙编钟等国宝,免费开放,需提前预约"


@tool
def search_hot_dry_noodles():
    """搜索热干面信息"""
    return "热干面是武汉特色小吃,推荐蔡林记、老通城等老字号,价格5-15元"


@tool
def search_duck_neck():
    """搜索鸭脖信息"""
    return "周黑鸭和精武鸭脖是武汉著名品牌,香辣可口,价格20-50元/斤"


@tool
def search_doupi():
    """搜索豆皮信息"""
    return "豆皮是武汉传统早点,老通城豆皮最为有名,价格8-15元"


@tool
def search_metro():
    """搜索武汉地铁信息"""
    return "武汉地铁有12条线路,覆盖三镇,单程票价2-7元,支持支付宝/微信"


@tool
def search_bus():
    """搜索武汉公交信息"""
    return "武汉公交线路众多,普通车1-2元,空调车2元,支持刷卡和扫码"


@tool
def search_ferry():
    """搜索武汉轮渡信息"""
    return "武汉轮渡连接汉口、武昌、汉阳,票价1.5元,可欣赏长江风光"


@tool
def search_hotels():
    """搜索武汉酒店信息"""
    return "武汉酒店从经济型到五星级齐全,价格100-2000元,建议选择地铁沿线"


@tool
def search_weather():
    """搜索武汉天气信息"""
    return "武汉属亚热带季风气候,夏季炎热,冬季湿冷,春秋最适合旅游"


@tool
def book_hotel(hotel_name: str, check_in: str, nights: int):
    """预订酒店"""
    return f"已预订{hotel_name},入住日期{check_in},共{nights}晚"


@tool
def book_ticket(attraction: str, date: str, count: int):
    """预订景点门票"""
    return f"已预订{attraction}门票{count}张,游览日期{date}"


@tool
def plan_route(start: str, end: str, transport: str):
    """规划路线"""
    return f"从{start}到{end},建议乘坐{transport},预计30分钟"


# ============================================================================
# 创建单智能体 - 配备所有工具
# ============================================================================

def create_single_agent_with_all_tools():
    """创建一个配备所有工具的单智能体"""
    
    # 所有工具列表 - 共15个工具
    all_tools = [
        # 景点查询工具(4个)
        search_yellow_crane_tower,
        search_east_lake,
        search_wuhan_university,
        search_hubei_museum,
        # 美食查询工具(3个)
        search_hot_dry_noodles,
        search_duck_neck,
        search_doupi,
        # 交通查询工具(3个)
        search_metro,
        search_bus,
        search_ferry,
        # 其他查询工具(2个)
        search_hotels,
        search_weather,
        # 预订工具(3个)
        book_hotel,
        book_ticket,
        plan_route,
    ]
    
    # 创建智能体
    agent = create_agent(
        model=get_llm(),
        tools=all_tools,
        system_prompt="""你是武汉旅游规划助手,负责帮助游客规划武汉之旅。
你需要:
1. 推荐景点并提供详细信息
2. 推荐美食并告知价格
3. 规划交通路线
4. 预订酒店和门票
5. 提供天气信息

请根据用户需求,使用合适的工具提供帮助。"""
    )
    
    return agent


# ============================================================================
# 演示工具过载问题
# ============================================================================

def demo_tool_overload():
    """演示工具过载导致的决策困难"""
    
    print("=" * 80)
    print("演示1: 工具过载问题")
    print("=" * 80)
    print("\n单智能体配备了15个工具,在简单查询时也需要从大量工具中选择\n")
    
    agent = create_single_agent_with_all_tools()
    
    # 简单查询
    query = "我想了解黄鹤楼的信息"
    print(f"用户查询: {query}\n")
    
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    
    # 统计工具调用
    tool_calls = [msg for msg in result["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls]
    print(f"\n工具调用次数: {sum(len(msg.tool_calls) for msg in tool_calls)}")
    print(f"消息总数: {len(result['messages'])}")
    print("\n问题: 即使是简单查询,智能体也需要从15个工具中选择,增加了决策复杂度")


# ============================================================================
# 演示上下文爆炸问题
# ============================================================================

def demo_context_explosion():
    """演示上下文快速膨胀问题"""
    
    print("\n" + "=" * 80)
    print("演示2: 上下文爆炸问题")
    print("=" * 80)
    print("\n执行复杂任务时,上下文会快速增长\n")
    
    agent = create_single_agent_with_all_tools()
    
    # 复杂查询
    query = """我计划3月份来武汉旅游3天,请帮我:
1. 推荐必去景点(至少3个)
2. 推荐特色美食(至少3种)
3. 规划交通方式
4. 推荐酒店
5. 查询天气情况"""
    
    print(f"用户查询: {query}\n")
    
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    
    # 统计上下文信息
    total_messages = len(result["messages"])
    total_chars = sum(len(str(msg.content)) for msg in result["messages"] if hasattr(msg, "content"))
    
    print(f"\n上下文统计:")
    print(f"- 消息总数: {total_messages}")
    print(f"- 总字符数: {total_chars}")
    print(f"- 估计token数: {total_chars // 3}")  # 粗略估计
    
    print("\n问题: 所有信息都保留在一个上下文中,导致:")
    print("1. 上下文快速膨胀")
    print("2. 处理成本增加")
    print("3. 可能超出上下文窗口限制")


# ============================================================================
# 演示专业化缺失问题
# ============================================================================

def demo_lack_of_specialization():
    """演示专业化不足的问题"""
    
    print("\n" + "=" * 80)
    print("演示3: 专业化缺失问题")
    print("=" * 80)
    print("\n单智能体需要处理多个领域,难以在每个领域都做到专业\n")
    
    print("问题分析:")
    print("1. 景点推荐需要深入了解历史文化")
    print("2. 美食推荐需要了解口味特点和价格")
    print("3. 交通规划需要了解路线和时间")
    print("4. 酒店预订需要了解位置和性价比")
    print("\n单个智能体很难在所有领域都达到专家水平")
    print("系统提示词需要包含所有领域的指导,导致提示词过长且难以优化")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("第9章示例1: 单智能体的局限性")
    print("场景: 武汉旅游规划助手")
    print("=" * 80)
    
    # 演示1: 工具过载
    demo_tool_overload()
    
    # 演示2: 上下文爆炸
    demo_context_explosion()
    
    # 演示3: 专业化缺失
    demo_lack_of_specialization()
    
    print("\n" + "=" * 80)
    print("总结: 单智能体在处理复杂任务时面临三大局限:")
    print("1. 工具过载 - 工具数量过多导致决策质量下降")
    print("2. 上下文爆炸 - 所有信息集中导致上下文快速膨胀")
    print("3. 专业化缺失 - 难以在多个领域都达到专家水平")
    print("\n解决方案: 采用多智能体架构,将任务分解给专业智能体")
    print("=" * 80)

