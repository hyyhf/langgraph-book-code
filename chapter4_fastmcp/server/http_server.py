"""
HTTP传输的MCP服务器示例

这个服务器演示了如何使用FastMCP创建一个基于HTTP传输的MCP服务器。
HTTP传输适合Web服务和远程访问场景。

运行方式:
    uv run python server/http_server.py
    
服务器将在 http://127.0.0.1:8000/mcp 启动
"""

import httpx
from fastmcp import FastMCP

# 创建FastMCP服务器实例
mcp = FastMCP("Weather Server")


# 天气代码映射
WEATHER_CODES = {
    0: "晴朗", 1: "主要晴朗", 2: "部分多云", 3: "阴天",
    45: "有雾", 48: "雾凇",
    51: "小雨", 53: "中雨", 55: "大雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "中阵雨", 82: "大阵雨",
    95: "雷暴", 96: "雷暴伴冰雹"
}


@mcp.tool()
async def get_weather(city: str) -> str:
    """
    获取指定城市的当前天气
    
    Args:
        city: 城市名称(英文),如London、Beijing、Tokyo
    
    Returns:
        当前天气信息的文本描述
    """
    try:
        # 1. 地理编码:将城市名称转换为经纬度
        async with httpx.AsyncClient(timeout=10.0) as client:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_response = await client.get(
                geocoding_url,
                params={"name": city, "count": 1, "language": "zh"}
            )
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return f"错误: 找不到城市 '{city}',请检查拼写或使用英文名称"
            
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location["name"]
            
            # 2. 获取天气数据
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_response = await client.get(
                weather_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                }
            )
            weather_data = weather_response.json()
            current = weather_data["current"]
            
            # 3. 格式化输出
            weather_code = current["weather_code"]
            description = WEATHER_CODES.get(weather_code, "未知")
            
            return f"""
{city_name} 当前天气:
- 温度: {current['temperature_2m']}°C
- 湿度: {current['relative_humidity_2m']}%
- 风速: {current['wind_speed_10m']} km/h
- 天气: {description}
"""
    except httpx.TimeoutException:
        return "错误: 请求超时,请稍后重试"
    except Exception as e:
        return f"错误: 获取天气信息失败 - {str(e)}"


@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """
    获取指定城市的天气预报
    
    Args:
        city: 城市名称(英文)
        days: 预报天数,范围1-7,默认3天
    
    Returns:
        天气预报信息的文本描述
    """
    if days < 1 or days > 7:
        return "错误: 预报天数必须在1-7之间"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 地理编码
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_response = await client.get(
                geocoding_url,
                params={"name": city, "count": 1, "language": "zh"}
            )
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return f"错误: 找不到城市 '{city}'"
            
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location["name"]
            
            # 获取预报数据
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_response = await client.get(
                weather_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "forecast_days": days
                }
            )
            weather_data = weather_response.json()
            daily = weather_data["daily"]
            
            # 格式化输出
            result = f"{city_name} 未来{days}天天气预报:\n\n"
            for i in range(len(daily["time"])):
                date = daily["time"][i]
                max_temp = daily["temperature_2m_max"][i]
                min_temp = daily["temperature_2m_min"][i]
                weather_code = daily["weather_code"][i]
                description = WEATHER_CODES.get(weather_code, "未知")
                
                result += f"{date}: {description}, {min_temp}°C ~ {max_temp}°C\n"
            
            return result
    except Exception as e:
        return f"错误: 获取天气预报失败 - {str(e)}"


@mcp.resource("info://server")
def server_info() -> str:
    """服务器信息"""
    return """
天气查询MCP服务器
版本: 1.0.0
传输协议: HTTP (Streamable HTTP)
数据来源: Open-Meteo API (免费天气数据)
支持功能: 当前天气查询、天气预报
"""


@mcp.resource("info://supported-cities")
def supported_cities() -> str:
    """支持的城市列表示例"""
    return """
支持全球主要城市,使用英文名称查询:
- 中国: Beijing, Shanghai, Guangzhou, Shenzhen
- 美国: New York, Los Angeles, Chicago, Houston
- 欧洲: London, Paris, Berlin, Rome
- 亚洲: Tokyo, Seoul, Singapore, Bangkok
"""


@mcp.prompt()
def weather_assistant() -> str:
    """天气助手提示词"""
    return """你是一个专业的天气助手。
当用户询问天气时,使用get_weather工具获取当前天气。
当用户询问未来天气时,使用get_forecast工具获取天气预报。
请用友好、简洁的方式回答用户的问题。"""


if __name__ == "__main__":
    # 使用HTTP传输运行服务器
    # HTTP传输支持远程访问和多个并发客户端
    # 使用Streamable HTTP协议(MCP推荐的HTTP传输方式)
    print("启动天气查询MCP服务器...")
    print("服务器地址: http://127.0.0.1:8000/mcp")
    print("按 Ctrl+C 停止服务器")
    
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000
    )

