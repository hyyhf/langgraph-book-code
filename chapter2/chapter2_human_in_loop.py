"""
第2章：人在环路演示

这个模块演示了人工干预在智能体中的作用。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class InterventionType(Enum):
    """干预类型"""
    APPROVAL = "approval"
    REJECTION = "rejection"
    MODIFICATION = "modification"
    GUIDANCE = "guidance"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Decision:
    """智能体的决策"""
    
    decision_id: str
    description: str
    action: str
    risk_level: RiskLevel
    confidence: float
    requires_approval: bool = False
    
    def __str__(self) -> str:
        return f"决策: {self.description}\n  行动: {self.action}\n  风险等级: {self.risk_level.value}\n  置信度: {self.confidence:.2f}"


@dataclass
class HumanIntervention:
    """人工干预"""
    
    intervention_id: str
    decision_id: str
    intervention_type: InterventionType
    reviewer: str
    timestamp: str
    feedback: str
    approved: bool = False
    
    def __str__(self) -> str:
        return f"干预: {self.intervention_type.value}\n  审查者: {self.reviewer}\n  反馈: {self.feedback}\n  批准: {self.approved}"


class DecisionEvaluator:
    """决策评估器：判断是否需要人工干预"""
    
    def __init__(self):
        self.high_risk_actions = ["删除", "修改", "转账", "发送"]
        self.confidence_threshold = 0.7
    
    def evaluate(self, decision: Decision) -> bool:
        """评估决策是否需要人工干预"""
        # 高风险决策需要干预
        if decision.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # 低置信度的决策需要干预
        if decision.confidence < self.confidence_threshold:
            return True
        
        # 包含高风险操作的决策需要干预
        for action in self.high_risk_actions:
            if action in decision.action:
                return True
        
        return False


class HumanInLoopAgent:
    """人在环路智能体"""
    
    def __init__(self):
        self.decisions: List[Decision] = []
        self.interventions: List[HumanIntervention] = []
        self.evaluator = DecisionEvaluator()
        self.decision_counter = 0
        self.intervention_counter = 0
    
    def make_decision(self, description: str, action: str, risk_level: RiskLevel, confidence: float) -> Decision:
        """做出决策"""
        self.decision_counter += 1
        decision = Decision(
            decision_id=f"D{self.decision_counter:03d}",
            description=description,
            action=action,
            risk_level=risk_level,
            confidence=confidence,
            requires_approval=self.evaluator.evaluate(Decision(
                decision_id="",
                description=description,
                action=action,
                risk_level=risk_level,
                confidence=confidence
            ))
        )
        
        self.decisions.append(decision)
        return decision
    
    def process_decision(self, decision: Decision) -> None:
        """处理决策"""
        print(f"\n=== 处理决策 {decision.decision_id} ===\n")
        print(decision)
        
        if decision.requires_approval:
            print(f"\n⚠ 此决策需要人工审查")
            self._request_human_review(decision)
        else:
            print(f"\n✓ 此决策可以自动执行")
            self._execute_decision(decision)
    
    def _request_human_review(self, decision: Decision) -> None:
        """请求人工审查"""
        print(f"\n【请求人工审查】")
        print(f"  决策ID: {decision.decision_id}")
        print(f"  描述: {decision.description}")
        print(f"  建议行动: {decision.action}")
        print(f"  风险等级: {decision.risk_level.value}")
        print(f"  置信度: {decision.confidence:.2f}")
        
        # 模拟人工审查
        print(f"\n【人工审查过程】")
        
        # 这里可以集成实际的人工审查流程
        # 例如：发送通知、等待用户输入等
        
        # 模拟不同的审查结果
        if decision.risk_level == RiskLevel.CRITICAL:
            self._record_intervention(
                decision.decision_id,
                InterventionType.REJECTION,
                "安全审查员",
                "此操作风险过高，建议拒绝"
            )
        elif decision.confidence < 0.5:
            self._record_intervention(
                decision.decision_id,
                InterventionType.GUIDANCE,
                "业务专家",
                "建议增加更多验证步骤"
            )
        else:
            self._record_intervention(
                decision.decision_id,
                InterventionType.APPROVAL,
                "审查员",
                "已批准执行"
            )
    
    def _record_intervention(self, decision_id: str, intervention_type: InterventionType, reviewer: str, feedback: str) -> None:
        """记录干预"""
        self.intervention_counter += 1
        intervention = HumanIntervention(
            intervention_id=f"I{self.intervention_counter:03d}",
            decision_id=decision_id,
            intervention_type=intervention_type,
            reviewer=reviewer,
            timestamp=datetime.now().isoformat(),
            feedback=feedback,
            approved=(intervention_type == InterventionType.APPROVAL)
        )
        
        self.interventions.append(intervention)
        
        print(f"\n【干预记录】")
        print(intervention)
        
        # 根据干预类型采取行动
        if intervention_type == InterventionType.APPROVAL:
            self._execute_decision_by_id(decision_id)
        elif intervention_type == InterventionType.REJECTION:
            self._reject_decision_by_id(decision_id)
        elif intervention_type == InterventionType.MODIFICATION:
            self._modify_decision_by_id(decision_id)
        elif intervention_type == InterventionType.GUIDANCE:
            self._provide_guidance_by_id(decision_id)
    
    def _execute_decision(self, decision: Decision) -> None:
        """执行决策"""
        print(f"\n✓ 执行决策: {decision.action}")
    
    def _execute_decision_by_id(self, decision_id: str) -> None:
        """根据ID执行决策"""
        decision = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if decision:
            print(f"\n✓ 已批准，执行决策: {decision.action}")
    
    def _reject_decision_by_id(self, decision_id: str) -> None:
        """根据ID拒绝决策"""
        decision = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if decision:
            print(f"\n✗ 已拒绝，不执行决策: {decision.action}")
    
    def _modify_decision_by_id(self, decision_id: str) -> None:
        """根据ID修改决策"""
        decision = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if decision:
            print(f"\n~ 已修改，重新评估决策: {decision.action}")
    
    def _provide_guidance_by_id(self, decision_id: str) -> None:
        """根据ID提供指导"""
        decision = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if decision:
            print(f"\n→ 已提供指导，建议改进决策: {decision.action}")
    
    def show_statistics(self) -> None:
        """显示统计信息"""
        print(f"\n=== 人在环路统计 ===\n")
        print(f"总决策数: {len(self.decisions)}")
        print(f"需要审查的决策: {sum(1 for d in self.decisions if d.requires_approval)}")
        print(f"自动执行的决策: {sum(1 for d in self.decisions if not d.requires_approval)}")
        print(f"总干预数: {len(self.interventions)}")
        
        if self.interventions:
            print(f"\n干预类型分布:")
            for intervention_type in InterventionType:
                count = sum(1 for i in self.interventions if i.intervention_type == intervention_type)
                if count > 0:
                    print(f"  {intervention_type.value}: {count}")
        
        # 计算平均置信度
        if self.decisions:
            avg_confidence = sum(d.confidence for d in self.decisions) / len(self.decisions)
            print(f"\n平均置信度: {avg_confidence:.2f}")
        
        # 风险等级分布
        print(f"\n风险等级分布:")
        for risk_level in RiskLevel:
            count = sum(1 for d in self.decisions if d.risk_level == risk_level)
            if count > 0:
                print(f"  {risk_level.value}: {count}")


def main():
    """主函数：演示人在环路"""
    agent = HumanInLoopAgent()
    
    print("="*60)
    print("人在环路智能体演示")
    print("="*60)
    
    # 场景1：低风险、高置信度 - 自动执行
    print("\n【场景1：低风险、高置信度】")
    decision1 = agent.make_decision(
        description="生成报告摘要",
        action="生成文本摘要",
        risk_level=RiskLevel.LOW,
        confidence=0.95
    )
    agent.process_decision(decision1)
    
    # 场景2：中等风险、中等置信度 - 需要审查
    print("\n【场景2：中等风险、中等置信度】")
    decision2 = agent.make_decision(
        description="修改用户账户信息",
        action="修改数据库记录",
        risk_level=RiskLevel.MEDIUM,
        confidence=0.65
    )
    agent.process_decision(decision2)
    
    # 场景3：高风险、低置信度 - 需要审查
    print("\n【场景3：高风险、低置信度】")
    decision3 = agent.make_decision(
        description="处理财务转账",
        action="转账10000元到指定账户",
        risk_level=RiskLevel.HIGH,
        confidence=0.45
    )
    agent.process_decision(decision3)
    
    # 场景4：关键风险 - 必须审查
    print("\n【场景4：关键风险】")
    decision4 = agent.make_decision(
        description="删除重要数据",
        action="删除用户数据库",
        risk_level=RiskLevel.CRITICAL,
        confidence=0.30
    )
    agent.process_decision(decision4)
    
    # 显示统计信息
    agent.show_statistics()


if __name__ == "__main__":
    main()

