"""
7.4节 函数API - 高级示例
场景:武汉天气预报与出行建议系统

这个示例展示了:
1. 确定性执行的重要性
2. 并行执行多个task
3. 函数API与图API的对比
"""

from typing import TypedDict, Optional, List
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
import time
import random
import uuid


# ============================================================================
# 示例1: 确定性执行
# ============================================================================

@task
def get_current_weather() -> dict:
    """获取当前天气(模拟API调用,结果可能不同)"""
    print(f"\n  获取武汉当前天气...")
    time.sleep(0.3)
    
    # 模拟天气API返回的数据(每次可能不同)
    weather_conditions = ["晴天", "多云", "小雨", "阴天"]
    temperature = random.randint(15, 35)
    condition = random.choice(weather_conditions)
    
    weather = {
        "temperature": temperature,
        "condition": condition,
        "humidity": random.randint(40, 80),
        "wind_speed": random.randint(5, 20)
    }
    
    print(f"   温度: {weather['temperature']}°C")
    print(f"   天气: {weather['condition']}")
    
    return weather


@task
def get_air_quality() -> dict:
    """获取空气质量"""
    print(f"\n  获取空气质量...")
    time.sleep(0.3)
    
    aqi = random.randint(50, 200)
    
    if aqi <= 50:
        level = "优"
    elif aqi <= 100:
        level = "良"
    elif aqi <= 150:
        level = "轻度污染"
    else:
        level = "中度污染"
    
    air_quality = {
        "aqi": aqi,
        "level": level
    }
    
    print(f"   AQI: {aqi} ({level})")
    
    return air_quality


@task
def analyze_travel_conditions(weather: dict, air_quality: dict) -> dict:
    """分析出行条件"""
    print(f"\n 分析出行条件...")
    
    # 基于天气和空气质量给出建议
    score = 100
    suggestions = []
    
    # 天气因素
    if weather["condition"] in ["小雨", "大雨"]:
        score -= 20
        suggestions.append("建议携带雨具")
    
    if weather["temperature"] > 35:
        score -= 15
        suggestions.append("注意防暑降温")
    elif weather["temperature"] < 5:
        score -= 15
        suggestions.append("注意保暖")
    
    # 空气质量因素
    if air_quality["aqi"] > 150:
        score -= 25
        suggestions.append("建议减少户外活动")
    elif air_quality["aqi"] > 100:
        score -= 10
        suggestions.append("敏感人群注意防护")
    
    # 综合评分
    if score >= 80:
        recommendation = "适合出行"
    elif score >= 60:
        recommendation = "可以出行,需注意"
    else:
        recommendation = "不建议出行"
    
    result = {
        "score": score,
        "recommendation": recommendation,
        "suggestions": suggestions
    }
    
    print(f"  出行评分: {score}/100")
    print(f"  建议: {recommendation}")
    
    return result


@entrypoint(checkpointer=MemorySaver())
def travel_advisor_deterministic(inputs: Optional[dict] = None) -> dict:
    """确定性的出行建议系统"""
    print(f"\n{'='*60}")
    print(f"武汉出行建议系统(确定性版本)")
    print(f"{'='*60}")
    
    # 关键:将随机性封装在task中
    # 这样在恢复执行时,会使用保存的结果,而不是重新获取
    weather = get_current_weather().result()
    air_quality = get_air_quality().result()
    
    # 询问用户是否需要详细分析
    need_analysis = interrupt({
        "weather": weather,
        "air_quality": air_quality,
        "question": "是否需要详细的出行分析?"
    })
    
    if need_analysis:
        print(f"\n 用户选择: 需要详细分析")
        analysis = analyze_travel_conditions(weather, air_quality).result()
        
        return {
            "weather": weather,
            "air_quality": air_quality,
            "analysis": analysis
        }
    else:
        print(f"\n 用户选择: 不需要详细分析")
        return {
            "weather": weather,
            "air_quality": air_quality
        }


# ============================================================================
# 示例2: 并行执行多个task
# ============================================================================

@task
def check_traffic(route: str) -> dict:
    """检查交通状况"""
    print(f"\n 检查 {route} 的交通状况...")
    time.sleep(0.5)
    
    congestion_level = random.randint(1, 5)
    estimated_time = random.randint(20, 60)
    
    result = {
        "route": route,
        "congestion_level": congestion_level,
        "estimated_time": estimated_time
    }
    
    print(f"   拥堵等级: {congestion_level}/5")
    print(f"   预计用时: {estimated_time}分钟")
    
    return result


@task
def check_parking(location: str) -> dict:
    """检查停车情况"""
    print(f"\n 检查 {location} 的停车情况...")
    time.sleep(0.5)
    
    available_spots = random.randint(0, 50)
    price_per_hour = random.randint(5, 15)
    
    result = {
        "location": location,
        "available_spots": available_spots,
        "price_per_hour": price_per_hour
    }
    
    print(f"   可用车位: {available_spots}个")
    print(f"   停车费: {price_per_hour}元/小时")
    
    return result


