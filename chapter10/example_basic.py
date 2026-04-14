"""
基础示例 - 快速开始

这是一个最简单的示例,展示如何使用研究助手
"""

from research_agent import create_research_agent
from research_agent.utils.state import ResearchState


def main():
    """运行基础研究示例"""
    
    print("="*80)
    print("自动化研究助手 - 基础示例")
    print("="*80)
    
    # 1. 创建研究助手(不包含人工审核)
    graph = create_research_agent(with_human_review=False)
    
    # 2. 定义研究主题
    topic = "武汉热干面的历史与文化"
    print(f"\n研究主题: {topic}\n")
    
    # 3. 初始化状态
    initial_state: ResearchState = {
        "messages": [],
        "topic": topic,
        "research_data": "",
        "analysis_result": "",
        "final_report": "",
        "current_stage": "init",
        "human_approved": False
    }
    
    # 4. 配置线程ID(用于状态持久化)
    config = {"configurable": {"thread_id": "example_001"}}
    
    # 5. 执行研究流程
    print("开始执行研究流程...\n")
    result = graph.invoke(initial_state, config)
    
    # 6. 查看结果
    print("\n" + "="*80)
    print("研究完成!")
    print("="*80)
    print(f"\n最终阶段: {result['current_stage']}")
    print(f"\n最终报告已生成,长度: {len(result['final_report'])} 字符")
    
    # 7. 保存报告到文件
    output_file = "research_report.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"研究主题: {topic}\n")
        f.write("="*80 + "\n\n")
        f.write(result['final_report'])

    print(f"\n报告已保存到: {output_file}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

