# POI 2.0 API 升级说明

## 升级概述

本项目的 `search_poi` 工具已从高德地图 POI 1.0 API 升级到 POI 2.0 API,以获得更好的搜索能力和更丰富的数据返回。

## 主要变化

### 1. API URL 变化

**旧版本 (POI 1.0):**
```
https://restapi.amap.com/v3/place/text
```

**新版本 (POI 2.0):**
```
https://restapi.amap.com/v5/place/text
```

### 2. 请求参数变化

| 参数名 | POI 1.0 | POI 2.0 | 说明 |
|--------|---------|---------|------|
| 城市参数 | `city` | `region` | 参数名变更 |
| 分页大小 | `offset` | `page_size` | 参数名变更 |
| 页码 | `page` | `page_num` | 参数名变更 |
| 扩展信息 | `extensions` | `show_fields` | 参数名和使用方式变更 |

**POI 1.0 请求示例:**
```python
params = {
    "key": AMAP_API_KEY,
    "keywords": "黄鹤楼",
    "city": "武汉",
    "offset": 10,
    "page": 1,
    "extensions": "all"
}
```

**POI 2.0 请求示例:**
```python
params = {
    "key": AMAP_API_KEY,
    "keywords": "黄鹤楼",
    "region": "武汉",
    "page_size": 10,
    "page_num": 1,
    "show_fields": "business,photos"
}
```

### 3. 返回数据结构变化

#### 基础信息字段 (无需 show_fields 即可返回)

POI 1.0 和 POI 2.0 的基础字段基本一致:
- `name`: POI名称
- `id`: POI唯一标识
- `location`: 经纬度坐标
- `type`: POI类型
- `typecode`: POI分类编码
- `address`: 详细地址
- `pname`: 省份名称
- `cityname`: 城市名称
- `adname`: 区县名称

#### 扩展信息字段 (需要通过 show_fields 指定)

**POI 2.0 新增的 business 对象结构:**

```json
{
  "business": {
    "business_area": "商圈名称",
    "opentime_today": "今日营业时间",
    "opentime_week": "每周营业时间",
    "tel": "联系电话",
    "tag": "特色标签",
    "rating": "评分",
    "cost": "人均消费",
    "parking_type": "停车场类型",
    "alias": "别名",
    "keytag": "POI标识",
    "rectag": "信息类型确认"
  }
}
```

**主要改进:**
1. 商业信息统一放在 `business` 对象中,结构更清晰
2. 新增 `opentime_today` 字段,提供今日营业时间
3. 新增 `opentime_week` 字段,提供每周营业时间描述
4. 评分、人均消费等信息更加准确

### 4. show_fields 参数说明

POI 2.0 使用 `show_fields` 参数来控制返回的可选字段,可选值包括:

- `children`: 子POI信息
- `business`: 商业信息(营业时间、电话、评分等)
- `indoor`: 室内地图相关信息
- `navi`: 导航位置相关信息
- `photos`: POI图片信息

**使用示例:**
```python
# 只返回商业信息
"show_fields": "business"

# 返回商业信息和图片
"show_fields": "business,photos"

# 返回所有可选字段
"show_fields": "children,business,indoor,navi,photos"
```

## 代码改动示例

### 旧代码 (POI 1.0)

```python
@tool
def search_poi(keyword: str, city: str = "武汉", poi_type: str = "") -> str:
    url = f"{AMAP_BASE_URL}/place/text"
    params = {
        "key": AMAP_API_KEY,
        "keywords": keyword,
        "city": city,
        "offset": 10,
        "page": 1,
        "extensions": "all"
    }
    
    # ... 处理响应
    tel = poi.get("tel", "")  # 直接从POI对象获取
```

### 新代码 (POI 2.0)

```python
@tool
def search_poi(keyword: str, city: str = "武汉", poi_type: str = "") -> str:
    url = "https://restapi.amap.com/v5/place/text"
    params = {
        "key": AMAP_API_KEY,
        "keywords": keyword,
        "region": city,
        "page_size": 10,
        "page_num": 1,
        "show_fields": "business,photos"
    }
    
    # ... 处理响应
    business = poi.get("business")
    if business:
        tel = business.get("tel", "")  # 从business对象获取
        rating = business.get("rating", "")
        cost = business.get("cost", "")
```

## 升级优势

1. **更丰富的数据**: 提供营业时间、评分、人均消费等更多信息
2. **更清晰的结构**: 商业信息统一在 business 对象中
3. **更灵活的控制**: 通过 show_fields 精确控制返回字段
4. **更好的性能**: 只请求需要的字段,减少数据传输
5. **更准确的搜索**: POI 2.0 提供更智能的搜索算法

## 测试结果
**测试输出示例:**
```
在武汉搜索到10个关于'黄鹤楼'的地点:

1. 黄鹤楼
   类型: 风景名胜;风景名胜;国家级景点
   地址: 蛇山西山坡特1号(地铁司门口黄鹤楼站A出口步行500m)
   评分: 4.8
   商圈: 武珞路
   坐标: 114.302467,30.544649

2. 黄鹤楼公园
   类型: 风景名胜;风景名胜相关;旅游景点
   地址: 蛇山西山坡特1号
   电话: 4007009798
   营业时间: 08:30-18:00 19:30-22:00
   评分: 4.7
   商圈: 武珞路
   坐标: 114.307795,30.542529
```

## 参考文档

- [高德地图 POI 2.0 官方文档](https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch)
- [POI 分类码表下载](https://lbs.amap.com/api/webservice/download)

## 注意事项

1. POI 2.0 API 的 URL 路径从 `/v3/` 变更为 `/v5/`
2. 必须使用 `show_fields` 参数才能获取扩展信息
3. 商业信息(电话、营业时间等)现在在 `business` 对象中
4. 建议在生产环境中添加错误重试机制
5. 注意 API 调用频率限制,避免超出配额

## 兼容性说明

- POI 1.0 API 仍然可用,但建议使用 POI 2.0 获得更好的体验
- 本项目已完全迁移到 POI 2.0,无需额外配置
- 如需回退到 POI 1.0,请参考 git 历史记录

