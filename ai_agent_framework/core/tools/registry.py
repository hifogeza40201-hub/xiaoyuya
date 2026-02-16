from typing import Dict, List, Any, Optional, Callable, Union, Type, get_type_hints
from dataclasses import dataclass, field
from enum import Enum
import inspect
import json
import asyncio
from functools import wraps
import time
from abc import ABC, abstractmethod


class ToolCategory(Enum):
    """工具分类"""
    WEB = "web"              # 网络工具
    FILE = "file"            # 文件操作
    DATA = "data"            # 数据处理
    CALCULATION = "calc"     # 计算
    COMMUNICATION = "comm"   # 通信
    SYSTEM = "system"        # 系统操作
    CUSTOM = "custom"        # 自定义


class ToolRiskLevel(Enum):
    """工具风险等级"""
    SAFE = "safe"            # 安全，只读
    NORMAL = "normal"        # 正常，有限写操作
    RISKY = "risky"          # 有风险，可能影响系统
    DANGEROUS = "dangerous"  # 危险，需要沙箱


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None
    enum_values: Optional[List[Any]] = None  # 枚举值
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self._get_json_type(),
            "description": self.description
        }
        if not self.required:
            result["required"] = False
        if self.default is not None:
            result["default"] = self.default
        if self.enum_values:
            result["enum"] = self.enum_values
        return result
    
    def _get_json_type(self) -> str:
        """转换为JSON Schema类型"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_map.get(self.type, "string")


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    category: ToolCategory = ToolCategory.CUSTOM
    risk_level: ToolRiskLevel = ToolRiskLevel.NORMAL
    parameters: List[ToolParameter] = field(default_factory=list)
    return_type: Type = str
    examples: List[Dict[str, Any]] = field(default_factory=list)
    timeout: float = 30.0
    cache_enabled: bool = False
    cache_ttl: int = 300  # 秒
    rate_limit: Optional[int] = None  # 每分钟调用次数


class ToolResult:
    """工具执行结果"""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def success(cls, data: Any, metadata: Dict[str, Any] = None):
        return cls(True, data=data, metadata=metadata)
    
    @classmethod
    def failure(cls, error: str, metadata: Dict[str, Any] = None):
        return cls(False, error=error, metadata=metadata)


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.call_count = 0
        self.last_called = None
        self._cache: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取OpenAI Function Calling格式的Schema"""
        return {
            "type": "function",
            "function": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: p.to_dict() for p in self.metadata.parameters
                    },
                    "required": [
                        p.name for p in self.metadata.parameters if p.required
                    ]
                }
            }
        }
    
    def _get_cache_key(self, kwargs: Dict[str, Any]) -> str:
        """生成缓存键"""
        return hash(json.dumps(kwargs, sort_keys=True))
    
    def _get_from_cache(self, kwargs: Dict[str, Any]) -> Optional[Any]:
        """从缓存获取"""
        if not self.metadata.cache_enabled:
            return None
        
        key = self._get_cache_key(kwargs)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.metadata.cache_ttl:
                return result
            else:
                del self._cache[key]
        return None
    
    def _save_to_cache(self, kwargs: Dict[str, Any], result: Any):
        """保存到缓存"""
        if self.metadata.cache_enabled:
            key = self._get_cache_key(kwargs)
            self._cache[key] = (result, time.time())


class ToolRegistry:
    """
    工具注册中心
    
    功能:
    - 工具注册与发现
    - 权限管理
    - 使用统计
    - 自动文档生成
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._permissions: Dict[str, List[str]] = {}  # 角色->工具列表
        self._stats: Dict[str, Dict[str, Any]] = {}
    
    def register(self, tool: BaseTool, allowed_roles: List[str] = None):
        """注册工具"""
        self._tools[tool.metadata.name] = tool
        self._categories[tool.metadata.category].append(tool.metadata.name)
        
        # 初始化统计
        self._stats[tool.metadata.name] = {
            "calls": 0,
            "errors": 0,
            "avg_duration": 0.0
        }
        
        # 设置权限
        if allowed_roles:
            for role in allowed_roles:
                if role not in self._permissions:
                    self._permissions[role] = []
                self._permissions[role].append(tool.metadata.name)
    
    def unregister(self, name: str):
        """注销工具"""
        if name in self._tools:
            tool = self._tools[name]
            self._categories[tool.metadata.category].remove(name)
            del self._tools[name]
            del self._stats[name]
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        role: Optional[str] = None
    ) -> List[str]:
        """列出可用工具"""
        if role and role in self._permissions:
            tools = self._permissions[role]
        else:
            tools = list(self._tools.keys())
        
        if category:
            tools = [t for t in tools if t in self._categories[category]]
        
        return tools
    
    def get_schemas(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取工具Schemas (用于Function Calling)"""
        tools = self.list_tools(role=role)
        return [self._tools[t].get_schema() for t in tools]
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具Schema"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def check_permission(self, tool_name: str, role: str) -> bool:
        """检查权限"""
        if role not in self._permissions:
            return True  # 默认允许
        return tool_name in self._permissions[role]