@task
def check_restaurant_wait_time(restaurant: str) -> dict:
    """检查餐厅等位时间"""
    print(f"\n 检查 {restaurant} 的等位时间...")
    time.sleep(0.5)
    
    wait_time = random.randint(0, 60)
    
    result = {
        "restaurant": restaurant,
        "wait_time": wait_time
    }
    
    print(f"   等位时间: {wait_time}分钟")
    
    return result


@entrypoint(checkpointer=MemorySaver())
def plan_trip_parallel(destination: str) -> dict:
    """并行规划出行(检查交通、停车、餐厅)"""
    print(f"\n{'='*60}")
    print(f"规划前往 {destination} 的出行")
    print(f"{'='*60}")
    
    # 并行启动多个task
    # 注意:这些task会并发执行,不会阻塞
    traffic_future = check_traffic(f"前往{destination}")
    parking_future = check_parking(destination)
    restaurant_future = check_restaurant_wait_time(f"{destination}附近餐厅")
    
    print(f"\n 等待所有检查完成...")
    
    # 等待所有结果
    traffic = traffic_future.result()
    parking = parking_future.result()
    restaurant = restaurant_future.result()
    
    # 综合评估
    print(f"\n 综合评估:")
    
    total_time = traffic["estimated_time"] + restaurant["wait_time"]
    print(f"   总用时: {total_time}分钟")
    
    if parking["available_spots"] > 10:
        parking_status = "充足"
    elif parking["available_spots"] > 0:
        parking_status = "紧张"
    else:
        parking_status = "无车位"
    print(f"   停车: {parking_status}")
    
    return {
        "destination": destination,
        "traffic": traffic,
        "parking": parking,
        "restaurant": restaurant,
        "total_time": total_time
    }


# ============================================================================
# 示例3: 错误处理与重试
# ============================================================================

@task
def fetch_scenic_spot_info(spot_name: str, retry_count: int = 0) -> dict:
    """获取景点信息(可能失败)"""
    print(f"\n  获取 {spot_name} 的信息... (尝试 {retry_count + 1})")
    time.sleep(0.3)
    
    # 模拟30%的失败率
    if random.random() < 0.3 and retry_count < 2:
        print(f" 获取失败,需要重试")
        raise Exception("API调用失败")
    
    info = {
        "name": spot_name,
        "opening_hours": "8:00-18:00",
        "ticket_price": random.randint(50, 100),
        "visitor_count": random.randint(100, 1000)
    }
    
    print(f" 获取成功")
    print(f"   门票: {info['ticket_price']}元")
    
    return info


@entrypoint(checkpointer=MemorySaver())
def get_scenic_info_with_retry(spot_name: str) -> dict:
    """获取景点信息(带重试)"""
    print(f"\n{'='*60}")
    print(f"获取景点信息: {spot_name}")
    print(f"{'='*60}")
    
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            info = fetch_scenic_spot_info(spot_name, retry).result()
            return {"success": True, "info": info, "retries": retry}
        except Exception as e:
            print(f"\n 第 {retry + 1} 次尝试失败")
            if retry == max_retries - 1:
                print(f"达到最大重试次数")
                return {"success": False, "error": str(e), "retries": retry + 1}
            time.sleep(0.5)  # 等待后重试


# ============================================================================
# 演示函数
# ============================================================================

def demo_deterministic_execution():
    """演示确定性执行"""
    print("\n" + "="*70)
    print("示例1: 确定性执行")
    print("="*70)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 第一次调用
    print("\n第一次调用:")
    result = travel_advisor_deterministic.invoke({}, config)
    
    if "__interrupt__" in result:
        print(f"\n 工作流已暂停")
        print(f"天气: {result['__interrupt__'][0].value['weather']['condition']}")
        print(f"温度: {result['__interrupt__'][0].value['weather']['temperature']}°C")
        
        # 恢复执行
        print("\n 用户选择: 需要详细分析")
        from langgraph.types import Command
        final_result = travel_advisor_deterministic.invoke(
            Command(resume=True),
            config
        )
        
        print(f"\n 分析完成")
        print(f"注意:恢复执行时,天气数据保持不变(确定性)")


def demo_parallel_execution():
    """演示并行执行"""
    print("\n\n" + "="*70)
    print("示例2: 并行执行多个task")
    print("="*70)
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    start_time = time.time()
    result = plan_trip_parallel.invoke("黄鹤楼", config)
    end_time = time.time()
    
    print(f"\n 总执行时间: {end_time - start_time:.2f}秒")
    print(f"(如果串行执行,需要约1.5秒)")


def demo_error_handling():
    """演示错误处理"""
    print("\n\n" + "="*70)
    print("示例3: 错误处理与重试")
    print("="*70)
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    result = get_scenic_info_with_retry.invoke("黄鹤楼", config)
    
    if result["success"]:
        print(f"\n 成功获取信息 (重试{result['retries']}次)")
    else:
        print(f"\n 获取失败 (重试{result['retries']}次)")


if __name__ == "__main__":
    demo_deterministic_execution()
    demo_parallel_execution()
    demo_error_handling()
    
    print("\n\n 所有示例运行完成!")

