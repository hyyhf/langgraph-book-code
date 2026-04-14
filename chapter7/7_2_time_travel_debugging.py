"""
7.2节 时间旅行 - 调试与错误恢复示例
场景:武汉东湖绿道智能导览系统

这个示例展示时间旅行在实际场景中的应用:
1. 调试复杂的执行流程
2. 错误恢复与重试
3. A/B测试不同的决策路径
4. 使用LLM生成个性化推荐
"""

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import uuid
import os

# 加载环境变量
load_dotenv()

# 初始化LLM
llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL_NAME"),
    temperature=0.7
)


class TourState(TypedDict):
    """导览状态"""
    tourist_name: str  # 游客姓名
    current_location: str  # 当前位置
    interests: list[str]  # 兴趣点
    visited_spots: list[str]  # 已访问景点
    recommendations: list[str]  # 推荐景点
    route: list[str]  # 规划路线
    satisfaction: int  # 满意度(0-100)
    error_count: int  # 错误计数


# 东湖绿道景点
EAST_LAKE_SPOTS = {
    "湖光序曲": {"type": "观景", "time": 30, "rating": 4.5},
    "湖中道": {"type": "骑行", "time": 45, "rating": 4.8},
    "磨山景区": {"type": "登山", "time": 90, "rating": 4.7},
    "听涛景区": {"type": "观景", "time": 60, "rating": 4.6},
    "落雁景区": {"type": "观鸟", "time": 50, "rating": 4.4},
    "白马景区": {"type": "休闲", "time": 40, "rating": 4.3},
    "梅园": {"type": "赏花", "time": 50, "rating": 4.9},
    "樱园": {"type": "赏花", "time": 55, "rating": 4.9}
}


def analyze_interests(state: TourState) -> dict:
    """分析游客兴趣 - 使用LLM生成个性化推荐"""
    print(f"\n AI分析游客兴趣...")
    print(f"游客: {state['tourist_name']}")
    print(f"兴趣: {', '.join(state['interests'])}")

    # 构建景点信息字符串
    spots_info = "\n".join([
        f"- {spot}: {info['type']}, 游览时间{info['time']}分钟, 评分{info['rating']}"
        for spot, info in EAST_LAKE_SPOTS.items()
    ])

    # 使用LLM生成个性化推荐
    prompt = f"""你是武汉东湖绿道的智能导览助手。请根据游客的兴趣推荐合适的景点。

游客信息:
- 姓名: {state['tourist_name']}
- 兴趣: {', '.join(state['interests'])}

可选景点:
{spots_info}

请从以上景点中选择3-5个最适合该游客的景点,只需要返回景点名称,用逗号分隔,不要其他说明。
例如: 湖光序曲,磨山景区,梅园
"""

    try:
        response = llm.invoke(prompt)
        recommended_spots = [s.strip() for s in response.content.strip().split(',')]
        # 过滤掉不存在的景点
        recommendations = [s for s in recommended_spots if s in EAST_LAKE_SPOTS]
        print(f"AI推荐景点: {', '.join(recommendations)}")
        return {"recommendations": recommendations}
    except Exception as e:
        print(f"AI推荐失败: {e},使用默认推荐")
        # 降级方案:根据兴趣推荐景点
        recommendations = []
        for spot, info in EAST_LAKE_SPOTS.items():
            if info["type"] in state["interests"]:
                recommendations.append(spot)
        print(f"默认推荐景点: {', '.join(recommendations)}")
        return {"recommendations": recommendations}


def plan_route(state: TourState) -> dict:
    """规划路线"""
    print(f"\n  规划游览路线...")
    
    # 模拟可能出错的路线规划
    recommendations = state.get("recommendations", [])
    
    # 故意引入一个错误:如果推荐景点太多,规划会失败
    if len(recommendations) > 5:
        print(f" 错误: 推荐景点过多({len(recommendations)}个),无法规划合理路线")
        error_count = state.get("error_count", 0) + 1
        return {
            "route": [],
            "error_count": error_count,
            "satisfaction": 0
        }
    
    # 简单的路线规划
    route = recommendations[:4]  # 最多选4个景点
    print(f"规划路线: {' → '.join(route)}")
    
    return {
        "route": route,
        "satisfaction": 70
    }


