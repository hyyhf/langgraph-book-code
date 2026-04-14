"""
第3章 - ReAct智能体实现
演示ReAct模式的完整实现,包括思考-行动-观察循环
"""

import os
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import re

# 加载环境变量
load_dotenv()


class ReActAgent:
    """ReAct模式智能体的完整实现"""

    def __init__(self, model: str = None):
        """初始化ReAct智能体

        Args:
            model: 使用的模型名称,默认从环境变量读取
        """
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = model or os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")
        self.tools = self._init_tools()

    def _init_tools(self) -> Dict[str, Any]:
        """初始化可用工具"""
        return {
            "search": self._search_tool,
            "calculate": self._calculate_tool,
            "get_current_date": self._get_current_date_tool,
        }

    def _search_tool(self, query: str) -> str:
        """模拟搜索工具

        在实际应用中,这里会调用真实的搜索API(如Google、Bing等)
        这里我们模拟一些常见查询的结果
        """
        # 模拟搜索结果
        mock_results = {
            "langgraph": "LangGraph是一个用于构建有状态、多参与者应用的框架,基于LangChain构建。它允许开发者创建复杂的智能体工作流。",
            "deepseek": "DeepSeek是一个大语言模型,提供高质量的对话和推理能力。",
            "react pattern": "ReAct是一种将推理(Reasoning)和行动(Acting)结合的智能体设计模式,由普林斯顿大学和Google Research在2022年提出。",
            "python": "Python是一种高级编程语言,以其简洁的语法和强大的库生态系统而闻名。",
        }

        # 简单的关键词匹配
        query_lower = query.lower()
        for key, value in mock_results.items():
            if key in query_lower:
                return f"搜索'{query}'的结果: {value}"

        return f"搜索'{query}'的结果: 未找到相关信息。"

    def _calculate_tool(self, expression: str) -> str:
        """计算工具

        安全地计算数学表达式
        """
        try:
            # 只允许数字和基本运算符,提高安全性
            allowed_chars = set('0123456789+-*/()., ')
            if not all(c in allowed_chars for c in expression):
                return "错误: 表达式包含不允许的字符"

            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"

    def _get_current_date_tool(self) -> str:
        """获取当前日期"""
        from datetime import datetime
        return f"当前日期: {datetime.now().strftime('%Y年%m月%d日')}"

    def run(self, question: str, max_steps: int = 10, verbose: bool = True) -> str:
        """运行ReAct循环

        Args:
            question: 用户问题
            max_steps: 最大步数
            verbose: 是否打印详细信息

        Returns:
            最终答案
        """
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": question}
        ]

        if verbose:
            print(f"\n{'='*60}")
            print(f"问题: {question}")
            print(f"{'='*60}\n")

        for step in range(1, max_steps + 1):
            if verbose:
                print(f"--- 步骤 {step} ---")

            # 获取模型响应
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content
            messages.append({"role": "assistant", "content": content})

            if verbose:
                print(f"{content}\n")

            # 检查是否完成
            if "Finish[" in content or "完成[" in content:
                answer = self._extract_answer(content)
                if verbose:
                    print(f"{'='*60}")
                    print(f"最终答案: {answer}")
                    print(f"{'='*60}\n")
                return answer

            # 执行工具调用
            if "Action:" in content or "行动:" in content:
                action, params = self._parse_action(content)
                if action:
                    observation = self._execute_action(action, params)

                    # 添加观察结果
                    obs_message = f"Observation: {observation}"
                    messages.append({"role": "user", "content": obs_message})

                    if verbose:
                        print(f"观察: {observation}\n")

        return "达到最大步数限制,未能完成任务"

    def _get_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个ReAct智能体。你需要通过交替进行思考(Thought)和行动(Action)来解决问题。

可用工具:
1. search[query]: 搜索相关信息
2. calculate[expression]: 计算数学表达式
3. get_current_date[]: 获取当前日期

你的响应格式应该严格遵循:
Thought: [你的思考过程,解释你为什么要采取这个行动]
Action: [工具名称][参数]

当你准备好给出最终答案时,使用:
Thought: [最终思考]
Action: Finish[答案]

示例1:
Question: 2023年加1是哪一年?
Thought: 我需要计算2023+1
Action: calculate[2023+1]
Observation: 计算结果: 2024
Thought: 答案是2024年
Action: Finish[2024年]

示例2:
Question: LangGraph是什么?
Thought: 我需要搜索LangGraph的信息
Action: search[LangGraph]
Observation: 搜索'LangGraph'的结果: LangGraph是一个用于构建有状态、多参与者应用的框架...
Thought: 我已经找到了LangGraph的定义
Action: Finish[LangGraph是一个用于构建有状态、多参与者应用的框架,基于LangChain构建]

重要提示:
- 每次只执行一个Action
- 在给出最终答案前,确保你有足够的信息
- 如果搜索没有找到信息,尝试使用不同的关键词
"""

    def _parse_action(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """解析行动和参数

        Returns:
            (action_name, parameters) 或 (None, None)
        """
        # 匹配 Action: tool[params] 格式
        pattern = r'Action:\s*(\w+)\[(.*?)\]'
        match = re.search(pattern, content)

        if match:
            action = match.group(1)
            params = match.group(2)
            return action, params

        # 尝试中文格式
        pattern = r'行动:\s*(\w+)\[(.*?)\]'
        match = re.search(pattern, content)

        if match:
            action = match.group(1)
            params = match.group(2)
            return action, params

        return None, None

    def _execute_action(self, action: str, params: str) -> str:
        """执行工具调用"""
        if action in self.tools:
            try:
                if params:
                    return self.tools[action](params)
                else:
                    return self.tools[action]()
            except Exception as e:
                return f"工具执行错误: {str(e)}"
        else:
            return f"未知工具: {action}"

    def _extract_answer(self, content: str) -> str:
        """提取最终答案"""
        # 匹配 Finish[answer] 格式
        pattern = r'(?:Finish|完成)\[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return content


def main():
    """主函数 - 演示ReAct智能体的使用"""
    agent = ReActAgent()

    # 测试案例1: 简单计算
    print("\n" + "="*60)
    print("测试案例1: 数学计算")
    print("="*60)
    agent.run("计算 (123 + 456) * 2 的结果是多少?")

    # 测试案例2: 信息检索
    print("\n" + "="*60)
    print("测试案例2: 信息检索")
    print("="*60)
    agent.run("ReAct模式是什么?")

    # 测试案例3: 组合使用工具
    print("\n" + "="*60)
    print("测试案例3: 组合使用多个工具")
    print("="*60)
    agent.run("今天是几号?如果加上7天是几号?")


if __name__ == "__main__":
    main()
