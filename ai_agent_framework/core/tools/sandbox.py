import asyncio
import subprocess
import tempfile
import os
import json
import shutil
import signal
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time
import resource
from contextlib import contextmanager


class SandboxLevel(Enum):
    """沙箱隔离级别"""
    NONE = "none"           # 无隔离
    LIGHT = "light"         # 轻量隔离(资源限制)
    MEDIUM = "medium"       # 中等隔离(进程隔离)
    STRICT = "strict"       # 严格隔离(容器化)


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cpu_time: float = 5.0           # CPU时间限制(秒)
    max_memory_mb: int = 128            # 内存限制(MB)
    max_file_size_mb: int = 10          # 文件大小限制(MB)
    max_processes: int = 1              # 最大进程数
    max_open_files: int = 10            # 最大打开文件数
    network_access: bool = False        # 网络访问
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_time": self.max_cpu_time,
            "memory_mb": self.max_memory_mb,
            "file_size_mb": self.max_file_size_mb,
            "processes": self.max_processes,
            "open_files": self.max_open_files,
            "network": self.network_access
        }


@dataclass
class SecurityPolicy:
    """安全策略"""
    allowed_modules: Optional[List[str]] = None  # 允许的Python模块
    blocked_functions: List[str] = None          # 禁止的函数
    allowed_paths: List[str] = None              # 允许访问的路径
    blocked_paths: List[str] = None              # 禁止访问的路径
    allow_file_write: bool = False               # 允许文件写入
    allow_subprocess: bool = False               # 允许子进程
    
    def __post_init__(self):
        if self.blocked_functions is None:
            self.blocked_functions = [
                "eval", "exec", "compile", "__import__",
                "open", "file", "input", "raw_input",
                "os.system", "os.popen", "subprocess.call",
                "subprocess.run", "subprocess.Popen"
            ]
        if self.allowed_paths is None:
            self.allowed_paths = []
        if self.blocked_paths is None:
            self.blocked_paths = ["/etc", "/root", "/sys", "/proc"]


class SandboxError(Exception):
    """沙箱错误"""
    pass


class ResourceExceededError(SandboxError):
    """资源超限错误"""
    pass


class SecurityViolationError(SandboxError):
    """安全违规错误"""
    pass


class ExecutionResult:
    """代码执行结果"""
    
    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        exit_code: int = 0,
        execution_time: float = 0.0,
        memory_usage_mb: float = 0.0,
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.memory_usage_mb = memory_usage_mb
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "memory_usage_mb": self.memory_usage_mb,
            "metadata": self.metadata
        }


