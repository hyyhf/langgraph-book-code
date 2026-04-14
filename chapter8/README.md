# 第8章：调试与可视化集成 (LangSmith & LangGraph Studio)

本章代码演示了如何对 LangGraph 智能体进行全链路观测（Tracing）、精细化调试，以及如何使用 LangGraph Studio 这一强大的专用可视化工具。

当智能体的节点数与边数增加时，状态管理与故障排查变得异常困难。因此，接入 LangSmith 了解大模型的内部调用与思考细节，并在 LangGraph Studio 中进行时间旅行（Time Travel）和数据重现，是迈向生产级不可或缺的重要一步。

## 文件结构说明

- `8_1_langsmith_tracing_basic.py`：展示了如何在纯代码中调用并接入 LangSmith 测试，你可以观察到基础的 Tracing 和 Token 监控。
- `8_2_studio_visualization.py`：提供了一个二手书交易助手图，用于在 LangGraph Studio 中观察图流程控制（包含状态修改机制）。
- `8_3_advanced_tracing.py`：提供了一个包含平行搜索和多步骤推荐的并发子图项目，非常适合在 Studio 中观测并发追踪（Trace）。
- `langgraph.json`：LangGraph CLI 启动配置文件，定义了如何将我们的图结构通过 API 或 Studio 暴露出去。

---

## 运行准则：非常重要！

本章的核心是使用 `langgraph` 命令行工具来启动本地可视化服务。由于该工具是在依赖同步时安装在本地虚拟环境中的，如果在外部终端直接执行 `langgraph dev`，系统很可能会提示**“无法识别命令”**。

因此，**启动前必须先激活虚拟环境！**

### 1. 环境准备与激活

确保你目前处于项目根目录。

如果你使用的是 Windows PowerShell，请执行以下命令激活环境（注意路径）：

```powershell
.\.venv\Scripts\activate
```

> **注意：** 激活成功后，你的命令行提示符前面应该会出现 `(%根目录名%)` 的字样。
> （如果是 macOS/Linux 系统，请运行 `source .venv/bin/activate`）

进入当前章节的目录：

```powershell
cd chapter8
```

### 2. 检查配置密钥

因为我们需要将数据推送到 LangSmith，所以在上一步激活虚拟环境前（或任意时刻），请确保你在根目录的 `.env` 文件中开启了 LangSmith：

```env
LANGSMITH_API_KEY="你的LangSmith密钥"
```

如果没有密钥，请前往 [Smith.langchain.com](https://smith.langchain.com) 注册并免费申请一个。

---

## 快速运行指南

### 基础演示：运行脚本获取链路追踪

在激活好虚拟环境并在 `chapter8` 目录中后，可以直接通过 Python 执行基础脚本（你可以在自己的 LangSmith 云控制台上查看到调用链）：

```bash
uv 8_1_langsmith_tracing_basic.py
```

### 进阶可视化：启动 LangGraph Studio（强推！）

为了启动图形化调试环境，并且允许它热重载我们定义的 `book_trade`（二手书交易助手）和 `activity_recommender`（周末活动推荐）两张图，请执行以下命令：

```bash
langgraph dev
```

**运行预期与体验：**
执行上述命令后，终端将输出一组正在运行的本地 HTTP 服务地址（如 `http://127.0.0.1:2024`，端口如果有占用会自动顺延），以及一条自动指向 LangGraph Studio Web 端的重定向链接（如：`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`）。

```bash
INFO:langgraph_api.cli:

        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs

This in-memory server is designed for development and testing.
For production use, please use LangSmith Deployment.
```

打开游览器访问该链接，你将进入可视化的开发面板：
1. 你可以在这个面板直观地与你的智能体聊天。
2. 可以在右侧观测所有中间状态（State）的动态更新。
3. 如果发生了调用错误或者想要回滚，可以在状态历史上“点击节点”直接覆写参数，体验“时间漫游”与断点继续。

> **结束实验**：如需停止运行，直接在命令行中按下 `Ctrl + C` 即可。此时可输入 `deactivate` 退出虚拟环境。
