"""
7.1节 人在环路 - 编译时中断示例
场景:武汉长江大桥交通管制系统

这个示例展示了如何使用编译时中断(interrupt_before/interrupt_after)
来实现调试和人工干预功能。
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import uuid


class TrafficState(TypedDict):
    """交通状态"""
    vehicle_id: str  # 车辆ID
    vehicle_type: str  # 车辆类型
    current_section: str  # 当前路段
    speed: float  # 当前速度(km/h)
    weather: str  # 天气状况
    alert_level: int  # 警报级别 0-正常 1-注意 2-警告 3-危险
    action_taken: Optional[str]  # 采取的措施


def detect_vehicle(state: TrafficState) -> dict:
    """检测车辆"""
    print(f"\n 检测到车辆: {state['vehicle_id']}")
    print(f"类型: {state['vehicle_type']}")
    print(f"位置: {state['current_section']}")
    return {}


def check_speed(state: TrafficState) -> dict:
    """检查速度"""
    print(f"\n 速度检测: {state['speed']} km/h")
    
    # 长江大桥限速60km/h
    speed_limit = 60
    alert_level = 0
    
    if state['speed'] > speed_limit + 20:
        alert_level = 3  # 危险
        print(f"  严重超速! (限速{speed_limit}km/h)")
    elif state['speed'] > speed_limit + 10:
        alert_level = 2  # 警告
        print(f"  超速警告! (限速{speed_limit}km/h)")
    elif state['speed'] > speed_limit:
        alert_level = 1  # 注意
        print(f"  轻微超速 (限速{speed_limit}km/h)")
    else:
        print(f" 速度正常")
    
    return {"alert_level": alert_level}


def check_weather(state: TrafficState) -> dict:
    """检查天气状况"""
    print(f"\n  天气检测: {state['weather']}")
    
    # 恶劣天气提升警报级别
    if state['weather'] in ["大雾", "暴雨", "冰雪"]:
        current_level = state.get('alert_level', 0)
        new_level = min(current_level + 1, 3)
        print(f" 恶劣天气,警报级别提升至 {new_level}")
        return {"alert_level": new_level}
    
    return {}


def take_action(state: TrafficState) -> dict:
    """采取措施"""
    print(f"\n 警报级别: {state['alert_level']}")
    
    actions = {
        0: "正常通行",
        1: "发送提醒短信",
        2: "启动电子警示牌",
        3: "交警拦截检查"
    }
    
    action = actions.get(state['alert_level'], "正常通行")
    print(f" 采取措施: {action}")
    
    return {"action_taken": action}


def build_traffic_monitor_graph(interrupt_before=None, interrupt_after=None):
    """构建交通监控图
    
    Args:
        interrupt_before: 在哪些节点之前中断
        interrupt_after: 在哪些节点之后中断
    """
    builder = StateGraph(TrafficState)
    
    # 添加节点
    builder.add_node("detect", detect_vehicle)
    builder.add_node("check_speed", check_speed)
    builder.add_node("check_weather", check_weather)
    builder.add_node("action", take_action)
    
    # 添加边
    builder.add_edge(START, "detect")
    builder.add_edge("detect", "check_speed")
    builder.add_edge("check_speed", "check_weather")
    builder.add_edge("check_weather", "action")
    builder.add_edge("action", END)
    
    # 编译时指定中断点
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after
    )
    
    return graph


def demo_interrupt_before():
    """演示interrupt_before - 在节点执行前中断"""
    print("=" * 70)
    print("示例1: 编译时中断 - interrupt_before")
    print("=" * 70)
    print("场景: 在采取措施前暂停,让交警确认")
    
    # 在action节点之前中断
    graph = build_traffic_monitor_graph(interrupt_before=["action"])
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = {
        "vehicle_id": "鄂A88888",
        "vehicle_type": "小轿车",
        "current_section": "长江大桥主桥段",
        "speed": 85.0,  # 超速
        "weather": "晴天",
        "alert_level": 0,
        "action_taken": None
    }
    
    print("\n 开始监控...")
    # 第一次调用会在action节点前停止
    result = graph.invoke(state, config)
    
    print(f"\n  执行暂停在 action 节点之前")
    print(f"当前警报级别: {result['alert_level']}")
    print(f"下一步将执行: {result.get('__next__', 'N/A')}")
    
    # 交警确认后继续
    print("\n 交警确认,继续执行...")
    final_result = graph.invoke(None, config)  # 传入None继续执行
    print(f"\n 执行完成")
    print(f"采取的措施: {final_result['action_taken']}")


def demo_interrupt_after():
    """演示interrupt_after - 在节点执行后中断"""
    print("\n\n" + "=" * 70)
    print("示例2: 编译时中断 - interrupt_after")
    print("=" * 70)
    print("场景: 在速度检测后暂停,让交警查看数据")
    
    # 在check_speed节点之后中断
    graph = build_traffic_monitor_graph(interrupt_after=["check_speed"])
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = {
        "vehicle_id": "鄂A66666",
        "vehicle_type": "货车",
        "current_section": "长江大桥汉阳端",
        "speed": 75.0,
        "weather": "小雨",
        "alert_level": 0,
        "action_taken": None
    }
    
    print("\n 开始监控...")
    # 第一次调用会在check_speed节点后停止
    result = graph.invoke(state, config)
    
    print(f"\n  执行暂停在 check_speed 节点之后")
    print(f"检测到的警报级别: {result['alert_level']}")
    
    # 交警查看数据后继续
    print("\n 交警查看数据,继续执行...")
    final_result = graph.invoke(None, config)
    print(f"\n 执行完成")
    print(f"采取的措施: {final_result['action_taken']}")


def demo_multiple_interrupts():
    """演示多个中断点"""
    print("\n\n" + "=" * 70)
    print("示例3: 多个中断点")
    print("=" * 70)
    print("场景: 在多个关键节点暂停检查")
    
    # 在多个节点设置中断
    graph = build_traffic_monitor_graph(
        interrupt_before=["action"],
        interrupt_after=["check_speed", "check_weather"]
    )
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = {
        "vehicle_id": "鄂A12345",
        "vehicle_type": "客车",
        "current_section": "长江大桥武昌端",
        "speed": 90.0,  # 严重超速
        "weather": "大雾",  # 恶劣天气
        "alert_level": 0,
        "action_taken": None
    }
    
    print("\n 开始监控...")
    
    # 第一次中断: check_speed之后
    result = graph.invoke(state, config)
    print(f"\n  第1次暂停: check_speed 之后")
    print(f"警报级别: {result['alert_level']}")
    print("\n 继续...")
    
    # 第二次中断: check_weather之后
    result = graph.invoke(None, config)
    print(f"\n  第2次暂停: check_weather 之后")
    print(f"警报级别: {result['alert_level']}")
    print("\n 继续...")
    
    # 第三次中断: action之前
    result = graph.invoke(None, config)
    print(f"\n 第3次暂停: action 之前")
    print(f"即将采取措施")
    print("\n 确认,继续...")
    
    # 最终执行
    final_result = graph.invoke(None, config)
    print(f"\n 执行完成")
    print(f"采取的措施: {final_result['action_taken']}")


def demo_debugging():
    """演示使用中断进行调试"""
    print("\n\n" + "=" * 70)
    print("示例4: 使用中断进行调试")
    print("=" * 70)
    print("场景: 逐步执行,检查每个节点的输出")
    
    # 在每个节点后都中断
    graph = build_traffic_monitor_graph(
        interrupt_after=["detect", "check_speed", "check_weather", "action"]
    )
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = {
        "vehicle_id": "鄂A99999",
        "vehicle_type": "摩托车",
        "current_section": "长江大桥中段",
        "speed": 55.0,
        "weather": "晴天",
        "alert_level": 0,
        "action_taken": None
    }
    
    print("\n 开始调试模式...")
    
    nodes = ["detect", "check_speed", "check_weather", "action"]
    for i, node in enumerate(nodes, 1):
        if i == 1:
            result = graph.invoke(state, config)
        else:
            result = graph.invoke(None, config)
        
        print(f"\n 调试点 {i}: {node} 节点执行完毕")
        print(f"当前状态: alert_level={result.get('alert_level', 0)}")
        
        if i < len(nodes):
            input("按回车继续...")
    
    print(f"\n 调试完成")
    print(f"最终措施: {result['action_taken']}")


if __name__ == "__main__":
    demo_interrupt_before()
    demo_interrupt_after()
    demo_multiple_interrupts()
    
    print("\n\n" + "=" * 70)
    print("提示: 运行 demo_debugging() 可以体验交互式调试")
    print("=" * 70)
    
    print("\n 所有示例运行完成!")

