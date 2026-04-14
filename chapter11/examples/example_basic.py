"""
基础示例：热干面店铺评分系统
演示智能体如何生成简单的数据分析代码
"""
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_agent import agent


async def run_example():
    """运行热干面店铺评分示例"""
    
    print("=" * 60)
    print("示例：武汉热干面店铺评分系统")
    print("=" * 60)
    
    task = """
请编写一个Python脚本来分析武汉热干面店铺的评分数据。

要求：
1. 创建一个包含5家热干面店铺的数据
   - 店铺名称：蔡林记、老通城、石记、田记、巴厘龙虾
   - 评分分别是：4.5, 4.8, 4.2, 4.9, 4.6
2. 计算平均评分
3. 找出评分最高和最低的店铺
4. 用表格形式展示所有店铺的评分
5. 将代码保存为 reganmian_rating.py
6. 运行这个脚本并展示结果
"""
    
    print(f"\n任务描述：\n{task}\n")
    print("=" * 60)
    
    # 配置
    config = {"recursion_limit": 50}

    # 运行智能体（使用ainvoke避免重复输出）
    result = await agent.ainvoke({"input": task}, config=config)

    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)

    # 显示最终结果
    if result.get("response"):
        print(f"\n最终结果：\n{result['response']}")


if __name__ == "__main__":
    asyncio.run(run_example())

