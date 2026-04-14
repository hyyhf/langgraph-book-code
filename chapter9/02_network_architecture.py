"""
第9章示例2: Network架构 - 全互联的协作网络
场景: 武汉旅游咨询系统 - 景点、美食、交通智能体相互协作
"""

from typing import Annotated, Literal
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langgraph.prebuilt import InjectedState
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 定义专业工具
# ============================================================================

# 景点相关工具
@tool
def search_attractions(keyword: str):
    """搜索武汉景点信息"""
    attractions = {
        "黄鹤楼": "中国四大名楼之一,门票70元,位于武昌区蛇山,地铁4号线复兴路站",
        "东湖": "中国最大城中湖,免费开放,有听涛、磨山、落雁景区,地铁8号线",
        "武汉大学": "百年名校,樱花胜地,免费开放,3-4月最佳,地铁2号线街道口站",
        "湖北省博物馆": "收藏曾侯乙编钟,免费但需预约,地铁4号线东亭站"
    }
    for name, info in attractions.items():
        if keyword in name:
            return f"{name}: {info}"
    return "未找到相关景点"


@tool
def get_attraction_nearby(attraction: str):
    """获取景点附近的美食和交通信息"""
    nearby = {
        "黄鹤楼": "附近有户部巷美食街,可乘地铁4号线或公交",
        "东湖": "附近有楚河汉街美食区,可乘地铁8号线",
        "武汉大学": "附近有街道口美食街,可乘地铁2号线",
        "湖北省博物馆": "附近有东湖绿道,可乘地铁4号线"
    }
    return nearby.get(attraction, "暂无附近信息")


# 美食相关工具
@tool
def search_food(food_type: str):
    """搜索武汉美食信息"""
    foods = {
        "热干面": "武汉特色早餐,推荐蔡林记、老通城,价格5-15元",
        "鸭脖": "周黑鸭和精武鸭脖,香辣可口,20-50元/斤",
        "豆皮": "传统早点,老通城豆皮最有名,8-15元",
        "武昌鱼": "清蒸武昌鱼是经典菜,推荐大中华酒楼,50-100元"
    }
    for name, info in foods.items():
        if food_type in name:
            return f"{name}: {info}"
    return "未找到相关美食"


@tool
def recommend_food_near_attraction(attraction: str):
    """推荐景点附近的美食"""
    recommendations = {
        "黄鹤楼": "户部巷有热干面、豆皮等传统小吃",
        "东湖": "楚河汉街有各类餐厅,推荐试试武昌鱼",
        "武汉大学": "街道口有众多小吃店,热干面和鸭脖很受欢迎",
        "湖北省博物馆": "东湖绿道有特色餐厅"
    }
    return recommendations.get(attraction, "暂无推荐")


# 交通相关工具
@tool
def plan_route(start: str, end: str):
    """规划两地之间的路线"""
    routes = {
        ("黄鹤楼", "东湖"): "地铁4号线转8号线,约40分钟,票价4元",
        ("黄鹤楼", "武汉大学"): "地铁4号线转2号线,约35分钟,票价4元",
        ("东湖", "武汉大学"): "地铁8号线转2号线,约30分钟,票价3元",
        ("武汉大学", "湖北省博物馆"): "地铁2号线转4号线,约25分钟,票价3元"
    }
    route = routes.get((start, end)) or routes.get((end, start))
    return route if route else f"从{start}到{end}的路线规划中..."


@tool
def get_transport_to_attraction(attraction: str):
    """获取到达景点的交通方式"""
    transport = {
        "黄鹤楼": "地铁4号线复兴路站,或公交10、61、401路",
        "东湖": "地铁8号线梨园站,或公交402、413路",
        "武汉大学": "地铁2号线街道口站,或公交564、572路",
        "湖北省博物馆": "地铁4号线东亭站,或公交14、108路"
    }
    return transport.get(attraction, "暂无交通信息")


# ============================================================================
# 创建专业智能体
# ============================================================================

def create_attraction_agent():
    """创建景点咨询智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_attractions, get_attraction_nearby],
        system_prompt="""你是武汉景点咨询专家。
你的职责:
1. 提供景点的详细信息(门票、位置、特色)
2. 推荐必去景点
3. 如果用户询问美食,转交给美食专家
4. 如果用户询问交通,转交给交通专家

重要: 当用户询问美食或交通时,使用transfer工具转交给相应专家。""",
        name="attraction_agent"
    )


def create_food_agent():
    """创建美食推荐智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_food, recommend_food_near_attraction],
        system_prompt="""你是武汉美食推荐专家。
你的职责:
1. 推荐武汉特色美食
2. 提供美食的价格和位置信息
3. 根据景点推荐附近美食
4. 如果用户询问景点,转交给景点专家
5. 如果用户询问交通,转交给交通专家

重要: 当用户询问景点或交通时,使用transfer工具转交给相应专家。""",
        name="food_agent"
    )


