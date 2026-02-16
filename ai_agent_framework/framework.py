from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
import asyncio
import json

# 导入框架组件
from core.react_engine import ReActEngine, ReActStep, ReActStepType
from core.memory import (
    MemoryManager, ShortTermMemory, WorkingMemory,
    LongTermMemory, MemoryType
)
from core.tools.registry import (
    ToolRegistry, ToolExecutor, BaseTool,
    ToolMetadata, ToolCategory, ToolRiskLevel
)
from core.tools.sandbox import (
    PythonSandbox, SandboxLevel, ResourceLimits, SecurityPolicy
)
from core.security import (
    SecurityManager, PermissionManager, AuditLogger,
    Permission, Role, AccessPolicy
)
from multi_agent.orchestrator import (
    AgentCrew, BaseAgent, AgentRole,
    Task, AgentMessage
)


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str = "Agent"
    description: str = "An intelligent agent"
    
    # ReAct配置
    max_iterations: int = 10
    enable_self_correction: bool = True
    
    # 记忆配置
    short_term_capacity: int = 20
    long_term_storage: Optional[str] = None
    
    # 安全配置
    default_role: Role = Role.USER
    sandbox_level: SandboxLevel = SandboxLevel.MEDIUM
    
    # 多Agent配置
    enable_multi_agent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "max_iterations": self.max_iterations,
            "enable_self_correction": self.enable_self_correction,
            "sandbox_level": self.sandbox_level.value
        }


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """聊天接口"""
        pass
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """补全接口"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """嵌入接口"""
        pass


class AgentFramework:
    """
    AI Agent 开发框架主入口
    
    集成所有组件，提供统一的Agent开发接口
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[AgentConfig] = None
    ):
        self.config = config or AgentConfig()
        self.llm_client = llm_client
        
        # 初始化记忆系统
        self.memory = MemoryManager(
            short_term=ShortTermMemory(max_entries=self.config.short_term_capacity),
            working=WorkingMemory(),
            long_term=LongTermMemory(storage_path=self.config.long_term_storage)
        )
        
        # 初始化工具系统
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        
        # 初始化ReAct引擎
        self.react_engine = ReActEngine(
            llm_client=llm_client,
            max_iterations=self.config.max_iterations,
            enable_self_correction=self.config.enable_self_correction
        )
        
        # 初始化沙箱
        self.sandbox = PythonSandbox(
            level=self.config.sandbox_level,
            resource_limits=ResourceLimits(
                max_cpu_time=10.0,
                max_memory_mb=256
            )
        )
        
        # 初始化安全系统
        self.security = SecurityManager()
        
        # 初始化多Agent系统
        self.crew: Optional[AgentCrew] = None
        if self.config.enable_multi_agent:
            self.crew = AgentCrew(name=f"{self.config.name}_Crew")
    
    async def run(
        self,
        query: str,
        user_id: str = "default",
        context: Optional[str] = None,
        use_react: bool = True,
        tools: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        运行Agent处理查询
        
        Args:
            query: 用户查询
            user_id: 用户ID(用于权限检查)
            context: 额外上下文
            use_react: 是否使用ReAct模式
            tools: 本次查询专用工具
            
        Returns:
            包含响应和元数据的字典
        """
        start_time = asyncio.get_event_loop().time()
        
        # 安全检查
        threats = self.security.scan_for_threats(query)
        if threats:
            self.security.audit.log_security_event(
                user_id=user_id,
                event="suspicious_input",
                details={"threats": threats}
            )
        
        # 检索记忆上下文
        memory_context = self.memory.retrieve_context(query)
        formatted_context = self.memory.format_context_for_prompt(memory_context)
        
        # 合并上下文
        full_context = f"{formatted_context}\n\n{context}" if context else formatted_context
        
        # 执行查询
        if use_react:
            result = await self._run_react(
                query=query,
                context=full_context,
                tools=tools,
                user_id=user_id
            )
        else:
            result = await self._run_direct(query, full_context)
        
        # 记录到记忆
        self.memory.add_interaction(query, result["response"])
        
        # 计算执行时间
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # 记录审计日志
        self.security.audit.log(
            event_type="agent_query",
            user_id=user_id,
            action="process_query",
            details={
                "query_length": len(query),
                "use_react": use_react,
                "execution_time": execution_time
            }
        )
        
        return {
            **result,
            "execution_time": execution_time,
            "memory_stats": self.memory.get_stats(),
            "security_context": self.security.get_user_context(user_id)
        }
    
    async def _run_react(
        self,
        query: str,
        context: str,
        tools: Optional[Dict[str, Callable]],
        user_id: str
    ) -> Dict[str, Any]:
        """使用ReAct模式运行"""
        # 收集可用工具
        available_tools = {}
        
        # 从注册中心获取工具
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool and self.security.permissions.check_tool_permission(
                user_id, tool_name
            ):
                available_tools[tool_name] = self._wrap_tool(tool, user_id)
        
        # 添加本次专用工具
        if tools:
            for name, func in tools.items():
                available_tools[name] = func
        
        # 执行ReAct
        result = self.react_engine.execute(query, available_tools, context)
        
        return {
            "response": result["final_answer"],
            "reasoning": result["reasoning_chain"],
            "iterations": result["iterations"],
            "incomplete": result.get("incomplete", False)
        }
    
    async def _run_direct(self, query: str, context: str) -> Dict[str, Any]:
        """直接运行(无ReAct)"""
        messages = [
            {"role": "system", "content": f"You are {self.config.name}. {self.config.description}"},
            {"role": "system", "content": f"Context:\n{context}"} if context else None,
            {"role": "user", "content": query}
        ]
        messages = [m for m in messages if m]
        
        response = await self.llm_client.chat(messages)
        
        return {
            "response": response,
            "reasoning": [],
            "iterations": 1,
            "incomplete": False
        }
    
    def _wrap_tool(self, tool: BaseTool, user_id: str) -> Callable:
        """包装工具以添加安全和审计"""
        async def wrapped(**kwargs):
            # 检查权限
            if not self.security.permissions.check_tool_permission(
                user_id, tool.metadata.name
            ):
                raise PermissionError(f"Tool '{tool.metadata.name}' not allowed")
            
            # 执行工具
            start_time = asyncio.get_event_loop().time()
            result = await self.tool_executor.execute(
                tool_name=tool.metadata.name,
                parameters=kwargs,
                role=user_id
            )
            
            # 记录审计
            duration = asyncio.get_event_loop().time() - start_time
            self.security.audit.log_tool_execution(
                user_id=user_id,
                tool_name=tool.metadata.name,
                parameters=kwargs,
                result=result.data,
                duration_ms=duration * 1000
            )
            
            return result.data if result.success else result.error
        
        return wrapped
    
    def register_tool(
        self,
        tool: BaseTool,
        allowed_roles: List[Role] = None
    ):
        """注册工具"""
        role_names = [r.value for r in (allowed_roles or [])]
        self.tool_registry.register(tool, allowed_roles=role_names)
    
    def create_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: ToolCategory = ToolCategory.CUSTOM
    ) -> BaseTool:
        """从函数创建工具"""
        from core.tools.registry import tool
        
        decorator = tool(
            name=name,
            description=description,
            category=category
        )
        return decorator(func)
    
    async def execute_code(
        self,
        code: str,
        user_id: str = "default",
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        在沙箱中执行代码
        
        Args:
            code: Python代码
            user_id: 用户ID
            input_data: 标准输入
        """
        # 检查权限
        self.security.require_permission(user_id, Permission.CODE_EXECUTE)
        
        # 记录审计
        self.security.audit.log(
            event_type="code_execution",
            user_id=user_id,
            action="execute_python",
            details={"code_length": len(code)}
        )
        
        # 执行
        result = await self.sandbox.execute(code, input_data)
        
        return result.to_dict()
    
    def add_to_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        importance: float = 0.5,
        **kwargs
    ):
        """手动添加记忆"""
        if memory_type == MemoryType.SHORT_TERM:
            self.memory.short_term.add(content, **kwargs)
        elif memory_type == MemoryType.WORKING:
            self.memory.working.add(content, **kwargs)
        else:
            self.memory.long_term.add(content, importance=importance, **kwargs)
    
    def create_crew(self, name: Optional[str] = None) -> AgentCrew:
        """创建多Agent协作组"""
        crew = AgentCrew(name or f"{self.config.name}_Crew")
        
        # 创建默认角色
        from multi_agent.orchestrator import PlannerAgent, ExecutorAgent, CriticAgent
        
        planner = PlannerAgent("Planner", self.llm_client)
        executor = ExecutorAgent("Executor", self.llm_client)
        critic = CriticAgent("Critic", self.llm_client)
        
        crew.add_agent(planner)
        crew.add_agent(executor)
        crew.add_agent(critic)
        
        return crew
    
    def get_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        return {
            "config": self.config.to_dict(),
            "tools": {
                "registered": len(self.tool_registry.list_tools()),
                "list": self.tool_registry.list_tools()
            },
            "memory": self.memory.get_stats(),
            "sandbox": {
                "level": self.config.sandbox_level.value,
                "work_dir": self.sandbox.work_dir
            }
        }


