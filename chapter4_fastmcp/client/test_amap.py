"""高德地图MCP服务器测试 - 运行: uv run client/test_amap.py"""

import asyncio
import json
from pathlib import Path
from fastmcp import Client


async def test_amap():
    """测试高德地图MCP服务器"""
    print("\n高德地图MCP服务器测试")
    print("="*60)

    config_path = Path(__file__).parent / "mcp_config.json"
    with open(config_path) as f:
        config = json.load(f)

    amap_config = {"mcpServers": {"amap": config["mcpServers"]["amap"]}}

    try:
        async with Client(amap_config) as client:

                        # 2. 列出所有工具
            print("\n2. 列出可用工具:")

            tools = await client.list_tools()
            print(f"   共有 {len(tools)} 个工具:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.name}")
                if tool.description:
                    desc_first_line = tool.description.split('\n')[0] #只显示第一行
                    print(f"      描述: {desc_first_line}")

            # 1. 地理编码
            print("\n1. 地理编码 - 地址转坐标")
            result = await client.call_tool("maps_geo", {"address": "武汉市武昌区黄鹤楼"})
            print(f"✓ 黄鹤楼坐标: {result.content[0].text[:100]}...")

            # 2. 周边搜索
            print("\n2. 周边搜索 - 黄鹤楼附近的餐厅")
            result = await client.call_tool("maps_around_search", {
                "keywords": "餐厅",
                "location": "114.305392,30.545606",  # 黄鹤楼坐标
                "radius": "1000"
            })
            print(f"✓ 搜索成功: {result.content[0].text[:100]}...")

            # 3. 关键词搜索
            print("\n3. 关键词搜索 - 武汉的热干面")
            result = await client.call_tool("maps_text_search", {
                "keywords": "热干面",
                "city": "武汉"
            })
            print(f"✓ 搜索成功: {result.content[0].text[:100]}...")

            # 4. 天气查询
            print("\n4. 天气查询 - 武汉天气")
            result = await client.call_tool("maps_weather", {"city": "武汉"})
            print(f"✓ 天气查询成功: {result.content[0].text[:150]}...")

            # 5. 路径规划
            print("\n5. 驾车路径规划 - 黄鹤楼到武汉站")
            result = await client.call_tool("maps_direction_driving", {
                "origin": "114.305392,30.545606",  # 黄鹤楼
                "destination": "114.426957,30.610155"  # 武汉站
            })
            print(f"✓ 路径规划成功: {result.content[0].text[:100]}...")

            print("\n" + "="*60)
            print("✓ 所有测试通过!")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_amap())

