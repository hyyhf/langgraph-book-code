"""
可视化图结构

生成智能编程助手的图结构可视化
"""

from code_agent.agent import create_agent


def visualize_graph():
    """可视化智能编程助手的图结构"""
    print("生成智能编程助手图结构...")

    # 创建智能体
    graph = create_agent()

    # 生成Mermaid图
    try:
        mermaid_code = graph.get_graph().draw_mermaid()

        # 保存到文件
        output_file = "code_agent_graph.mmd"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        print(f"图结构已保存到: {output_file}")
        print("\n图结构(Mermaid):")
        print(mermaid_code)

        return mermaid_code
    except Exception as e:
        print(f"生成图结构失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_graph_description():
    """打印图结构的文字描述"""
    print("\n" + "="*80)
    print("智能编程助手图结构说明")
    print("="*80)

    print("\n【Plan-and-Execute模式】")
    print("-"*80)
    print("""
执行流程:
1. START → planner (规划者节点)
   - 分析用户任务
   - 判断任务复杂度
   - 生成执行计划（步骤列表）

2. planner → executor (执行者节点)
   - 执行当前步骤
   - 使用ReAct模式调用工具
   - 记录执行结果

3. executor → replanner (重新规划者节点)
   - 评估执行结果
   - 判断任务是否完成
   - 决定下一步行动

4. replanner → [条件判断]
   - 如果任务完成 → END
   - 如果任务未完成 → executor (继续执行下一步)

关键点:
- 规划者只在开始时执行一次
- 执行者和重新规划者形成循环
- 每次循环执行一个步骤
- 重新规划者决定是否继续循环
- 支持复杂任务的多步骤执行
    """)

    print("\n【三个角色的职责】")
    print("-"*80)
    print("""
1. Planner (规划者)
   - 输入: 用户任务描述
   - 输出: 步骤列表
   - 职责: 任务分解、复杂度判断

2. Executor (执行者)
   - 输入: 当前步骤
   - 输出: 执行结果
   - 职责: 工具调用、代码生成、命令执行
   - 工具: write_file, read_file, list_files, execute_command

3. Replanner (重新规划者)
   - 输入: 原始任务、当前计划、已完成步骤
   - 输出: 是否完成、最终回复、剩余步骤
   - 职责: 结果评估、决策制定
    """)


def main():
    """主函数"""
    print("="*80)
    print("智能编程助手图结构可视化")
    print("="*80)

    # 打印文字描述
    print_graph_description()

    # 生成可视化文件
    print("\n" + "="*80)
    print("生成Mermaid图文件")
    print("="*80)

    mermaid_code = visualize_graph()

    if mermaid_code:
        print("\n" + "="*80)
        print("完成!")
        print("="*80)
        print("\n提示: 可以使用Mermaid在线编辑器查看生成的.mmd文件")
        print("在线编辑器: https://mermaid.live/")
        print("\n或者使用以下命令查看:")
        print("  cat code_agent_graph.mmd")
    else:
        print("\n生成失败，请检查错误信息")


if __name__ == "__main__":
    main()

