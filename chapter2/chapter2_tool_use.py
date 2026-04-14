"""
第2章：工具调用完整流程演示

本模块使用 OpenAI SDK 演示工具调用的完整生命周期:
1. 定义工具的 JSON Schema
2. 将工具注册到模型请求中
3. 模型返回 function call, 解析出函数名称和参数
4. 在本地执行对应的函数
5. 将函数结果以 tool message 的形式回传给模型
6. 模型结合工具结果生成最终回答
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# 环境配置
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
MODEL = os.getenv("OPENAI_MODEL_NAME")


# ===========================================================================
# 第1步: 定义本地函数 (工具的实际实现)
# ===========================================================================

def get_current_weather(city: str, unit: str = "celsius") -> dict:
    """获取指定城市的当前天气 (模拟数据)"""
    weather_db = {
        "北京": {"temperature": 22, "condition": "晴", "humidity": 45},
        "上海": {"temperature": 26, "condition": "多云", "humidity": 72},
        "广州": {"temperature": 30, "condition": "雷阵雨", "humidity": 85},
    }
    data = weather_db.get(city, {"temperature": 20, "condition": "未知", "humidity": 50})
    if unit == "fahrenheit":
        data["temperature"] = round(data["temperature"] * 9 / 5 + 32, 1)
    return {"city": city, "unit": unit, **data}


# 建立 函数名 -> 函数对象 的映射, 方便后续根据模型返回的名称动态调用
available_functions = {
    "get_current_weather": get_current_weather,
}


# ===========================================================================
# 第2步: 定义工具的 JSON Schema (OpenAI Tool 格式)
# ===========================================================================
# 这个 schema 会被发送给模型, 使模型了解可调用的工具及其参数结构。
# 格式遵循 OpenAI 的 tools 规范: type 固定为 "function",
# 内部 parameters 遵循 JSON Schema 标准。

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定城市的当前天气信息, 包括温度、天气状况和湿度",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称, 例如: 北京、上海、广州",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位, 默认为摄氏度",
                    },
                },
                "required": ["city"],
            },
        },
    }
]


# ===========================================================================
# 第3步: 执行完整的工具调用循环
# ===========================================================================

def run_tool_call_demo():
    """演示工具调用的完整生命周期"""

    # --- 3.1 构造初始消息并发送请求 ---
    user_question = "北京和上海今天的天气怎么样?"
    print(f"用户提问: {user_question}\n")

    messages = [
        {"role": "user", "content": user_question}
    ]

    # 第一次调用: 模型分析用户意图, 决定是否需要调用工具
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,           # 传入工具定义
        tool_choice="auto",    # 让模型自主决定是否调用工具
    )
    assistant_message = response.choices[0].message

    # --- 3.2 检查模型是否要求调用工具 ---
    if not assistant_message.tool_calls:
        # 模型认为不需要工具, 直接返回文本回答
        print("模型直接回答:", assistant_message.content)
        return

    # 模型返回了 tool_calls, 说明它需要调用工具来获取信息
    print(f"模型请求调用 {len(assistant_message.tool_calls)} 个工具:\n")

    # 将 assistant 的完整消息 (包含 tool_calls) 加入对话历史
    messages.append(assistant_message)

    # --- 3.3 解析并执行每个工具调用 ---
    for tool_call in assistant_message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"  调用函数: {function_name}")
        print(f"  解析参数: {json.dumps(function_args, ensure_ascii=False)}")

        # 根据函数名找到对应的本地函数并执行
        func = available_functions[function_name]
        result = func(**function_args)

        print(f"  执行结果: {json.dumps(result, ensure_ascii=False)}\n")

        # --- 3.4 将工具结果作为 tool message 回传 ---
        # role 必须为 "tool", tool_call_id 必须与请求中的 id 对应
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })

    # --- 3.5 第二次调用: 模型结合工具结果生成最终回答 ---
    print("将工具结果回传给模型, 生成最终回答...\n")

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    final_answer = final_response.choices[0].message.content
    print(f"最终回答:\n{final_answer}")


# ===========================================================================
# 主函数
# ===========================================================================

if __name__ == "__main__":
    run_tool_call_demo()
