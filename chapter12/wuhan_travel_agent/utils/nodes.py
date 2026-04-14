"""
节点函数模块
定义旅行规划助手的各个节点
"""

import os
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from .state import TravelPlanState
from .tools import tools


# 初始化LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "deepseek-chat"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    max_tokens=8000,
    temperature=0.7,
    streaming=True
)

# 绑定工具到LLM
llm_with_tools = llm.bind_tools(tools)


def planner_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    规划助手节点

    负责理解用户需求,调用工具收集信息,生成旅行计划
    """
    messages = state["messages"]
    current_stage = state.get("current_stage", "init")

    # 如果是第一次调用,添加系统提示
    if len(messages) == 1 or not any(isinstance(msg, SystemMessage) for msg in messages):
        system_prompt = """你是一个专业的武汉旅行规划助手。你的任务是:

1. 理解用户的旅行需求(目的地、天数、兴趣等)
2. 使用工具收集必要的信息:
   - 使用get_weather查询天气
   - 使用search_poi搜索景点、美食、酒店等
   - 使用plan_route规划路线
3. 基于收集的信息,生成详细的旅行计划

**重要规则: 路线规划必须逐一连接**

在规划路线时,你必须:
1. 确定每天要游览的所有景点/地点(按游览顺序排列)
2. 使用plan_route工具规划**每两个相邻地点之间**的路线
3. 例如: 如果一天要去A→B→C→D四个地点,你必须调用plan_route规划:
   - A到B的路线
   - B到C的路线
   - C到D的路线
4. plan_route工具会自动选择最优交通方式(步行/公交/驾车),你只需提供起点和终点
5. 在最终计划中,必须包含每段路线的详细信息(交通方式、距离、时间、费用)

**重要规则: 透明化思考过程**

在每次回复时,你必须遵循以下格式:

1. **首先输出思考过程** (必须包含):
   - 当前状态分析: 我现在处于什么阶段?
   - 已有信息: 我已经收集了哪些信息?
   - 缺失信息: 我还需要什么信息?
   - 下一步计划: 我接下来要做什么?为什么?

2. **然后执行行动**:
   - 如果需要收集信息,说明要调用什么工具、为什么调用
   - 如果已有足够信息,开始生成旅行计划

3. **收到工具结果后**:
   - 先分析工具返回的信息
   - 说明这些信息如何帮助规划
   - 判断是否需要更多信息

**示例格式**:

```
【思考过程】
- 当前状态: 用户刚提出需求,我需要开始收集信息
- 已有信息: 用户想在武汉玩2天,喜欢文化和美食
- 缺失信息: 天气情况、具体景点信息、路线规划
- 下一步计划: 先查询天气,了解适合的出行时间;然后搜索文化景点和美食地点

【执行行动】
现在我来查询武汉的天气情况...
[调用工具: get_weather]
```

**路线规划示例**:

```
【思考过程】
- 当前状态: 已确定第一天的行程: 黄鹤楼→户部巷→武汉长江大桥
- 已有信息: 三个景点的位置信息
- 缺失信息: 各景点之间的交通路线
- 下一步计划: 依次规划黄鹤楼→户部巷、户部巷→武汉长江大桥的路线

【执行行动】
现在我来规划第一天的交通路线,需要规划两段:
1. 黄鹤楼到户部巷
2. 户部巷到武汉长江大桥
[调用工具: plan_route(黄鹤楼, 户部巷)]
[调用工具: plan_route(户部巷, 武汉长江大桥)]
```

**禁止**:
- 禁止直接调用工具而不说明原因
- 禁止跳过思考过程
- 禁止使用过于简短的回复
- 禁止只规划起点到终点的路线,必须规划所有相邻地点之间的路线

生成的计划应该包括:
- 每天的详细行程安排
- 推荐的景点和美食(包含地址、评分等)
- 每两个相邻地点之间的交通路线(交通方式、距离、时间、费用)
- 温馨提示和注意事项

