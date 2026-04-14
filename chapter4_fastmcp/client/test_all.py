"""FastMCP服务器测试 - 运行: uv run python client/test_all.py"""

import asyncio
import json
from pathlib import Path
from fastmcp import Client


async def test_stdio_server():
    """测试STDIO服务器"""
    print("\n测试STDIO服务器(计算器)")
    print("="*60)

    config_path = Path(__file__).parent / "mcp_config.json"
    with open(config_path) as f:
        config = json.load(f)

    calculator_config = {"mcpServers": {"calculator": config["mcpServers"]["calculator"]}}

    async with Client(calculator_config) as client:
        result = await client.call_tool("add", {"a": 10, "b": 5})
        print(f"✓ add(10, 5) = {result.content[0].text}")

        result = await client.call_tool("multiply", {"a": 7, "b": 8})
        print(f"✓ multiply(7, 8) = {result.content[0].text}")


async def test_http_server():
    """测试HTTP服务器"""
    print("\n测试HTTP服务器(天气查询)")
    print("="*60)

    config_path = Path(__file__).parent / "mcp_config.json"
    with open(config_path) as f:
        config = json.load(f)

    weather_config = {"mcpServers": {"weather": config["mcpServers"]["weather"]}}

    try:
        async with Client(weather_config) as client:
            result = await client.call_tool("get_weather", {"city": "Beijing"})
            print(f"✓ 天气查询成功: {result.content[0].text[:80]}...")
    except Exception as e:
        print(f"✗ 测试失败: {e} (提示: 请先启动HTTP服务器)")
        raise


async def main():
    print("\nFastMCP 自动化测试")
    print("="*60)

    try:
        await test_stdio_server()
        await test_http_server()
        print("\n" + "="*60)
        print("✓ 所有测试通过!")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

