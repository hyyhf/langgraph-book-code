"""
STDIO传输的MCP服务器示例

这个服务器演示了如何使用FastMCP创建一个基于STDIO传输的MCP服务器。
STDIO传输是MCP的默认传输方式,适合本地工具和桌面应用集成。

运行方式:
    uv run python server/stdio_server.py
"""

from fastmcp import FastMCP

# 创建FastMCP服务器实例
mcp = FastMCP("Calculator Server")


# 定义工具(Tools)
@mcp.tool()
def add(a: float, b: float) -> float:
    """
    两个数字相加
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两个数字的和
    """
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """
    两个数字相乘
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两个数字的积
    """
    return a * b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """
    计算幂运算
    
    Args:
        base: 底数
        exponent: 指数
    
    Returns:
        base的exponent次方
    """
    return base ** exponent


# 定义资源(Resources)
@mcp.resource("info://server")
def get_server_info() -> str:
    """
    获取服务器信息
    
    Returns:
        服务器的基本信息
    """
    return """
计算器MCP服务器
版本: 1.0.0
传输协议: STDIO
支持的运算: 加法、乘法、幂运算
"""


@mcp.resource("info://capabilities")
def get_capabilities() -> str:
    """
    获取服务器能力列表
    
    Returns:
        服务器支持的所有功能
    """
    return """
服务器能力:
- 工具(Tools): 3个数学运算工具
- 资源(Resources): 服务器信息和能力说明
- 提示词(Prompts): 数学问题求解模板
- 传输协议: STDIO (标准输入输出)
"""


# 定义提示词(Prompts)
@mcp.prompt()
def math_tutor(topic: str = "algebra") -> str:
    """
    数学辅导提示词模板
    
    Args:
        topic: 数学主题,如algebra(代数)、geometry(几何)等
    
    Returns:
        格式化的提示词
    """
    return f"""你是一位专业的数学老师,擅长{topic}。
请用简单易懂的方式解释数学概念,并提供实际例子。
如果需要计算,可以使用可用的计算工具。"""


@mcp.prompt()
def problem_solver() -> str:
    """
    数学问题求解提示词
    
    Returns:
        问题求解的提示词
    """
    return """请帮我解决这个数学问题。
首先分析问题,然后使用可用的计算工具进行计算,最后给出详细的解答步骤和最终答案。"""


if __name__ == "__main__":
    # 使用STDIO传输运行服务器(默认)
    mcp.run()