def execute_tour(state: TourState) -> dict:
    """执行游览"""
    print(f"\n 开始游览...")
    
    route = state.get("route", [])
    if not route:
        print(" 没有可执行的路线")
        return {"satisfaction": 0}
    
    visited = []
    total_time = 0
    
    for spot in route:
        if spot in EAST_LAKE_SPOTS:
            info = EAST_LAKE_SPOTS[spot]
            visited.append(spot)
            total_time += info["time"]
            print(f"  {spot} ({info['type']}, {info['time']}分钟)")
    
    satisfaction = min(100, 50 + len(visited) * 10)
    
    print(f"\n总用时: {total_time}分钟")
    print(f"满意度: {satisfaction}/100")
    
    return {
        "visited_spots": visited,
        "satisfaction": satisfaction
    }


def build_tour_graph():
    """构建导览图"""
    builder = StateGraph(TourState)
    
    builder.add_node("analyze", analyze_interests)
    builder.add_node("plan", plan_route)
    builder.add_node("execute", execute_tour)
    
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "plan")
    builder.add_edge("plan", "execute")
    builder.add_edge("execute", END)
    
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


# ============================================================================
# 示例1: 使用时间旅行调试错误
# ============================================================================

def demo_debugging_with_time_travel():
    """演示使用时间旅行调试错误"""
    print("=" * 70)
    print("示例1: 使用时间旅行调试错误")
    print("=" * 70)
    
    graph = build_tour_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 创建一个会导致错误的状态(兴趣太多)
    state = {
        "tourist_name": "张三",
        "current_location": "湖光序曲",
        "interests": ["观景", "骑行", "登山", "观鸟", "休闲", "赏花"],  # 6个兴趣
        "visited_spots": [],
        "recommendations": [],
        "route": [],
        "satisfaction": 0,
        "error_count": 0
    }
    
    print("\n 第一次尝试(会失败)...")
    result = graph.invoke(state, config)
    
    print(f"\n结果: 满意度 = {result['satisfaction']}/100")
    
    if result["satisfaction"] < 50:
        print("\n 调试: 使用时间旅行查看执行过程...")
        
        # 获取历史记录
        history = list(graph.get_state_history(config))
        
        print("\n 执行历史:")
        for i, checkpoint in enumerate(history):
            values = checkpoint.values
            print(f"\n步骤 {len(history) - i - 1}:")
            print(f"  推荐数量: {len(values.get('recommendations', []))}")
            print(f"  路线长度: {len(values.get('route', []))}")
            print(f"  错误计数: {values.get('error_count', 0)}")
        
        # 找到analyze节点之后的检查点
        analyze_checkpoint = history[len(history) - 2]  # analyze之后
        
        print(f"\n 发现问题: 推荐景点过多({len(analyze_checkpoint.values['recommendations'])}个)")
        print("解决方案: 修改推荐列表,只保留评分最高的5个")
        
        # 修改历史状态
        top_recommendations = sorted(
            analyze_checkpoint.values['recommendations'],
            key=lambda x: EAST_LAKE_SPOTS[x]["rating"],
            reverse=True
        )[:5]
        
        graph.update_state(
            analyze_checkpoint.config,
            {"recommendations": top_recommendations}
        )
        
        print(f"修正后的推荐: {', '.join(top_recommendations)}")
        
        # 从修改后的检查点继续执行
        print("\n 从修正点重新执行...")
        resume_config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": analyze_checkpoint.config["configurable"]["checkpoint_id"]
            }
        }
        
        # 继续执行plan和execute
        final_result = graph.invoke(None, resume_config)
        
        print(f"\n 修正后的结果: 满意度 = {final_result['satisfaction']}/100")
        print(f"游览路线: {' → '.join(final_result['route'])}")


# ============================================================================
# 示例2: 错误恢复与重试
# ============================================================================

