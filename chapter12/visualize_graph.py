"""
可视化图结构
生成智能体工作流的Mermaid图
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from wuhan_travel_agent import create_travel_agent


def generate_mermaid():
    """生成Mermaid图"""
    print("生成智能体工作流图...")
    
    agent = create_travel_agent()
    
    # 获取Mermaid图
    mermaid_code = agent.get_graph().draw_mermaid()
    
    # 保存到文件
    output_file = "wuhan_travel_agent_graph.mmd"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    
    print(f"Mermaid图已保存到: {output_file}")
    print("\n图结构:")
    print("=" * 80)
    print(mermaid_code)
    print("=" * 80)
    
    return mermaid_code


def print_graph_info():
    """打印图的基本信息"""
    agent = create_travel_agent()
    graph = agent.get_graph()
    
    print("\n图的基本信息:")
    print("=" * 80)
    print(f"节点数量: {len(graph.nodes)}")
    print(f"节点列表: {list(graph.nodes.keys())}")
    print("\n边的连接:")
    for node, edges in graph.nodes.items():
        print(f"  {node}:")
        if hasattr(edges, 'edges'):
            for edge in edges.edges:
                print(f"    -> {edge}")
    print("=" * 80)


if __name__ == "__main__":
    generate_mermaid()
    print_graph_info()

