"""
第9章示例5: Hierarchical架构 - 层级化的组织结构
场景: 武汉智慧城市管理系统 - 多层级的智能体组织
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
# 交通管理模块 - 工具定义
# ============================================================================

@tool
def check_traffic_flow(road: str):
    """查询道路交通流量"""
    traffic = {
        "珞喻路": "当前流量: 中等,预计通行时间15分钟",
        "中南路": "当前流量: 拥堵,预计通行时间30分钟",
        "解放大道": "当前流量: 畅通,预计通行时间10分钟"
    }
    return traffic.get(road, "暂无该路段信息")


@tool
def check_metro_status(line: str):
    """查询地铁运行状态"""
    metro = {
        "2号线": "正常运行,间隔3分钟",
        "4号线": "正常运行,间隔4分钟",
        "11号线": "部分延误,间隔6分钟"
    }
    return metro.get(line, "暂无该线路信息")


@tool
def report_traffic_incident(location: str, incident: str):
    """报告交通事故"""
    return f"已记录{location}的{incident},交警将在10分钟内到达"


# ============================================================================
# 环境监测模块 - 工具定义
# ============================================================================

@tool
def check_air_quality(area: str):
    """查询空气质量"""
    aqi = {
        "武昌": "AQI: 65, 良好",
        "汉口": "AQI: 78, 良好",
        "汉阳": "AQI: 55, 优秀"
    }
    return aqi.get(area, "暂无该区域数据")


@tool
def check_water_quality(river: str):
    """查询水质"""
    water = {
        "长江": "水质: II类,良好",
        "汉江": "水质: II类,良好",
        "东湖": "水质: III类,合格"
    }
    return water.get(river, "暂无该水域数据")


@tool
def report_pollution(location: str, type: str):
    """报告污染情况"""
    return f"已记录{location}的{type}污染,环保部门将调查处理"


# ============================================================================
# 公共服务模块 - 工具定义
# ============================================================================

@tool
def check_hospital_info(hospital: str):
    """查询医院信息"""
    hospitals = {
        "协和医院": "三甲医院,24小时急诊,地铁2号线中南路站",
        "同济医院": "三甲医院,24小时急诊,地铁3号线云飞路站",
        "武汉大学人民医院": "三甲医院,24小时急诊,地铁2号线街道口站"
    }
    return hospitals.get(hospital, "暂无该医院信息")


@tool
def check_school_info(school: str):
    """查询学校信息"""
    schools = {
        "武汉大学": "985/211高校,位于武昌区珞珈山",
        "华中科技大学": "985/211高校,位于洪山区喻家山",
        "武汉理工大学": "211高校,位于洪山区珞狮路"
    }
    return schools.get(school, "暂无该学校信息")


@tool
def report_public_facility_issue(facility: str, issue: str):
    """报告公共设施问题"""
    return f"已记录{facility}的{issue},相关部门将在24小时内处理"


# ============================================================================
# 创建底层专业智能体
# ============================================================================

def create_traffic_agent():
    """交通管理智能体"""
    return create_agent(
        model=get_llm(),
        tools=[check_traffic_flow, check_metro_status, report_traffic_incident],
        system_prompt="你是交通管理专家,负责交通流量监控和事故处理",
        name="traffic_agent"
    )


def create_environment_agent():
    """环境监测智能体"""
    return create_agent(
        model=get_llm(),
        tools=[check_air_quality, check_water_quality, report_pollution],
        system_prompt="你是环境监测专家,负责空气和水质监测",
        name="environment_agent"
    )


def create_hospital_agent():
    """医疗服务智能体"""
    return create_agent(
        model=get_llm(),
        tools=[check_hospital_info],
        system_prompt="你是医疗服务专家,提供医院信息",
        name="hospital_agent"
    )


def create_education_agent():
    """教育服务智能体"""
    return create_agent(
        model=get_llm(),
        tools=[check_school_info],
        system_prompt="你是教育服务专家,提供学校信息",
        name="education_agent"
    )


# ============================================================================
# 创建中层模块Supervisor
# ============================================================================

def create_traffic_module_supervisor():
    """交通管理模块Supervisor"""
    
    def supervisor_node(state: MessagesState) -> Command:
        """路由到交通或环境智能体"""
        last_message = state["messages"][-1].content
        
        if "环境" in last_message or "空气" in last_message or "水质" in last_message:
            return Command(goto="environment_agent")
        else:
            return Command(goto="traffic_agent")
    
    # 创建子图
    graph = StateGraph(MessagesState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("traffic_agent", create_traffic_agent())
    graph.add_node("environment_agent", create_environment_agent())
    
    graph.add_edge(START, "supervisor")
    graph.add_edge("traffic_agent", END)
    graph.add_edge("environment_agent", END)
    
    return graph.compile()


def create_public_service_module_supervisor():
    """公共服务模块Supervisor"""
    
    def supervisor_node(state: MessagesState) -> Command:
        """路由到医疗或教育智能体"""
        last_message = state["messages"][-1].content
        
        if "医院" in last_message or "医疗" in last_message or "看病" in last_message:
            return Command(goto="hospital_agent")
        else:
            return Command(goto="education_agent")
    
    # 创建子图
    graph = StateGraph(MessagesState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("hospital_agent", create_hospital_agent())
    graph.add_node("education_agent", create_education_agent())
    
    graph.add_edge(START, "supervisor")
    graph.add_edge("hospital_agent", END)
    graph.add_edge("education_agent", END)
    
    return graph.compile()


# ============================================================================
# 创建顶层Supervisor
# ============================================================================

def create_top_level_supervisor():
    """顶层Supervisor - 协调各个模块"""
    
    def supervisor_node(state: MessagesState) -> Command:
        """路由到不同的模块"""
        last_message = state["messages"][-1].content
        
        # 判断属于哪个模块
        if any(keyword in last_message for keyword in ["交通", "地铁", "道路", "环境", "空气", "水质"]):
            return Command(goto="traffic_module")
        elif any(keyword in last_message for keyword in ["医院", "学校", "医疗", "教育"]):
            return Command(goto="public_service_module")
        else:
            return Command(goto=END)
    
    # 创建模块子图
    traffic_module = create_traffic_module_supervisor()
    public_service_module = create_public_service_module_supervisor()
    
    # 创建顶层图
    graph = StateGraph(MessagesState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("traffic_module", traffic_module)
    graph.add_node("public_service_module", public_service_module)
    
    graph.add_edge(START, "supervisor")
    graph.add_edge("traffic_module", END)
    graph.add_edge("public_service_module", END)
    
    return graph.compile()


# ============================================================================
# 测试函数
# ============================================================================

def test_hierarchical_architecture():
    """测试Hierarchical架构"""
    
    print("=" * 80)
    print("第9章示例5: Hierarchical架构 - 武汉智慧城市管理系统")
    print("=" * 80)
    print("\n架构层级:")
    print("顶层: 总协调Supervisor")
    print("├─ 交通管理模块")
    print("│  ├─ 交通智能体")
    print("│  └─ 环境智能体")
    print("└─ 公共服务模块")
    print("   ├─ 医疗智能体")
    print("   └─ 教育智能体\n")
    
    system = create_top_level_supervisor()
    
    # 测试用例1: 交通查询
    print("\n测试1: 交通查询(路由到交通模块)")
    print("-" * 80)
    query1 = "珞喻路现在堵不堵?"
    print(f"用户: {query1}\n")
    
    result1 = system.invoke({
        "messages": [HumanMessage(content=query1)]
    })
    
    print(f"系统: {result1['messages'][-1].content}\n")
    
    # 测试用例2: 环境查询
    print("\n测试2: 环境查询(路由到交通模块->环境智能体)")
    print("-" * 80)
    query2 = "武昌区今天空气质量怎么样?"
    print(f"用户: {query2}\n")
    
    result2 = system.invoke({
        "messages": [HumanMessage(content=query2)]
    })
    
    print(f"系统: {result2['messages'][-1].content}\n")
    
    # 测试用例3: 医疗查询
    print("\n测试3: 医疗查询(路由到公共服务模块->医疗智能体)")
    print("-" * 80)
    query3 = "协和医院在哪里?有急诊吗?"
    print(f"用户: {query3}\n")
    
    result3 = system.invoke({
        "messages": [HumanMessage(content=query3)]
    })
    
    print(f"系统: {result3['messages'][-1].content}\n")
    
    # 测试用例4: 教育查询
    print("\n测试4: 教育查询(路由到公共服务模块->教育智能体)")
    print("-" * 80)
    query4 = "武汉大学在哪个区?"
    print(f"用户: {query4}\n")
    
    result4 = system.invoke({
        "messages": [HumanMessage(content=query4)]
    })
    
    print(f"系统: {result4['messages'][-1].content}\n")
    
    print("\n" + "=" * 80)
    print("Hierarchical架构优势:")
    print("1. 关注点分离 - 每层只关注自己的职责")
    print("2. 可扩展性强 - 可以方便地添加新模块和智能体")
    print("3. 支持大规模系统 - 通过层级化管理复杂度")
    print("4. 团队协作友好 - 不同团队负责不同模块")
    print("=" * 80)


if __name__ == "__main__":
    test_hierarchical_architecture()

