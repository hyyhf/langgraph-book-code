"""
第9章示例3: Supervisor架构 - 中央协调的管理模式
场景: 武汉大学生活助手 - 学习、生活、娱乐三个专业智能体由Supervisor协调
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 定义专业工具
# ============================================================================

# 学习相关工具
@tool
def search_library_info():
    """查询武汉大学图书馆信息"""
    return """武汉大学图书馆:
- 总馆位于珞珈山,藏书700万册
- 开放时间: 周一至周日 7:00-22:30
- 需要校园卡进入
- 提供自习室、研讨室预约服务"""


@tool
def search_course_info(course_name: str):
    """查询课程信息"""
    courses = {
        "高等数学": "周一、周三 8:00-9:40, 教学楼A101, 张教授",
        "大学英语": "周二、周四 10:00-11:40, 教学楼B203, 李老师",
        "计算机基础": "周五 14:00-16:40, 信息学部机房, 王老师"
    }
    return courses.get(course_name, "未找到该课程信息")


@tool
def book_study_room(room_type: str, date: str, time: str):
    """预约自习室或研讨室"""
    return f"已预约{room_type},日期{date},时间{time},请凭校园卡使用"


# 生活相关工具
@tool
def search_canteen_info(canteen_name: str = ""):
    """查询食堂信息"""
    canteens = {
        "桂园": "位于桂园宿舍区,早餐6:30-9:00,午餐11:00-13:00,晚餐17:00-19:00",
        "枫园": "位于枫园宿舍区,提供清真餐,营业时间同桂园",
        "梅园": "位于梅园宿舍区,有特色小吃窗口,营业时间同桂园"
    }
    if canteen_name:
        return canteens.get(canteen_name, "未找到该食堂")
    return "武大主要食堂: " + ", ".join(canteens.keys())


@tool
def search_dormitory_info():
    """查询宿舍信息"""
    return """武汉大学宿舍:
- 本科生宿舍: 4人间,有空调、热水器
- 宿舍区: 桂园、枫园、梅园、樱园等
- 门禁时间: 23:00(周日至周四), 23:30(周五周六)
- 可在宿舍楼下刷卡进入"""


@tool
def report_facility_issue(location: str, issue: str):
    """报修宿舍设施"""
    return f"已提交报修: {location} - {issue},维修人员将在24小时内处理"


# 娱乐相关工具
@tool
def search_campus_activities():
    """查询校园活动"""
    return """近期校园活动:
1. 樱花节 - 3月中旬至4月初,赏樱花、文艺演出
2. 社团招新 - 每学期开学第一周
3. 运动会 - 每年10月
4. 元旦晚会 - 12月底
详情请关注武大青年公众号"""


@tool
def search_sports_facilities():
    """查询体育设施"""
    return """武汉大学体育设施:
- 体育馆: 篮球场、羽毛球场、游泳馆
- 田径场: 400米标准跑道,免费开放
- 网球场: 需预约,10元/小时
- 开放时间: 6:00-22:00"""


@tool
def book_sports_venue(venue: str, date: str, time: str):
    """预约体育场馆"""
    return f"已预约{venue},日期{date},时间{time},费用10元"


# ============================================================================
# 创建专业智能体
# ============================================================================

def create_study_agent():
    """创建学习助手智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_library_info, search_course_info, book_study_room],
        system_prompt="""你是武汉大学学习助手。
你的职责:
1. 提供图书馆信息和服务
2. 查询课程安排
3. 预约自习室和研讨室
4. 解答学习相关问题

只处理学习相关的问题,其他问题应该由Supervisor分配给其他专家。""",
        name="study_agent"
    )


def create_life_agent():
    """创建生活助手智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_canteen_info, search_dormitory_info, report_facility_issue],
        system_prompt="""你是武汉大学生活助手。
你的职责:
1. 提供食堂信息和推荐
2. 解答宿舍相关问题
3. 处理设施报修
4. 提供生活服务信息

只处理生活相关的问题,其他问题应该由Supervisor分配给其他专家。""",
        name="life_agent"
    )


def create_entertainment_agent():
    """创建娱乐助手智能体"""
    return create_agent(
        model=get_llm(),
        tools=[search_campus_activities, search_sports_facilities, book_sports_venue],
        system_prompt="""你是武汉大学娱乐助手。
你的职责:
1. 介绍校园活动
2. 提供体育设施信息
3. 预约体育场馆
4. 推荐娱乐活动

