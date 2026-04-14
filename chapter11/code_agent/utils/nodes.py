"""
节点模块
定义智能体的各个节点函数
"""
import os
import json
import re
import threading
from typing import Union
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

from .state import PlanExecuteState
from .tools import tools


# 使用线程本地存储来跟踪打印状态
_print_tracker = threading.local()


def _should_print(key: str) -> bool:
    """检查是否应该打印（避免重复）"""
    if not hasattr(_print_tracker, 'printed'):
        _print_tracker.printed = set()

    if key in _print_tracker.printed:
        return False

    _print_tracker.printed.add(key)
    return True


def _reset_print_tracker():
    """重置打印跟踪器（用于新的任务）"""
    if hasattr(_print_tracker, 'printed'):
        _print_tracker.printed.clear()


# 加载环境变量
load_dotenv()


# 定义计划模型
class Plan(BaseModel):
    """执行计划"""
    steps: list[str] = Field(
        description="需要执行的步骤列表，按顺序排列"
    )


# 定义响应模型
class Response(BaseModel):
    """最终响应"""
    response: str = Field(description="给用户的最终回复")


# 定义行动模型
class Act(BaseModel):
    """下一步行动"""
    action: Union[Response, Plan] = Field(
        description="下一步行动。如果可以回复用户，使用Response；如果需要继续执行，使用Plan"
    )


# 创建LLM实例（使用DeepSeek）
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "deepseek-chat"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
    temperature=0
)


# 创建规划器
planner_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """你是一个智能编程助手的规划者。你需要分析任务的复杂度，并制定合理的执行计划。

**任务复杂度分析标准：**

请仔细分析任务，判断是否满足以下**复杂任务特征**（满足任一条即为复杂任务）：

1. **需要创建3个或更多独立的程序文件**
   - 例如：数据文件 + 分析程序 + 可视化程序 + 测试程序
   - 注意：HTML+CSS+JS算作一个整体，不算多个独立程序

2. **需要构建数据处理流水线**
   - 例如：数据生成 → 数据清洗 → 数据分析 → 可视化 → 报告生成
   - 每个阶段都需要独立的程序或脚本

3. **需要迭代式开发流程**
   - 例如：创建程序 → 运行测试 → 发现问题 → 修复代码 → 重新测试
   - 需要根据前一步的结果来决定后续操作

4. **包含多个相互依赖的子系统**
   - 例如：推荐系统 = 数据层 + 分析层 + 推荐引擎 + 可视化层
   - 每个子系统需要单独实现和测试

5. **任务描述中明确提到多个阶段或步骤**
   - 即使没有"第一步、第二步"的标记，但内容暗示需要分阶段完成
   - 例如："创建数据，然后分析，最后生成报告"

**简单任务特征**（需要同时满足以下所有条件）：
- 只需要创建1-2个文件（或HTML+CSS+JS这种配套文件）
- 不需要多个程序之间的协作
- 可以一次性完成，不需要根据中间结果调整
- 没有明显的阶段划分

**规划示例：**

示例1（简单任务）：
任务："创建一个贪吃蛇游戏，包含HTML、CSS、JavaScript文件"
分析：虽然有3个文件，但它们是配套的前端文件，属于一个整体
规划：1个步骤 - "创建完整的贪吃蛇游戏（HTML+CSS+JS）"

示例2（复杂任务）：
任务："创建一个美食推荐系统，包含数据文件、分析程序、推荐引擎、可视化程序，并测试验证"
分析：需要创建4个独立程序，每个程序有不同功能，需要按顺序执行和测试
规划：5个步骤
  1. 创建美食数据JSON文件
  2. 编写数据分析程序
  3. 编写推荐引擎程序
  4. 编写可视化程序
  5. 运行测试并生成报告

示例3（复杂任务）：
任务："构建天气数据分析流水线，包括数据生成、清洗、分析、可视化、报告"
分析：明确的数据处理流水线，每个阶段需要独立程序
规划：5个步骤
  1. 创建数据生成程序
  2. 创建数据清洗程序
  3. 创建数据分析程序
  4. 创建可视化程序
  5. 创建报告生成程序并运行完整流水线

示例4（简单任务）：
任务："编写一个程序分析东湖旅游数据并生成图表"
分析：虽然包含分析和可视化，但可以在一个程序中完成
规划：1个步骤 - "创建数据分析程序，包含统计分析和图表生成功能，并运行展示结果"

**规划原则：**
1. 仔细阅读任务描述，识别独立的子任务和依赖关系
2. 如果多个操作可以在一个程序中完成，就不要拆分
3. 如果需要多个独立的程序文件，每个程序一个步骤
4. 测试验证通常作为最后一个独立步骤
5. 每个步骤应该清晰、具体、可执行

你可以使用以下工具：
- read_file: 读取文件内容
- write_file: 写入文件内容
- list_files: 列出目录文件
- execute_command: 执行终端命令

请用中文制定计划，并按照以下JSON格式输出：
{{"steps": ["步骤1", "步骤2", ...]}}

只输出JSON，不要有其他内容。"""
    ),
    ("placeholder", "{messages}"),
])

planner = planner_prompt | llm


