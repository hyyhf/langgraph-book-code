"""
测试脚本 - 验证所有功能

这个脚本会测试研究助手的所有核心功能
"""

from research_agent import create_research_agent
from research_agent.utils.state import ResearchState


def test_basic_workflow():
    """测试1: 基础工作流"""
    print("\n" + "="*80)
    print("测试1: 基础工作流")
    print("="*80)
    
    try:
        graph = create_research_agent(with_human_review=False)
        
        initial_state: ResearchState = {
            "messages": [],
            "topic": "武汉热干面",
            "research_data": "",
            "analysis_result": "",
            "final_report": "",
            "current_stage": "init",
            "human_approved": False
        }
        
        config = {"configurable": {"thread_id": "test_001"}}
        
        print("执行基础工作流...")
        result = graph.invoke(initial_state, config)
        
        # 验证结果
        assert result["current_stage"] == "complete", "工作流未完成"
        assert len(result["final_report"]) > 0, "未生成报告"
        
        print("✅ 测试通过: 基础工作流正常")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_streaming():
    """测试2: 流式输出"""
    print("\n" + "="*80)
    print("测试2: 流式输出")
    print("="*80)
    
    try:
        graph = create_research_agent(with_human_review=False)
        
        initial_state: ResearchState = {
            "messages": [],
            "topic": "武汉长江大桥",
            "research_data": "",
            "analysis_result": "",
            "final_report": "",
            "current_stage": "init",
            "human_approved": False
        }
        
        config = {"configurable": {"thread_id": "test_002"}}
        
        print("测试流式输出...")
        chunk_count = 0
        for chunk in graph.stream(initial_state, config):
            chunk_count += 1
            print(f"  收到chunk {chunk_count}: {list(chunk.keys())}")
        
        assert chunk_count > 0, "未收到任何chunk"
        
        print(f"测试通过: 流式输出正常 (共{chunk_count}个chunk)")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_state_persistence():
    """测试3: 状态持久化"""
    print("\n" + "="*80)
    print("测试3: 状态持久化")
    print("="*80)
    
    try:
        graph = create_research_agent(with_human_review=False)
        
        initial_state: ResearchState = {
            "messages": [],
            "topic": "武汉黄鹤楼",
            "research_data": "",
            "analysis_result": "",
            "final_report": "",
            "current_stage": "init",
            "human_approved": False
        }
        
        config = {"configurable": {"thread_id": "test_003"}}
        
        print("执行工作流...")
        result = graph.invoke(initial_state, config)
        
        print("获取保存的状态...")
        saved_state = graph.get_state(config)
        
        assert saved_state is not None, "状态未保存"
        assert saved_state.values["current_stage"] == "complete", "状态不正确"
        
        print("测试通过: 状态持久化正常")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_graph_structure():
    """测试4: 图结构"""
    print("\n" + "="*80)
    print("测试4: 图结构")
    print("="*80)
    
    try:
        # 测试基础图
        graph_basic = create_research_agent(with_human_review=False)
        nodes_basic = graph_basic.get_graph().nodes
        print(f"基础图节点: {list(nodes_basic.keys())}")
        
        assert "researcher" in nodes_basic, "缺少researcher节点"
        assert "analyst" in nodes_basic, "缺少analyst节点"
        assert "reporter" in nodes_basic, "缺少reporter节点"
        
        # 测试包含人工审核的图
        graph_review = create_research_agent(with_human_review=True)
        nodes_review = graph_review.get_graph().nodes
        print(f"完整图节点: {list(nodes_review.keys())}")
        
        assert "human_review" in nodes_review, "缺少human_review节点"
        
        print("测试通过: 图结构正确")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_tools():
    """测试5: 工具调用"""
    print("\n" + "="*80)
    print("测试5: 工具调用")
    print("="*80)
    
    try:
        from research_agent.utils.tools import search_web, analyze_text
        
        # 测试搜索工具
        print("测试search_web工具...")
        result1 = search_web.invoke({"query": "武汉热干面"})
        assert len(result1) > 0, "搜索工具返回空结果"
        print(f"  搜索结果长度: {len(result1)}")
        
        # 测试分析工具
        print("测试analyze_text工具...")
        result2 = analyze_text.invoke({
            "text": "武汉热干面是一种传统美食",
            "focus": "历史"
        })
        assert len(result2) > 0, "分析工具返回空结果"
        print(f"  分析结果长度: {len(result2)}")
        
        print("测试通过: 工具调用正常")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_武汉_elements():
    """测试6: 武汉元素"""
    print("\n" + "="*80)
    print("测试6: 武汉元素")
    print("="*80)

    try:
        from research_agent.utils.tools import search_web

        print("检查武汉元素数据...")

        # 测试不同的武汉元素搜索
        test_queries = [
            "武汉热干面",
            "武汉长江大桥",
            "武汉黄鹤楼",
            "武汉东湖"
        ]

        for query in test_queries:
            result = search_web.invoke({"query": query})
            assert len(result) > 0, f"{query}搜索结果为空"
            assert query in result or "武汉" in result, f"{query}搜索结果不相关"
            print(f"  ✓ {query} - 搜索成功")

        print("测试通过: 武汉元素完整")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("自动化研究助手 - 功能测试")
    print("="*80)
    
    tests = [
        ("基础工作流", test_basic_workflow),
        ("流式输出", test_streaming),
        ("状态持久化", test_state_persistence),
        ("图结构", test_graph_structure),
        ("工具调用", test_tools),
        ("武汉元素", test_武汉_elements),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n测试 '{name}' 发生异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print("\n" + "-"*80)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n 所有测试通过!")
    else:
        print(f"\n 有 {total - passed} 个测试失败")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

