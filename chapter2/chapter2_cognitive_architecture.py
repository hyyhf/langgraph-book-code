"""
第2章：认知架构四要素演示

这个模块演示了智能体的核心机制：感知-规划-记忆-行动循环。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum


class ActionType(Enum):
    """行动类型枚举"""
    SEARCH = "search"
    RETRIEVE = "retrieve"
    ANALYZE = "analyze"
    RESPOND = "respond"


@dataclass
class Perception:
    """感知阶段：理解环境和输入"""
    
    user_input: str
    context: Dict[str, Any] = field(default_factory=dict)
    extracted_intent: str = ""
    identified_entities: List[str] = field(default_factory=list)
    
    def process(self) -> None:
        """处理输入，提取意图和实体"""
        # 简单的意图识别
        if "天气" in self.user_input:
            self.extracted_intent = "weather_query"
        elif "订单" in self.user_input:
            self.extracted_intent = "order_query"
        else:
            self.extracted_intent = "general_query"
        
        # 简单的实体提取
        if "北京" in self.user_input:
            self.identified_entities.append("location:beijing")
        if "着急" in self.user_input or "紧急" in self.user_input:
            self.identified_entities.append("urgency:high")
    
    def __str__(self) -> str:
        return f"Perception(intent={self.extracted_intent}, entities={self.identified_entities})"


@dataclass
class Plan:
    """规划阶段：制定行动计划"""
    
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    
    def add_step(self, action_type: ActionType, parameters: Dict[str, Any]) -> None:
        """添加一个规划步骤"""
        self.steps.append({
            "action": action_type,
            "parameters": parameters
        })
    
    def get_next_step(self) -> Dict[str, Any] | None:
        """获取下一个步骤"""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def advance(self) -> None:
        """推进到下一个步骤"""
        self.current_step += 1
    
    def __str__(self) -> str:
        return f"Plan(steps={len(self.steps)}, current={self.current_step})"


@dataclass
class Memory:
    """记忆系统：维护短期和长期记忆"""
    
    short_term: List[str] = field(default_factory=list)
    long_term: Dict[str, Any] = field(default_factory=dict)
    max_short_term_size: int = 10
    
    def add_short_term(self, item: str) -> None:
        """添加到短期记忆"""
        self.short_term.append(item)
        # 保持短期记忆的大小限制
        if len(self.short_term) > self.max_short_term_size:
            self.short_term.pop(0)
    
    def add_long_term(self, key: str, value: Any) -> None:
        """添加到长期记忆"""
        self.long_term[key] = value
    
    def retrieve(self, key: str) -> Any | None:
        """从长期记忆中检索"""
        return self.long_term.get(key)
    
    def get_context(self) -> str:
        """获取当前的记忆上下文"""
        context = "短期记忆: " + ", ".join(self.short_term[-3:])
        return context
    
    def __str__(self) -> str:
        return f"Memory(short_term={len(self.short_term)}, long_term={len(self.long_term)})"


@dataclass
class Action:
    """行动阶段：执行计划中的步骤"""
    
    action_type: ActionType
    parameters: Dict[str, Any]
    result: Any = None
    success: bool = False
    
    def execute(self) -> None:
        """执行行动"""
        if self.action_type == ActionType.SEARCH:
            self.result = self._execute_search()
        elif self.action_type == ActionType.RETRIEVE:
            self.result = self._execute_retrieve()
        elif self.action_type == ActionType.ANALYZE:
            self.result = self._execute_analyze()
        elif self.action_type == ActionType.RESPOND:
            self.result = self._execute_respond()
        
        self.success = self.result is not None
    
    def _execute_search(self) -> str:
        """模拟搜索操作"""
        query = self.parameters.get("query", "")
        return f"搜索结果: 找到关于'{query}'的10条结果"
    
    def _execute_retrieve(self) -> str:
        """模拟检索操作"""
        key = self.parameters.get("key", "")
        return f"检索结果: 获取了'{key}'的数据"
    
    def _execute_analyze(self) -> str:
        """模拟分析操作"""
        data = self.parameters.get("data", "")
        return f"分析结果: 数据'{data}'已分析"
    
    def _execute_respond(self) -> str:
        """模拟响应操作"""
        message = self.parameters.get("message", "")
        return f"响应: {message}"
    
    def __str__(self) -> str:
        return f"Action({self.action_type.value}, success={self.success})"


class CognitiveAgent:
    """认知架构智能体：演示PPAM循环"""
    
    def __init__(self):
        self.perception = None
        self.plan = None
        self.memory = Memory()
        self.actions_executed = []
    
    def run(self, user_input: str) -> str:
        """运行智能体的完整循环"""
        print(f"\n=== 智能体循环开始 ===")
        print(f"用户输入: {user_input}\n")
        
        # 1. 感知阶段
        print("【感知阶段】")
        self.perception = Perception(user_input=user_input)
        self.perception.process()
        print(f"  意图识别: {self.perception.extracted_intent}")
        print(f"  实体提取: {self.perception.identified_entities}")
        self.memory.add_short_term(f"用户输入: {user_input}")
        
        # 2. 规划阶段
        print("\n【规划阶段】")
        self.plan = Plan()
        self._create_plan()
        print(f"  规划步骤数: {len(self.plan.steps)}")
        for i, step in enumerate(self.plan.steps):
            print(f"    步骤{i+1}: {step['action'].value}")
        
        # 3. 行动阶段
        print("\n【行动阶段】")
        while self.plan.get_next_step() is not None:
            step = self.plan.get_next_step()
            action = Action(
                action_type=step['action'],
                parameters=step['parameters']
            )
            action.execute()
            self.actions_executed.append(action)
            print(f"  执行: {action.action_type.value}")
            print(f"    结果: {action.result}")
            self.memory.add_short_term(f"行动结果: {action.result}")
            self.plan.advance()
        
        # 4. 记忆更新
        print("\n【记忆更新】")
        self.memory.add_long_term(
            f"session_{len(self.memory.long_term)}",
            {
                "input": user_input,
                "intent": self.perception.extracted_intent,
                "actions": len(self.actions_executed)
            }
        )
        print(f"  已保存到长期记忆")
        print(f"  当前记忆状态: {self.memory}")
        
        # 生成最终响应
        response = self._generate_response()
        print(f"\n【最终响应】")
        print(f"  {response}")
        
        return response
    
    def _create_plan(self) -> None:
        """根据感知结果创建计划"""
        if self.perception.extracted_intent == "weather_query":
            self.plan.add_step(ActionType.SEARCH, {"query": "天气信息"})
            self.plan.add_step(ActionType.ANALYZE, {"data": "天气数据"})
        elif self.perception.extracted_intent == "order_query":
            self.plan.add_step(ActionType.RETRIEVE, {"key": "订单信息"})
            self.plan.add_step(ActionType.ANALYZE, {"data": "订单状态"})
        else:
            self.plan.add_step(ActionType.SEARCH, {"query": "通用信息"})
        
        self.plan.add_step(ActionType.RESPOND, {"message": "已完成处理"})
    
    def _generate_response(self) -> str:
        """生成最终响应"""
        if self.perception.extracted_intent == "weather_query":
            return "根据搜索结果，今天的天气信息已为您查询。"
        elif self.perception.extracted_intent == "order_query":
            urgency = "urgency:high" in self.perception.identified_entities
            if urgency:
                return "您的订单已被标记为紧急处理，我们会优先处理。"
            else:
                return "您的订单信息已检索，正在为您分析。"
        else:
            return "已为您处理请求。"


def main():
    """主函数：演示认知架构"""
    agent = CognitiveAgent()
    
    # 测试用例1：天气查询
    agent.run("北京今天的天气怎么样？")
    
    # 测试用例2：订单查询（紧急）
    agent.run("我的订单还没有收到，我很着急。")
    
    # 测试用例3：通用查询
    agent.run("告诉我关于Python的信息")


if __name__ == "__main__":
    main()

