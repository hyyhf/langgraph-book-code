"""
第9章示例4: Supervisor(Tool-calling)变体 - 智能体即工具
场景: 武汉房产服务 - 租房、买房、装修智能体作为工具被Supervisor调用
"""

from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.prebuilt import InjectedState
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 定义专业工具
# ============================================================================

# 租房相关工具
@tool
def search_rental(area: str, budget: int):
    """搜索租房信息"""
    rentals = {
        "光谷": f"光谷软件园附近,2室1厅,{budget}元/月,地铁2号线光谷广场站",
        "街道口": f"武汉大学附近,1室1厅,{budget}元/月,地铁2号线街道口站",
        "汉口": f"江汉路商圈,2室1厅,{budget}元/月,地铁2号线江汉路站",
        "武昌": f"楚河汉街附近,1室1厅,{budget}元/月,地铁4号线楚河汉街站"
    }
    return rentals.get(area, f"{area}地区暂无{budget}元左右的房源")


@tool
def check_rental_contract(house_id: str):
    """查看租房合同"""
    return f"房源{house_id}的租赁合同: 租期1年,押一付三,包含物业费,不包含水电费"


# 买房相关工具
@tool
def search_house_sale(area: str, budget: int):
    """搜索二手房信息"""
    houses = {
        "光谷": f"光谷东,90平米,{budget}万,地铁11号线",
        "街道口": f"珞狮路,80平米,{budget}万,地铁2号线",
        "汉口": f"后湖,100平米,{budget}万,地铁3号线",
        "武昌": f"中南路,85平米,{budget}万,地铁2/4号线"
    }
    return houses.get(area, f"{area}地区暂无{budget}万左右的房源")


@tool
def calculate_loan(price: int, down_payment_ratio: float, years: int):
    """计算房贷"""
    down_payment = price * down_payment_ratio
    loan_amount = price - down_payment
    # 简化计算,假设年利率4.5%
    monthly_rate = 0.045 / 12
    months = years * 12
    monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
    return f"总价{price}万,首付{down_payment:.1f}万,贷款{loan_amount:.1f}万,{years}年期,月供约{monthly_payment:.2f}万"


# 装修相关工具
@tool
def get_decoration_quote(area: int, style: str):
    """获取装修报价"""
    prices = {
        "简约": 800,
        "现代": 1000,
        "中式": 1200,
        "欧式": 1500
    }
    price_per_sqm = prices.get(style, 1000)
    total = area * price_per_sqm
    return f"{style}风格装修,{area}平米,预计{total}元,工期3-4个月"


@tool
def recommend_decoration_company(area: str):
    """推荐装修公司"""
    companies = {
        "光谷": "光谷装饰公司 - 专注科技园区精装,口碑好",
        "街道口": "珞珈装饰 - 武大周边老牌公司,性价比高",
        "汉口": "江城装饰 - 汉口地区龙头企业,品质保证",
        "武昌": "楚天装饰 - 武昌本地公司,服务周到"
    }
    return companies.get(area, "推荐: 武汉市装饰协会会员单位")


# ============================================================================
# 创建专业智能体
# ============================================================================

def create_rental_agent():
    """创建租房智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_rental, check_rental_contract],
        system_prompt="你是租房专家,帮助用户找到合适的租房,解答租房相关问题",
        name="rental_agent"
    )


def create_sale_agent():
    """创建买房智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_house_sale, calculate_loan],
        system_prompt="你是买房专家,帮助用户找房和计算房贷",
        name="sale_agent"
    )


def create_decoration_agent():
    """创建装修智能体"""
    return create_agent(
        model=get_llm(),
        tools=[get_decoration_quote, recommend_decoration_company],
        system_prompt="你是装修专家,提供装修报价和公司推荐",
        name="decoration_agent"
    )


# ============================================================================
# 将智能体包装为工具
# ============================================================================

