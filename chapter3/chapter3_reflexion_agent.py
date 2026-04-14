"""
第3章 - Reflexion智能体实现
演示Reflexion模式的完整实现,包括Actor-Evaluator-Self-Reflection循环
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Episode:
    """一次尝试的完整记录"""
    task: str
    trajectory: str
    evaluation: Dict
    reflection: str
    success: bool
    trial_number: int


class ReflexionAgent:
    """Reflexion模式智能体"""

    def __init__(self, model: str = None):
        """初始化Reflexion智能体

        Args:
            model: 使用的模型名称,默认从环境变量读取
        """
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = model or os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")
        self.memory: List[Episode] = []

    def solve(self, task: str, max_trials: int = 3, verbose: bool = True) -> Tuple[str, bool]:
        """尝试解决任务,最多尝试max_trials次

        Args:
            task: 要解决的任务
            max_trials: 最大尝试次数
            verbose: 是否打印详细信息

        Returns:
            (最终结果, 是否成功)
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"任务: {task}")
            print(f"{'='*60}\n")

        for trial in range(1, max_trials + 1):
            if verbose:
                print(f"\n{'='*60}")
                print(f"第 {trial} 次尝试")
                print(f"{'='*60}\n")

            # 1. Actor: 执行任务
            trajectory = self._execute_task(task, trial, verbose)

            # 2. Evaluator: 评估结果
            evaluation = self._evaluate(task, trajectory, verbose)

            if evaluation['success']:
                if verbose:
                    print(f"\n✓ 任务成功完成!")
                return trajectory, True

            # 3. Self-Reflection: 生成反思
            reflection = self._reflect(task, trajectory, evaluation, verbose)

            # 4. 存储到记忆
            episode = Episode(
                task=task,
                trajectory=trajectory,
                evaluation=evaluation,
                reflection=reflection,
                success=False,
                trial_number=trial
            )
            self.memory.append(episode)

            if verbose:
                print(f"\n反思: {reflection}\n")

        if verbose:
            print(f"\n✗ 未能在 {max_trials} 次尝试内完成任务")
        return trajectory, False

    def _execute_task(self, task: str, trial: int, verbose: bool = True) -> str:
        """执行任务,生成轨迹"""
        # 构建提示词,包含历史反思
        prompt = self._build_execution_prompt(task, trial)

        if verbose and trial > 1:
            print("基于之前的反思重新尝试...\n")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个问题解决专家。请仔细思考并给出详细的解决方案。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        trajectory = response.choices[0].message.content

        if verbose:
            print(f"解决方案:\n{trajectory}\n")

        return trajectory

    def _build_execution_prompt(self, task: str, trial: int) -> str:
        """构建执行提示词,包含历史反思"""
        prompt = f"任务: {task}\n\n"

        if trial > 1:
            prompt += "你之前尝试过这个任务但失败了。以下是你的反思:\n\n"
            for i, episode in enumerate(self.memory):
                prompt += f"第{i+1}次尝试的反思:\n{episode.reflection}\n\n"
            prompt += "请基于这些反思,重新尝试完成任务。避免之前的错误,采用更好的方法。\n\n"

        prompt += "请给出你的解决方案:"
        return prompt

    def _evaluate(self, task: str, trajectory: str, verbose: bool = True) -> Dict:
        """评估任务完成情况"""
        eval_prompt = f"""请评估以下解决方案是否正确完成了任务:

任务: {task}

解决方案: {trajectory}

请判断:
1. 解决方案是否正确?
2. 如果不正确,主要问题是什么?

请严格按照以下格式回答:
成功: [是/否]
反馈: [具体反馈]
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个严格的评估者。请客观评估解决方案的正确性。"},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        # 解析评估结果
        success = "成功: 是" in content or "成功:是" in content

        if verbose:
            print(f"评估结果:\n{content}\n")

        return {
            "success": success,
            "feedback": content
        }

    def _reflect(self, task: str, trajectory: str, evaluation: Dict, verbose: bool = True) -> str:
        """生成反思"""
        reflect_prompt = f"""你刚刚尝试完成以下任务,但失败了:

任务: {task}

你的解决方案:
{trajectory}

评估反馈:
{evaluation['feedback']}

请深入分析你失败的原因,并提供具体的改进建议。你的反思应该:
1. 指出具体的错误点(不要泛泛而谈)
2. 解释为什么会出错(分析根本原因)
3. 提供明确的改进方向(下次应该怎么做)

请用2-3段话总结你的反思:
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个善于自我反思的学习者。请深入分析失败原因并提出改进建议。"},
                {"role": "user", "content": reflect_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content


def main():
    """主函数 - 演示Reflexion智能体的使用"""
    agent = ReflexionAgent()

    # 测试案例1: 数学问题
    print("\n" + "="*60)
    print("测试案例1: 数学推理问题")
    print("="*60)

    task1 = """一个数字序列: 2, 6, 12, 20, 30, ...
请找出这个序列的规律,并给出第10个数字是多少。
要求: 必须解释清楚规律是什么,并展示计算过程。"""

    solution1, success1 = agent.solve(task1, max_trials=3)

    # 清空记忆,准备下一个测试
    agent.memory = []

    # 测试案例2: 逻辑推理
    print("\n\n" + "="*60)
    print("测试案例2: 逻辑推理问题")
    print("="*60)

    task2 = """有三个人:Alice、Bob、Charlie。
- Alice说: "Bob在说谎"
- Bob说: "Charlie在说谎"
- Charlie说: "Alice和Bob都在说谎"

假设只有一个人说真话,请问谁说的是真话?
要求: 必须通过逻辑推理,列出所有可能性并逐一验证。"""

    solution2, success2 = agent.solve(task2, max_trials=3)

    # 总结
    print("\n\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"案例1 (数学推理): {'成功' if success1 else '失败'}")
    print(f"案例2 (逻辑推理): {'成功' if success2 else '失败'}")


if __name__ == "__main__":
    main()