# 示例：OpenAI LLM客户端实现
class OpenAIClient(LLMClient):
    """OpenAI LLM客户端示例"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        # 实际使用时需要导入openai库
        # import openai
        # openai.api_key = api_key
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用OpenAI Chat API"""
        # 实际实现:
        # response = await openai.ChatCompletion.acreate(
        #     model=self.model,
        #     messages=messages,
        #     **kwargs
        # )
        # return response.choices[0].message.content
        
        # 模拟响应
        return f"[OpenAI {self.model} response to: {messages[-1]['content'][:50]}...]"
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """调用OpenAI Completion API"""
        # 实际实现使用openai.Completion.acreate
        return f"[Completion response to: {prompt[:50]}...]"
    
    async def embed(self, text: str) -> List[float]:
        """获取文本嵌入"""
        # 实际实现使用openai.Embedding.acreate
        import numpy as np
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(1536).tolist()


# 使用示例
async def main():
    """框架使用示例"""
    
    # 创建模拟LLM客户端
    class MockLLM(LLMClient):
        async def chat(self, messages, **kwargs):
            return "This is a mock response"
        
        async def complete(self, prompt, **kwargs):
            return "Mock completion"
        
        async def embed(self, text):
            return [0.1] * 384
    
    # 初始化框架
    config = AgentConfig(
        name="ResearchAssistant",
        description="A helpful research assistant",
        max_iterations=5,
        sandbox_level=SandboxLevel.MEDIUM
    )
    
    framework = AgentFramework(
        llm_client=MockLLM(),
        config=config
    )
    
    # 注册工具
    from core.tools.registry import CalculatorTool, WebSearchTool
    framework.register_tool(CalculatorTool())
    framework.register_tool(WebSearchTool())
    
    # 创建自定义工具
    def get_weather(location: str) -> str:
        """获取天气信息"""
        return f"Weather in {location}: Sunny, 25°C"
    
    weather_tool = framework.create_tool(
        get_weather,
        name="get_weather",
        description="Get weather information for a location",
        category=ToolCategory.WEB
    )
    framework.register_tool(weather_tool)
    
    # 运行Agent
    result = await framework.run(
        query="What is the weather in Tokyo?",
        user_id="user_001"
    )
    
    print("Agent Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 获取框架状态
    print("\n\nFramework Status:")
    print(json.dumps(framework.get_status(), indent=2))
    
    # 代码执行示例
    code_result = await framework.execute_code(
        code="print('Hello from sandbox!')",
        user_id="user_001"
    )
    print("\n\nCode Execution Result:")
    print(json.dumps(code_result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
