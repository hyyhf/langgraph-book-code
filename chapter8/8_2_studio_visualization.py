"""
第8章 示例8.2: LangGraph Studio 可视化调试
=============================================
本示例展示一个适合在LangGraph Studio中运行和调试的智能体,
模拟"校园二手书交易助手"场景。

案例背景:校园二手书智能估价助手
- 学生输入想卖的书籍信息
- AI评估书籍状况并自动估价
- 根据估价结果决定是否推荐上架
- 整个流程可在LangGraph Studio中可视化调试

本文件的结构遵循LangGraph应用标准规范,
可以通过 langgraph dev 命令在Studio中运行。
"""

import os
from typing import TypedDict, Optional, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 加载环境变量
load_dotenv()

# 初始化LLM
llm = ChatOpenAI(
  base_url=os.getenv("OPENAI_BASE_URL"),
  api_key=os.getenv("OPENAI_API_KEY"),
  model=os.getenv("OPENAI_MODEL_NAME"),
  temperature=0.7,
)


# ========================================
# State定义
# ========================================
class BookTradeState(TypedDict):
  """二手书交易状态"""
  book_title: str        # 书名
  book_isbn: str        # ISBN号(可选)
  original_price: float     # 原价
  condition: str        # 书籍状况: 全新/良好/一般/较差
  seller_name: str       # 卖家姓名
  ai_evaluation: Optional[str] # AI评估
  estimated_price: Optional[float] # 估价
  recommendation: Optional[str]   # 推荐意见
  status: str          # 处理状态


# ========================================
# 节点函数
# ========================================
def evaluate_condition(state: BookTradeState) -> dict:
  """AI评估书籍状况"""
  print(f"\n正在评估书籍: {state['book_title']}")

  prompt = f"""你是校园二手书交易平台的智能估价师。
请根据以下信息评估这本书的实际状况。

书名: {state['book_title']}
原价: {state['original_price']}元
卖家描述的状况: {state['condition']}

请从以下几个维度简要评估(总计不超过60字):
1. 该书的市场需求(教材/畅销书/冷门书)
2. 当前状况对价格的影响
3. 二手书市场的一般折价规律"""

  try:
    response = llm.invoke(prompt)
    evaluation = response.content.strip()
    print(f" 评估结果: {evaluation}")
    return {"ai_evaluation": evaluation, "status": "已评估"}
  except Exception as e:
    return {"ai_evaluation": f"评估失败: {e}", "status": "评估失败"}


def calculate_price(state: BookTradeState) -> dict:
  """根据AI评估计算建议价格"""
  print(f"\n正在计算建议价格...")

  # 基础折价率
  condition_rates = {
    "全新": 0.7,
    "良好": 0.5,
    "一般": 0.35,
    "较差": 0.2,
  }

  rate = condition_rates.get(state["condition"], 0.3)
  estimated = round(state["original_price"] * rate, 2)

  print(f" 原价: {state['original_price']}元")
  print(f" 状况: {state['condition']} (折价率: {rate*100}%)")
  print(f" 建议价格: {estimated}元")

  return {"estimated_price": estimated, "status": "已估价"}


def decide_recommendation(state: BookTradeState) -> Literal["recommend_listing", "suggest_donation"]:
  """决定推荐上架还是建议捐赠"""
  # 如果估价低于5元,建议捐赠;否则推荐上架
  if state["estimated_price"] < 5:
    return "suggest_donation"
  else:
    return "recommend_listing"


def recommend_listing(state: BookTradeState) -> dict:
  """推荐上架出售"""
  print(f"\n推荐上架出售")

  prompt = f"""你是校园二手书交易助手。请为以下书籍写一段简短的上架推荐语(不超过40字)。

书名: {state['book_title']}
建议售价: {state['estimated_price']}元
书籍状况: {state['condition']}
AI评估: {state['ai_evaluation']}"""

  try:
    response = llm.invoke(prompt)
    recommendation = response.content.strip()
  except Exception:
    recommendation = f"推荐上架,建议售价{state['estimated_price']}元"

  print(f" 推荐语: {recommendation}")
  return {"recommendation": recommendation, "status": "推荐上架"}


