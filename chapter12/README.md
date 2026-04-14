# 第12章: 武汉旅行规划助手

这是一个完整的实战案例,展示如何使用LangGraph构建一个多角色智能体系统。

## 项目概述

武汉旅行规划助手是一个智能的旅行规划系统,它能够:

1. 理解用户的旅行需求
2. 调用高德地图API获取实时信息(天气、景点、路线)
3. 生成详细的旅行计划
4. 支持人工审核和修改
5. 生成精美的HTML格式旅行文档

## 技术特点

### 1. 多角色智能体架构

- **规划助手**: 理解需求,协调工作流程
- **工具调用**: 集成高德地图API
- **HTML生成助手**: 创建精美的文档

### 2. Human-in-the-Loop

使用LangGraph的`interrupt`功能实现人机协作:
- 智能体生成初步计划后暂停
- 用户审核并提供反馈
- 根据反馈决定是否重新规划

### 3. 流式输出

实时展示智能体的思考过程:
- AI消息流式输出
- 工具调用实时显示
- 工具结果即时反馈

### 4. 工具集成

集成高德地图API:
- `get_weather`: 查询天气预报
- `search_poi`: 搜索景点、美食、酒店 (使用POI 2.0 API)
- `plan_route`: 规划交通路线

## 项目结构

```
chapter12/
├── wuhan_travel_agent/          # 智能体主模块
│   ├── __init__.py
│   ├── agent.py                 # 图构建
│   └── utils/                   # 工具包
│       ├── __init__.py
│       ├── state.py             # 状态定义
│       ├── nodes.py             # 节点函数
│       └── tools.py             # 高德地图工具
├── outputs/                     # 生成的HTML文档
├── main.py                      # 主程序
└── README.md                    # 项目说明
```

## 工作流程

```
用户输入需求
    ↓
规划助手(理解需求)
    ↓
工具调用(收集信息)
    ↓
规划助手(生成计划)
    ↓
人工审核(interrupt)
    ↓
用户反馈
    ↓
是否需要修改? ──是→ 返回规划助手
    ↓ 否
HTML生成助手
    ↓
完成
```

## 使用方法

### 1. 环境准备

确保`.env`文件中配置了以下环境变量:

```env
# AI模型配置
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL_NAME=deepseek-chat

# 高德地图API配置
AMAP_API_KEY=your_amap_key
AMAP_BASE_URL=https://restapi.amap.com/v3
```

### 2. 运行程序

```bash
cd code_for_learning/chapter12
uv run python main.py
```

### 3. 交互流程

1. 输入旅行需求,例如: "我想在武汉玩3天,喜欢历史文化和美食"
2. 等待智能体收集信息并生成计划
3. 审核计划,输入"确认"或提出修改建议
4. 查看生成的HTML文档

## 示例输出

### 控制台输出

```
欢迎使用武汉旅行规划助手!
================================================================================

请描述您的旅行需求: 我想在武汉玩3天,喜欢历史文化和美食

开始规划您的旅行...
--------------------------------------------------------------------------------

阶段1: 收集信息并生成初步计划
================================================================================

[智能体]: 好的,我来帮您规划一次精彩的武汉3日游...

[工具调用]: get_weather
  参数: {'city': '武汉'}

[工具结果 - get_weather]:
  武汉未来几天天气预报:
  日期: 2025-10-25
    白天: 晴, 温度22度, 东风3级
  ...

[工具调用]: search_poi
  参数: {'keyword': '黄鹤楼', 'city': '武汉'}

...
```

### HTML文档

生成的HTML文档包含:
- 精美的页面设计
- 完整的行程安排
- 景点介绍和图片
- 交通路线建议
- 美食推荐
- 注意事项

## 核心代码解析

### 1. 状态定义 (state.py)

```python
class TravelPlanState(TypedDict):
    messages: Annotated[list, add_messages]
    user_request: str
    destination: str
    travel_days: int
    weather_info: str
    poi_info: str
    route_info: str
    travel_plan: str
    user_feedback: str
    final_plan: str
    html_path: str
    current_stage: Literal[...]
    need_replan: bool
```

### 2. Human-in-the-Loop (nodes.py)

```python
def human_review_node(state: TravelPlanState):
    travel_plan = state.get("travel_plan", "")
    
    # 使用interrupt暂停执行
    user_feedback = interrupt({
        "type": "plan_review",
        "plan": travel_plan,
        "message": "请审核计划..."
    })
    
    # 处理用户反馈
    if user_feedback in ["确认", "ok"]:
        return {"need_replan": False, ...}
    else:
        return {"need_replan": True, ...}
```

### 3. 图构建 (agent.py)

```python
def create_travel_agent():
    workflow = StateGraph(TravelPlanState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("review", human_review_node)
    workflow.add_node("html_generator", html_generator_node)
    
    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges("planner", ...)
    workflow.add_edge("tools", "planner")
    workflow.add_conditional_edges("review", ...)
    workflow.add_edge("html_generator", END)
    
    return workflow.compile(checkpointer=MemorySaver())
```

## 扩展建议

1. **增加更多工具**: 
   - 酒店预订
   - 餐厅推荐
   - 门票查询

2. **优化计划生成**:
   - 考虑用户预算
   - 个性化推荐
   - 多日行程优化

3. **增强交互**:
   - 支持多轮对话
   - 实时修改计划
   - 保存历史记录

4. **美化输出**:
   - 添加地图展示
   - 集成图片
   - 生成PDF版本

## 学习要点

通过这个案例,您将学习到:

1. 如何设计多角色智能体系统
2. 如何集成外部API作为工具
3. 如何实现Human-in-the-Loop
4. 如何使用流式输出提升用户体验
5. 如何生成结构化的输出文档
6. 如何使用条件边控制工作流
7. 如何使用检查点实现状态持久化

## 注意事项

1. 确保高德地图API密钥有效
2. 网络连接正常
3. Python版本 >= 3.10
4. 已安装所有依赖包

## 故障排除

### 问题1: API调用失败

检查:
- API密钥是否正确
- 网络连接是否正常
- API配额是否充足

### 问题2: HTML生成失败

检查:
- outputs目录是否存在
- 是否有写入权限
- LLM是否正常响应

### 问题3: 中断恢复失败

检查:
- 是否使用了checkpointer
- thread_id是否一致
- 状态是否正确保存

