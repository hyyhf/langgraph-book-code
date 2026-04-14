"""
7.3节 子图 - 高级示例
场景:武汉大学智能选课系统

这个示例展示了:
1. 从节点内部调用子图
2. 独立State vs 共享State
3. 子图的持久化与检查点
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import operator


# ============================================================================
# 子图1: 课程推荐子图(独立State)
# ============================================================================

class CourseRecommendationState(TypedDict):
    """课程推荐状态(独立)"""
    student_major: str  # 学生专业
    completed_courses: list[str]  # 已完成课程
    recommended_courses: list[str]  # 推荐课程


def analyze_student_profile(state: CourseRecommendationState) -> dict:
    """分析学生档案"""
    print(f"\n分析学生档案")
    print(f"   专业: {state['student_major']}")
    print(f"   已完成: {len(state['completed_courses'])}门课程")
    return {}


def recommend_courses(state: CourseRecommendationState) -> dict:
    """推荐课程"""
    # 课程库
    course_catalog = {
        "计算机科学": ["数据结构", "算法设计", "操作系统", "计算机网络", "数据库系统"],
        "软件工程": ["软件设计", "软件测试", "项目管理", "敏捷开发", "DevOps"],
        "人工智能": ["机器学习", "深度学习", "自然语言处理", "计算机视觉", "强化学习"]
    }
    
    major = state['student_major']
    completed = set(state['completed_courses'])
    
    # 推荐该专业的课程,排除已完成的
    available = course_catalog.get(major, [])
    recommended = [c for c in available if c not in completed][:3]
    
    print(f"   推荐课程: {', '.join(recommended)}")
    
    return {"recommended_courses": recommended}


def build_recommendation_subgraph():
    """构建课程推荐子图"""
    builder = StateGraph(CourseRecommendationState)
    
    builder.add_node("analyze", analyze_student_profile)
    builder.add_node("recommend", recommend_courses)
    
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "recommend")
    builder.add_edge("recommend", END)
    
    return builder.compile()


# ============================================================================
# 子图2: 选课冲突检测子图(共享State)
# ============================================================================

class ConflictCheckState(TypedDict):
    """冲突检测状态"""
    selected_courses: list[str]  # 已选课程
    new_course: str  # 新课程
    conflicts: Annotated[list[str], operator.add]  # 冲突列表
    can_select: bool  # 是否可以选择


def check_time_conflict(state: ConflictCheckState) -> dict:
    """检查时间冲突"""
    print(f"\n检查时间冲突")
    print(f"   新课程: {state['new_course']}")
    
    # 模拟课程时间表
    course_schedule = {
        "数据结构": "周一 8:00-10:00",
        "算法设计": "周一 8:00-10:00",  # 与数据结构冲突
        "操作系统": "周二 14:00-16:00",
        "计算机网络": "周三 10:00-12:00",
        "数据库系统": "周四 8:00-10:00",
        "机器学习": "周一 14:00-16:00",
        "深度学习": "周二 14:00-16:00",  # 与操作系统冲突
        "软件设计": "周五 10:00-12:00"
    }
    
    new_time = course_schedule.get(state['new_course'], "")
    conflicts = []
    
    for course in state.get('selected_courses', []):
        if course_schedule.get(course, "") == new_time and new_time:
            conflicts.append(f"时间冲突: {course} 与 {state['new_course']} 都在 {new_time}")
    
    if conflicts:
        print(f"发现 {len(conflicts)} 个冲突")
    else:
        print(f"无时间冲突")
    
    return {"conflicts": conflicts}


def check_prerequisite(state: ConflictCheckState) -> dict:
    """检查先修课程"""
    print(f"\n检查先修课程")
    
    # 先修课程要求
    prerequisites = {
        "算法设计": ["数据结构"],
        "操作系统": ["数据结构"],
        "数据库系统": ["数据结构"],
        "深度学习": ["机器学习"],
        "计算机视觉": ["机器学习"]
    }
    
    required = prerequisites.get(state['new_course'], [])
    selected = set(state.get('selected_courses', []))
    
    conflicts = []
    for req in required:
        if req not in selected:
            conflicts.append(f"先修课程缺失: {state['new_course']} 需要先完成 {req}")
    
    if conflicts:
        print(f"缺少先修课程")
    else:
        print(f"先修课程满足")
    
    return {"conflicts": conflicts}


def make_decision(state: ConflictCheckState) -> dict:
    """做出决策"""
    conflicts = state.get('conflicts', [])
    can_select = len(conflicts) == 0
    
    if can_select:
        print(f"可以选择 {state['new_course']}")
    else:
        print(f"不能选择 {state['new_course']}")
        for conflict in conflicts:
            print(f"      • {conflict}")
    
    return {"can_select": can_select}


def build_conflict_check_subgraph():
    """构建冲突检测子图"""
    builder = StateGraph(ConflictCheckState)
    
    builder.add_node("check_time", check_time_conflict)
    builder.add_node("check_prereq", check_prerequisite)
    builder.add_node("decide", make_decision)
    
    builder.add_edge(START, "check_time")
    builder.add_edge("check_time", "check_prereq")
    builder.add_edge("check_prereq", "decide")
    builder.add_edge("decide", END)
    
    return builder.compile()


# ============================================================================
# 主系统: 选课系统
# ============================================================================

class CourseSelectionState(TypedDict):
    """选课系统状态"""
    student_id: str
    student_name: str
    student_major: str
    completed_courses: list[str]
    selected_courses: list[str]
    recommended_courses: list[str]
    new_course: str
    conflicts: Annotated[list[str], operator.add]
    can_select: bool
    final_courses: list[str]


def get_recommendations_node(state: CourseSelectionState) -> dict:
    """获取推荐(调用推荐子图)"""
    print(f"\n 为学生 {state['student_name']} 获取课程推荐...")
    
    # 创建推荐子图
    recommendation_graph = build_recommendation_subgraph()
    
    # 准备子图的输入状态(独立State)
    sub_state = {
        "student_major": state['student_major'],
        "completed_courses": state['completed_courses'],
        "recommended_courses": []
    }
    
    # 调用子图
    result = recommendation_graph.invoke(sub_state)
    
    # 将子图的结果合并到主状态
    return {"recommended_courses": result['recommended_courses']}


def select_course_node(state: CourseSelectionState) -> dict:
    """选择课程(调用冲突检测子图)"""
    print(f"\n尝试选择课程: {state['new_course']}")
    
    # 创建冲突检测子图
    conflict_graph = build_conflict_check_subgraph()
    
    # 准备子图的输入状态(共享部分State)
    sub_state = {
        "selected_courses": state['selected_courses'],
        "new_course": state['new_course'],
        "conflicts": [],
        "can_select": False
    }
    
    # 调用子图
    result = conflict_graph.invoke(sub_state)
    
    # 合并结果
    return {
        "conflicts": result['conflicts'],
        "can_select": result['can_select']
    }


def finalize_selection(state: CourseSelectionState) -> dict:
    """完成选课"""
    print(f"\n完成选课")
    
    final_courses = state['selected_courses'].copy()
    
    if state.get('can_select', False):
        final_courses.append(state['new_course'])
        print(f"   成功添加: {state['new_course']}")
    
    print(f"   最终课程列表: {', '.join(final_courses)}")
    
    return {"final_courses": final_courses}


def build_course_selection_graph():
    """构建选课系统主图"""
    builder = StateGraph(CourseSelectionState)
    
    builder.add_node("get_recommendations", get_recommendations_node)
    builder.add_node("select_course", select_course_node)
    builder.add_node("finalize", finalize_selection)
    
    builder.add_edge(START, "get_recommendations")
    builder.add_edge("get_recommendations", "select_course")
    builder.add_edge("select_course", "finalize")
    builder.add_edge("finalize", END)
    
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# 示例演示
# ============================================================================

def demo_calling_subgraph_from_node():
    """演示从节点调用子图"""
    print("=" * 70)
    print("示例1: 从节点调用子图 - 成功选课")
    print("=" * 70)
    
    graph = build_course_selection_graph()
    
    config = {"configurable": {"thread_id": "student-001"}}
    state = {
        "student_id": "2021301001",
        "student_name": "张三",
        "student_major": "计算机科学",
        "completed_courses": ["数据结构"],
        "selected_courses": ["数据结构", "机器学习"],
        "recommended_courses": [],
        "new_course": "算法设计",
        "conflicts": [],
        "can_select": False,
        "final_courses": []
    }
    
    result = graph.invoke(state, config)
    
    print("\n" + "=" * 70)


def demo_conflict_detection():
    """演示冲突检测"""
    print("\n\n" + "=" * 70)
    print("示例2: 从节点调用子图 - 检测到冲突")
    print("=" * 70)
    
    graph = build_course_selection_graph()
    
    config = {"configurable": {"thread_id": "student-002"}}
    state = {
        "student_id": "2021301002",
        "student_name": "李四",
        "student_major": "人工智能",
        "completed_courses": [],
        "selected_courses": ["操作系统"],
        "recommended_courses": [],
        "new_course": "深度学习",  # 需要先修机器学习,且时间冲突
        "conflicts": [],
        "can_select": False,
        "final_courses": []
    }
    
    result = graph.invoke(state, config)
    
    print("\n" + "=" * 70)


def demo_persistence():
    """演示子图的持久化"""
    print("\n\n" + "=" * 70)
    print("示例3: 子图的持久化")
    print("=" * 70)
    
    graph = build_course_selection_graph()
    
    thread_id = "student-003"
    config = {"configurable": {"thread_id": thread_id}}
    
    # 第一次选课
    print("\n第一次选课:")
    state1 = {
        "student_id": "2021301003",
        "student_name": "王五",
        "student_major": "软件工程",
        "completed_courses": [],
        "selected_courses": [],
        "recommended_courses": [],
        "new_course": "软件设计",
        "conflicts": [],
        "can_select": False,
        "final_courses": []
    }
    
    result1 = graph.invoke(state1, config)
    
    # 第二次选课(使用同一个thread_id,状态会累积)
    print("\n\n第二次选课:")
    state2 = {
        "student_id": "2021301003",
        "student_name": "王五",
        "student_major": "软件工程",
        "completed_courses": [],
        "selected_courses": result1['final_courses'],  # 使用上次的结果
        "recommended_courses": [],
        "new_course": "软件测试",
        "conflicts": [],
        "can_select": False,
        "final_courses": []
    }
    
    result2 = graph.invoke(state2, config)
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_calling_subgraph_from_node()
    demo_conflict_detection()
    demo_persistence()
    
    print("\n\n 所有示例运行完成!")

