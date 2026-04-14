"""
主程序 - 运行自动化研究助手

这个文件演示如何使用研究助手进行完整的研究流程
"""

from research_agent import create_research_agent
from research_agent.utils.state import ResearchState


def run_basic_research():
    """
    示例1: 基础研究流程(不包含人工审核)
    """
    print("\n" + "="*80)
    print("示例1: 基础研究流程")
    print("="*80)
    
    # 创建不包含人工审核的研究助手
    graph = create_research_agent(with_human_review=False)
    
    # 定义研究主题(使用武汉元素)
    topic = "武汉热干面的历史与文化"
    
    print(f"\n研究主题: {topic}\n")
    
    # 初始化状态
    initial_state: ResearchState = {
        "messages": [],
        "topic": topic,
        "research_data": "",
        "analysis_result": "",
        "final_report": "",
        "current_stage": "init",
        "human_approved": False
    }
    
    # 配置(用于状态持久化)
    config = {"configurable": {"thread_id": "basic_research_001"}}
    
    # 执行研究流程
    print("开始执行研究流程...\n")
    result = graph.invoke(initial_state, config)
    
    # 输出最终结果
    print("\n" + "="*80)
    print("研究流程完成!")
    print("="*80)
    print(f"\n当前阶段: {result['current_stage']}")
    print(f"消息数量: {len(result['messages'])}")
    
    return result


def run_research_with_human_review():
    """
    示例2: 包含人工审核的研究流程
    """
    print("\n" + "="*80)
    print("示例2: 包含人工审核的研究流程")
    print("="*80)
    
    # 创建包含人工审核的研究助手
    graph = create_research_agent(with_human_review=True)
    
    # 定义研究主题
    topic = "武汉长江大桥的建设历程"
    
    print(f"\n研究主题: {topic}\n")
    
    # 初始化状态
    initial_state: ResearchState = {
        "messages": [],
        "topic": topic,
        "research_data": "",
        "analysis_result": "",
        "final_report": "",
        "current_stage": "init",
        "human_approved": False
    }
    
    # 配置
    config = {"configurable": {"thread_id": "human_review_research_001"}}
    
    # 第一阶段: 执行到人工审核前
    print("【第一阶段】执行到人工审核节点...\n")
    result = graph.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("图已在人工审核节点前暂停")
    print("="*80)
    print(f"\n当前阶段: {result['current_stage']}")
    
    # 模拟人工审核
    print("\n【模拟人工审核】")
    print("假设人工审核通过...")
    
    # 第二阶段: 继续执行
    print("\n【第二阶段】继续执行...\n")
    result = graph.invoke(
        {"human_approved": True},
        config
    )
    
    print("\n" + "="*80)
    print("研究流程完成!")
    print("="*80)
    print(f"\n当前阶段: {result['current_stage']}")
    
    return result


def run_streaming_research():
    """
    示例3: 使用流式模式观察执行过程
    """
    print("\n" + "="*80)
    print("示例3: 流式模式观察执行过程")
    print("="*80)
    
    # 创建研究助手(不包含人工审核,便于演示)
    graph = create_research_agent(with_human_review=False)
    
    # 定义研究主题
    topic = "武汉黄鹤楼的诗词文化"
    
    print(f"\n研究主题: {topic}\n")
    
    # 初始化状态
    initial_state: ResearchState = {
        "messages": [],
        "topic": topic,
        "research_data": "",
        "analysis_result": "",
        "final_report": "",
        "current_stage": "init",
        "human_approved": False
    }
    
    # 配置
    config = {"configurable": {"thread_id": "streaming_research_001"}}
    
    print("使用stream模式执行,可以观察每个节点的输出...\n")
    print("-"*80)
    
    # 使用stream方法
    for i, chunk in enumerate(graph.stream(initial_state, config), 1):
        print(f"\n步骤 {i}:")
        for node_name, output in chunk.items():
            print(f"  节点: {node_name}")
            if "current_stage" in output:
                print(f"  阶段: {output['current_stage']}")
    
    print("\n" + "-"*80)
    print("\n流式执行完成!")
    
    # 获取最终状态
    final_state = graph.get_state(config)
    return final_state.values


def main():
    """
    主函数 - 运行所有示例
    """
    print("\n" + "="*80)
    print("自动化研究助手 - 完整演示")
    print("一个简易版的Deep Research智能体")
    print("="*80)
    
    # 选择要运行的示例
    print("\n请选择要运行的示例:")
    print("1. 基础研究流程(不包含人工审核)")
    print("2. 包含人工审核的研究流程")
    print("3. 流式模式观察执行过程")
    print("4. 运行所有示例")
    
    choice = input("\n请输入选项(1-4): ").strip()
    
    if choice == "1":
        run_basic_research()
    elif choice == "2":
        run_research_with_human_review()
    elif choice == "3":
        run_streaming_research()
    elif choice == "4":
        print("\n运行所有示例...\n")
        run_basic_research()
        print("\n" + "="*80 + "\n")
        run_research_with_human_review()
        print("\n" + "="*80 + "\n")
        run_streaming_research()
    else:
        print("\n无效的选项,默认运行示例1")
        run_basic_research()
    
    print("\n" + "="*80)
    print("演示完成!")
    print("="*80)


if __name__ == "__main__":
    main()

