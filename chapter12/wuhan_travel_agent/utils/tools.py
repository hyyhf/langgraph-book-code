"""
工具模块
提供高德地图API相关的工具函数
"""

import os
import requests
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool


# 从环境变量获取高德地图API配置
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
AMAP_BASE_URL = os.getenv("AMAP_BASE_URL", "https://restapi.amap.com/v3")


@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的天气信息
    
    Args:
        city: 城市名称,例如"武汉"、"北京"等
        
    Returns:
        天气信息的文本描述
    """
    try:
        url = f"{AMAP_BASE_URL}/weather/weatherInfo"
        params = {
            "key": AMAP_API_KEY,
            "city": city,
            "extensions": "all"  # 获取预报天气
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "1" and data.get("forecasts"):
            forecast = data["forecasts"][0]
            city_name = forecast.get("city", city)
            casts = forecast.get("casts", [])
            
            if not casts:
                return f"{city_name}的天气信息暂时无法获取"
            
            weather_info = f"{city_name}未来几天天气预报:\n"
            for cast in casts[:3]:  # 只显示前3天
                date = cast.get("date", "")
                dayweather = cast.get("dayweather", "")
                nightweather = cast.get("nightweather", "")
                daytemp = cast.get("daytemp", "")
                nighttemp = cast.get("nighttemp", "")
                daywind = cast.get("daywind", "")
                daypower = cast.get("daypower", "")
                
                weather_info += f"\n日期: {date}\n"
                weather_info += f"  白天: {dayweather}, 温度{daytemp}度, {daywind}风{daypower}级\n"
                weather_info += f"  夜间: {nightweather}, 温度{nighttemp}度\n"
            
            return weather_info
        else:
            return f"无法获取{city}的天气信息,请检查城市名称是否正确"
            
    except Exception as e:
        return f"查询天气时出错: {str(e)}"


@tool
def search_poi(keyword: str, city: str = "武汉", poi_type: str = "") -> str:
    """
    搜索指定城市的兴趣点(POI) - 使用高德地图POI 2.0 API

    Args:
        keyword: 搜索关键词,例如"黄鹤楼"、"美食"、"酒店"等
        city: 城市名称,默认为"武汉"
        poi_type: POI类型编码,例如"060000"(购物服务)、"110000"(旅游景点)等,可选
                 完整类型编码参考: https://lbs.amap.com/api/webservice/download

    Returns:
        POI搜索结果的文本描述
    """
    try:
        # 使用POI 2.0 API的新URL
        url = "https://restapi.amap.com/v5/place/text"
        params = {
            "key": AMAP_API_KEY,
            "keywords": keyword,
            "region": city,  # v5使用region参数代替city
            "page_size": 10,  # v5使用page_size代替offset
            "page_num": 1,    # v5使用page_num代替page
            "show_fields": "business,photos"  # 请求返回商业信息和图片
        }

        # 如果指定了POI类型,添加types参数
        if poi_type:
            params["types"] = poi_type

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # v5 API返回格式: status为"1"表示成功
        if data.get("status") == "1" and data.get("pois"):
            pois = data["pois"]
            count = data.get("count", len(pois))
            result = f"在{city}搜索到{count}个关于'{keyword}'的地点:\n\n"

            for i, poi in enumerate(pois[:5], 1):  # 只显示前5个
                name = poi.get("name", "未知")
                address = poi.get("address", "地址未知")
                poi_type_name = poi.get("type", "")
                location = poi.get("location", "")

                result += f"{i}. {name}\n"
                result += f"   类型: {poi_type_name}\n"
                result += f"   地址: {address}\n"

                # 获取商业信息(如果有)
                business = poi.get("business")
                if business:
                    tel = business.get("tel", "")
                    if tel:
                        result += f"   电话: {tel}\n"

                    # 营业时间
                    opentime_today = business.get("opentime_today", "")
                    if opentime_today:
                        result += f"   营业时间: {opentime_today}\n"

                    # 评分和人均消费(餐饮、酒店、景点类POI)
                    rating = business.get("rating", "")
                    cost = business.get("cost", "")
                    if rating:
                        result += f"   评分: {rating}\n"
                    if cost:
                        result += f"   人均消费: {cost}元\n"

                    # 商圈信息
                    business_area = business.get("business_area", "")
                    if business_area:
                        result += f"   商圈: {business_area}\n"

                result += f"   坐标: {location}\n\n"

            return result
        else:
            error_info = data.get("info", "未知错误")
            return f"在{city}没有找到关于'{keyword}'的地点 (错误信息: {error_info})"

    except Exception as e:
        return f"搜索POI时出错: {str(e)}"


@tool
def plan_route(
    origin: str,
    destination: str,
    city: str = "武汉",
    mode: str = "auto"
) -> str:
    """
    智能规划两地之间的最优路线(路径规划2.0 API)

    支持驾车、步行、公交三种交通方式,可以自动选择最优方式或手动指定。

    Args:
        origin: 起点名称或坐标(经度,纬度)
        destination: 终点名称或坐标(经度,纬度)
        city: 城市名称,默认为"武汉"
        mode: 交通方式,可选值:
            - "auto": 自动选择最优方式(根据距离智能判断)
            - "walking": 步行
            - "transit": 公交
            - "driving": 驾车

    Returns:
        路线规划结果的文本描述,包含距离、时间、费用等信息

    智能选择规则:
        - 距离 < 2km: 推荐步行
        - 2km <= 距离 < 10km: 推荐公交
        - 距离 >= 10km: 推荐驾车/打车
    """
    try:
        # 地理编码辅助函数
        def get_location(place_name: str) -> Optional[str]:
            """将地点名称转换为坐标"""
            if "," in place_name:
                parts = place_name.replace(" ", "").split(",")
                if len(parts) == 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return place_name
                    except ValueError:
                        pass

            # 进行地理编码
            geo_url = f"{AMAP_BASE_URL}/geocode/geo"
            geo_params = {
                "key": AMAP_API_KEY,
                "address": place_name,
                "city": city
            }
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            geo_data = geo_response.json()

            if geo_data.get("status") == "1" and geo_data.get("geocodes"):
                return geo_data["geocodes"][0].get("location")
            return None

        # 获取起终点坐标
        origin_location = get_location(origin)
        destination_location = get_location(destination)

        if not origin_location:
            return f"无法找到起点'{origin}'的位置"
        if not destination_location:
            return f"无法找到终点'{destination}'的位置"

        # 计算直线距离用于智能选择交通方式
        def calculate_distance(loc1: str, loc2: str) -> float:
            """计算两点间直线距离(km)"""
            try:
                lon1, lat1 = map(float, loc1.split(","))
                lon2, lat2 = map(float, loc2.split(","))
                from math import radians, sin, cos, sqrt, atan2

                R = 6371  # 地球半径(km)
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            except:
                return 5.0  # 默认值

        straight_distance = calculate_distance(origin_location, destination_location)

        # 智能选择交通方式
        selected_mode = mode
        if mode == "auto":
            if straight_distance < 2:
                selected_mode = "walking"
            elif straight_distance < 10:
                selected_mode = "transit"
            else:
                selected_mode = "driving"

        # 根据交通方式调用不同的API
        result = ""

        if selected_mode == "walking":
            # 步行路线规划 (路径规划2.0)
            url = "https://restapi.amap.com/v5/direction/walking"
            params = {
                "key": AMAP_API_KEY,
                "origin": origin_location,
                "destination": destination_location,
                "show_fields": "cost"
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "1" and data.get("route"):
                route = data["route"]
                paths = route.get("paths", [])

                if paths:
                    path = paths[0]
                    distance = float(path.get("distance", 0))
                    duration = path.get("cost", {}).get("duration", 0)

                    result = f"从'{origin}'到'{destination}'的步行路线:\n\n"
                    result += f"交通方式: 步行\n"
                    result += f"总距离: {distance/1000:.2f}公里 ({int(distance)}米)\n"
                    result += f"预计时间: {int(duration)//60}分钟\n"
                    result += f"推荐理由: 距离较近,步行即可到达\n"

        elif selected_mode == "transit":
            # 公交路线规划 (路径规划2.0)
            city_code = "027"  # 武汉城市编码

            url = "https://restapi.amap.com/v5/direction/transit/integrated"
            params = {
                "key": AMAP_API_KEY,
                "origin": origin_location,
                "destination": destination_location,
                "city1": city_code,
                "city2": city_code,
                "strategy": 0,  # 推荐模式
                "show_fields": "cost",
                "AlternativeRoute": 1  # 返回1条路线
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "1" and data.get("route"):
                route = data["route"]
                transits = route.get("transits", [])

                if transits:
                    transit = transits[0]
                    distance = float(transit.get("distance", 0))
                    duration = transit.get("cost", {}).get("duration", 0)
                    transit_fee = transit.get("cost", {}).get("transit_fee", 0)

                    result = f"从'{origin}'到'{destination}'的公交路线:\n\n"
                    result += f"交通方式: 公共交通\n"
                    result += f"总距离: {distance/1000:.2f}公里\n"
                    result += f"预计时间: {int(duration)//60}分钟\n"
                    result += f"预计费用: {transit_fee}元\n"
                    result += f"推荐理由: 经济实惠,适合中等距离出行\n"

        else:  # driving
            # 驾车路线规划 (路径规划2.0)
            url = "https://restapi.amap.com/v5/direction/driving"
            params = {
                "key": AMAP_API_KEY,
                "origin": origin_location,
                "destination": destination_location,
                "strategy": 32,  # 高德推荐
                "show_fields": "cost"
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "1" and data.get("route"):
                route = data["route"]
                paths = route.get("paths", [])

                if paths:
                    path = paths[0]
                    distance = float(path.get("distance", 0))
                    duration = path.get("cost", {}).get("duration", 0)
                    tolls = path.get("cost", {}).get("tolls", 0)
                    taxi_fee = route.get("taxi_cost", 0)

                    result = f"从'{origin}'到'{destination}'的驾车路线:\n\n"
                    result += f"交通方式: 驾车/打车\n"
                    result += f"总距离: {distance/1000:.2f}公里\n"
                    result += f"预计时间: {int(duration)//60}分钟\n"
                    result += f"过路费: {tolls}元\n"
                    result += f"打车费用: 约{taxi_fee}元\n"
                    result += f"推荐理由: 距离较远,驾车更快捷\n"

        if not result:
            return f"无法规划从'{origin}'到'{destination}'的路线"

        return result

    except Exception as e:
        return f"规划路线时出错: {str(e)}"


# 导出所有工具
tools = [get_weather, search_poi, plan_route]

