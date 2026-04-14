"""
第8章 示例8.1: LangSmith 追踪基础
=================================
本示例展示如何为LangGraph智能体启用LangSmith追踪,
并通过代码观察追踪数据的生成和查看。

案例背景:校园失物招领智能助手
- 学生可以报告丢失物品或捡到物品
- 系统使用AI分析描述并尝试匹配
- 所有执行过程通过LangSmith追踪记录
"""

import os
from typing import TypedDict, Optional, Annotated
from operator import add
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 加载环境变量
load_dotenv()

# ========================================
# 第一步: 配置LangSmith环境变量
# ========================================
# LangSmith追踪的核心配置,只需设置以下环境变量即可自动启用
# 在实际使用时,请将这些值替换为你自己的LangSmith API Key
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = "campus-lost-found" # 项目名称,用于在LangSmith中分类管理

# 初始化LLM
llm = ChatOpenAI(
  base_url=os.getenv("OPENAI_BASE_URL"),
  api_key=os.getenv("OPENAI_API_KEY"),
  model=os.getenv("OPENAI_MODEL_NAME"),
  temperature=0.7,
)


# ========================================
# 第二步: 定义State
# ========================================
class LostFoundState(TypedDict):
  """失物招领系统状态"""
  item_description: str     # 物品描述
  item_type: str         # 类型: lost(丢失) / found(捡到)
  reporter_name: str       # 报告人姓名
  location: str         # 地点
  ai_category: Optional[str]   # AI分类结果
  ai_analysis: Optional[str]   # AI分析结果
  match_result: Optional[str]  # 匹配结果
  status: str          # 处理状态


# ========================================
# 第三步: 定义各个处理节点
# ========================================
def classify_item(state: LostFoundState) -> dict:
  """使用AI对物品进行分类"""
  print(f"\n正在分类物品: {state['item_description']}")

  prompt = f"""你是校园失物招领系统的智能助手。
请对以下物品进行分类,类别包括:电子设备、证件文件、生活用品、衣物配饰、其他。

物品描述: {state['item_description']}
发现/丢失地点: {state['location']}

请直接返回类别名称,不需要其他解释。"""

  try:
    response = llm.invoke(prompt)
    category = response.content.strip()
    print(f" 分类结果: {category}")
    return {"ai_category": category, "status": "已分类"}
  except Exception as e:
    print(f" 分类失败: {e}")
    return {"ai_category": "未分类", "status": "分类失败"}


def analyze_item(state: LostFoundState) -> dict:
  """AI分析物品特征,生成详细描述"""
  print(f"\nAI正在分析物品特征...")

  prompt = f"""你是校园失物招领系统的智能助手。
请分析以下物品的关键特征,提取用于匹配的关键信息。

物品描述: {state['item_description']}
物品类别: {state['ai_category']}
地点: {state['location']}
类型: {"丢失物品" if state['item_type'] == 'lost' else '捡到物品'}

请用简洁的语言总结物品的关键特征(颜色、品牌、大小、独特标记等),
不超过50字。"""

  try:
    response = llm.invoke(prompt)
    analysis = response.content.strip()
    print(f" 分析结果: {analysis}")
    return {"ai_analysis": analysis, "status": "已分析"}
  except Exception as e:
    print(f" 分析失败: {e}")
    return {"ai_analysis": "分析暂时不可用", "status": "分析失败"}


