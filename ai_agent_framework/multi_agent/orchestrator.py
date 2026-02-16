from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
from datetime import datetime


class AgentRole(Enum):
    """Agent角色类型"""
    PLANNER = "planner"         # 规划者 - 制定计划
    EXECUTOR = "executor"       # 执行者 - 执行任务
    CRITIC = "critic"           # 批判者 - 审查结果
    RESEARCHER = "researcher"   # 研究者 - 收集信息
    WRITER = "writer"           # 撰写者 - 生成内容
    COORDINATOR = "coordinator" # 协调者 - 管理协作


class MessageType(Enum):
    """消息类型"""
    TASK = "task"               # 任务分配
    RESULT = "result"           # 任务结果
    QUERY = "query"             # 查询
    RESPONSE = "response"       # 响应
    FEEDBACK = "feedback"       # 反馈
    BROADCAST = "broadcast"     # 广播


@dataclass
class AgentMessage:
    """Agent间消息"""
    sender: str
    receiver: Optional[str]      # None表示广播
    message_type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    assignee: Optional[str] = None
    status: str = "pending"      # pending, in_progress, completed, failed
    priority: int = 1            # 1-5
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class BaseAgent(ABC):
    """基础Agent类"""
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        llm_client: Any,
        system_prompt: Optional[str] = None
    ):
        self.name = name
        self.role = role
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, Task] = {}
        self.peers: Dict[str, 'BaseAgent'] = {}  # 其他Agent引用
        self.message_history: List[AgentMessage] = []
    
    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """处理任务"""
        pass
    
    async def run(self):
        """Agent主循环"""
        while True:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                await self._idle_work()
    
    async def _handle_message(self, message: AgentMessage):
        """处理消息"""
        self.message_history.append(message)
        
        if message.message_type == MessageType.TASK:
            # 接收任务
            task = Task(**message.content)
            self.tasks[task.id] = task
            
            # 检查依赖
            if self._check_dependencies(task):
                task.status = "in_progress"
                try:
                    result = await self.process_task(task)
                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    
                    # 发送结果
                    await self.send_message(
                        receiver=message.sender,
                        message_type=MessageType.RESULT,
                        content={
                            "task_id": task.id,
                            "result": result,
                            "status": "completed"
                        }
                    )
                except Exception as e:
                    task.status = "failed"
                    await self.send_message(
                        receiver=message.sender,
                        message_type=MessageType.RESULT,
                        content={
                            "task_id": task.id,
                            "error": str(e),
                            "status": "failed"
                        }
                    )
        
        elif message.message_type == MessageType.QUERY:
            # 响应查询
            response = await self._answer_query(message.content)
            await self.send_message(
                receiver=message.sender,
                message_type=MessageType.RESPONSE,
                content=response
            )
        
        elif message.message_type == MessageType.FEEDBACK:
            # 处理反馈
            await self._process_feedback(message.content)
    
    async def send_message(
        self,
        receiver: Optional[str],
        message_type: MessageType,
        content: Any
    ):
        """发送消息"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        
        if receiver is None:
            # 广播
            for agent in self.peers.values():
                await agent.message_queue.put(message)
        elif receiver in self.peers:
            await self.peers[receiver].message_queue.put(message)
    
    def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                if self.tasks[dep_id].status != "completed":
                    return False
            else:
                return False
        return True
    
    async def _idle_work(self):
        """空闲时的工作"""
        pass
    
    async def _answer_query(self, query: Dict[str, Any]) -> Any:
        """回答查询"""
        return {"status": "not_implemented"}
    
    async def _process_feedback(self, feedback: Dict[str, Any]):
        """处理反馈"""
        pass
    
    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return f"You are a {self.role.value} agent named {self.name}."
    
    def register_peer(self, agent: 'BaseAgent'):
        """注册其他Agent"""
        self.peers[agent.name] = agent


class PlannerAgent(BaseAgent):
    """规划者Agent"""
    
    def __init__(self, name: str, llm_client: Any):
        super().__init__(
            name=name,
            role=AgentRole.PLANNER,
            llm_client=llm_client,
            system_prompt="""You are a planning agent. Your role is to:
