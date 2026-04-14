"""
第2章：智能体评估演示

这个模块演示了如何评估智能体的性能。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum
import random


class TaskStatus(Enum):
    """任务状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class EvaluationMetric:
    """评估指标"""
    
    name: str
    value: float
    weight: float = 1.0
    description: str = ""
    
    def __str__(self) -> str:
        return f"{self.name}: {self.value:.2%} (权重: {self.weight})"


@dataclass
class TaskResult:
    """任务结果"""
    
    task_id: str
    task_description: str
    status: TaskStatus
    accuracy: float
    completion_time: float
    tool_calls: int
    cost: float
    hallucination_detected: bool = False
    
    def __str__(self) -> str:
        return f"任务{self.task_id}: {self.task_description}\n  状态: {self.status.value}\n  准确性: {self.accuracy:.2%}\n  耗时: {self.completion_time:.2f}s\n  工具调用: {self.tool_calls}\n  成本: ${self.cost:.2f}"


class TaskCompletionEvaluator:
    """任务完成率评估器"""
    
    def __init__(self):
        self.results: List[TaskResult] = []
    
    def add_result(self, result: TaskResult) -> None:
        """添加任务结果"""
        self.results.append(result)
    
    def calculate_completion_rate(self) -> float:
        """计算任务完成率"""
        if not self.results:
            return 0.0
        
        successful = sum(1 for r in self.results if r.status == TaskStatus.SUCCESS)
        return successful / len(self.results)
    
    def calculate_quality_score(self) -> float:
        """计算质量分数"""
        if not self.results:
            return 0.0
        
        # 综合考虑准确性、完成时间和成本
        scores = []
        for result in self.results:
            # 准确性权重50%
            accuracy_score = result.accuracy * 0.5
            
            # 效率权重30%（完成时间越短越好）
            efficiency_score = max(0, 1 - result.completion_time / 100) * 0.3
            
            # 成本权重20%（成本越低越好）
            cost_score = max(0, 1 - result.cost / 10) * 0.2
            
            scores.append(accuracy_score + efficiency_score + cost_score)
        
        return sum(scores) / len(scores)
    
    def get_metrics(self) -> List[EvaluationMetric]:
        """获取评估指标"""
        metrics = [
            EvaluationMetric(
                name="任务完成率",
                value=self.calculate_completion_rate(),
                weight=0.4,
                description="成功完成的任务比例"
            ),
            EvaluationMetric(
                name="质量分数",
                value=self.calculate_quality_score(),
                weight=0.6,
                description="综合质量评分"
            )
        ]
        return metrics


class HallucinationDetector:
    """幻觉检测器"""
    
    def __init__(self):
        self.known_facts = {
            "Python": "编程语言",
            "北京": "中国首都",
            "2024": "年份",
            "LangGraph": "AI框架"
        }
    
    def detect_hallucination(self, output: str) -> bool:
        """检测输出中的幻觉"""
        # 简单的幻觉检测：检查是否包含虚构的事实
        suspicious_patterns = [
            "根据我的知识",
            "我记得",
            "据我所知",
            "我相信"
        ]
        
        for pattern in suspicious_patterns:
            if pattern in output:
                return True
        
        return False
    
    def verify_facts(self, output: str) -> Dict[str, bool]:
        """验证输出中的事实"""
        verified = {}
        for fact, definition in self.known_facts.items():
            if fact in output:
                verified[fact] = True
            else:
                verified[fact] = False
        
        return verified


