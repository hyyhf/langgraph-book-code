"""
7.3节 子图(Subgraphs)示例代码
场景:武汉智慧城市管理系统

这个示例展示了如何使用子图构建模块化的复杂系统:
1. 子图作为节点
2. 状态传递机制
3. 子图的持久化
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import operator


# ============================================================================
# 子系统1: 交通管理子图
# ============================================================================

class TrafficState(TypedDict):
    """交通状态"""
    area: str  # 区域
    traffic_flow: int  # 车流量
    congestion_level: int  # 拥堵等级 0-5
    signal_status: str  # 信号灯状态
    recommendations: Annotated[list[str], operator.add]  # 建议(累加)


def monitor_traffic(state: TrafficState) -> dict:
    """监控交通"""
    print(f"\n🚦 监控交通 - {state['area']}")
    print(f"   车流量: {state['traffic_flow']} 辆/小时")
    
    # 根据车流量判断拥堵等级
    if state['traffic_flow'] > 2000:
        level = 5
    elif state['traffic_flow'] > 1500:
        level = 4
    elif state['traffic_flow'] > 1000:
        level = 3
    elif state['traffic_flow'] > 500:
        level = 2
    else:
        level = 1
    
    print(f"   拥堵等级: {level}/5")
    
    return {"congestion_level": level}


def adjust_signals(state: TrafficState) -> dict:
    """调整信号灯"""
    level = state.get("congestion_level", 0)
    
    if level >= 4:
        signal = "延长绿灯时间"
        recommendations = [f"{state['area']}: 建议启用潮汐车道"]
    elif level >= 3:
        signal = "正常配时"
        recommendations = [f"{state['area']}: 建议优化信号配时"]
    else:
        signal = "正常配时"
        recommendations = []
    
    print(f"   信号灯: {signal}")
    
    return {
        "signal_status": signal,
        "recommendations": recommendations
    }


def build_traffic_subgraph():
    """构建交通管理子图"""
    builder = StateGraph(TrafficState)
    
    builder.add_node("monitor", monitor_traffic)
    builder.add_node("adjust", adjust_signals)
    
    builder.add_edge(START, "monitor")
    builder.add_edge("monitor", "adjust")
    builder.add_edge("adjust", END)
    
    return builder.compile()


# ============================================================================
# 子系统2: 环境监测子图
# ============================================================================

class EnvironmentState(TypedDict):
    """环境状态"""
    area: str  # 区域
    aqi: int  # 空气质量指数
    temperature: float  # 温度
    humidity: float  # 湿度
    air_quality: str  # 空气质量等级
    recommendations: Annotated[list[str], operator.add]  # 建议(累加)


def monitor_air_quality(state: EnvironmentState) -> dict:
    """监测空气质量"""
    print(f"\n 监测空气质量 - {state['area']}")
    print(f"   AQI: {state['aqi']}")
    
    # 判断空气质量等级
    if state['aqi'] <= 50:
        quality = "优"
    elif state['aqi'] <= 100:
        quality = "良"
    elif state['aqi'] <= 150:
        quality = "轻度污染"
    elif state['aqi'] <= 200:
        quality = "中度污染"
    else:
        quality = "重度污染"
    
    print(f"   等级: {quality}")
    
    return {"air_quality": quality}


def environment_recommendations(state: EnvironmentState) -> dict:
    """环境建议"""
    recommendations = []
    
    if state['aqi'] > 150:
        recommendations.append(f"{state['area']}: 建议减少户外活动")
        recommendations.append(f"{state['area']}: 建议启动应急预案")
    elif state['aqi'] > 100:
        recommendations.append(f"{state['area']}: 建议敏感人群减少外出")
    
    if state.get('temperature', 0) > 35:
        recommendations.append(f"{state['area']}: 高温预警,注意防暑")
    
    return {"recommendations": recommendations}


def build_environment_subgraph():
    """构建环境监测子图"""
    builder = StateGraph(EnvironmentState)
    
    builder.add_node("monitor_air", monitor_air_quality)
    builder.add_node("recommend", environment_recommendations)
    
    builder.add_edge(START, "monitor_air")
    builder.add_edge("monitor_air", "recommend")
    builder.add_edge("recommend", END)
    
    return builder.compile()


# ============================================================================
# 主系统: 城市管理系统
# ============================================================================

class CityState(TypedDict):
    """城市管理状态"""
    area: str  # 区域
    # 交通相关
    traffic_flow: int
    congestion_level: int
    signal_status: str
    # 环境相关
    aqi: int
    temperature: float
    humidity: float
    air_quality: str
    # 综合
    recommendations: Annotated[list[str], operator.add]
    overall_status: str


def prepare_traffic_data(state: CityState) -> dict:
    """准备交通数据"""
    print(f"\n 准备交通数据...")
    return {}


def prepare_environment_data(state: CityState) -> dict:
    """准备环境数据"""
    print(f"\n 准备环境数据...")
    return {}


def generate_report(state: CityState) -> dict:
    """生成综合报告"""
    print(f"\n 生成综合报告 - {state['area']}")
    print(f"=" * 60)
    
    # 交通状况
    print(f"\n 交通状况:")
    print(f"  车流量: {state.get('traffic_flow', 0)} 辆/小时")
    print(f"  拥堵等级: {state.get('congestion_level', 0)}/5")
    print(f"  信号灯: {state.get('signal_status', 'N/A')}")
    
    # 环境状况
    print(f"\n 环境状况:")
    print(f"  AQI: {state.get('aqi', 0)}")
    print(f"  空气质量: {state.get('air_quality', 'N/A')}")
    print(f"  温度: {state.get('temperature', 0)}°C")
    print(f"  湿度: {state.get('humidity', 0)}%")
    
    # 建议
    recommendations = state.get('recommendations', [])
    if recommendations:
        print(f"\n 建议:")
        for rec in recommendations:
            print(f"   • {rec}")
    
    # 综合评估
    congestion = state.get('congestion_level', 0)
    aqi = state.get('aqi', 0)
    
    if congestion >= 4 or aqi > 150:
        overall = "需要关注"
    elif congestion >= 3 or aqi > 100:
        overall = "基本正常"
    else:
        overall = "良好"
    
    print(f"\n 综合状态: {overall}")
    
    return {"overall_status": overall}


def build_city_management_graph():
    """构建城市管理主图(使用子图作为节点)"""
    # 创建子图
    traffic_graph = build_traffic_subgraph()
    environment_graph = build_environment_subgraph()
    
    # 创建主图
    builder = StateGraph(CityState)
    
    # 添加普通节点
    builder.add_node("prepare_traffic", prepare_traffic_data)
    builder.add_node("prepare_environment", prepare_environment_data)
    builder.add_node("report", generate_report)
    
    # 添加子图作为节点
    builder.add_node("traffic_system", traffic_graph)
    builder.add_node("environment_system", environment_graph)
    
    # 构建流程
    builder.add_edge(START, "prepare_traffic")
    builder.add_edge("prepare_traffic", "traffic_system")
    builder.add_edge("traffic_system", "prepare_environment")
    builder.add_edge("prepare_environment", "environment_system")
    builder.add_edge("environment_system", "report")
    builder.add_edge("report", END)
    
    # 使用检查点器
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# 示例演示
# ============================================================================

def demo_subgraph_as_node():
    """演示子图作为节点"""
    print("=" * 70)
    print("示例1: 子图作为节点")
    print("=" * 70)
    print("场景: 武汉光谷区域智慧城市管理")
    
    graph = build_city_management_graph()
    
    config = {"configurable": {"thread_id": "guanggu-001"}}
    state = {
        "area": "光谷广场",
        "traffic_flow": 1800,  # 较高车流量
        "congestion_level": 0,
        "signal_status": "",
        "aqi": 120,  # 轻度污染
        "temperature": 32.0,
        "humidity": 65.0,
        "air_quality": "",
        "recommendations": [],
        "overall_status": ""
    }
    
    result = graph.invoke(state, config)
    
    print("\n" + "=" * 70)


def demo_multiple_areas():
    """演示多个区域的管理"""
    print("\n\n" + "=" * 70)
    print("示例2: 多个区域的城市管理")
    print("=" * 70)
    
    graph = build_city_management_graph()
    
    areas = [
        {
            "area": "武汉天地",
            "traffic_flow": 2200,
            "aqi": 85,
            "temperature": 28.0,
            "humidity": 70.0
        },
        {
            "area": "楚河汉街",
            "traffic_flow": 1200,
            "aqi": 160,
            "temperature": 30.0,
            "humidity": 68.0
        },
        {
            "area": "汉口江滩",
            "traffic_flow": 600,
            "aqi": 75,
            "temperature": 26.0,
            "humidity": 72.0
        }
    ]
    
    for area_data in areas:
        config = {"configurable": {"thread_id": f"area-{area_data['area']}"}}
        
        state = {
            "area": area_data["area"],
            "traffic_flow": area_data["traffic_flow"],
            "congestion_level": 0,
            "signal_status": "",
            "aqi": area_data["aqi"],
            "temperature": area_data["temperature"],
            "humidity": area_data["humidity"],
            "air_quality": "",
            "recommendations": [],
            "overall_status": ""
        }
        
        result = graph.invoke(state, config)
        
        print("\n" + "-" * 70)


if __name__ == "__main__":
    demo_subgraph_as_node()
    demo_multiple_areas()
    
    print("\n\n 所有示例运行完成!")

