"""
可视化图结构

生成研究助手的图结构可视化
"""

from research_agent import create_research_agent


def visualize_basic_graph():
    """可视化基础图结构(不包含人工审核)"""
    print("生成基础图结构...")
    graph = create_research_agent(with_human_review=False)

    # 生成Mermaid图
    try:
        import os
        mermaid_code = graph.get_graph().draw_mermaid()

        # 保存到文件
        output_file = "graph_basic.mmd"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        print(f"基础图结构已保存到: {output_file}")
        print("\n图结构(Mermaid):")
        print(mermaid_code)
    except Exception as e:
        print(f"生成图结构失败: {e}")


def visualize_human_review_graph():
    """可视化包含人工审核的图结构"""
    print("\n生成包含人工审核的图结构...")
    graph = create_research_agent(with_human_review=True)

    # 生成Mermaid图
    try:
        import os
        mermaid_code = graph.get_graph().draw_mermaid()

        # 保存到文件
        output_file = "graph_with_review.mmd"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        print(f"包含人工审核的图结构已保存到: {output_file}")
        print("\n图结构(Mermaid):")
        print(mermaid_code)
    except Exception as e:
        print(f"生成图结构失败: {e}")


def print_graph_description():
    """打印图结构的文字描述"""
    print("\n" + "="*80)
    print("研究助手图结构说明")
    print("="*80)
    
    print("\n【基础版本 - 不包含人工审核】")
    print("-"*80)
    print("""
执行流程:
1. START → researcher (研究员节点)
2. researcher → [条件判断]
   - 如果有工具调用 → tools (工具节点)
   - 否则 → analyst (分析师节点)
3. tools → researcher (工具执行后返回研究员)
4. analyst → reporter (报告员节点)
5. reporter → END

关键点:
- 研究员可能多次调用工具
- 工具执行后返回研究员继续处理
- 研究员完成后直接进入分析阶段
    """)
    
    print("\n【完整版本 - 包含人工审核】")
    print("-"*80)
    print("""
执行流程:
1. START → researcher (研究员节点)
2. researcher → [条件判断]
   - 如果有工具调用 → tools (工具节点)
   - 如果有研究数据 → human_review (人工审核节点)
3. tools → researcher (工具执行后返回研究员)
4. human_review → [条件判断]
   - 如果审核通过 → analyst (分析师节点)
   - 如果审核未通过 → researcher (返回研究员重新收集)
5. analyst → reporter (报告员节点)
6. reporter → END

关键点:
- 在human_review节点前会中断执行
- 需要人工输入后才能继续
- 审核未通过会返回研究员重新收集信息
    """)


def main():
    """主函数"""
    print("="*80)
    print("研究助手图结构可视化")
    print("="*80)
    
    # 打印文字描述
    print_graph_description()
    
    # 生成可视化文件
    print("\n" + "="*80)
    print("生成Mermaid图文件")
    print("="*80)
    
    visualize_basic_graph()
    visualize_human_review_graph()
    
    print("\n" + "="*80)
    print("完成!")
    print("="*80)
    print("\n提示: 可以使用Mermaid在线编辑器查看生成的.mmd文件")
    print("在线编辑器: https://mermaid.live/")


if __name__ == "__main__":
    main()