1. Analyze complex tasks and break them down into subtasks
2. Determine the optimal order of execution
3. Assign tasks to appropriate agents
4. Monitor progress and adjust plans as needed

Provide your plan in structured format with clear dependencies."""
        )
    
    async def process_task(self, task: Task) -> Any:
        """生成执行计划"""
        prompt = f"""Create a detailed plan for the following task:

Task: {task.description}

Break this down into subtasks. For each subtask, specify:
- Description
- Required role (executor, researcher, writer, etc.)
- Dependencies on other subtasks

Format your response as JSON:
{{
    "subtasks": [
        {{
            "id": "task_1",
            "description": "...",
            "role": "executor",
            "dependencies": []
        }}
    ],
    "reasoning": "..."
}}"""
        
        response = await self._call_llm(prompt)
        
        try:
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError:
            return {"subtasks": [], "raw_response": response}
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        if hasattr(self.llm_client, 'complete'):
            return await self.llm_client.complete(prompt)
        return "Mock LLM response"


class ExecutorAgent(BaseAgent):
    """执行者Agent"""
    
    def __init__(self, name: str, llm_client: Any, tools: Dict[str, Callable] = None):
        super().__init__(
            name=name,
            role=AgentRole.EXECUTOR,
            llm_client=llm_client,
            system_prompt="""You are an execution agent. Your role is to:
1. Execute assigned tasks using available tools
2. Produce concrete outputs
3. Report progress and results accurately
4. Ask for clarification when needed"""
        )
        self.tools = tools or {}
    
    async def process_task(self, task: Task) -> Any:
        """执行任务"""
        prompt = f"""Execute the following task:

Task: {task.description}

Available tools: {list(self.tools.keys())}

Think step by step and produce the required output."""
        
        result = await self._call_llm(prompt)
        return result
    
    async def _call_llm(self, prompt: str) -> str:
        if hasattr(self.llm_client, 'complete'):
            return await self.llm_client.complete(prompt)
        return "Mock execution result"


class CriticAgent(BaseAgent):
    """批判者Agent"""
    
    def __init__(self, name: str, llm_client: Any):
        super().__init__(
            name=name,
            role=AgentRole.CRITIC,
            llm_client=llm_client,
            system_prompt="""You are a critic agent. Your role is to:
1. Review outputs from other agents
2. Identify errors, inconsistencies, or improvements
3. Provide constructive feedback
4. Ensure quality standards are met

Be thorough but fair in your assessments."""
        )
    
    async def process_task(self, task: Task) -> Any:
        """审查任务结果"""
        content_to_review = task.description
        
        prompt = f"""Review the following content:

{content_to_review}

Provide your review in JSON format:
{{
    "score": <1-10>,
    "issues": ["..."],
    "suggestions": ["..."],
    "approved": <true/false>
}}"""
        
        response = await self._call_llm(prompt)
        
        try:
            review = json.loads(response)
            return review
        except json.JSONDecodeError:
            return {"score": 5, "issues": [], "approved": False, "raw": response}
    
    async def _call_llm(self, prompt: str) -> str:
        if hasattr(self.llm_client, 'complete'):
            return await self.llm_client.complete(prompt)
        return '{"score": 7, "issues": [], "suggestions": [], "approved": true}'


class ResearcherAgent(BaseAgent):
    """研究者Agent"""
    
    def __init__(self, name: str, llm_client: Any, search_tool: Optional[Callable] = None):
        super().__init__(
            name=name,
            role=AgentRole.RESEARCHER,
            llm_client=llm_client,
            system_prompt="""You are a research agent. Your role is to:
