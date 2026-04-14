"""
进阶示例：东湖旅游数据分析
演示智能体如何生成包含数据可视化的代码
"""
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_agent import agent


async def run_example():
    """运行东湖旅游数据分析示例"""
    
    print("=" * 60)
    print("示例：武汉东湖旅游数据分析")
    print("=" * 60)
    
    task = """
请编写一个Python脚本来分析武汉东湖的旅游数据。
（周一到周日）的游客数量数据
- 数据：1200, 1500, 1800, 2000, 2200, 2500, 2800
要求：
2. 计算以下统计信息：
   - 总游客数
   - 平均每天游客数
   - 游客最多和最少的一天
   - 周末（周六、周日）vs 工作日的游客数对比
3. 使用柱状图展示每天的游客数量
4. 将代码保存为 donghu_analysis.py
5. 运行这个脚本并展示结果
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

