"""
复杂任务示例：武汉美食推荐系统
演示智能体如何处理需要多个步骤的复杂任务
"""
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_agent import agent


async def run_example():
    """运行武汉美食推荐系统示例"""
    
    print("=" * 60)
    print("复杂任务示例：武汉美食推荐系统")
    print("=" * 60)
    
    task = """请创建一个武汉美食推荐系统，要求如下：

第一步：数据准备
1. 创建一个JSON文件 wuhan_food_data.json，包含至少5种武汉美食的信息
   每种美食包含：名称、类型、价格区间、推荐指数(1-5星)、特色描述

第二步：数据分析程序
2. 创建 food_analyzer.py 程序，实现以下功能：
   - 读取JSON数据
   - 按价格区间分类统计
   - 按推荐指数排序
   - 计算平均价格
   - 生成统计报告

第三步：推荐引擎
3. 创建 food_recommender.py 程序，实现智能推荐功能：
   - 根据预算推荐美食（如预算50元以下）
   - 根据类型推荐（如只推荐小吃类）
   - 综合推荐指数给出Top3推荐

第四步：可视化
4. 创建 food_visualizer.py 程序：
   - 使用matplotlib绘制价格分布柱状图
   - 绘制推荐指数饼图
   - 保存图表为PNG文件

第五步：测试
5. 依次运行所有程序，验证功能，生成测试报告 test_report.txt

所有文件保存在workspace目录中，使用真实的武汉美食数据（热干面、豆皮、鸭脖、武昌鱼、排骨藕汤等）和合理的价格信息。"""
    
    print(f"\n任务描述：\n{task}\n")
    print("=" * 60)
    
    # 配置
    config = {"recursion_limit": 50}

    # 运行智能体
    result = await agent.ainvoke({"input": task}, config=config)

    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)

    # 显示最终结果
    if result.get("response"):
        print(f"\n最终结果：\n{result['response']}")


if __name__ == "__main__":
    asyncio.run(run_example())