# 创建执行器（ReAct agent）
executor_prompt = """你是一个智能编程助手的执行者。

你需要完成给定的任务。你可以使用多个工具来一次性完成整个任务。

**重要原则：**
1. **一次性完成**：如果任务包含多个子步骤（如创建文件、运行脚本、展示结果），你应该连续使用工具一次性完成所有步骤
2. **不要等待**：不要说"请执行下一步"，而是直接完成所有工作
3. **完整执行**：确保任务的所有要求都被满足

**示例**：
任务："创建一个计算器程序并运行"
正确做法：
1. 使用write_file创建程序
2. 使用execute_command运行程序
3. 报告结果
错误做法：只创建文件，然后说"请运行程序"

可用工具：
- read_file: 读取文件内容
- write_file: 写入文件内容
- list_files: 列出目录文件
- execute_command: 执行终端命令

注意：
1. 写Python代码时，确保代码正确、完整
2. 代码中不要包含emoji符号
3. 执行Python脚本使用: uv run python 文件名.py
4. 所有文件操作都在workspace目录下进行
5. 一次性完成所有子任务，不要分步等待

请用中文回复。"""

executor = create_agent(llm, tools, system_prompt=executor_prompt)


# 创建重新规划器
replanner_prompt = ChatPromptTemplate.from_template(
    """你是一个智能编程助手的重新规划者。

原始任务：
{input}

原始计划：
{plan}

已完成的步骤：
{past_steps}

请根据已完成的步骤更新计划。
如果任务已完成，可以直接回复用户，输出JSON格式：
{{"action_type": "response", "content": "给用户的回复"}}

如果还需要继续执行，更新计划，输出JSON格式：
{{"action_type": "plan", "steps": ["步骤1", "步骤2"]}}

只输出JSON，不要有其他内容。"""
)

replanner = replanner_prompt | llm


# 辅助函数：从LLM响应中提取JSON
def extract_json(text: str) -> dict:
    """从文本中提取JSON"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except:
        # 尝试提取JSON代码块
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # 尝试提取花括号内容
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        raise ValueError(f"无法从响应中提取JSON: {text}")


# 节点函数
async def plan_step(state: PlanExecuteState) -> dict:
    """规划步骤

    根据用户输入生成执行计划
    """
    # 使用唯一key来跟踪打印
    task_key = f"plan_{state['input'][:50]}"

    if _should_print(f"{task_key}_start"):
        print("\n[规划者] 正在分析任务并制定计划...", flush=True)

    response = await planner.ainvoke({"messages": [("user", state["input"])]})

    # 解析响应
    plan_data = extract_json(response.content)
    steps = plan_data.get("steps", [])

    # 只在第一次调用时打印
    if _should_print(f"{task_key}_result"):
        print(f"\n[规划者] 已生成计划，共 {len(steps)} 个步骤：", flush=True)
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}", flush=True)

    return {"plan": steps}


async def execute_step(state: PlanExecuteState) -> dict:
    """执行步骤

    执行计划中的当前步骤
    """
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    task = plan[0]

    # 使用唯一key来跟踪打印
    task_key = f"execute_{task[:50]}"

    if _should_print(f"{task_key}_start"):
        past_steps = state.get("past_steps", [])
        print(f"\n[执行者] 正在执行步骤 {len(past_steps) + 1}: {task}", flush=True)

    task_formatted = f"""完整计划：
{plan_str}

你现在需要执行第 1 步：{task}"""

    # 执行任务（使用astream来捕获工具调用过程）
    tool_call_count = 0
    seen_tool_calls = set()
    result = ""

    async for event in executor.astream(
        {"messages": [("user", task_formatted)]},
        {"recursion_limit": 25}
    ):
        # 检查是否有工具调用
        if "model" in event:
            messages = event["model"].get("messages", [])
            for msg in messages:
                # 检查是否是AI消息且包含工具调用
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        # 使用工具调用ID来避免重复
                        tool_id = tool_call.get("id", "")
                        if tool_id and tool_id not in seen_tool_calls:
                            seen_tool_calls.add(tool_id)
                            tool_call_count += 1
                            tool_name = tool_call.get("name", "未知工具")
                            print(f"  → 工具调用 #{tool_call_count}: {tool_name}", flush=True)

        # 检查是否有工具执行结果
        if "tools" in event:
            messages = event["tools"].get("messages", [])
            for msg in messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    # 截断过长的内容
                    if len(content) > 500:
                        content = content[:500] + "..."
                    print(f"  ← 工具返回: {content}", flush=True)

        # 保存最终的AI消息
        if "model" in event:
            messages = event["model"].get("messages", [])
            if messages and hasattr(messages[-1], "content"):
                result = messages[-1].content

    if _should_print(f"{task_key}_result"):
        print(f"\n[执行者] 步骤执行完成（共调用 {tool_call_count} 次工具）", flush=True)
        print(f"结果: {result[:200]}..." if len(result) > 200 else f"结果: {result}", flush=True)

    return {
        "past_steps": [(task, result)],
    }


async def replan_step(state: PlanExecuteState) -> dict:
    """重新规划步骤

    根据执行结果决定下一步行动
    """
    # 使用past_steps作为唯一标识
    past_steps = state.get("past_steps", [])
    replan_key = f"replan_{len(past_steps)}"

    if _should_print(f"{replan_key}_start"):
        print("\n[重新规划者] 正在评估执行结果...", flush=True)

    response = await replanner.ainvoke(state)

    # 解析响应
    action_data = extract_json(response.content)
    action_type = action_data.get("action_type", "")

    if action_type == "response":
        if _should_print(f"{replan_key}_response"):
            print(f"\n[重新规划者] 任务完成，准备回复用户", flush=True)
        return {"response": action_data.get("content", "")}
    else:
        steps = action_data.get("steps", [])
        if _should_print(f"{replan_key}_plan"):
            print(f"\n[重新规划者] 更新计划，剩余 {len(steps)} 个步骤", flush=True)
            for i, step in enumerate(steps, 1):
                print(f"  {i}. {step}", flush=True)
        return {"plan": steps}