def try_match(state: LostFoundState) -> dict:
  """尝试匹配丢失和捡到的物品"""
  print(f"\n正在尝试匹配...")

  # 模拟数据库中已有的记录
  existing_records = [
    {"type": "found", "desc": "黑色华为手机", "location": "图书馆三楼", "category": "电子设备"},
    {"type": "lost", "desc": "蓝色书包,里面有课本", "location": "教学楼A栋", "category": "生活用品"},
    {"type": "found", "desc": "校园卡一张,姓名模糊", "location": "食堂门口", "category": "证件文件"},
  ]

  prompt = f"""你是校园失物招领系统的匹配助手。
请判断当前物品是否可能与已有记录匹配。

当前物品:
- 描述: {state['item_description']}
- 类别: {state['ai_category']}
- 特征: {state['ai_analysis']}
- 地点: {state['location']}
- 类型: {"丢失" if state['item_type'] == 'lost' else '捡到'}

已有记录:
{chr(10).join([f"- [{r['type']}] {r['desc']} (地点:{r['location']}, 类别:{r['category']})" for r in existing_records])}

请判断是否有匹配的记录。如果有,说明匹配原因;如果没有,说明已登记等待匹配。
回复不超过80字。"""

  try:
    response = llm.invoke(prompt)
    match_result = response.content.strip()
    print(f" 匹配结果: {match_result}")
    return {"match_result": match_result, "status": "已完成"}
  except Exception as e:
    print(f" 匹配失败: {e}")
    return {"match_result": "匹配服务暂时不可用,已登记等待人工处理", "status": "待人工处理"}


def generate_response(state: LostFoundState) -> dict:
  """生成最终回复"""
  print(f"\n生成回复...")

  action = "丢失报告" if state["item_type"] == "lost" else "拾获登记"
  response = f"""
{'='*50}
 {action}处理完毕
{'='*50}
报告人: {state['reporter_name']}
物品描述: {state['item_description']}
AI分类: {state['ai_category']}
特征摘要: {state['ai_analysis']}
地点: {state['location']}
匹配结果: {state['match_result']}
状态: {state['status']}
{'='*50}
"""
  print(response)
  return {"status": "已回复"}


# ========================================
# 第四步: 构建工作流图
# ========================================
def build_lost_found_graph():
  """构建失物招领工作流"""
  builder = StateGraph(LostFoundState)

  # 添加节点
  builder.add_node("classify", classify_item)
  builder.add_node("analyze", analyze_item)
  builder.add_node("match", try_match)
  builder.add_node("respond", generate_response)

  # 定义流程
  builder.add_edge(START, "classify")
  builder.add_edge("classify", "analyze")
  builder.add_edge("analyze", "match")
  builder.add_edge("match", "respond")
  builder.add_edge("respond", END)

  # 配置检查点器和编译
  checkpointer = MemorySaver()
  return builder.compile(checkpointer=checkpointer)


# ========================================
# 第五步: 运行并观察追踪
# ========================================
def main():
  """主函数 - 运行失物招领系统"""
  graph = build_lost_found_graph()

  print("=" * 60)
  print(" 校园失物招领智能助手 (LangSmith追踪已启用)")
  print("=" * 60)

  # 场景1: 学生丢失物品
  print("\n场景1: 丢失物品报告")
  print("-" * 40)
  lost_item = {
    "item_description": "一个白色的小米充电宝,20000毫安,背面有贴纸",
    "item_type": "lost",
    "reporter_name": "张同学",
    "location": "图书馆二楼自习室",
    "ai_category": None,
    "ai_analysis": None,
    "match_result": None,
    "status": "待处理",
  }

  config_1 = {"configurable": {"thread_id": "lost-001"}}
  result_1 = graph.invoke(lost_item, config_1)

  # 场景2: 另一个学生捡到物品
  print("\n\n场景2: 拾获物品登记")
  print("-" * 40)
  found_item = {
    "item_description": "在食堂捡到一张校园卡,上面写着计算机学院",
    "item_type": "found",
    "reporter_name": "李同学",
    "location": "第一食堂二楼",
    "ai_category": None,
    "ai_analysis": None,
    "match_result": None,
    "status": "待处理",
  }

  config_2 = {"configurable": {"thread_id": "found-001"}}
  result_2 = graph.invoke(found_item, config_2)

  # 提示查看LangSmith
  print("\n" + "=" * 60)
  print(" 所有场景执行完毕!")
  print("=" * 60)
  print("\n现在你可以打开 https://smith.langchain.com 查看追踪数据:")
  print(f" 项目名称: {os.environ.get('LANGSMITH_PROJECT', 'default')}")
  print(" 你将看到:")
  print(" - 每个场景的完整执行链路(Trace)")
  print(" - 每个节点的输入输出详情(Run)")
  print(" - LLM调用的Prompt和Response")
  print(" - 执行时间、Token消耗等性能指标")


if __name__ == "__main__":
  main()