1. Gather relevant information on topics
2. Synthesize findings from multiple sources
3. Provide well-sourced, accurate information
4. Identify knowledge gaps"""
        )
        self.search_tool = search_tool
    
    async def process_task(self, task: Task) -> Any:
        """执行研究任务"""
        query = task.description
        
        # 模拟研究过程
        research_result = {
            "query": query,
            "findings": [
                f"Finding 1 related to {query}",
                f"Finding 2 related to {query}"
            ],
            "sources": ["source1", "source2"],
            "summary": f"Research summary for: {query}"
        }
        
        return research_result


class AgentCrew:
    """
    Agent Crew - 多Agent协作团队
    
    参考CrewAI的设计模式
    """
    
    def __init__(self, name: str = "Crew"):
        self.name = name
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: List[Task] = []
        self.results: Dict[str, Any] = {}
    
    def add_agent(self, agent: BaseAgent):
        """添加Agent"""
        self.agents[agent.name] = agent
        
        # 让每个Agent知道其他Agent
        for other_agent in self.agents.values():
            if other_agent != agent:
                agent.register_peer(other_agent)
                other_agent.register_peer(agent)
    
    def create_task(
        self,
        description: str,
        assignee: Optional[str] = None,
        priority: int = 1,
        dependencies: List[str] = None
    ) -> Task:
        """创建任务"""
        task = Task(
            id=f"task_{len(self.tasks)}",
            description=description,
            assignee=assignee,
            priority=priority,
            dependencies=dependencies or []
        )
        self.tasks.append(task)
        return task
    
    async def execute(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """
        执行所有任务
        
        Args:
            max_concurrent: 最大并发任务数
        """
        # 启动所有Agent
        agent_tasks = [
            asyncio.create_task(agent.run())
            for agent in self.agents.values()
        ]
        
        # 按依赖顺序分配任务
        pending_tasks = self.tasks.copy()
        in_progress = set()
        completed = set()
        
        while pending_tasks or in_progress:
            # 找出可以执行的任务
            ready_tasks = [
                t for t in pending_tasks
                if all(dep in completed for dep in t.dependencies)
                and len(in_progress) < max_concurrent
            ]
            
            for task in ready_tasks:
                if task.assignee and task.assignee in self.agents:
                    # 分配给指定Agent
                    await self.agents[task.assignee].message_queue.put(
                        AgentMessage(
                            sender="coordinator",
                            receiver=task.assignee,
                            message_type=MessageType.TASK,
                            content=task.__dict__
                        )
                    )
                else:
                    # 自动分配给合适的Agent
                    assignee = self._find_best_agent(task)
                    if assignee:
                        await self.agents[assignee].message_queue.put(
                            AgentMessage(
                                sender="coordinator",
                                receiver=assignee,
                                message_type=MessageType.TASK,
                                content=task.__dict__
                            )
                        )
                
                pending_tasks.remove(task)
                in_progress.add(task.id)
            
            # 等待任务完成
            await asyncio.sleep(0.5)
            
            # 检查完成的任务
            for task_id in list(in_progress):
                for agent in self.agents.values():
                    if task_id in agent.tasks:
                        if agent.tasks[task_id].status in ("completed", "failed"):
                            in_progress.remove(task_id)
                            completed.add(task_id)
                            self.results[task_id] = agent.tasks[task_id].result
        
        return self.results
    
    def _find_best_agent(self, task: Task) -> Optional[str]:
        """找到最适合执行任务的Agent"""
        # 简单策略：根据任务描述选择
        description_lower = task.description.lower()
        
        for name, agent in self.agents.items():
            if "research" in description_lower and agent.role == AgentRole.RESEARCHER:
                return name
            if "write" in description_lower and agent.role == AgentRole.WRITER:
                return name
            if "plan" in description_lower and agent.role == AgentRole.PLANNER:
                return name
            if agent.role == AgentRole.EXECUTOR:
                return name  # 默认使用执行者
        
        return None
    
    def get_execution_report(self) -> Dict[str, Any]:
        """获取执行报告"""
        return {
            "crew_name": self.name,
            "total_tasks": len(self.tasks),
            "completed": len([t for t in self.tasks if t.status == "completed"]),
            "failed": len([t for t in self.tasks if t.status == "failed"]),
            "agents": list(self.agents.keys()),
            "results": self.results
        }


class AutoGenStyleGroup:
    """
    AutoGen风格的多Agent对话组
    
    特点:
    - 对话驱动
    - 选择性发言
    - 自然协作流程
    """
    
    def __init__(self, name: str = "Group"):
        self.name = name
        self.agents: Dict[str, BaseAgent] = {}
        self.conversation: List[AgentMessage] = []
        self.max_rounds = 10
    
    def add_agent(self, agent: BaseAgent):
        """添加Agent"""
        self.agents[agent.name] = agent
    
    async def chat(
        self,
        initial_message: str,
        speaker_selection: str = "auto"
    ) -> List[AgentMessage]:
        """
        启动群聊
        
        Args:
            initial_message: 初始消息
            speaker_selection: 发言者选择策略 (auto/round_robin/random)
        """
        # 添加初始消息
        self.conversation.append(AgentMessage(
            sender="user",
            receiver=None,
            message_type=MessageType.BROADCAST,
            content=initial_message
        ))
        
        current_round = 0
        
        while current_round < self.max_rounds:
            # 选择下一个发言者
            next_speaker = self._select_next_speaker(speaker_selection)
            
            if not next_speaker:
                break
            
            # 构建上下文
            context = self._build_context()
            
            # 获取发言
            response = await self._get_agent_response(next_speaker, context)
            
            message = AgentMessage(
                sender=next_speaker,
                receiver=None,
                message_type=MessageType.BROADCAST,
                content=response
            )
            self.conversation.append(message)
            
            # 检查是否结束
            if "TERMINATE" in response.upper():
                break
            
            current_round += 1
        
        return self.conversation
    
    def _select_next_speaker(self, strategy: str) -> Optional[str]:
        """选择下一个发言者"""
        available = list(self.agents.keys())
        
        if not available:
            return None
        
        if strategy == "round_robin":
            if not hasattr(self, '_last_speaker_idx'):
                self._last_speaker_idx = -1
            self._last_speaker_idx = (self._last_speaker_idx + 1) % len(available)
            return available[self._last_speaker_idx]
        
        elif strategy == "random":
            import random
            return random.choice(available)
        
        else:  # auto
            # 根据上一轮内容选择最合适的Agent
            if self.conversation:
                last_message = self.conversation[-1].content.lower()
                for name, agent in self.agents.items():
                    if agent.role.value in last_message:
                        return name
            return available[0]
    
    def _build_context(self) -> str:
        """构建对话上下文"""
        return "\n".join([
            f"{msg.sender}: {msg.content}"
            for msg in self.conversation[-5:]  # 最近5条
        ])
    
    async def _get_agent_response(self, agent_name: str, context: str) -> str:
        """获取Agent响应"""
        agent = self.agents[agent_name]
        
        prompt = f"""You are {agent_name}, a {agent.role.value}.

