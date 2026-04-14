# 第6章代码示例: LangGraph进阶 - 状态、流与记忆

本目录包含第6章的所有代码示例,演示LangGraph的三大进阶特性:持久化、流式输出和记忆管理。

## 🔧 环境配置

### 1. 安装依赖

```bash
cd code_for_learning
uv sync
```

### 2. 配置DeepSeek API

本章所有代码都使用**DeepSeek大模型API**。请确保`.env`文件中包含以下配置:

```env
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL_NAME=deepseek-chat
```

**重要提示**:
- ✅ 所有代码都使用真实的LLM API,会产生费用
- ✅ Windows系统已自动处理UTF-8编码,支持emoji显示
- ✅ 代码通过`ChatOpenAI`类的`base_url`参数连接DeepSeek

## 📁 文件列表

### 持久化示例

#### 01_persistence_basic.py
**基础持久化功能演示**
- 使用AsyncSqliteSaver实现对话历史持久化
- 演示多轮对话的状态保存和恢复
- 展示多用户并发场景下的状态隔离
- 查看检查点历史

**运行方式:**
```bash
uv run code_for_learning/chapter6/01_persistence_basic.py
```

**关键知识点:**
- AsyncSqliteSaver的使用
- thread_id的作用
- 检查点的自动创建和恢复
- 多用户状态隔离

---

#### 02_persistence_advanced.py
**持久化进阶示例**
- 使用SQLite文件数据库进行持久化
- 演示程序重启后恢复对话
- 介绍PostgreSQL数据库的使用(含配置说明)
- 展示多种线程管理策略

**运行方式:**
```bash
uv run code_for_learning/chapter6/02_persistence_advanced.py
```

**关键知识点:**
- 文件数据库 vs 内存数据库
- 程序重启后的状态恢复
- PostgreSQL配置(生产环境)
- 线程ID设计策略

---

### 流式输出示例

#### 03_streaming_modes.py
**流式输出模式演示**
- values模式:输出完整状态快照
- updates模式:只输出状态变化
- custom模式:自定义流式数据
- 多模式组合使用
- 不同模式的对比分析

**运行方式:**
```bash
uv run code_for_learning/chapter6/03_streaming_modes.py
```

**关键知识点:**
- stream_mode参数的使用
- values vs updates的区别
- get_stream_writer()发送自定义数据
- 多模式同时使用

---

#### 04_streaming_research_assistant.py
**流式输出实战 - 智能研究助手**
- 模拟多步骤研究流程(搜索、分析、摘要)
- 实时发送进度信息和状态更新
- 展示流式输出在实际应用中的价值
- 对比有无流式输出的用户体验差异

**运行方式:**
```bash
uv run code_for_learning/chapter6/04_streaming_research_assistant.py
```

**关键知识点:**
- 在实际应用中使用流式输出
- 发送进度条和状态信息
- 提升用户体验
- 实时反馈的重要性

---

### 记忆管理示例

#### 05_memory_trim_messages.py
**消息裁剪功能演示**
- 按消息数量裁剪
- 按token数量裁剪
- 保留系统消息的策略
- 在图节点中集成裁剪逻辑
- 高级裁剪策略(start_on, end_on等)

**运行方式:**
```bash
uv run code_for_learning/chapter6/05_memory_trim_messages.py
```

**关键知识点:**
- trim_messages函数的使用
- 不同裁剪策略的对比
- token计数器的配置
- 保留系统消息和关键上下文

---

#### 06_memory_remove_and_summary.py
**消息删除和摘要功能演示**
- 删除特定消息
- 删除所有消息
- 实现"撤回"功能
- 生成对话摘要
- 摘要与删除的组合使用

**运行方式:**
```bash
uv run code_for_learning/chapter6/06_memory_remove_and_summary.py
```

**关键知识点:**
- RemoveMessage的使用
- REMOVE_ALL_MESSAGES常量
- update_state方法
- 对话摘要的实现策略

---

