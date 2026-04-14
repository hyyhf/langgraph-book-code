"""
第9章示例8: 状态管理策略
场景: 图书馆管理系统 - 展示共享状态vs私有状态
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from operator import add
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, BaseMessage
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from config import get_llm


# ============================================================================
# 示例1: 共享状态模式
# ============================================================================

class SharedState(TypedDict):
    """共享状态 - 所有智能体都可以访问和修改"""
    messages: Annotated[Sequence[BaseMessage], add]  # 消息历史
    user_id: str  # 用户ID
    borrowed_books: list[str]  # 已借图书
    reserved_books: list[str]  # 已预约图书
    reading_room: str  # 预约的阅览室
    total_operations: int  # 总操作数


@tool
def search_book(title: str):
    """搜索图书"""
    books = {
        "三体": "刘慈欣著,科幻小说,馆藏3本,可借2本",
        "活着": "余华著,当代文学,馆藏5本,可借3本",
        "百年孤独": "马尔克斯著,外国文学,馆藏2本,可借1本"
    }
    return books.get(title, "未找到该图书")


@tool
def borrow_book(title: str):
    """借阅图书"""
    return f"已成功借阅《{title}》,借期30天"


@tool
def reserve_book(title: str):
    """预约图书"""
    return f"已成功预约《{title}》,有书时将通知您"


@tool
def book_reading_room(room: str, date: str):
    """预约阅览室"""
    return f"已预约{room},日期{date}"


def demo_shared_state():
    """演示共享状态模式"""
    
    print("=" * 80)
    print("示例1: 共享状态模式")
    print("=" * 80)
    print("特点: 所有智能体共享同一个状态对象\n")
    
    # 创建智能体
    search_agent = create_agent(
        model=get_llm(),
        tools=[search_book],
        system_prompt="你是图书搜索助手",
        name="search_agent"
    )
    
    borrow_agent = create_agent(
        model=get_llm(),
        tools=[borrow_book, reserve_book],
        system_prompt="你是图书借阅助手",
        name="borrow_agent"
    )
    
    room_agent = create_agent(
        model=get_llm(),
        tools=[book_reading_room],
        system_prompt="你是阅览室预约助手",
        name="room_agent"
    )
    
    # 定义节点 - 更新共享状态
    def search_node(state: SharedState) -> SharedState:
        """搜索节点 - 更新共享状态"""
        print(f"[搜索] 用户{state['user_id']}搜索图书")
        result = search_agent.invoke(state)
        
        return {
            **state,
            "messages": result["messages"],
            "total_operations": state.get("total_operations", 0) + 1
        }
    
    def borrow_node(state: SharedState) -> SharedState:
        """借阅节点 - 更新共享状态"""
        print(f"[借阅] 用户{state['user_id']}借阅图书")
        result = borrow_agent.invoke(state)
        
        # 更新已借图书列表
        borrowed = state.get("borrowed_books", [])
        borrowed.append("三体")  # 简化处理
        
        return {
            **state,
            "messages": result["messages"],
            "borrowed_books": borrowed,
            "total_operations": state.get("total_operations", 0) + 1
        }
    
    def room_node(state: SharedState) -> SharedState:
        """阅览室节点 - 更新共享状态"""
        print(f"[阅览室] 用户{state['user_id']}预约阅览室")
        result = room_agent.invoke(state)
        
        return {
            **state,
            "messages": result["messages"],
            "reading_room": "自习室A",
            "total_operations": state.get("total_operations", 0) + 1
        }
    
    # 构建图
    graph = StateGraph(SharedState)
    graph.add_node("search", search_node)
    graph.add_node("borrow", borrow_node)
    graph.add_node("room", room_node)
    
    graph.add_edge(START, "search")
    graph.add_edge("search", "borrow")
    graph.add_edge("borrow", "room")
    graph.add_edge("room", END)
    
    workflow = graph.compile()
    
    # 测试
    result = workflow.invoke({
        "messages": [HumanMessage(content="我想借《三体》")],
        "user_id": "U001",
        "borrowed_books": [],
        "reserved_books": [],
        "reading_room": "",
        "total_operations": 0
    })
    
    print("\n共享状态最终结果:")
    print(f"- 用户ID: {result['user_id']}")
    print(f"- 已借图书: {result['borrowed_books']}")
    print(f"- 预约阅览室: {result['reading_room']}")
    print(f"- 总操作数: {result['total_operations']}")
    print(f"- 消息数: {len(result['messages'])}")
    
    print("\n共享状态优势:")
    print("✓ 信息透明 - 所有智能体都能看到完整信息")
    print("✓ 实现简单 - 不需要复杂的信息传递")
    print("✓ 易于协调 - 智能体可以了解其他智能体的工作")
    
    print("\n共享状态挑战:")
    print("✗ 上下文膨胀 - 状态会不断增长")
    print("✗ 信息污染 - 不相关信息也会被包含")
    print("✗ 耦合度高 - 修改状态结构影响所有智能体")


# ============================================================================
# 示例2: 私有状态模式(子图)
# ============================================================================

class ParentState(TypedDict):
    """父图状态 - 精简的全局状态"""
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: str
    summary: str  # 只保留摘要信息


class BorrowModuleState(TypedDict):
    """借阅模块私有状态"""
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: str
    borrowed_books: list[str]
    borrow_history: list[dict]  # 借阅历史(私有)
    overdue_count: int  # 逾期次数(私有)


class RoomModuleState(TypedDict):
    """阅览室模块私有状态"""
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: str
    room_reservations: list[dict]  # 预约记录(私有)
    preferred_room: str  # 偏好阅览室(私有)


def demo_private_state():
    """演示私有状态模式"""
    
    print("\n\n" + "=" * 80)
    print("示例2: 私有状态模式(子图)")
    print("=" * 80)
    print("特点: 每个模块有自己的私有状态,通过接口与父图交互\n")
    
    # 创建借阅模块子图
    def create_borrow_module():
        """借阅模块 - 有私有状态"""
        
        def borrow_node(state: BorrowModuleState) -> BorrowModuleState:
            """借阅节点 - 使用模块私有状态"""
            print(f"[借阅模块] 用户{state['user_id']}借书")
            print(f"  私有信息 - 历史借阅: {len(state.get('borrow_history', []))}次")
            print(f"  私有信息 - 逾期次数: {state.get('overdue_count', 0)}次")
            
            # 更新私有状态
            borrowed = state.get("borrowed_books", [])
            borrowed.append("三体")
            
            history = state.get("borrow_history", [])
            history.append({"book": "三体", "date": "2024-01-15"})
            
            return {
                **state,
                "borrowed_books": borrowed,
                "borrow_history": history
            }
        
        graph = StateGraph(BorrowModuleState)
        graph.add_node("borrow", borrow_node)
        graph.add_edge(START, "borrow")
        graph.add_edge("borrow", END)
        
        return graph.compile()
    
    # 创建阅览室模块子图
    def create_room_module():
        """阅览室模块 - 有私有状态"""
        
        def room_node(state: RoomModuleState) -> RoomModuleState:
            """阅览室节点 - 使用模块私有状态"""
            print(f"[阅览室模块] 用户{state['user_id']}预约阅览室")
            print(f"  私有信息 - 历史预约: {len(state.get('room_reservations', []))}次")
            print(f"  私有信息 - 偏好: {state.get('preferred_room', '无')}")
            
            # 更新私有状态
            reservations = state.get("room_reservations", [])
            reservations.append({"room": "自习室A", "date": "2024-01-15"})
            
            return {
                **state,
                "room_reservations": reservations,
                "preferred_room": "自习室A"
            }
        
        graph = StateGraph(RoomModuleState)
        graph.add_node("room", room_node)
        graph.add_edge(START, "room")
        graph.add_edge("room", END)
        
        return graph.compile()
    
    # 创建父图
    borrow_module = create_borrow_module()
    room_module = create_room_module()
    
    def parent_borrow_node(state: ParentState) -> ParentState:
        """父图调用借阅模块 - 状态转换"""
        print("\n[父图] 调用借阅模块")
        
        # 输入转换: 父图状态 -> 子图状态
        module_input = {
            "messages": state["messages"],
            "user_id": state["user_id"],
            "borrowed_books": [],
            "borrow_history": [
                {"book": "活着", "date": "2024-01-01"},
                {"book": "百年孤独", "date": "2024-01-10"}
            ],
            "overdue_count": 1
        }
        
        # 调用子图
        module_result = borrow_module.invoke(module_input)
        
        # 输出转换: 子图状态 -> 父图状态(只提取摘要)
        summary = f"借阅了{len(module_result['borrowed_books'])}本书"
        
        return {
            **state,
            "summary": summary
        }
    
    def parent_room_node(state: ParentState) -> ParentState:
        """父图调用阅览室模块 - 状态转换"""
        print("\n[父图] 调用阅览室模块")
        
        # 输入转换
        module_input = {
            "messages": state["messages"],
            "user_id": state["user_id"],
            "room_reservations": [
                {"room": "自习室B", "date": "2024-01-05"}
            ],
            "preferred_room": "自习室B"
        }
        
        # 调用子图
        module_result = room_module.invoke(module_input)
        
        # 输出转换(只提取摘要)
        summary = state["summary"] + f", 预约了阅览室"
        
        return {
            **state,
            "summary": summary
        }
    
    # 构建父图
    parent_graph = StateGraph(ParentState)
    parent_graph.add_node("borrow_module", parent_borrow_node)
    parent_graph.add_node("room_module", parent_room_node)
    
    parent_graph.add_edge(START, "borrow_module")
    parent_graph.add_edge("borrow_module", "room_module")
    parent_graph.add_edge("room_module", END)
    
    workflow = parent_graph.compile()
    
    # 测试
    result = workflow.invoke({
        "messages": [HumanMessage(content="我要借书和预约阅览室")],
        "user_id": "U001",
        "summary": ""
    })
    
    print("\n\n私有状态最终结果(父图):")
    print(f"- 用户ID: {result['user_id']}")
    print(f"- 摘要: {result['summary']}")
    print(f"- 消息数: {len(result['messages'])}")
    print("\n注意: 子图的私有状态(借阅历史、逾期次数、预约记录等)不会暴露给父图")
    
    print("\n私有状态优势:")
    print("✓ 信息隔离 - 模块内部信息不会污染全局状态")
    print("✓ 控制上下文 - 只传递必要信息,避免膨胀")
    print("✓ 降低耦合 - 模块可以独立修改内部状态")
    print("✓ 提高可维护性 - 模块边界清晰")
    
    print("\n私有状态挑战:")
    print("✗ 需要状态转换 - 父图和子图之间需要映射")
    print("✗ 实现复杂 - 需要精心设计接口")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行状态管理演示"""
    
    print("=" * 80)
    print("第9章示例8: 状态管理策略 - 图书馆管理系统")
    print("=" * 80)
    
    # 演示共享状态
    demo_shared_state()
    
    # 演示私有状态
    demo_private_state()
    
    print("\n\n" + "=" * 80)
    print("状态管理策略总结:")
    print("1. 共享状态 - 适合简单系统,信息需要全局共享")
    print("2. 私有状态 - 适合复杂系统,需要模块化和信息隔离")
    print("3. 混合策略 - 顶层共享核心状态,模块内部使用私有状态")
    print("=" * 80)


if __name__ == "__main__":
    main()