def suggest_donation(state: BookTradeState) -> dict:
  """建议捐赠给图书角"""
  print(f"\n建议捐赠")
  recommendation = (
    f"《{state['book_title']}》估价较低({state['estimated_price']}元),"
    f"建议捐赠到学院图书角,让更多同学受益 "
  )
  print(f" 建议: {recommendation}")
  return {"recommendation": recommendation, "status": "建议捐赠"}


def generate_report(state: BookTradeState) -> dict:
  """生成最终报告"""
  report = f"""
{'='*50}
 二手书估价报告
{'='*50}
卖 家: {state['seller_name']}
书 名: {state['book_title']}
原 价: {state['original_price']}元
状 况: {state['condition']}
AI评估: {state['ai_evaluation']}
建议价: {state['estimated_price']}元
推 荐: {state['recommendation']}
状 态: {state['status']}
{'='*50}
"""
  print(report)
  return {"status": "已完成"}


# ========================================
# 构建图 - 这个变量会被langgraph.json引用
# ========================================
def build_book_trade_graph():
  """构建二手书交易工作流"""
  builder = StateGraph(BookTradeState)

  # 添加节点
  builder.add_node("evaluate", evaluate_condition)
  builder.add_node("price", calculate_price)
  builder.add_node("recommend_listing", recommend_listing)
  builder.add_node("suggest_donation", suggest_donation)
  builder.add_node("report", generate_report)

  # 定义流程
  builder.add_edge(START, "evaluate")
  builder.add_edge("evaluate", "price")

  # 条件路由: 根据估价决定推荐还是捐赠
  builder.add_conditional_edges(
    "price",
    decide_recommendation,
    {
      "recommend_listing": "recommend_listing",
      "suggest_donation": "suggest_donation",
    },
  )
  builder.add_edge("recommend_listing", "report")
  builder.add_edge("suggest_donation", "report")
  builder.add_edge("report", END)

  # 编译图
  return builder.compile()


# 创建图实例 - Studio会使用这个变量
graph = build_book_trade_graph()


# ========================================
# 本地测试
# ========================================
def main():
  """本地测试主函数"""
  print("=" * 60)
  print(" 校园二手书智能估价助手")
  print("=" * 60)

  # 测试场景1: 一本状况良好的教材
  print("\n测试场景1: 高价值教材")
  print("-" * 40)
  book1 = {
    "book_title": "数据结构与算法分析(C语言描述)",
    "book_isbn": "978-7-111-12345-6",
    "original_price": 59.0,
    "condition": "良好",
    "seller_name": "王同学",
    "ai_evaluation": None,
    "estimated_price": None,
    "recommendation": None,
    "status": "待处理",
  }
  config1 = {"configurable": {"thread_id": "book-001"}}
  graph.invoke(book1, config1)

  # 测试场景2: 一本状况较差的旧书
  print("\n\n测试场景2: 低价值旧书")
  print("-" * 40)
  book2 = {
    "book_title": "大学英语精读(第一册)",
    "book_isbn": "978-7-544-00000-0",
    "original_price": 15.0,
    "condition": "较差",
    "seller_name": "陈同学",
    "ai_evaluation": None,
    "estimated_price": None,
    "recommendation": None,
    "status": "待处理",
  }
  config2 = {"configurable": {"thread_id": "book-002"}}
  graph.invoke(book2, config2)

  # 提示Studio用法
  print("\n" + "=" * 60)
  print(" 在LangGraph Studio中调试本示例:")
  print(" 1. 安装CLI: pip install 'langgraph-cli[inmem]'")
  print(" 2. 启动开发服务器: langgraph dev")
  print(" 3. 打开Studio界面查看图的可视化结构")
  print(" 4. 在Studio中输入不同的书籍信息测试")
  print(" 5. 观察条件路由如何根据估价选择不同路径")
  print("=" * 60)


if __name__ == "__main__":
  main()