#### 07_memory_complete_chatbot.py
**完整的记忆管理聊天机器人**
- 综合演示持久化、流式输出和记忆管理
- 实现智能消息裁剪
- 支持多用户独立记忆
- 支持会话暂停和恢复
- 完整的生产级聊天机器人示例

**运行方式:**
```bash
uv run code_for_learning/chapter6/07_memory_complete_chatbot.py
```

**关键知识点:**
- 三大特性的综合应用
- 生产级聊天机器人的实现
- 多用户场景处理
- 会话管理

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- 已安装uv工具
- 已安装LangGraph相关依赖

### 安装依赖
```bash
cd code_for_learning
uv sync
```

### 运行示例
```bash
# 运行任意示例
uv run code_for_learning/chapter6/01_persistence_basic.py

# 或者进入chapter6目录
cd code_for_learning/chapter6
uv run 01_persistence_basic.py
```

---

## 📚 学习路径建议

### 初学者路径
1. **01_persistence_basic.py** - 理解持久化的基本概念
2. **03_streaming_modes.py** - 了解流式输出的不同模式
3. **05_memory_trim_messages.py** - 学习消息裁剪
4. **07_memory_complete_chatbot.py** - 看完整应用示例

### 进阶路径
1. **02_persistence_advanced.py** - 学习生产环境配置
2. **04_streaming_research_assistant.py** - 实战流式输出
3. **06_memory_remove_and_summary.py** - 高级记忆管理
4. **07_memory_complete_chatbot.py** - 综合应用

---

## 💡 关键概念总结

### 持久化 (Persistence)
- **检查点 (Checkpoint)**: 自动保存图的执行状态
- **线程 (Thread)**: 通过thread_id隔离不同会话
- **存储后端**: SQLite(开发)、PostgreSQL(生产)

### 流式输出 (Streaming)
- **values模式**: 完整状态快照,适合UI渲染
- **updates模式**: 状态增量,适合性能优化
- **custom模式**: 自定义数据,适合进度反馈

### 记忆管理 (Memory Management)
- **消息裁剪**: 控制上下文大小,避免超出LLM限制
- **消息删除**: 隐私保护、错误纠正
- **对话摘要**: 压缩历史,保留关键信息

---

## 🔧 常见问题

### Q: 为什么使用AsyncSqliteSaver而不是SqliteSaver?
A: AsyncSqliteSaver使用异步IO,性能更好,不会阻塞主线程。在现代Python应用中推荐使用异步版本。

### Q: 如何选择合适的流式模式?
A: 
- UI渲染 → values模式
- 性能优化 → updates模式
- 进度反馈 → custom模式
- 复杂场景 → 多模式组合

### Q: 消息裁剪会丢失重要信息吗?
A: 可以通过以下策略避免:
- 设置include_system=True保留系统消息
- 使用对话摘要保存历史关键信息
- 实现多层次记忆系统

### Q: 如何在生产环境部署?
A: 
1. 使用PostgreSQL替代SQLite
2. 配置合适的连接池
3. 实现错误处理和重试机制
4. 监控检查点大小和性能

---

## 📖 相关文档

- [LangGraph官方文档 - 持久化](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph官方文档 - 流式输出](https://docs.langchain.com/oss/python/langgraph/streaming)
- [LangGraph官方文档 - 记忆管理](https://docs.langchain.com/oss/python/langgraph/add-memory)

---

## ⚠️ 注意事项

1. **数据库文件**: 某些示例会创建临时数据库文件,运行后会自动清理
2. **模拟LLM**: 示例中使用模拟的LLM响应,实际应用需要配置真实的LLM API
3. **性能**: 示例中使用time.sleep()模拟延迟,实际应用中应该是真实的异步操作
4. **生产环境**: 示例代码仅用于学习,生产环境需要添加错误处理、日志、监控等

---

## 🤝 贡献

如果发现示例代码有问题或有改进建议,欢迎提出Issue或Pull Request。