只处理娱乐相关的问题,其他问题应该由Supervisor分配给其他专家。""",
        name="entertainment_agent"
    )


# ============================================================================
# 创建Supervisor智能体
# ============================================================================

class SupervisorState(MessagesState):
    """Supervisor状态定义"""
    next: str  # 下一个要执行的智能体


class Router(TypedDict):
    """路由决策"""
    next: Literal["study_agent", "life_agent", "entertainment_agent", "FINISH"]


def create_supervisor_agent():
    """创建Supervisor智能体 - 负责任务分配和协调"""

    def supervisor_node(state: SupervisorState) -> Command[Literal["study_agent", "life_agent", "entertainment_agent", "__end__"]]:
        """Supervisor节点 - 分析任务并分配给合适的专业智能体"""

        # 获取最后一条消息
        messages = state["messages"]
        last_message = messages[-1]

        # 如果最后一条消息是AI消息(说明智能体已经处理完),直接结束
        if hasattr(last_message, 'type') and last_message.type == 'ai':
            return Command(goto=END)

        # 构建Supervisor的提示词
        system_prompt = """你是武汉大学生活助手的协调者。

你管理三个专业助手:
1. study_agent - 学习助手: 处理图书馆、课程、自习室等学习相关问题
2. life_agent - 生活助手: 处理食堂、宿舍、报修等生活相关问题
3. entertainment_agent - 娱乐助手: 处理校园活动、体育设施等娱乐相关问题

根据用户的问题,选择最合适的助手来处理。

只返回助手名称(study_agent/life_agent/entertainment_agent),不要其他内容。"""

        # 调用LLM做决策
        llm = get_llm()
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = llm.invoke(full_messages)

        # 解析响应
        next_agent = response.content.strip().lower()

        # 路由决策
        if "study" in next_agent or "学习" in next_agent:
            goto = "study_agent"
        elif "life" in next_agent or "生活" in next_agent:
            goto = "life_agent"
        elif "entertainment" in next_agent or "娱乐" in next_agent:
            goto = "entertainment_agent"
        else:
            # 默认选择study_agent
            goto = "study_agent"

        return Command(goto=goto, update={"next": goto})

    return supervisor_node


# ============================================================================
# 构建Supervisor架构图
# ============================================================================

def create_supervisor_graph():
    """创建Supervisor架构的多智能体图"""

    # 创建专业智能体
    study_agent = create_study_agent()
    life_agent = create_life_agent()
    entertainment_agent = create_entertainment_agent()

    # 创建Supervisor
    supervisor = create_supervisor_agent()

    # 构建图
    graph = StateGraph(SupervisorState)

    # 添加节点
    graph.add_node("supervisor", supervisor)
    graph.add_node("study_agent", study_agent)
    graph.add_node("life_agent", life_agent)
    graph.add_node("entertainment_agent", entertainment_agent)

    # 设置流程: START -> supervisor -> 专业智能体 -> END
    # 智能体处理完后直接结束,不再回到supervisor
    graph.add_edge(START, "supervisor")
    graph.add_edge("study_agent", END)
    graph.add_edge("life_agent", END)
    graph.add_edge("entertainment_agent", END)

    return graph.compile()


# ============================================================================
# 测试函数
# ============================================================================

def test_supervisor_architecture():
    """测试Supervisor架构"""
    
    print("=" * 80)
    print("第9章示例3: Supervisor架构 - 武汉大学生活助手")
    print("=" * 80)
    print("\n特点: Supervisor协调三个专业智能体(学习、生活、娱乐)\n")
    
    graph = create_supervisor_graph()
    
    # 测试用例1: 学习相关
    print("\n测试1: 学习相关查询")
    print("-" * 80)
    query1 = "图书馆几点开门?我想预约一个自习室"
    print(f"用户: {query1}\n")

    print("开始调用图...")
    result1 = graph.invoke(
        {"messages": [HumanMessage(content=query1)]},
        config={"recursion_limit": 50}  # 增加递归限制
    )
    print("图调用完成")

    print(f"系统: {result1['messages'][-1].content}\n")
    
    # 测试用例2: 生活相关
    print("\n测试2: 生活相关查询")
    print("-" * 80)
    query2 = "桂园食堂几点开饭?宿舍门禁是几点?"
    print(f"用户: {query2}\n")
    
    result2 = graph.invoke({
        "messages": [HumanMessage(content=query2)]
    })
    
    print(f"系统: {result2['messages'][-1].content}\n")
    
    # 测试用例3: 娱乐相关
    print("\n测试3: 娱乐相关查询")
    print("-" * 80)
    query3 = "最近有什么校园活动?体育馆可以打羽毛球吗?"
    print(f"用户: {query3}\n")
    
    result3 = graph.invoke({
        "messages": [HumanMessage(content=query3)]
    })
    
    print(f"系统: {result3['messages'][-1].content}\n")
    
    print("\n" + "=" * 80)
    print("Supervisor架构优势:")
    print("1. 清晰的责任划分 - Supervisor协调,专业智能体执行")
    print("2. 较好的可控性 - 执行流程由Supervisor控制")
    print("3. 易于扩展 - 添加新智能体只需让Supervisor了解其能力")
    print("=" * 80)


if __name__ == "__main__":
    test_supervisor_architecture()

