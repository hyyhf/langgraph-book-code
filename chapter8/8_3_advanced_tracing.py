"""
第8章 示例8.3: LangSmith追踪进阶 - 自定义追踪与状态捕获
=========================================================
本示例展示LangSmith的高级追踪功能,包括:
- 使用@traceable装饰器自定义追踪
- 添加元数据和标签
- 捕获状态变更
- 追踪数据分析

案例背景:校园活动智能推荐助手
- 根据学生的兴趣和空闲时间推荐校园活动
- 使用自定义追踪记录推荐过程的每个步骤
- 通过元数据和标签组织追踪数据
"""

import os
import time
import uuid
from typing import TypedDict, Optional, Annotated
from operator import add
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 加载环境变量
load_dotenv()

# ========================================
# LangSmith高级配置
# ========================================
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = "campus-activity-recommender"

# 尝试导入langsmith SDK (用于高级功能)
try:
  from langsmith import traceable
  from langsmith.run_helpers import get_current_run_tree

  LANGSMITH_SDK_AVAILABLE = True
  print(" LangSmith SDK 可用,高级追踪功能已启用")
except ImportError:
  LANGSMITH_SDK_AVAILABLE = False
  print("️ LangSmith SDK 未安装,将使用基础追踪模式")
  print(" 安装方式: pip install langsmith")

  # 创建一个空装饰器作为fallback
  def traceable(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
      return args[0]
    return lambda f: f

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
class ActivityState(TypedDict):
  """校园活动推荐状态"""
  student_name: str        # 学生姓名
  interests: list[str]       # 兴趣标签
  free_time: str          # 空闲时间段
  ai_profile: Optional[str]    # AI生成的用户画像
  recommended_activities: Optional[list[str]] # 推荐活动列表
  final_recommendation: Optional[str] # 最终推荐
  status: str           # 处理状态


# ========================================
# 模拟校园活动数据库
# ========================================
CAMPUS_ACTIVITIES = [
  {"name": "ACM程序设计竞赛培训", "category": "编程", "time": "周六下午", "location": "计算机学院实验室"},
  {"name": "英语角交流活动", "category": "语言", "time": "周三晚上", "location": "外语学院咖啡厅"},
  {"name": "摄影协会外拍", "category": "摄影", "time": "周日上午", "location": "校园各处"},
  {"name": "篮球联赛", "category": "运动", "time": "周四下午", "location": "体育馆"},
  {"name": "读书分享会", "category": "阅读", "time": "周五晚上", "location": "图书馆报告厅"},
  {"name": "AI技术沙龙", "category": "编程", "time": "周二晚上", "location": "创新创业中心"},
  {"name": "吉他社排练", "category": "音乐", "time": "周六上午", "location": "艺术楼"},
  {"name": "志愿者服务队", "category": "公益", "time": "周日下午", "location": "社区服务中心"},
  {"name": "数学建模训练", "category": "数学", "time": "周三下午", "location": "理学院"},
  {"name": "创业路演大赛", "category": "创业", "time": "周五下午", "location": "商学院报告厅"},
]


# ========================================
# 节点函数 (带自定义追踪)
# ========================================
@traceable(name="生成用户画像", tags=["ai", "profile"])
def build_user_profile(state: ActivityState) -> dict:
  """使用AI分析学生兴趣,生成用户画像"""
  print(f"\n正在为 {state['student_name']} 生成用户画像...")

  prompt = f"""你是校园活动推荐系统的用户画像分析师。
请根据以下信息生成简短的用户画像(不超过50字)。

学生姓名: {state['student_name']}
兴趣标签: {', '.join(state['interests'])}
空闲时间: {state['free_time']}

请总结该学生的特点和活动偏好。"""

  response = llm.invoke(prompt)
  profile = response.content.strip()
  print(f" 用户画像: {profile}")
  return {"ai_profile": profile, "status": "画像已生成"}


@traceable(name="筛选匹配活动", tags=["matching", "filter"])
def filter_activities(state: ActivityState) -> dict:
  """根据用户画像筛选匹配的活动"""
  print(f"\n正在筛选匹配活动...")

  # 构建活动列表字符串
  activities_text = "\n".join(
    [f"- {a['name']} ({a['category']}, {a['time']}, {a['location']})" for a in CAMPUS_ACTIVITIES]
  )

  prompt = f"""你是校园活动推荐系统的匹配引擎。
请从以下活动中选出最适合该学生的3个活动。

用户画像: {state['ai_profile']}
学生兴趣: {', '.join(state['interests'])}
空闲时间: {state['free_time']}

可选活动:
{activities_text}

请只返回活动名称,每行一个,最多3个。"""

  response = llm.invoke(prompt)
  activities = [line.strip().lstrip("- ·•") for line in response.content.strip().split("\n") if line.strip()]
  activities = activities[:3] # 最多3个

  print(f" 匹配到 {len(activities)} 个活动:")
  for act in activities:
    print(f"  {act}")

  return {"recommended_activities": activities, "status": "活动已匹配"}


@traceable(name="生成推荐报告", tags=["ai", "report"])
def generate_recommendation(state: ActivityState) -> dict:
  """生成个性化推荐报告"""
  print(f"\n正在生成个性化推荐报告...")

  activities_str = "、".join(state["recommended_activities"]) if state["recommended_activities"] else "暂无"

  prompt = f"""你是校园活动推荐系统的推荐官。
请为学生生成一段温馨、有趣的活动推荐语。

学生: {state['student_name']}
用户画像: {state['ai_profile']}
推荐活动: {activities_str}

要求:
- 语气亲切,像学长学姐推荐一样
- 简要说明为什么推荐这些活动
- 不超过100字"""

  response = llm.invoke(prompt)
  recommendation = response.content.strip()
  print(f" 推荐语: {recommendation}")

  return {"final_recommendation": recommendation, "status": "推荐已生成"}


# ========================================
# 构建图
# ========================================
def build_activity_recommender():
  """构建活动推荐工作流"""
  builder = StateGraph(ActivityState)

  builder.add_node("profile", build_user_profile)
  builder.add_node("filter", filter_activities)
  builder.add_node("recommend", generate_recommendation)

  builder.add_edge(START, "profile")
  builder.add_edge("profile", "filter")
  builder.add_edge("filter", "recommend")
  builder.add_edge("recommend", END)

  return builder.compile()


# 创建图实例
graph = build_activity_recommender()


# ========================================
# 运行示例
# ========================================
def main():
  """主函数"""
  print("=" * 60)
  print(" 校园活动智能推荐助手 (LangSmith高级追踪)")
  print("=" * 60)

  # 测试场景: 不同类型的学生
  students = [
    {
      "student_name": "小明",
      "interests": ["编程", "人工智能", "数学"],
      "free_time": "周二和周六",
      "ai_profile": None,
      "recommended_activities": None,
      "final_recommendation": None,
      "status": "待处理",
    },
    {
      "student_name": "小红",
      "interests": ["摄影", "阅读", "音乐"],
      "free_time": "周五和周日",
      "ai_profile": None,
      "recommended_activities": None,
      "final_recommendation": None,
      "status": "待处理",
    },
  ]

  for i, student in enumerate(students):
    print(f"\n{'='*60}")
    print(f"‍ 场景{i+1}: 为 {student['student_name']} 推荐活动")
    print(f" 兴趣: {', '.join(student['interests'])}")
    print(f" 空闲: {student['free_time']}")
    print(f"{'='*60}")

    # 使用带元数据的config
    config = {
      "configurable": {"thread_id": f"student-{i+1:03d}"},
      "metadata": {
        "student_name": student["student_name"],
        "scenario": f"test-scenario-{i+1}",
        "timestamp": datetime.now().isoformat(),
      },
      "tags": ["test", f"student-{student['student_name']}"],
    }

    result = graph.invoke(student, config)

    # 打印最终结果
    print(f"\n推荐结果:")
    print(f" {result.get('final_recommendation', '暂无推荐')}")

  # 提示
  print("\n" + "=" * 60)
  print(" 推荐完成!")
  print("=" * 60)
  print("\n在LangSmith中查看追踪数据:")
  print(" 1. 打开 https://smith.langchain.com")
  print(f" 2. 进入项目: {os.environ.get('LANGSMITH_PROJECT')}")
  print(" 3. 查看每个学生的推荐追踪链路")
  print(" 4. 使用标签(tags)过滤不同类型的操作")
  print(" 5. 查看元数据(metadata)中的学生信息")
  print(" 6. 对比不同学生的推荐过程差异")


if __name__ == "__main__":
  main()
