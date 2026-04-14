"""
工具模块
提供文件操作和命令执行等工具
"""
import os
import subprocess
from pathlib import Path
from langchain_core.tools import tool


# 工作目录配置
WORKSPACE_DIR = Path(__file__).parent.parent.parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)

# 安全配置
ALLOWED_COMMANDS = ["python", "uv", "pip", "ls", "dir", "cat", "type", "echo"]
FORBIDDEN_PATTERNS = ["rm", "del", "format", "shutdown", "reboot"]
COMMAND_TIMEOUT = 30


@tool
def read_file(file_path: str) -> str:
    """读取文件内容
    
    Args:
        file_path: 文件路径（相对于workspace目录）
        
    Returns:
        文件内容
    """
    try:
        full_path = WORKSPACE_DIR / file_path
        
        if not full_path.exists():
            return f"错误：文件不存在 - {file_path}"
        
        if not full_path.is_file():
            return f"错误：路径不是文件 - {file_path}"
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"成功读取文件 {file_path}:\n\n{content}"
    
    except Exception as e:
        return f"读取文件失败：{str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """写入文件内容
    
    Args:
        file_path: 文件路径（相对于workspace目录）
        content: 要写入的内容
        
    Returns:
        操作结果
    """
    try:
        full_path = WORKSPACE_DIR / file_path
        
        # 创建父目录
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"成功写入文件：{file_path}"
    
    except Exception as e:
        return f"写入文件失败：{str(e)}"


@tool
def list_files(directory: str = ".") -> str:
    """列出目录中的文件
    
    Args:
        directory: 目录路径（相对于workspace目录）
        
    Returns:
        文件列表
    """
    try:
        full_path = WORKSPACE_DIR / directory
        
        if not full_path.exists():
            return f"错误：目录不存在 - {directory}"
        
        if not full_path.is_dir():
            return f"错误：路径不是目录 - {directory}"
        
        files = []
        for item in full_path.iterdir():
            if item.is_file():
                files.append(f"  文件: {item.name}")
            elif item.is_dir():
                files.append(f"  目录: {item.name}/")
        
        if not files:
            return f"目录 {directory} 为空"
        
        return f"目录 {directory} 的内容:\n" + "\n".join(files)
    
    except Exception as e:
        return f"列出文件失败：{str(e)}"


@tool
def execute_command(command: str) -> str:
    """执行终端命令
    
    Args:
        command: 要执行的命令
        
    Returns:
        命令执行结果
    """
    try:
        # 安全检查
        cmd_lower = command.lower()
        
        # 检查是否包含危险命令
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in cmd_lower:
                return f"安全错误：禁止执行包含 '{pattern}' 的命令"
        
        # 检查命令是否在允许列表中
        cmd_parts = command.split()
        if cmd_parts and cmd_parts[0] not in ALLOWED_COMMANDS:
            return f"安全错误：命令 '{cmd_parts[0]}' 不在允许列表中。允许的命令：{', '.join(ALLOWED_COMMANDS)}"
        
        # 在workspace目录中执行命令
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT
        )
        
        output = []
        if result.stdout:
            output.append(f"标准输出:\n{result.stdout}")
        if result.stderr:
            output.append(f"标准错误:\n{result.stderr}")
        if result.returncode != 0:
            output.append(f"返回码: {result.returncode}")
        
        if not output:
            return "命令执行成功（无输出）"
        
        return "\n".join(output)
    
    except subprocess.TimeoutExpired:
        return f"命令执行超时（超过{COMMAND_TIMEOUT}秒）"
    except Exception as e:
        return f"命令执行失败：{str(e)}"


# 导出所有工具
tools = [read_file, write_file, list_files, execute_command]