def demo_error_recovery():
    """演示错误恢复"""
    print("\n\n" + "=" * 70)
    print("示例2: 错误恢复与重试")
    print("=" * 70)
    
    graph = build_tour_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    state = {
        "tourist_name": "李四",
        "current_location": "听涛景区",
        "interests": ["观景", "骑行", "登山", "观鸟", "休闲", "赏花"],
        "visited_spots": [],
        "recommendations": [],
        "route": [],
        "satisfaction": 0,
        "error_count": 0
    }
    
    print("\n 执行导览...")
    result = graph.invoke(state, config)
    
    if result.get("error_count", 0) > 0:
        print(f"\n  检测到错误 (错误计数: {result['error_count']})")
        print(" 自动恢复: 回退到分析阶段,调整推荐策略...")
        
        # 获取历史
        history = list(graph.get_state_history(config))
        
        # 找到analyze之后的检查点
        for checkpoint in history:
            if "recommendations" in checkpoint.values and checkpoint.values["recommendations"]:
                # 修改推荐策略:只推荐评分4.5以上的
                high_rated = [
                    spot for spot in checkpoint.values["recommendations"]
                    if EAST_LAKE_SPOTS[spot]["rating"] >= 4.5
                ][:4]
                
                print(f"调整后的推荐: {', '.join(high_rated)}")
                
                # 更新状态
                graph.update_state(
                    checkpoint.config,
                    {"recommendations": high_rated, "error_count": 0}
                )
                
                # 从该点重新执行
                resume_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": checkpoint.config["configurable"]["checkpoint_id"]
                    }
                }
                
                final_result = graph.invoke(None, resume_config)
                
                print(f"\n 恢复成功!")
                print(f"满意度: {final_result['satisfaction']}/100")
                print(f"游览路线: {' → '.join(final_result['route'])}")
                break


# ============================================================================
# 示例3: A/B测试不同决策
# ============================================================================

def demo_ab_testing():
    """演示A/B测试"""
    print("\n\n" + "=" * 70)
    print("示例3: A/B测试不同的推荐策略")
    print("=" * 70)
    
    graph = build_tour_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    state = {
        "tourist_name": "王五",
        "current_location": "磨山景区",
        "interests": ["观景", "赏花"],
        "visited_spots": [],
        "recommendations": [],
        "route": [],
        "satisfaction": 0,
        "error_count": 0
    }
    
    print("\n 执行基准方案...")
    result_baseline = graph.invoke(state, config)
    
    print(f"\n基准方案结果:")
    print(f"  路线: {' → '.join(result_baseline['route'])}")
    print(f"  满意度: {result_baseline['satisfaction']}/100")
    
    # 获取analyze之后的检查点
    history = list(graph.get_state_history(config))
    analyze_checkpoint = None
    for checkpoint in history:
        if "recommendations" in checkpoint.values and checkpoint.values["recommendations"]:
            analyze_checkpoint = checkpoint
            break
    
    if analyze_checkpoint:
        # 测试方案A:优先推荐高评分景点
        print("\n\n  测试方案A: 优先高评分景点")
        recommendations_a = sorted(
            analyze_checkpoint.values["recommendations"],
            key=lambda x: EAST_LAKE_SPOTS[x]["rating"],
            reverse=True
        )
        
        # 创建新的线程测试方案A
        thread_a = str(uuid.uuid4())
        config_a = {"configurable": {"thread_id": thread_a}}
        
        state_a = state.copy()
        state_a["recommendations"] = recommendations_a
        
        # 从plan节点开始执行
        graph_a = build_tour_graph()
        result_a = graph_a.invoke(state_a, config_a)
        
        print(f"  路线: {' → '.join(result_a['route'])}")
        print(f"  满意度: {result_a['satisfaction']}/100")
        
        # 测试方案B:优先推荐用时短的景点
        print("\n  测试方案B: 优先用时短的景点")
        recommendations_b = sorted(
            analyze_checkpoint.values["recommendations"],
            key=lambda x: EAST_LAKE_SPOTS[x]["time"]
        )
        
        thread_b = str(uuid.uuid4())
        config_b = {"configurable": {"thread_id": thread_b}}
        
        state_b = state.copy()
        state_b["recommendations"] = recommendations_b
        
        graph_b = build_tour_graph()
        result_b = graph_b.invoke(state_b, config_b)
        
        print(f"  路线: {' → '.join(result_b['route'])}")
        print(f"  满意度: {result_b['satisfaction']}/100")
        
        # 比较结果
        print("\n A/B测试结果对比:")
        print(f"  基准方案: {result_baseline['satisfaction']}/100")
        print(f"  方案A:    {result_a['satisfaction']}/100")
        print(f"  方案B:    {result_b['satisfaction']}/100")
        
        best = max(
            [("基准", result_baseline['satisfaction']),
             ("方案A", result_a['satisfaction']),
             ("方案B", result_b['satisfaction'])],
            key=lambda x: x[1]
        )
        print(f"\n 最佳方案: {best[0]} (满意度: {best[1]}/100)")


if __name__ == "__main__":
    demo_debugging_with_time_travel()
    demo_error_recovery()
    demo_ab_testing()
    
    print("\n\n 所有示例运行完成!")

