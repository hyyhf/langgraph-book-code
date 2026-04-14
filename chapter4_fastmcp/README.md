# 第4章：FastMCP 工具生态与系统集成实战

本章代码演示了如何使用最新的 [FastMCP](https://github.com/jlowin/fastmcp) 框架，遵循模型上下文协议 (Model Context Protocol, MCP) 来构建和测试智能体工具服务器。

MCP 协议允许你在一个地方编写各种工具、资源和提示词，并通过**标准输入输出 (STDIO)** 或 **HTTP/SSE** 等安全标准的传输协议向任何兼容 MCP 的智能体甚至其他系统开放访问权限。

## 目录结构说明

- `server/stdio_server.py`：基于 STDIO 传输协议的极简 MCP 服务端（主要提供基础的数学计算能力）。
- `server/http_server.py`：基于 HTTP (Streamable) 传输协议的 MCP 服务端（提供实时的在线天气查询能力）。
- `client/mcp_config.json`：MCP 客户端访问协议的连接配置文件。
- `client/test_all.py`：使用 Python 测试脚本作为客户端连接测试 stdio 和 http 两种通信协议 Server 的收发。
- `client/test_amap.py`：进阶的高德地图工具客户端集成演示代码。

---

## 快速运行指南

### 1. 环境准备

请确保你在项目根目录下已经配置好了 Python 虚拟环境和必要的依赖库。如果你还没有安装环境，可以在根目录运行：

```bash
uv sync
```

接着，进入当前第4章的目录：

```bash
cd chapter4_fastmcp
```

### 2. 本地测试与运行顺序

因为 HTTP Server 是一个驻留运行的 Web 服务程序，我们需要先启动它，然后再运行相关的测试脚本。

#### **步骤一：启动 HTTP Server (天气查询服务)**

在当前目录打开第一个终端，执行：

```bash
uv run server/http_server.py
```
> **提示**：启动成功后，终端将保持运行，HTTP 服务会监听在 `http://127.0.0.1:8000`。
> *(注意：STDIO 协议的计算器 Server 无需手动预先启动，MCP Client 会在通过 config.json 连接时自动拉起对应的子进程)*

#### **步骤二：运行客户端自动化测试**

然后再打开**第二个终端**，同样确保你在 `chapter4_fastmcp` 目录下，执行全量自动化测试脚本：

```bash
uv run client/test_all.py
```

如果看到以下类似输出，说明你的 MCP 客户端与两种类型的服务器之间的通信测试全部通过：

```text
测试STDIO服务器(计算器)
============================================================
✓ add(10, 5) = 15.0
✓ multiply(7, 8) = 56.0

测试HTTP服务器(天气查询)
============================================================
✓ 天气查询成功: Beijing 当前天气: ...
============================================================
✓ 所有测试通过!
```

#### **步骤三：运行进阶的高德地图集成测试**

如果你在根目录的 `.env` 中正确配置了高德地图的 API 密钥，还可以运行独立的高德地图客户端能力测试：

```bash
uv run client/test_amap.py
```
