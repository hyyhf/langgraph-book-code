"""
第3章 - Plan-and-Execute智能体实现
演示Plan-and-Execute模式的完整实现,包括规划器和执行器的分离
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Step:
    """计划中的一个步骤"""
    step_number: int
    description: str
    status: str  # pending, in_progress, completed, failed
    result: Optional[str] = None
    dependencies: List[int] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class Plan:
    """完整的执行计划"""
    task: str
    steps: List[Step]
    current_step: int = 0
    
    def get_next_step(self) -> Optional[Step]:
        """获取下一个待执行的步骤"""
        for step in self.steps:
            if step.status == "pending":
                # 检查依赖是否都已完成
                deps_completed = all(
                    self.steps[dep-1].status == "completed" 
                    for dep in step.dependencies
                )
                if deps_completed:
                    return step
        return None
    
    def is_complete(self) -> bool:
        """检查计划是否全部完成"""
        return all(step.status == "completed" for step in self.steps)
    
    def has_failed(self) -> bool:
        """检查是否有步骤失败"""
        return any(step.status == "failed" for step in self.steps)


class PlanAndExecuteAgent:
    """Plan-and-Execute模式智能体"""
    
    def __init__(self, model: str = None):
        """初始化Plan-and-Execute智能体
        
        Args:
            model: 使用的模型名称,默认从环境变量读取
        """
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = model or os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")
        self.tools = self._init_tools()
    
    def _init_tools(self) -> Dict:
        """初始化可用工具"""
        return {
            "search": self._search_tool,
            "calculate": self._calculate_tool,
            "summarize": self._summarize_tool,
            "analyze": self._analyze_tool
        }
    
    def _search_tool(self, query: str) -> str:
        """模拟搜索工具"""
        return f"[搜索结果] 关于'{query}'的相关信息..."
    
    def _calculate_tool(self, expression: str) -> str:
        """计算工具"""
        try:
            result = eval(expression)
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    def _summarize_tool(self, text: str) -> str:
        """总结工具"""
        return f"[总结] {text[:100]}..."
    
    def _analyze_tool(self, data: str) -> str:
        """分析工具"""
        return f"[分析结果] 对'{data}'的分析..."
    
    def solve(self, task: str, verbose: bool = True) -> str:
        """使用Plan-and-Execute模式解决任务
        
        Args:
            task: 要解决的任务
            verbose: 是否打印详细信息
            
        Returns:
            最终结果
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"任务: {task}")
            print(f"{'='*60}\n")
        
        # 阶段1: 规划
        plan = self._create_plan(task, verbose)
        
        if verbose:
            print(f"\n{'='*60}")
            print("执行计划:")
            print(f"{'='*60}")
            for step in plan.steps:
                deps = f" (依赖: {step.dependencies})" if step.dependencies else ""
                print(f"{step.step_number}. {step.description}{deps}")
            print()
        
        # 阶段2: 执行
        results = self._execute_plan(plan, verbose)
        
        # 阶段3: 总结
        final_result = self._synthesize_results(task, plan, results, verbose)
        
        return final_result
    
    def _create_plan(self, task: str, verbose: bool = True) -> Plan:
        """创建执行计划"""
        if verbose:
            print("正在制定计划...\n")
        
        planning_prompt = f"""请为以下任务制定详细的执行计划:

任务: {task}

可用工具:
- search(query): 搜索信息
- calculate(expression): 执行数学计算
- summarize(text): 总结文本
- analyze(data): 分析数据

请将任务分解为3-6个具体步骤。对于每个步骤,请说明:
1. 步骤编号
2. 步骤描述(包括要使用的工具)
3. 依赖的步骤编号(如果有)

请严格按照以下格式输出:
步骤1: [描述] | 依赖: []
步骤2: [描述] | 依赖: [1]
...
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个擅长任务规划的专家。请将复杂任务分解为清晰的步骤。"},
                {"role": "user", "content": planning_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        plan_text = response.choices[0].message.content
        
        if verbose:
            print(f"规划结果:\n{plan_text}\n")
        
        # 解析计划
        steps = self._parse_plan(plan_text)
        
        return Plan(task=task, steps=steps)
    
    def _parse_plan(self, plan_text: str) -> List[Step]:
        """解析计划文本为步骤列表"""
        steps = []
        lines = plan_text.strip().split('\n')
        
        for line in lines:
            if line.strip().startswith('步骤'):
                try:
                    # 解析格式: 步骤1: 描述 | 依赖: [1,2]
                    parts = line.split('|')
                    step_part = parts[0].strip()
                    
                    # 提取步骤编号和描述
                    step_num_str = step_part.split(':')[0].replace('步骤', '').strip()
                    step_num = int(step_num_str)
                    description = ':'.join(step_part.split(':')[1:]).strip()
                    
                    # 提取依赖
                    dependencies = []
                    if len(parts) > 1:
                        dep_part = parts[1].strip()
                        if '依赖:' in dep_part:
                            dep_str = dep_part.split('依赖:')[1].strip()
                            # 解析 [1,2] 格式
                            dep_str = dep_str.strip('[]')
                            if dep_str:
                                dependencies = [int(d.strip()) for d in dep_str.split(',') if d.strip()]
                    
                    steps.append(Step(
                        step_number=step_num,
                        description=description,
                        status="pending",
                        dependencies=dependencies
                    ))
                except Exception as e:
                    print(f"解析步骤时出错: {line}, 错误: {e}")
                    continue
        
        return steps
    
    def _execute_plan(self, plan: Plan, verbose: bool = True) -> List[str]:
        """执行计划"""
        results = []
        
        if verbose:
            print(f"\n{'='*60}")
            print("开始执行计划")
            print(f"{'='*60}\n")
        
        while not plan.is_complete() and not plan.has_failed():
            step = plan.get_next_step()
            
            if step is None:
                break
            
            if verbose:
                print(f"\n执行步骤 {step.step_number}: {step.description}")
            
            step.status = "in_progress"
            
            # 执行步骤
            result = self._execute_step(step, plan, verbose)
            
            if result:
                step.status = "completed"
                step.result = result
                results.append(result)
                
                if verbose:
                    print(f"✓ 步骤 {step.step_number} 完成")
                    print(f"结果: {result}\n")
            else:
                step.status = "failed"
                if verbose:
                    print(f"✗ 步骤 {step.step_number} 失败\n")
                break
        
        return results
    
    def _execute_step(self, step: Step, plan: Plan, verbose: bool = True) -> str:
        """执行单个步骤"""
        # 收集依赖步骤的结果
        context = ""
        if step.dependencies:
            context = "之前步骤的结果:\n"
            for dep in step.dependencies:
                dep_step = plan.steps[dep-1]
                context += f"步骤{dep}: {dep_step.result}\n"
            context += "\n"
        
        # 构建执行提示
        exec_prompt = f"""{context}当前任务: {plan.task}

