"""
7.2节 时间旅行(Time Travel)示例代码
场景:武汉地铁2号线智能调度系统

这个示例展示了如何使用LangGraph的时间旅行功能:
1. 访问历史状态
2. 从历史点恢复执行
3. 修改历史状态
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import uuid


class MetroState(TypedDict):
    """地铁状态"""
    train_id: str  # 列车编号
    current_station: str  # 当前站点
    next_station: Optional[str]  # 下一站
    passenger_count: int  # 乘客数量
    status: str  # 状态: running, stopped, maintenance
    stations_passed: list[str]  # 已经过的站点


# 武汉地铁2号线站点(部分)
METRO_LINE_2 = [
    "天河机场",
    "航空总部",
    "宋家岗",
    "巨龙大道",
    "盘龙城",
    "宏图大道",
    "金银潭",
    "常青花园",
    "长港路",
    "汉口火车站",
    "范湖",
    "王家墩东",
    "青年路",
    "中山公园",
    "循礼门",
    "江汉路",
    "积玉桥",
    "螃蟹岬",
    "小龟山",
    "洪山广场",
    "中南路",
    "宝通寺",
    "街道口",
    "广埠屯",
    "虎泉",
    "杨家湾",
    "光谷广场"
]


def move_to_next_station(state: MetroState) -> dict:
    """移动到下一站"""
    current = state["current_station"]
    
    # 找到当前站点的索引
    try:
        current_index = METRO_LINE_2.index(current)
    except ValueError:
        print(f"错误: 未知站点 {current}")
        return {"status": "error"}
    
    # 检查是否到达终点
    if current_index >= len(METRO_LINE_2) - 1:
        print(f"列车 {state['train_id']} 已到达终点站: {current}")
        return {
            "status": "stopped",
            "next_station": None
        }
    
    # 移动到下一站
    next_station = METRO_LINE_2[current_index + 1]
    stations_passed = state.get("stations_passed", []) + [current]
    
    print(f"列车 {state['train_id']}: {current} → {next_station}")
    print(f"   乘客数量: {state['passenger_count']}")
    
    return {
        "current_station": next_station,
        "next_station": METRO_LINE_2[current_index + 2] if current_index + 2 < len(METRO_LINE_2) else None,
        "stations_passed": stations_passed
    }


def update_passengers(state: MetroState) -> dict:
    """更新乘客数量(模拟上下车)"""
    import random
    
    # 模拟乘客上下车
    off = random.randint(10, 30)  # 下车人数
    on = random.randint(15, 40)  # 上车人数
    
    new_count = max(0, state["passenger_count"] - off + on)
    
    print(f"{state['current_station']}: 下车{off}人, 上车{on}人, 当前{new_count}人")
    
    return {"passenger_count": new_count}


def build_metro_graph():
    """构建地铁调度图"""
    builder = StateGraph(MetroState)
    
    # 添加节点
    builder.add_node("move", move_to_next_station)
    builder.add_node("update_passengers", update_passengers)
    
    # 添加边
    builder.add_edge(START, "move")
    builder.add_edge("move", "update_passengers")
    builder.add_edge("update_passengers", END)
    
    # 使用检查点器
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


# ============================================================================
# 示例1: 访问历史状态
# ============================================================================

def demo_access_history():
    """演示访问历史状态"""
    print("=" * 70)
    print("示例1: 访问历史状态")
    print("=" * 70)
    
    graph = build_metro_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 初始状态
    state = {
        "train_id": "2号线-001",
        "current_station": "天河机场",
        "next_station": "航空总部",
        "passenger_count": 50,
        "status": "running",
        "stations_passed": []
    }
    
    print("\n开始运行地铁...")
    
    # 运行5站
    for i in range(5):
        print(f"\n--- 第 {i+1} 站 ---")
        state = graph.invoke(state, config)
        
        if state["status"] == "stopped":
            break
    
    # 访问历史状态
    print("\n\n查看历史记录:")
    print("-" * 70)
    
    history = graph.get_state_history(config)
    
    for i, checkpoint in enumerate(history):
        state_values = checkpoint.values
        print(f"\n检查点 {i}:")
        print(f"  站点: {state_values.get('current_station', 'N/A')}")
        print(f"  乘客: {state_values.get('passenger_count', 0)}人")
        print(f"  已过站点: {len(state_values.get('stations_passed', []))}个")
        print(f"  checkpoint_id: {checkpoint.config['configurable']['checkpoint_id'][:8]}...")
        
        if i >= 9:  # 只显示前10个
            print("\n  ...")
            break


# ============================================================================
# 示例2: 从历史点恢复执行
# ============================================================================

def demo_resume_from_history():
    """演示从历史点恢复执行"""
    print("\n\n" + "=" * 70)
    print("示例2: 从历史点恢复执行")
    print("=" * 70)
    
    graph = build_metro_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 初始状态
    state = {
        "train_id": "2号线-002",
        "current_station": "汉口火车站",
        "next_station": "范湖",
        "passenger_count": 100,
        "status": "running",
        "stations_passed": []
    }
    
    print("\n 开始运行地铁...")
    
    # 运行3站
    for i in range(3):
        print(f"\n--- 第 {i+1} 站 ---")
        state = graph.invoke(state, config)
    
    print(f"\n当前位置: {state['current_station']}")
    
    # 获取历史记录
    history = list(graph.get_state_history(config))
    
    # 回到第2个检查点(第1站之后)
    if len(history) >= 3:
        checkpoint_to_resume = history[2]  # 索引2是第3个检查点
        resume_state = checkpoint_to_resume.values
        
        print(f"\n时间旅行: 回到 {resume_state['current_station']}")
        print(f"   (从检查点 {checkpoint_to_resume.config['configurable']['checkpoint_id'][:8]}... 恢复)")
        
        # 从该检查点继续执行
        resume_config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_to_resume.config["configurable"]["checkpoint_id"]
            }
        }
        
        print("\n 从历史点继续运行...")
        for i in range(2):
            print(f"\n--- 继续第 {i+1} 站 ---")
            state = graph.invoke(None, resume_config)
            resume_config = {"configurable": {"thread_id": thread_id}}  # 后续使用普通config
        
        print(f"\n最终位置: {state['current_station']}")


# ============================================================================
# 示例3: 修改历史状态
# ============================================================================

def demo_modify_history():
    """演示修改历史状态"""
    print("\n\n" + "=" * 70)
    print("示例3: 修改历史状态")
    print("=" * 70)
    print("场景: 发现数据错误,需要修正历史记录")
    
    graph = build_metro_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 初始状态
    state = {
        "train_id": "2号线-003",
        "current_station": "中山公园",
        "next_station": "循礼门",
        "passenger_count": 80,
        "status": "running",
        "stations_passed": []
    }
    
    print("\n 开始运行地铁...")
    
    # 运行2站
    for i in range(2):
        print(f"\n--- 第 {i+1} 站 ---")
        state = graph.invoke(state, config)
    
    print(f"\n当前状态:")
    print(f"  位置: {state['current_station']}")
    print(f"  乘客: {state['passenger_count']}人")
    
    # 获取历史记录
    history = list(graph.get_state_history(config))
    
    # 修改第一个检查点的乘客数量
    if len(history) >= 2:
        checkpoint_to_modify = history[1]
        
        print(f"\n 发现错误: 第一站的乘客数量记录有误")
        print(f"   原始值: {checkpoint_to_modify.values['passenger_count']}人")
        print(f"   修正为: 120人")
        
        # 更新状态
        graph.update_state(
            checkpoint_to_modify.config,
            {"passenger_count": 120}
        )
        
        # 查看修改后的历史
        print("\n 修改后的历史记录:")
        updated_history = list(graph.get_state_history(config))
        for i, checkpoint in enumerate(updated_history[:3]):
            state_values = checkpoint.values
            print(f"\n检查点 {i}:")
            print(f"  站点: {state_values.get('current_station', 'N/A')}")
            print(f"  乘客: {state_values.get('passenger_count', 0)}人")


if __name__ == "__main__":
    demo_access_history()
    demo_resume_from_history()
    demo_modify_history()
    
    print("\n\n 所有示例运行完成!")

