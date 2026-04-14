# 第9章代码示例: 多智能体系统设计

本目录包含第9章《多智能体系统设计》的所有代码示例。

## 环境要求

```bash
# 使用uv安装依赖
uv pip install -r requirements.txt
```

## 配置

所有示例使用DeepSeek API,配置文件位于 `../.env`。

`config.py` 提供统一的LLM配置:
```python
from config import get_llm

llm = get_llm()  # 获取配置好的ChatOpenAI实例
```

## 示例列表

### 1. 单智能体的局限性 (`01_single_agent_limitation.py`)
**场景**: 武汉旅游规划助手

演示单智能体在处理复杂任务时面临的三大局限:
- **工具过载**: 15个工具导致决策复杂度增加
- **上下文爆炸**: 复杂任务导致上下文快速膨胀
- **专业化缺失**: 难以在多个领域都达到专家水平

**运行**: `uv run python 01_single_agent_limitation.py`

### 2. Network架构 (`02_network_architecture.py`)
**场景**: 武汉旅游咨询系统(景点、美食、交通)

演示全互联的协作网络架构:
- 智能体之间可以相互转交任务
- 去中心化的协作模式
- 使用Handoffs机制实现动态路由

**运行**: `uv run python 02_network_architecture.py`

### 3. Supervisor架构 (`03_supervisor_architecture.py`)
**场景**: 武汉大学生活助手(学习、生活、娱乐)

演示中央协调的管理模式:
- Supervisor负责任务分配
- 专业智能体执行具体任务
- 清晰的责任划分

**运行**: `uv run python 03_supervisor_architecture.py`

### 4. Tool-calling变体 (`04_tool_calling_variant.py`)
**场景**: 武汉房产服务(租房、买房、装修、贷款)

演示智能体即工具的模式:
- 将智能体包装为工具
- Supervisor通过工具调用使用智能体
- 支持并行调用多个智能体

**运行**: `uv run python 04_tool_calling_variant.py`

### 5. Hierarchical架构 (`05_hierarchical_architecture.py`)
**场景**: 武汉智慧城市管理系统(交通、环境、医疗、教育)

演示层级化的组织结构:
- 多层Supervisor管理
- 使用子图实现模块化
- 关注点分离,支持大规模系统

**运行**: `uv run python 05_hierarchical_architecture.py`

### 6. Custom Workflow (`06_custom_workflow.py`)
**场景**: 武汉外卖订餐系统

演示定制化的控制流:
- 顺序执行(选餐厅→选菜品→确认)
- 条件分支(金额检查→人工审核)
- 混合控制流模式

**运行**: `uv run python 06_custom_workflow.py`

### 7. Handoffs模式详解 (`07_handoffs_patterns.py`)
**场景**: 武汉政务服务大厅

演示四种Handoffs模式:
- **直接交接**: 固定的顺序流转
- **条件交接**: 根据条件动态路由
- **循环交接**: 支持往返和迭代
- **终止交接**: 判断完成并结束

**运行**: `uv run python 07_handoffs_patterns.py`

### 8. 状态管理策略 (`08_state_management.py`)
**场景**: 武汉图书馆管理系统

演示两种状态管理策略:
- **共享状态模式**: 所有智能体共享同一状态
- **私有状态模式**: 使用子图实现信息隔离

**运行**: `uv run python 08_state_management.py`

## 运行所有示例

```bash
# PowerShell
1..8 | ForEach-Object { uv run python "0${_}_*.py" }

# Bash
for i in {01..08}; do uv run python ${i}_*.py; done
```

## 代码特点

1. ✅ **真实LLM调用**: 使用DeepSeek API,展示真实的多智能体交互
2. ✅ **武汉元素**: 所有场景使用武汉本地元素(黄鹤楼、热干面、武汉大学等)
3. ✅ **详细注释**: 代码注释详细,适合学习和参考
4. ✅ **循序渐进**: 从简单到复杂,逐步展示多智能体系统的设计模式
5. ✅ **可运行**: 所有示例都经过测试,可以直接运行

## 技术要点

- **LangGraph**: 多智能体编排框架
- **Command对象**: 控制流和状态更新的统一接口
- **create_agent**: 创建ReAct风格的智能体
- **Handoffs**: 智能体间的任务转交机制
- **子图(Subgraph)**: 实现模块化和状态隔离
- **状态管理**: 共享状态vs私有状态的权衡

## 学习路径

建议按以下顺序学习:
1. 01 - 理解单智能体的局限性
2. 02 - 学习Network架构的灵活性
3. 03 - 掌握Supervisor架构的控制性
4. 04 - 了解Tool-calling变体的简洁性
5. 05 - 理解Hierarchical架构的可扩展性
6. 06 - 学习Custom Workflow的灵活性
7. 07 - 深入理解Handoffs的四种模式
8. 08 - 掌握状态管理的两种策略

## 测试结果

所有示例已通过测试,运行正常:
- ✅ 01_single_agent_limitation.py
- ✅ 02_network_architecture.py
- ✅ 03_supervisor_architecture.py
- ✅ 04_tool_calling_variant.py
- ✅ 05_hierarchical_architecture.py
- ✅ 06_custom_workflow.py
- ✅ 07_handoffs_patterns.py
- ✅ 08_state_management.py