class ToolExecutor:
    """
    工具执行器
    
    功能:
    - 参数验证
    - 错误处理
    - 重试机制
    - 超时控制
    - 结果格式化
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        max_retries: int = 3,
        default_timeout: float = 30.0
    ):
        self.registry = registry
        self.max_retries = max_retries
        self.default_timeout = default_timeout
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        role: str = "default",
        request_id: Optional[str] = None
    ) -> ToolResult:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 调用参数
            role: 用户角色(用于权限检查)
            request_id: 请求ID(用于追踪)
        """
        # 查找工具
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult.failure(f"Tool '{tool_name}' not found")
        
        # 权限检查
        if not self.registry.check_permission(tool_name, role):
            return ToolResult.failure(
                f"Permission denied: role '{role}' cannot use tool '{tool_name}'"
            )
        
        # 参数验证
        validation_result = self._validate_parameters(tool, parameters)
        if not validation_result["valid"]:
            return ToolResult.failure(
                f"Parameter validation failed: {validation_result['error']}"
            )
        
        # 检查缓存
        cached_result = tool._get_from_cache(parameters)
        if cached_result:
            return ToolResult.success(
                cached_result,
                metadata={"cached": True, "request_id": request_id}
            )
        
        # 执行工具(带重试)
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    tool.execute(**parameters),
                    timeout=tool.metadata.timeout or self.default_timeout
                )
                
                # 更新统计
                duration = time.time() - start_time
                self._update_stats(tool_name, True, duration)
                
                # 缓存成功结果
                if result.success and tool.metadata.cache_enabled:
                    tool._save_to_cache(parameters, result.data)
                
                return ToolResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata={
                        "request_id": request_id,
                        "attempt": attempt + 1,
                        "duration": duration,
                        **result.metadata
                    }
                )
                
            except asyncio.TimeoutError:
                last_error = "Execution timeout"
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避
        
        # 所有重试失败
        self._update_stats(tool_name, False, time.time() - start_time)
        return ToolResult.failure(
            f"Failed after {self.max_retries} attempts. Last error: {last_error}",
            metadata={"request_id": request_id, "attempts": self.max_retries}
        )
    
    def _validate_parameters(
        self,
        tool: BaseTool,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证参数"""
        schema_params = {p.name: p for p in tool.metadata.parameters}
        
        # 检查必需参数
        for name, param in schema_params.items():
            if param.required and name not in parameters:
                return {
                    "valid": False,
                    "error": f"Missing required parameter: {name}"
                }
        
        # 检查类型
        for name, value in parameters.items():
            if name in schema_params:
                expected_type = schema_params[name].type
                if not isinstance(value, expected_type):
                    try:
                        # 尝试类型转换
                        parameters[name] = expected_type(value)
                    except (ValueError, TypeError):
                        return {
                            "valid": False,
                            "error": f"Parameter '{name}' should be {expected_type.__name__}, got {type(value).__name__}"
                        }
        
        return {"valid": True}
    
    def _update_stats(self, tool_name: str, success: bool, duration: float):
        """更新统计信息"""
        stats = self.registry._stats.get(tool_name, {})
        stats["calls"] = stats.get("calls", 0) + 1
        if not success:
            stats["errors"] = stats.get("errors", 0) + 1
        
        # 更新平均执行时间
        prev_avg = stats.get("avg_duration", 0)
        calls = stats["calls"]
        stats["avg_duration"] = (prev_avg * (calls - 1) + duration) / calls


# 装饰器 - 简化工具定义
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.CUSTOM,
    risk_level: ToolRiskLevel = ToolRiskLevel.NORMAL,
    cache_enabled: bool = False,
    timeout: float = 30.0
):
    """
    工具装饰器
    
    自动从函数签名提取参数定义
    
    Example:
        @tool(description="Search web content")
        async def search(query: str, limit: int = 10) -> str:
            return f"Results for {query}"
    """
    def decorator(func: Callable) -> BaseTool:
        # 获取函数签名
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # 构建参数定义
        params = []
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            param_desc = f"Parameter {param_name}"
            
            params.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=param_desc,
                required=param.default is inspect.Parameter.empty,
                default=param.default if param.default is not inspect.Parameter.empty else None
            ))
        
        # 构建元数据
        metadata = ToolMetadata(
            name=name or func.__name__,
            description=description or func.__doc__ or f"Tool: {func.__name__}",
            category=category,
            risk_level=risk_level,
            parameters=params,
            return_type=type_hints.get('return', str),
            cache_enabled=cache_enabled,
            timeout=timeout
        )
        
        # 创建工具类
        class DynamicTool(BaseTool):
            async def execute(self, **kwargs) -> ToolResult:
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(**kwargs)
                    else:
                        result = func(**kwargs)
                    return ToolResult.success(result)
                except Exception as e:
                    return ToolResult.failure(str(e))
        
        return DynamicTool(metadata)
    
    return decorator


# 内置工具示例
class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    def __init__(self):
        super().__init__(ToolMetadata(
            name="web_search",
            description="Search for information on the web",
            category=ToolCategory.WEB,
            risk_level=ToolRiskLevel.SAFE,
            parameters=[
                ToolParameter("query", str, "Search query", required=True),
                ToolParameter("limit", int, "Number of results", required=False, default=5)
            ],
            cache_enabled=True,
            cache_ttl=600
        ))
    
    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        limit = kwargs.get("limit", 5)
        
        # 模拟搜索
        results = [
            {"title": f"Result {i} for '{query}'", "url": f"https://example.com/{i}"}
            for i in range(limit)
        ]
        
        return ToolResult.success(results)


class CalculatorTool(BaseTool):
    """计算器工具"""
    
    def __init__(self):
        super().__init__(ToolMetadata(
            name="calculate",
            description="Perform mathematical calculations",
            category=ToolCategory.CALCULATION,
            risk_level=ToolRiskLevel.SAFE,
            parameters=[
                ToolParameter("expression", str, "Mathematical expression to evaluate", required=True)
            ]
        ))
    
    async def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "")
        
        # 安全检查 - 只允许基本数学运算
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return ToolResult.failure("Invalid characters in expression")
        
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.failure(f"Calculation error: {str(e)}")


class FileReadTool(BaseTool):
    """文件读取工具"""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        super().__init__(ToolMetadata(
            name="file_read",
            description="Read content from a file",
            category=ToolCategory.FILE,
            risk_level=ToolRiskLevel.NORMAL,
            parameters=[
                ToolParameter("path", str, "File path to read", required=True),
                ToolParameter("encoding", str, "File encoding", required=False, default="utf-8")
            ]
        ))
        self.allowed_paths = allowed_paths or []
    
    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        encoding = kwargs.get("encoding", "utf-8")
        
        # 路径安全检查
        if self.allowed_paths and not any(
            path.startswith(allowed) for allowed in self.allowed_paths
        ):
            return ToolResult.failure(f"Access denied: path '{path}' not allowed")
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            return ToolResult.success(content)
        except Exception as e:
            return ToolResult.failure(str(e))


# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建注册中心
        registry = ToolRegistry()
        
        # 注册工具
        registry.register(WebSearchTool())
        registry.register(CalculatorTool())
        
        # 使用装饰器定义工具
        @tool(description="Get current time")
        def get_current_time(timezone: str = "UTC") -> str:
            from datetime import datetime
            return datetime.now().strftime(f"%Y-%m-%d %H:%M:%S ({timezone})")
        
        time_tool = get_current_time
        registry.register(time_tool)
        
        # 创建执行器
        executor = ToolExecutor(registry)
        
        # 执行工具
        result = await executor.execute(
            "calculate",
            {"expression": "2 + 2 * 3"}
        )
        print(f"Calculation result: {result.to_dict()}")
        
        # 获取工具Schemas
        schemas = registry.get_all_schemas()
        print(f"\nAvailable tools: {len(schemas)}")
        for schema in schemas:
            print(f"  - {schema['function']['name']}")
    
    asyncio.run(main())