def create_transport_agent():
    """创建交通规划智能体"""
    return create_agent(
        model=get_llm(),
        tools=[plan_route, get_transport_to_attraction],
        system_prompt="""你是武汉交通规划专家。
你的职责:
1. 规划两地之间的路线
2. 提供到达景点的交通方式
3. 估算时间和费用
4. 如果用户询问景点,转交给景点专家
5. 如果用户询问美食,转交给美食专家

重要: 当用户询问景点或美食时,使用transfer工具转交给相应专家。""",
        name="transport_agent"
    )


# ============================================================================
# 创建交接工具
# ============================================================================

def create_handoff_tool(agent_name: str, description: str):
    """创建智能体间的交接工具"""

    @tool(f"transfer_to_{agent_name}", description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """转交给其他智能体"""
        tool_message = {
            "role": "tool",
            "content": f"已转交给{agent_name}",
            "name": f"transfer_to_{agent_name}",
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,
            update={"messages": state["messages"] + [tool_message]},
            graph=Command.PARENT
        )

    return handoff_tool


# 为每个智能体创建交接工具
transfer_to_attraction = create_handoff_tool(
    "attraction_agent",
    "当用户询问景点信息时,转交给景点专家"
)

transfer_to_food = create_handoff_tool(
    "food_agent",
    "当用户询问美食信息时,转交给美食专家"
)

transfer_to_transport = create_handoff_tool(
    "transport_agent",
    "当用户询问交通信息时,转交给交通专家"
)


# ============================================================================
# 构建Network架构图
# ============================================================================

def create_network_graph():
    """创建Network架构的多智能体图"""
    
    # 创建智能体(每个智能体都配备交接工具)
    attraction_agent = create_agent(
        model=get_llm(),
        tools=[search_attractions, get_attraction_nearby,
               transfer_to_food, transfer_to_transport],
        system_prompt="你是景点专家,可以转交给美食或交通专家",
        name="attraction_agent"
    )

    food_agent = create_agent(
        model=get_llm(),
        tools=[search_food, recommend_food_near_attraction,
               transfer_to_attraction, transfer_to_transport],
        system_prompt="你是美食专家,可以转交给景点或交通专家",
        name="food_agent"
    )

    transport_agent = create_agent(
        model=get_llm(),
        tools=[plan_route, get_transport_to_attraction,
               transfer_to_attraction, transfer_to_food],
        system_prompt="你是交通专家,可以转交给景点或美食专家",
        name="transport_agent"
    )
    
    # 构建图
    graph = StateGraph(MessagesState)
    
    # 添加节点
    graph.add_node("attraction_agent", attraction_agent)
    graph.add_node("food_agent", food_agent)
    graph.add_node("transport_agent", transport_agent)
    
    # 设置入口(默认从景点专家开始)
    graph.add_edge(START, "attraction_agent")
    
    return graph.compile()


# ============================================================================
# 测试函数
# ============================================================================

def test_network_architecture():
    """测试Network架构"""
    
    print("=" * 80)
    print("第9章示例2: Network架构 - 武汉旅游咨询系统")
    print("=" * 80)
    print("\n特点: 三个专业智能体(景点、美食、交通)可以相互转交任务\n")
    
    graph = create_network_graph()
    
    # 测试用例1: 需要多个智能体协作
    print("\n测试1: 综合查询(需要多个智能体协作)")
    print("-" * 80)
    query1 = "我想去黄鹤楼,附近有什么好吃的?怎么去?"
    print(f"用户: {query1}\n")
    
    result1 = graph.invoke({
        "messages": [HumanMessage(content=query1)]
    })
    
    print(f"最终回复: {result1['messages'][-1].content}\n")
    
    # 测试用例2: 动态路由
    print("\n测试2: 动态路由(根据对话内容自动转交)")
    print("-" * 80)
    query2 = "推荐一些武汉美食"
    print(f"用户: {query2}\n")
    
    result2 = graph.invoke({
        "messages": [HumanMessage(content=query2)]
    })
    
    print(f"最终回复: {result2['messages'][-1].content}\n")
    
    print("\n" + "=" * 80)
    print("Network架构优势:")
    print("1. 灵活性高 - 智能体可以根据需要相互转交")
    print("2. 去中心化 - 没有中央控制节点")
    print("3. 自适应强 - 可以处理复杂的非线性任务")
    print("=" * 80)


if __name__ == "__main__":
    test_network_architecture()

