"""
自定义示例：交互式运行
允许用户输入自己的编程任务
"""
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_agent import agent


async def run_custom_task(task: str):
    """运行自定义任务

    Args:
        task: 用户输入的任务描述
    """
    print("=" * 60)
    print("自定义任务执行")
    print("=" * 60)
    print(f"\n任务描述：\n{task}\n")
    print("=" * 60)

    # 配置
    config = {"recursion_limit": 50}

    # 运行智能体（使用ainvoke而不是astream，避免重复输出）
    result = await agent.ainvoke({"input": task}, config=config)

    print("\n" + "=" * 60)
    print("任务执行完成！")
    print("=" * 60)

    # 显示最终结果
    if result.get("response"):
        print(f"\n{result['response']}")


async def main():
    """主函数"""
    print("\n欢迎使用武汉智能编程助手！\n")
    print("这是一个基于LangGraph的Plan-and-Execute智能体")
    print("可以帮助你自动生成、测试和运行Python代码\n")
    
    while True:
        print("\n" + "-" * 60)
        print("请输入你的编程任务（输入 'quit' 退出）：")
        print("-" * 60)
        
        task = input("\n> ").strip()
        
        if task.lower() in ['quit', 'exit', 'q']:
            print("\n再见！")
            break
        
        if not task:
            print("任务不能为空，请重新输入")
            continue
        
        try:
            await run_custom_task(task)
        except KeyboardInterrupt:
            print("\n\n任务被中断")
            break
        except Exception as e:
            print(f"\n错误：{e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序退出")