Conversation history:
{context}

Respond naturally. If the task is complete, end with TERMINATE."""
        
        if hasattr(agent.llm_client, 'complete'):
            return await agent.llm_client.complete(prompt)
        
        return f"[Mock response from {agent_name}]"


# 使用示例
async def example_crew():
    """Crew模式示例"""
    # 创建Agent
    class MockLLM:
        async def complete(self, prompt):
            return "Mock response"
    
    llm = MockLLM()
    
    planner = PlannerAgent("Alice", llm)
    executor = ExecutorAgent("Bob", llm)
    critic = CriticAgent("Carol", llm)
    
    # 创建Crew
    crew = AgentCrew("Research Team")
    crew.add_agent(planner)
    crew.add_agent(executor)
    crew.add_agent(critic)
    
    # 创建任务
    crew.create_task(
        description="Research the impact of AI on healthcare",
        assignee="Alice",
        priority=1
    )
    crew.create_task(
        description="Execute research plan",
        assignee="Bob",
        priority=2,
        dependencies=["task_0"]
    )
    
    # 执行
    results = await crew.execute()
    print("Crew execution results:", results)


async def example_autogen():
    """AutoGen风格示例"""
    class MockLLM:
        async def complete(self, prompt):
            if "TERMINATE" not in prompt:
                return "I think we should research more. TERMINATE"
            return "TERMINATE"
    
    llm = MockLLM()
    
    group = AutoGenStyleGroup("Discussion")
    group.add_agent(ResearcherAgent("Researcher", llm))
    group.add_agent(CriticAgent("Critic", llm))
    
    conversation = await group.chat(
        "Let's discuss the future of AI agents",
        speaker_selection="round_robin"
    )
    
    print("\nConversation:")
    for msg in conversation:
        print(f"{msg.sender}: {msg.content}")


if __name__ == "__main__":
    asyncio.run(example_crew())