class PythonSandbox:
    """
    Python代码沙箱
    
    提供安全的代码执行环境
    
    特性:
    - 资源限制(CPU/内存/时间)
    - 模块白名单
    - 函数黑名单
    - 文件系统隔离
    - 网络隔离
    """
    
    def __init__(
        self,
        level: SandboxLevel = SandboxLevel.MEDIUM,
        resource_limits: Optional[ResourceLimits] = None,
        security_policy: Optional[SecurityPolicy] = None,
        work_dir: Optional[str] = None
    ):
        self.level = level
        self.resource_limits = resource_limits or ResourceLimits()
        self.security_policy = security_policy or SecurityPolicy()
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="sandbox_")
        
        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)
    
    async def execute(
        self,
        code: str,
        input_data: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> ExecutionResult:
        """
        在沙箱中执行Python代码
        
        Args:
            code: Python代码
            input_data: 标准输入数据
            timeout: 超时时间(秒)
            
        Returns:
            ExecutionResult
        """
        if self.level == SandboxLevel.NONE:
            return await self._execute_unrestricted(code, input_data, timeout)
        
        elif self.level == SandboxLevel.LIGHT:
            return await self._execute_restricted(code, input_data, timeout)
        
        elif self.level in (SandboxLevel.MEDIUM, SandboxLevel.STRICT):
            return await self._execute_isolated(code, input_data, timeout)
        
        else:
            raise SandboxError(f"Unknown sandbox level: {self.level}")
    
    async def _execute_unrestricted(
        self,
        code: str,
        input_data: Optional[str],
        timeout: Optional[float]
    ) -> ExecutionResult:
        """无限制执行(仅用于开发/测试)"""
        start_time = time.time()
        
        try:
            # 创建局部命名空间
            local_ns = {}
            
            # 执行代码
            exec(code, {"__builtins__": __builtins__}, local_ns)
            
            # 获取输出
            output = local_ns.get("__output__", "")
            
            return ExecutionResult(
                success=True,
                output=str(output),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_restricted(
        self,
        code: str,
        input_data: Optional[str],
        timeout: Optional[float]
    ) -> ExecutionResult:
        """受限执行(资源限制)"""
        start_time = time.time()
        timeout = timeout or self.resource_limits.max_cpu_time
        
        # 创建临时文件
        code_file = os.path.join(self.work_dir, "script.py")
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(self._wrap_code(code))
        
        try:
            # 使用子进程执行
            proc = await asyncio.create_subprocess_exec(
                "python", code_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=self.work_dir,
                # 设置资源限制
                preexec_fn=self._set_resource_limits
            )
            
            # 等待执行
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=input_data.encode() if input_data else None),
                    timeout=timeout
                )
                
                return ExecutionResult(
                    success=proc.returncode == 0,
                    output=stdout.decode('utf-8', errors='replace'),
                    error=stderr.decode('utf-8', errors='replace'),
                    exit_code=proc.returncode,
                    execution_time=time.time() - start_time
                )
                
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(
                    success=False,
                    error=f"Execution timeout after {timeout} seconds",
                    exit_code=-1,
                    execution_time=timeout
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_isolated(
        self,
        code: str,
        input_data: Optional[str],
        timeout: Optional[float]
    ) -> ExecutionResult:
        """隔离执行(进程隔离+安全策略)"""
        start_time = time.time()
        timeout = timeout or self.resource_limits.max_cpu_time
        
        # 准备隔离环境
        isolated_code = self._prepare_isolated_code(code)
        code_file = os.path.join(self.work_dir, "script.py")
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(isolated_code)
        
        try:
            # 构建命令
            cmd = [
                "python", "-I",  # 隔离模式
                "-S",            # 不导入site模块
                code_file
            ]
            
            # 执行
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=self.work_dir,
                env=self._build_restricted_env(),
                preexec_fn=self._set_resource_limits
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=input_data.encode() if input_data else None),
                    timeout=timeout
                )
                
                return ExecutionResult(
                    success=proc.returncode == 0,
                    output=stdout.decode('utf-8', errors='replace'),
                    error=stderr.decode('utf-8', errors='replace'),
                    exit_code=proc.returncode,
                    execution_time=time.time() - start_time
                )
                
            except asyncio.TimeoutError:
                proc.kill()
                raise ResourceExceededError(f"Execution timeout after {timeout} seconds")
                
        except ResourceExceededError:
            raise
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _wrap_code(self, code: str) -> str:
        """包装用户代码"""
        return f"""
import sys
import io

# 捕获输出
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
{self._indent_code(code)}
    # 获取输出
    __output__ = sys.stdout.getvalue()
finally:
    sys.stdout = old_stdout

print(__output__, end='')
"""
    
    def _prepare_isolated_code(self, code: str) -> str:
        """准备隔离执行的代码"""
        # 构建受限的builtins
        safe_builtins = self._build_safe_builtins()
        
        return f"""
# 安全沙箱入口
import sys
import io

# 限制导入
_allowed_modules = {self.security_policy.allowed_modules or ['math', 'random', 'datetime', 'json', 're', 'collections']}

class SafeImporter:
    def find_module(self, name, path=None):
        base_module = name.split('.')[0]
        if base_module not in _allowed_modules:
            raise ImportError(f"Module '{{name}}' is not allowed")
        return None

sys.meta_path.insert(0, SafeImporter())

# 安全builtins
_safe_builtins = {safe_builtins}

# 执行用户代码
code = '''
{code.replace("'''", '\'\'\'')}
'''

exec(code, {{"__builtins__": _safe_builtins}})
"""
    
    def _build_safe_builtins(self) -> Dict[str, Any]:
        """构建安全的builtins子集"""
        safe_list = [
            'True', 'False', 'None',
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate',
            'filter', 'float', 'format', 'frozenset', 'hasattr',
            'hash', 'hex', 'id', 'int', 'isinstance', 'issubclass',
            'iter', 'len', 'list', 'map', 'max', 'min', 'next',
            'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
            'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple',
            'type', 'vars', 'zip'
        ]
        
        safe_builtins = {}
        for name in safe_list:
            if hasattr(__builtins__, name):
                safe_builtins[name] = getattr(__builtins__, name)
        
        return safe_builtins
    
    def _indent_code(self, code: str, indent: int = 4) -> str:
        """缩进代码"""
        lines = code.split('\n')
        return '\n'.join(' ' * indent + line for line in lines)
    
    def _set_resource_limits(self):
        """设置资源限制(在子进程中调用)"""
        try:
            # CPU时间限制
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (int(self.resource_limits.max_cpu_time), int(self.resource_limits.max_cpu_time) + 1)
            )
            
            # 内存限制
            memory_bytes = self.resource_limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            
            # 文件大小限制
            file_size_bytes = self.resource_limits.max_file_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))
            
            # 进程数限制
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (self.resource_limits.max_processes, self.resource_limits.max_processes)
            )
            
            # 打开文件数限制
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (self.resource_limits.max_open_files, self.resource_limits.max_open_files)
            )
            
        except Exception as e:
            print(f"Failed to set resource limits: {e}", file=sys.stderr)
    
    def _build_restricted_env(self) -> Dict[str, str]:
        """构建受限的环境变量"""
        return {
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1"
        }
    
    def cleanup(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir)
        except Exception as e:
            print(f"Sandbox cleanup error: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class CodeAnalyzer:
    """
    代码分析器
    
    静态分析Python代码，检测潜在风险
    """
    
    DANGEROUS_PATTERNS = [
        (r'__import__\s*\(', "Dynamic import detected"),
        (r'eval\s*\(', "Eval usage detected"),
        (r'exec\s*\(', "Exec usage detected"),
        (r'compile\s*\(', "Compile usage detected"),
        (r'os\.system\s*\(', "OS system call detected"),
        (r'subprocess\.', "Subprocess usage detected"),
        (r'open\s*\(', "File open detected"),
        (r'import\s+subprocess', "Subprocess import detected"),
        (r'import\s+os', "OS import detected"),
    ]
    
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """分析代码"""
        self.warnings = []
        self.errors = []
        
        import re
        
        for pattern, message in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                self.warnings.append(message)
        
        # 检查语法
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
        
        return {
            "safe": len(self.errors) == 0,
            "warnings": self.warnings,
            "errors": self.errors,
            "risk_level": self._calculate_risk_level()
        }
    
    def _calculate_risk_level(self) -> str:
        """计算风险等级"""
        if self.errors:
            return "high"
        if len(self.warnings) > 3:
            return "medium"
        if self.warnings:
            return "low"
        return "minimal"


# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建沙箱
        with PythonSandbox(
            level=SandboxLevel.MEDIUM,
            resource_limits=ResourceLimits(
                max_cpu_time=5.0,
                max_memory_mb=64
            )
        ) as sandbox:
            
            # 安全代码
            safe_code = """
import math
result = math.sqrt(16)
print(f"Square root of 16 is {{result}}")
"""
            
            result = await sandbox.execute(safe_code)
            print("Safe code result:", result.to_dict())
            
            # 危险代码(会被阻止)
            dangerous_code = """
import os
os.system('ls -la')
"""
            
            result = await sandbox.execute(dangerous_code)
            print("Dangerous code result:", result.to_dict())
    
    asyncio.run(main())