def create_agent_tool(agent_name: str, agent_graph, description: str):
    """将智能体包装为可调用的工具"""

    @tool(f"consult_{agent_name}", description=description)
    def agent_tool(
        query: Annotated[str, "用户的具体问题"],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> str:
        """调用专业智能体"""
        # 调用智能体
        result = agent_graph.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        # 返回智能体的回复
        return result["messages"][-1].content
    
    return agent_tool


# ============================================================================
# 创建Supervisor(使用智能体工具)
# ============================================================================

def create_supervisor_with_agent_tools():
    """创建使用智能体作为工具的Supervisor"""
    
    # 创建专业智能体
    rental_agent = create_rental_agent()
    sale_agent = create_sale_agent()
    decoration_agent = create_decoration_agent()
    
    # 将智能体包装为工具
    rental_tool = create_agent_tool(
        "rental_agent",
        rental_agent,
        "咨询租房相关问题,包括搜索房源、查看合同等"
    )
    
    sale_tool = create_agent_tool(
        "sale_agent",
        sale_agent,
        "咨询买房相关问题,包括搜索房源、计算房贷等"
    )
    
    decoration_tool = create_agent_tool(
        "decoration_agent",
        decoration_agent,
        "咨询装修相关问题,包括装修报价、公司推荐等"
    )
    
    # 创建Supervisor,配备智能体工具
    supervisor = create_agent(
        model=get_llm(),
        tools=[rental_tool, sale_tool, decoration_tool],
        system_prompt="""你是武汉房产服务总协调员。

你可以调用三个专业顾问:
1. consult_rental_agent - 租房顾问: 处理租房相关问题
2. consult_sale_agent - 买房顾问: 处理买房相关问题
3. consult_decoration_agent - 装修顾问: 处理装修相关问题

根据用户问题,选择合适的顾问进行咨询。
可以同时咨询多个顾问,例如买房后需要装修。

重要: 使用工具时,将用户的具体问题作为query参数传递。""",
        name="supervisor"
    )
    
    return supervisor


# ============================================================================
# 测试函数
# ============================================================================

def test_tool_calling_variant():
    """测试Tool-calling变体"""
    
    print("=" * 80)
    print("第9章示例4: Tool-calling变体 - 武汉房产服务")
    print("=" * 80)
    print("\n特点: 专业智能体作为工具被Supervisor调用\n")
    
    supervisor = create_supervisor_with_agent_tools()
    
    # 测试用例1: 单一咨询
    print("\n测试1: 租房咨询")
    print("-" * 80)
    query1 = "我想在光谷租房,预算2000元左右"
    print(f"用户: {query1}\n")

    result1 = supervisor.invoke(
        {"messages": [HumanMessage(content=query1)]},
        config={"recursion_limit": 50}
    )

    print(f"系统: {result1['messages'][-1].content}\n")

    # 测试用例2: 复合咨询
    print("\n测试2: 买房+装修咨询")
    print("-" * 80)
    query2 = "我想在街道口买房,预算200万,买完后想装修成现代风格"
    print(f"用户: {query2}\n")

    result2 = supervisor.invoke(
        {"messages": [HumanMessage(content=query2)]},
        config={"recursion_limit": 50}
    )
    
    print(f"系统: {result2['messages'][-1].content}\n")
    
    # 测试用例3: 房贷计算
    print("\n测试3: 房贷计算")
    print("-" * 80)
    query3 = "200万的房子,首付30%,贷款30年,月供多少?"
    print(f"用户: {query3}\n")
    
    result3 = supervisor.invoke({
        "messages": [HumanMessage(content=query3)]
    })
    
    print(f"系统: {result3['messages'][-1].content}\n")
    
    print("\n" + "=" * 80)
    print("Tool-calling变体优势:")
    print("1. 简化实现 - 使用标准工具调用机制")
    print("2. 统一接口 - 智能体和工具使用相同的调用方式")
    print("3. 支持并行 - 可以同时调用多个智能体工具")
    print("4. 易于理解 - 符合工具调用的直觉")
    print("=" * 80)


if __name__ == "__main__":
    test_tool_calling_variant()