class RobustnessEvaluator:
    """鲁棒性评估器"""
    
    def __init__(self):
        self.test_cases = [
            {"name": "正常输入", "input": "正常的用户查询"},
            {"name": "边界情况", "input": ""},
            {"name": "长输入", "input": "a" * 1000},
            {"name": "特殊字符", "input": "!@#$%^&*()"},
            {"name": "多语言", "input": "Hello 你好 مرحبا"}
        ]
    
    def test_robustness(self, agent_func) -> Dict[str, Any]:
        """测试鲁棒性"""
        results = {
            "total_tests": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for test_case in self.test_cases:
            try:
                # 模拟智能体处理
                output = agent_func(test_case["input"])
                results["passed"] += 1
                results["details"].append({
                    "test": test_case["name"],
                    "status": "passed",
                    "output": output[:50] + "..." if len(output) > 50 else output
                })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "test": test_case["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        results["pass_rate"] = results["passed"] / results["total_tests"]
        return results


class AgentEvaluator:
    """智能体评估器：综合评估"""
    
    def __init__(self):
        self.completion_evaluator = TaskCompletionEvaluator()
        self.hallucination_detector = HallucinationDetector()
        self.robustness_evaluator = RobustnessEvaluator()
        self.overall_score = 0.0
    
    def evaluate_agent(self, task_results: List[TaskResult], agent_func=None) -> Dict[str, Any]:
        """评估智能体"""
        print("\n=== 智能体评估报告 ===\n")
        
        # 1. 任务完成率评估
        print("【1. 任务完成率评估】")
        for result in task_results:
            self.completion_evaluator.add_result(result)
        
        completion_rate = self.completion_evaluator.calculate_completion_rate()
        quality_score = self.completion_evaluator.calculate_quality_score()
        
        print(f"  任务完成率: {completion_rate:.2%}")
        print(f"  质量分数: {quality_score:.2%}")
        
        # 2. 幻觉控制评估
        print("\n【2. 幻觉控制评估】")
        hallucination_count = sum(1 for r in task_results if r.hallucination_detected)
        hallucination_rate = hallucination_count / len(task_results) if task_results else 0
        
        print(f"  检测到幻觉: {hallucination_count}/{len(task_results)}")
        print(f"  幻觉率: {hallucination_rate:.2%}")
        
        # 3. 鲁棒性评估
        print("\n【3. 鲁棒性评估】")
        if agent_func:
            robustness_results = self.robustness_evaluator.test_robustness(agent_func)
            print(f"  通过测试: {robustness_results['passed']}/{robustness_results['total_tests']}")
            print(f"  通过率: {robustness_results['pass_rate']:.2%}")
            
            for detail in robustness_results['details']:
                status_icon = "✓" if detail['status'] == 'passed' else "✗"
                print(f"    {status_icon} {detail['test']}")
        
        # 4. 效率评估
        print("\n【4. 效率评估】")
        avg_time = sum(r.completion_time for r in task_results) / len(task_results) if task_results else 0
        avg_cost = sum(r.cost for r in task_results) / len(task_results) if task_results else 0
        avg_tool_calls = sum(r.tool_calls for r in task_results) / len(task_results) if task_results else 0
        
        print(f"  平均耗时: {avg_time:.2f}s")
        print(f"  平均成本: ${avg_cost:.2f}")
        print(f"  平均工具调用数: {avg_tool_calls:.1f}")
        
        # 5. 综合评分
        print("\n【5. 综合评分】")
        
        # 计算综合分数（0-100）
        score_components = {
            "任务完成率": completion_rate * 40,
            "质量分数": quality_score * 30,
            "幻觉控制": (1 - hallucination_rate) * 20,
            "鲁棒性": (robustness_results['pass_rate'] * 10 if agent_func else 10)
        }
        
        self.overall_score = sum(score_components.values())
        
        for component, score in score_components.items():
            print(f"  {component}: {score:.1f}")
        
        print(f"\n  综合评分: {self.overall_score:.1f}/100")
        
        # 评级
        if self.overall_score >= 90:
            rating = "优秀"
        elif self.overall_score >= 75:
            rating = "良好"
        elif self.overall_score >= 60:
            rating = "及格"
        else:
            rating = "需要改进"
        
        print(f"  评级: {rating}")
        
        return {
            "completion_rate": completion_rate,
            "quality_score": quality_score,
            "hallucination_rate": hallucination_rate,
            "overall_score": self.overall_score,
            "rating": rating
        }


def mock_agent_function(input_text: str) -> str:
    """模拟智能体函数"""
    if not input_text:
        raise ValueError("输入不能为空")
    
    return f"处理了输入: {input_text[:20]}..."


def main():
    """主函数：演示智能体评估"""
    
    # 创建模拟任务结果
    task_results = [
        TaskResult(
            task_id="T001",
            task_description="查询天气信息",
            status=TaskStatus.SUCCESS,
            accuracy=0.95,
            completion_time=2.5,
            tool_calls=2,
            cost=0.05
        ),
        TaskResult(
            task_id="T002",
            task_description="生成报告摘要",
            status=TaskStatus.SUCCESS,
            accuracy=0.88,
            completion_time=5.2,
            tool_calls=3,
            cost=0.08
        ),
        TaskResult(
            task_id="T003",
            task_description="数据分析",
            status=TaskStatus.PARTIAL,
            accuracy=0.72,
            completion_time=8.1,
            tool_calls=5,
            cost=0.12,
            hallucination_detected=True
        ),
        TaskResult(
            task_id="T004",
            task_description="代码生成",
            status=TaskStatus.SUCCESS,
            accuracy=0.91,
            completion_time=3.8,
            tool_calls=2,
            cost=0.06
        ),
        TaskResult(
            task_id="T005",
            task_description="文本翻译",
            status=TaskStatus.FAILURE,
            accuracy=0.45,
            completion_time=2.0,
            tool_calls=1,
            cost=0.03
        )
    ]
    
    # 创建评估器并评估
    evaluator = AgentEvaluator()
    results = evaluator.evaluate_agent(task_results, mock_agent_function)
    
    print("\n" + "="*60)
    print("评估完成")
    print("="*60)


if __name__ == "__main__":
    main()