当前步骤: {step.description}

请执行这个步骤并给出结果。如果需要使用工具,请说明使用哪个工具以及参数。
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个任务执行专家。请按照指示完成步骤。"},
                {"role": "user", "content": exec_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _synthesize_results(self, task: str, plan: Plan, results: List[str], verbose: bool = True) -> str:
        """综合所有结果"""
        if verbose:
            print(f"\n{'='*60}")
            print("综合最终结果")
            print(f"{'='*60}\n")
        
        synthesis_prompt = f"""任务: {task}

执行的步骤和结果:
"""
        for i, step in enumerate(plan.steps):
            if step.result:
                synthesis_prompt += f"\n步骤{step.step_number}: {step.description}\n结果: {step.result}\n"
        
        synthesis_prompt += "\n请基于以上所有步骤的结果,给出对原始任务的完整回答:"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个总结专家。请综合所有信息给出完整答案。"},
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        final_result = response.choices[0].message.content
        
        if verbose:
            print(f"最终答案:\n{final_result}\n")
        
        return final_result


def main():
    """主函数 - 演示Plan-and-Execute智能体的使用"""
    agent = PlanAndExecuteAgent()
    
    # 测试案例: 复杂的研究任务
    print("\n" + "="*60)
    print("测试案例: 复杂研究任务")
    print("="*60)
    
    task = """请研究并总结:
1. 人工智能在医疗领域的三个主要应用方向
2. 每个方向的代表性技术
3. 当前面临的主要挑战
4. 未来发展趋势

请给出结构化的分析报告。"""
    
    result = agent.solve(task)
    
    print("\n" + "="*60)
    print("任务完成!")
    print("="*60)


if __name__ == "__main__":
    main()