请用中文回复,语言要生动有趣,让用户感受到你的专业性和用心。"""

        messages = [SystemMessage(content=system_prompt)] + messages

    # 调用LLM
    response = llm_with_tools.invoke(messages)

    # 更新状态
    updates = {"messages": [response]}

    # 检查是否生成了完整的旅行计划
    # 1. 如果没有工具调用
    # 2. 且当前阶段是collect_info(首次生成)或replan(重新规划)
    if not response.tool_calls:
        if current_stage == "collect_info" or current_stage == "replan":
            # 生成了计划,准备进入审核
            updates["travel_plan"] = response.content
            updates["current_stage"] = "plan_ready"
        elif current_stage == "init":
            # 刚开始,进入信息收集阶段
            updates["current_stage"] = "collect_info"

    return updates


# 创建工具节点
tool_node = ToolNode(tools)


def human_review_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    人工审核节点
    
    使用interrupt暂停执行,等待用户反馈
    """
    travel_plan = state.get("travel_plan", "")
    
    # 使用interrupt暂停执行,等待用户输入
    user_feedback = interrupt(
        {
            "type": "plan_review",
            "plan": travel_plan,
            "message": "请审核以下旅行计划,您可以:\n1. 输入'确认'接受计划\n2. 输入具体的修改建议"
        }
    )
    
    # 处理用户反馈
    if isinstance(user_feedback, str):
        feedback_lower = user_feedback.lower().strip()
        
        if feedback_lower in ["确认", "ok", "好的", "可以", "没问题"]:
            # 用户确认计划
            return {
                "user_feedback": user_feedback,
                "final_plan": travel_plan,
                "need_replan": False,
                "current_stage": "generate_html",
                "messages": [HumanMessage(content=f"用户反馈: {user_feedback}")]
            }
        else:
            # 用户要求修改
            return {
                "user_feedback": user_feedback,
                "need_replan": True,
                "current_stage": "replan",  # 设置为replan阶段
                "messages": [HumanMessage(content=f"用户反馈: {user_feedback}\n\n请根据反馈修改旅行计划。")]
            }
    
    # 默认情况
    return {
        "user_feedback": str(user_feedback),
        "need_replan": False,
        "current_stage": "generate_html"
    }


def html_generator_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    HTML生成节点
    
    将最终的旅行计划生成为精美的HTML文档
    """
    final_plan = state.get("final_plan", state.get("travel_plan", ""))
    destination = state.get("destination", "武汉")
    
    # 生成HTML提示
    html_prompt = f"""请将以下旅行计划转换为一个精美的HTML文档。

旅行计划:
{final_plan}

要求:
1. 使用现代化的CSS样式,包括渐变背景、卡片布局、阴影效果
2. 响应式设计,适配移动端
3. 包含标题、日期、行程安排、景点介绍等板块
4. 使用合适的颜色搭配(可以使用武汉的代表色,如黄鹤楼的黄色)
5. 添加一些图标或装饰元素
6. 确保HTML是完整的,可以直接在浏览器中打开

请直接输出完整的HTML代码,不要有任何其他说明文字。"""
    
    # 调用LLM生成HTML
    response = llm.invoke([HumanMessage(content=html_prompt)])
    html_content = response.content
    
    # 提取HTML代码(如果LLM用```html包裹了代码)
    if "```html" in html_content:
        html_content = html_content.split("```html")[1].split("```")[0].strip()
    elif "```" in html_content:
        html_content = html_content.split("```")[1].split("```")[0].strip()
    
    # 保存HTML文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 使用相对于当前文件的路径
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(current_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    html_filename = f"travel_plan_{destination}_{timestamp}.html"
    html_path = os.path.join(output_dir, html_filename)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return {
        "html_path": html_path,
        "current_stage": "complete",
        "messages": [AIMessage(content=f"已生成旅行计划HTML文档: {html_path}")]
    }


def should_continue_planning(state: TravelPlanState) -> str:
    """
    条件边: 判断规划助手的下一步行动
    优先级:
    1) 若有工具调用 -> tools
    2) 若已有可供审核的计划(travel_plan不为空) -> review
    3) 否则 -> 继续planner
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 1) 有工具调用: 继续到tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # 2) 若已有计划文本,进入审核
    travel_plan = state.get("travel_plan", "")
    if isinstance(travel_plan, str) and travel_plan.strip():
        return "review"

    # 3) 默认继续规划
    return "continue"


def should_continue_after_review(state: TravelPlanState) -> str:
    """
    条件边: 根据用户反馈决定下一步
    """
    if state.get("need_replan", False):
        # 需要重新规划
        return "replan"
    else:
        # 生成HTML
        return "generate_html"

