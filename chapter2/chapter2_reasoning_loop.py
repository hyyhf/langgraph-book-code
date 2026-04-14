"""
第2章：推理循环演示

这个模块演示了Chain-of-Thought和Self-Reflection的推理循环。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class ReflectionType(Enum):
    """反思类型"""
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"


@dataclass
class ReasoningStep:
    """推理步骤"""
    
    step_number: int
    description: str
    reasoning: str
    conclusion: str
    confidence: float = 0.5
    
    def __str__(self) -> str:
        return f"步骤{self.step_number}: {self.description}\n  推理: {self.reasoning}\n  结论: {self.conclusion}\n  置信度: {self.confidence:.2f}"


@dataclass
class ReflectionResult:
    """反思结果"""
    
    reflection_type: ReflectionType
    is_correct: bool
    issues_found: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        result = f"反思类型: {self.reflection_type.value}\n"
        result += f"  是否正确: {'是' if self.is_correct else '否'}\n"
        if self.issues_found:
            result += f"  发现的问题: {', '.join(self.issues_found)}\n"
        if self.suggestions:
            result += f"  建议: {', '.join(self.suggestions)}\n"
        return result


class ChainOfThought:
    """思维链：显式推理过程"""
    
    def __init__(self, problem: str):
        self.problem = problem
        self.steps: List[ReasoningStep] = []
        self.final_answer = None
    
    def add_step(self, description: str, reasoning: str, conclusion: str, confidence: float = 0.5) -> None:
        """添加推理步骤"""
        step = ReasoningStep(
            step_number=len(self.steps) + 1,
            description=description,
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=confidence
        )
        self.steps.append(step)
    
    def solve_math_problem(self, problem: str) -> None:
        """解决数学问题的示例"""
        self.problem = problem
        
        if "概率" in problem:
            self.add_step(
                description="理解问题",
                reasoning="问题要求计算从盒子中随机取出红球的概率",
                conclusion="这是一个基础概率问题",
                confidence=0.95
            )
            
            self.add_step(
                description="计算总数",
                reasoning="盒子中有3个红球和5个蓝球，总共8个球",
                conclusion="总球数 = 3 + 5 = 8",
                confidence=0.99
            )
            
            self.add_step(
                description="计算有利结果",
                reasoning="红球的数量就是有利结果的数量",
                conclusion="红球数 = 3",
                confidence=0.99
            )
            
            self.add_step(
                description="计算概率",
                reasoning="概率 = 有利结果数 / 总结果数",
                conclusion="概率 = 3/8 = 0.375 = 37.5%",
                confidence=0.98
            )
            
            self.final_answer = "3/8 或 37.5%"
    
    def solve_logic_problem(self, problem: str) -> None:
        """解决逻辑问题的示例"""
        self.problem = problem
        
        if "推理" in problem:
            self.add_step(
                description="分析前提",
                reasoning="题目给出了几个逻辑前提，需要推导结论",
                conclusion="已识别所有前提条件",
                confidence=0.9
            )
            
            self.add_step(
                description="应用逻辑规则",
                reasoning="使用演绎推理，从一般到特殊",
                conclusion="可以推导出中间结论",
                confidence=0.85
            )
            
            self.add_step(
                description="得出最终结论",
                reasoning="综合所有推理步骤",
                conclusion="最终答案是...",
                confidence=0.8
            )
            
            self.final_answer = "逻辑推导完成"
    
    def display_reasoning(self) -> None:
        """显示完整的推理过程"""
        print(f"\n=== 思维链推理过程 ===")
        print(f"问题: {self.problem}\n")
        
        for step in self.steps:
            print(step)
            print()
        
        print(f"最终答案: {self.final_answer}")
        
        # 计算平均置信度
        avg_confidence = sum(s.confidence for s in self.steps) / len(self.steps) if self.steps else 0
        print(f"平均置信度: {avg_confidence:.2f}")


class SelfReflection:
    """自我反思：评估和改进推理"""
    
    def __init__(self, reasoning_chain: ChainOfThought):
        self.reasoning_chain = reasoning_chain
        self.reflections: List[ReflectionResult] = []
        self.improvements: List[str] = []
    
    def reflect_on_correctness(self) -> ReflectionResult:
        """反思推理的正确性"""
        result = ReflectionResult(
            reflection_type=ReflectionType.CORRECTNESS,
            is_correct=True
        )
        
        # 检查每个步骤
        for step in self.reasoning_chain.steps:
            if step.confidence < 0.7:
                result.is_correct = False
                result.issues_found.append(f"步骤{step.step_number}的置信度过低")
                result.suggestions.append(f"重新审视步骤{step.step_number}的推理")
        
        self.reflections.append(result)
        return result
    
    def reflect_on_completeness(self) -> ReflectionResult:
        """反思推理的完整性"""
        result = ReflectionResult(
            reflection_type=ReflectionType.COMPLETENESS,
            is_correct=len(self.reasoning_chain.steps) >= 3
        )
        
        if len(self.reasoning_chain.steps) < 3:
            result.issues_found.append("推理步骤不足")
            result.suggestions.append("添加更多中间步骤以完整展示推理过程")
        
        self.reflections.append(result)
        return result
    
    def reflect_on_efficiency(self) -> ReflectionResult:
        """反思推理的效率"""
        result = ReflectionResult(
            reflection_type=ReflectionType.EFFICIENCY,
            is_correct=len(self.reasoning_chain.steps) <= 5
        )
        
        if len(self.reasoning_chain.steps) > 5:
            result.issues_found.append("推理步骤过多")
            result.suggestions.append("尝试合并相关步骤以提高效率")
        
        self.reflections.append(result)
        return result
    
    def reflect_on_quality(self) -> ReflectionResult:
        """反思推理的质量"""
        avg_confidence = sum(s.confidence for s in self.reasoning_chain.steps) / len(self.reasoning_chain.steps) if self.reasoning_chain.steps else 0
        
        result = ReflectionResult(
            reflection_type=ReflectionType.QUALITY,
            is_correct=avg_confidence >= 0.8
        )
        
        if avg_confidence < 0.8:
            result.issues_found.append(f"平均置信度较低: {avg_confidence:.2f}")
            result.suggestions.append("增加更多验证步骤")
        
        self.reflections.append(result)
        return result
    
    def perform_full_reflection(self) -> None:
        """执行完整的反思"""
        print(f"\n=== 自我反思过程 ===\n")
        
        # 执行所有反思
        self.reflect_on_correctness()
        self.reflect_on_completeness()
        self.reflect_on_efficiency()
        self.reflect_on_quality()
        
        # 显示反思结果
        for reflection in self.reflections:
            print(reflection)
        
        # 生成改进建议
        print("\n=== 改进建议 ===")
        all_suggestions = set()
        for reflection in self.reflections:
            all_suggestions.update(reflection.suggestions)
        
        for i, suggestion in enumerate(all_suggestions, 1):
            print(f"{i}. {suggestion}")
    
    def should_revise(self) -> bool:
        """判断是否需要修改推理"""
        for reflection in self.reflections:
            if not reflection.is_correct:
                return True
        return False


class ReasoningLoop:
    """推理循环：结合CoT和Self-Reflection"""
    
    def __init__(self, problem: str):
        self.problem = problem
        self.iteration = 0
        self.max_iterations = 3
    
    def run(self) -> None:
        """运行推理循环"""
        print(f"\n{'='*50}")
        print(f"推理循环开始")
        print(f"问题: {self.problem}")
        print(f"{'='*50}")
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n--- 迭代 {self.iteration} ---")
            
            # 第一步：思维链推理
            cot = ChainOfThought(self.problem)
            cot.solve_math_problem(self.problem)
            cot.display_reasoning()
            
            # 第二步：自我反思
            reflection = SelfReflection(cot)
            reflection.perform_full_reflection()
            
            # 第三步：判断是否需要继续
            if not reflection.should_revise():
                print(f"\n✓ 推理已收敛，无需进一步修改")
                break
            else:
                print(f"\n✗ 需要进一步改进，继续迭代...")
        
        print(f"\n推理循环完成（共{self.iteration}次迭代）")


def main():
    """主函数：演示推理循环"""
    
    # 示例1：数学问题
    print("\n" + "="*60)
    print("示例1：数学概率问题")
    print("="*60)
    
    loop1 = ReasoningLoop("一个盒子里有3个红球和5个蓝球，随机取出一个球，它是红球的概率是多少？")
    loop1.run()
    
    # 示例2：简单的逻辑问题
    print("\n" + "="*60)
    print("示例2：逻辑推理问题")
    print("="*60)
    
    cot2 = ChainOfThought("如果所有人都是凡人，而苏格拉底是人，那么苏格拉底是凡人吗？")
    cot2.solve_logic_problem(cot2.problem)
    cot2.display_reasoning()
    
    reflection2 = SelfReflection(cot2)
    reflection2.perform_full_reflection()


if __name__ == "__main__":
    main()

