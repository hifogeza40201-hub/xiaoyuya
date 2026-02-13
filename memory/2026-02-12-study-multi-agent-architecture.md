# 主题3：多Agent协作架构设计

> 研究日期：2026-02-12  
> 研究目标：设计"小雨主控 + 多AI工具"工作流，搭建自动化pipeline

---

## 一、Multi-Agent架构基础

### 1.1 什么是Multi-Agent系统？

**定义：**
Multi-Agent系统是由多个自主Agent组成的系统，它们通过协作、通信和协调来完成单个Agent无法完成的复杂任务。

**核心特征：**
- 🔄 **自治性**：每个Agent独立运行
- 🤝 **协作性**：Agent之间可以合作
- 🗣️ **通信性**：Agent之间交换信息
- 🎯 **目标导向**：共同或互补的目标

### 1.2 主流框架对比

| 框架 | 开发者 | 架构风格 | 最佳场景 | 学习曲线 |
|------|--------|---------|---------|---------|
| **CrewAI** | CrewAI Inc | 角色扮演 + 任务流 | 工作流自动化 | ⭐⭐ 简单 |
| **LangGraph** | LangChain | 图结构状态机 | 复杂对话系统 | ⭐⭐⭐⭐ 中等 |
| **AutoGen** | Microsoft | 多Agent对话 | 代码生成协作 | ⭐⭐⭐ 中等 |
| **OpenAI Swarm** | OpenAI | 轻量级多Agent | 简单协作 | ⭐ 极简 |
| **BeeAI** | IBM | 企业级编排 | 企业工作流 | ⭐⭐⭐⭐ 较陡 |

### 1.3 框架深度分析

#### CrewAI（推荐入门）

**架构特点：**
```
Crew（团队）
├── Agents（角色定义）
│   ├── 研究员 Agent
│   ├── 写手 Agent
│   └── 审核员 Agent
├── Tasks（任务定义）
│   ├── 研究任务 → 分配给研究员
│   ├── 写作任务 → 分配给写手
│   └── 审核任务 → 分配给审核员
└── Process（流程模式）
    ├── Sequential（顺序）
    ├── Hierarchical（层级）
    └── Parallel（并行）
```

**代码示例：**
```python
from crewai import Agent, Task, Crew

# 定义Agent角色
researcher = Agent(
    role='研究员',
    goal='收集并分析最新信息',
    backstory='你是一位专业的行业研究员',
    tools=[search_tool, web_scraper],
    allow_delegation=True
)

writer = Agent(
    role='内容创作者',
    goal='撰写高质量报告',
    backstory='你是一位经验丰富的写作专家',
    allow_delegation=False
)

# 定义任务链
task1 = Task(
    description='搜索{topic}的最新资料',
    agent=researcher,
    expected_output='关键发现列表'
)

task2 = Task(
    description='基于研究结果撰写报告',
    agent=writer,
    context=[task1],  # 依赖task1的输出
    expected_output='完整报告文档'
)

# 组建团队
crew = Crew(
    agents=[researcher, writer],
    tasks=[task1, task2],
    process='sequential',
    verbose=True
)

result = crew.kickoff(inputs={'topic': 'AI发展趋势'})
```

**性能数据：**
- 比LangGraph快 **5.76倍**（某些QA任务）
- 更高的评估分数
- 更快的完成时间

#### LangGraph

**架构特点：**
```
图结构状态机
├── Nodes（节点 = Agent/函数）
│   ├── 解析用户查询
│   ├── 执行Web搜索
│   ├── 数据聚合
│   └── 生成响应
└── Edges（边 = 流转规则）
    ├── 条件边：if/else逻辑
    ├── 普通边：顺序执行
    └── 循环边：迭代优化
```

**适用场景：**
- 需要复杂状态管理的对话系统
- 需要条件分支的决策流程
- 与LangChain生态深度集成

---

## 二、"小雨主控"架构设计

### 2.1 架构愿景

**目标：**
构建以小雨为核心的多Agent协作系统，协调多个专业AI工具完成复杂任务。

**架构图：**
```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层                                │
│              （Discord/WhatsApp/WebChat）                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    小雨主控 Agent                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  - 意图理解                                          │   │
│  │  - 任务分解                                          │   │
│  │  - Agent调度                                         │   │
│  │  - 结果整合                                          │   │
│  │  - 质量检查                                          │   │
│  └─────────────────────────────────────────────────────┘   │
└──────┬─────────────┬─────────────┬─────────────┬────────────┘
       │             │             │             │
┌──────▼──────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼────────┐
│ 研究Agent   │ │ 代码Agent │ │ 创意Agent │ │ 执行Agent   │
│ (Search)   │ │ (Cursor)  │ │ (Claude)  │ │ (Terminal)  │
└─────────────┘ └──────────┘ └──────────┘ └─────────────┘
       │             │             │             │
       └─────────────┴──────┬──────┴─────────────┘
                            │
              ┌─────────────▼──────────────┐
              │       工具层               │
              │  Search │ TTS │ Browser   │
              │  CodeExec │ FileSystem   │
              └────────────────────────────┘
```

### 2.2 Agent角色定义

#### 1️⃣ 研究Agent
```yaml
name: ResearchAgent
role: 信息收集专家
goal: 快速准确地收集用户需要的信息
tools:
  - web_search
  - web_fetch
  - file_read
skills:
  - 搜索策略制定
  - 信息验证
  - 多源对比
output_format: 结构化数据 + 来源标注
```

#### 2️⃣ 代码Agent
```yaml
name: CodeAgent
role: 软件工程师
goal: 编写高质量、可维护的代码
tools:
  - code_writer
  - code_executor
  - git_operations
skills:
  - 代码生成
  - 代码审查
  - 测试生成
  - 重构优化
integrations:
  - Cursor API
  - Claude Code CLI
  - GitHub Actions
```

#### 3️⃣ 创意Agent
```yaml
name: CreativeAgent
role: 创意助手
goal: 提供创意内容和设计建议
tools:
  - text_generation
  - image_analysis
  - brainstorming
skills:
  - 文案创作
  - 创意发散
  - 风格匹配
  - 情感调性
```

#### 4️⃣ 执行Agent
```yaml
name: ExecutionAgent
role: 系统管理员
goal: 安全地执行系统操作
tools:
  - shell_executor
  - file_manager
  - process_manager
constraints:
  - 需要显式授权
  - 危险操作需确认
  - 完整审计日志
```

### 2.3 任务分解策略

#### 分解算法
```python
def decompose_task(user_request: str) -> List[SubTask]:
    """
    将用户请求分解为可执行的子任务
    """
    # 1. 意图识别
    intent = classify_intent(user_request)
    
    # 2. 任务分解
    if intent == "research":
        return [
            SubTask(agent="research", action="search", query=user_request),
            SubTask(agent="research", action="synthesize", sources="prev"),
            SubTask(agent="creative", action="format", content="prev")
        ]
    
    elif intent == "coding":
        return [
            SubTask(agent="research", action="analyze_requirements"),
            SubTask(agent="code", action="design_architecture"),
            SubTask(agent="code", action="implement"),
            SubTask(agent="code", action="test"),
            SubTask(agent="creative", action="document")
        ]
    
    # 3. 依赖排序
    return topological_sort(subtasks)
```

#### 任务模板

**研究任务模板：**
```yaml
task_type: research
steps:
  1_analyze:
    action: 分析用户问题的关键词和范围
    agent: coordinator
  
  2_search:
    action: 多源搜索
    agent: research
    parallel: true
    sources: [web, docs, internal_kb]
  
  3_verify:
    action: 交叉验证信息准确性
    agent: research
  
  4_synthesize:
    action: 整合信息，生成结构化回答
    agent: coordinator
  
  5_format:
    action: 格式化输出，适配平台
    agent: creative
```

---

## 三、实际工作流设计

### 3.1 工作流1：智能研究报告生成

```mermaid
flowchart TD
    A[用户: "研究AI编程工具趋势"] --> B[小雨主控: 意图识别]
    B --> C[任务分解]
    
    C --> D1[研究Agent: 搜索最新工具]
    C --> D2[研究Agent: 搜索对比评测]
    C --> D3[研究Agent: 搜索用户反馈]
    
    D1 --> E[结果整合]
    D2 --> E
    D3 --> E
    
    E --> F[创意Agent: 撰写报告]
    F --> G[小雨主控: 质量检查]
    G --> H[输出给用户]
```

**实现代码：**
```python
# workflow_research.py
from crewai import Crew, Agent, Task

class ResearchWorkflow:
    def __init__(self):
        self.searcher = Agent(
            role='搜索专家',
            goal='从多角度收集信息',
            tools=[WebSearchTool(), WebFetchTool()]
        )
        self.writer = Agent(
            role='报告撰写专家', 
            goal='撰写结构化研究报告'
        )
    
    def execute(self, topic: str) -> str:
        # 并行搜索任务
        search_tasks = [
            Task(f"搜索{topic}的最新发展", agent=self.searcher),
            Task(f"搜索{topic}的市场分析", agent=self.searcher),
            Task(f"搜索{topic}的用户评价", agent=self.searcher)
        ]
        
        # 撰写任务（依赖搜索结果）
        write_task = Task(
            f"基于搜索结果撰写{topic}报告",
            agent=self.writer,
            context=search_tasks
        )
        
        crew = Crew(
            agents=[self.searcher, self.writer],
            tasks=search_tasks + [write_task],
            process='parallel'  # 搜索并行，写作顺序
        )
        
        return crew.kickoff()
```

### 3.2 工作流2：代码生成与审查

```mermaid
flowchart TD
    A[用户: "创建一个REST API"] --> B[小雨主控]
    B --> C[需求分析Agent]
    C --> D[设计API规范]
    
    D --> E1[代码Agent: 生成后端代码]
    D --> E2[代码Agent: 生成测试]
    D --> E3[代码Agent: 生成文档]
    
    E1 --> F[代码审查Agent]
    E2 --> F
    E3 --> F
    
    F --> G{通过审查?}
    G -->|否| H[代码Agent: 修复]
    H --> F
    G -->|是| I[执行Agent: 部署]
    I --> J[输出结果]
```

### 3.3 工作流3：多媒体内容创作

**场景：** 用户请求"制作一个关于Python装饰器的教学视频脚本"

```yaml
workflow:
  name: video_script_creation
  
  phase_1_research:
    agent: research
    tasks:
      - 搜索装饰器核心概念
      - 搜索常见使用场景
      - 搜索学习者常见困惑
  
  phase_2_script:
    agent: creative
    tasks:
      - 撰写开场白（30秒）
      - 设计概念解释（2分钟）
      - 编写代码示例（3分钟）
      - 设计总结（1分钟）
  
  phase_3_enhancement:
    agent: creative
    tasks:
      - 添加视觉描述
      - 设计过渡效果
      - 编写字幕文本
  
  phase_4_review:
    agent: coordinator
    tasks:
      - 检查教学逻辑
      - 验证代码正确性
      - 评估时长分配
```

---

## 四、自动化Pipeline搭建

### 4.1 Pipeline架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Pipeline引擎                            │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  触发层     │  编排层      │  执行层     │  输出层           │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ • 定时任务  │ • DAG定义   │ • Agent池   │ • 结果存储        │
│ • Webhook   │ • 状态管理  │ • 工具调用  │ • 通知推送        │
│ • 用户触发  │ • 错误恢复  │ • 并发控制  │ • 日志记录        │
│ • 事件驱动  │ • 重试机制  │ • 资源隔离  │ • 审计追踪        │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

### 4.2 关键组件实现

#### 组件1：任务调度器
```python
# scheduler.py
from datetime import datetime
from typing import Callable, Dict
import asyncio

class TaskScheduler:
    def __init__(self):
        self.workflows: Dict[str, Callable] = {}
        self.scheduled_tasks = []
    
    def register(self, name: str, workflow: Callable):
        """注册工作流"""
        self.workflows[name] = workflow
    
    async def schedule(self, workflow_name: str, 
                       trigger: str,
                       params: dict = None):
        """
        trigger: 
          - "immediate": 立即执行
          - "cron:*": 定时执行
          - "event:*": 事件触发
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        if trigger == "immediate":
            return await workflow(**(params or {}))
        elif trigger.startswith("cron:"):
            cron_expr = trigger[5:]
            # 使用APScheduler等库
            pass
        elif trigger.startswith("event:"):
            event_name = trigger[6:]
            # 注册事件监听器
            pass
```

#### 组件2：状态管理器
```python
# state_manager.py
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class StateManager:
    """
    管理工作流的执行状态
    支持持久化和恢复
    """
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    async def create_workflow_run(self, workflow_id: str, 
                                   inputs: dict) -> str:
        """创建新的工作流运行实例"""
        run_id = generate_uuid()
        state = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": TaskStatus.PENDING,
            "inputs": inputs,
            "outputs": {},
            "task_states": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        await self.storage.save(run_id, state)
        return run_id
    
    async def update_task_state(self, run_id: str, 
                                 task_id: str,
                                 status: TaskStatus,
                                 output: any = None):
        """更新任务状态"""
        state = await self.storage.get(run_id)
        state["task_states"][task_id] = {
            "status": status,
            "output": output,
            "updated_at": datetime.now()
        }
        await self.storage.save(run_id, state)
```

#### 组件3：错误恢复机制
```python
# error_recovery.py
from typing import Optional

class RecoveryStrategy:
    """错误恢复策略"""
    
    @staticmethod
    async def retry(task, max_attempts: int = 3):
        """重试策略"""
        for attempt in range(max_attempts):
            try:
                return await task.execute()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
    
    @staticmethod
    async def fallback(task, fallback_agent):
        """降级策略"""
        try:
            return await task.execute()
        except Exception:
            return await fallback_agent.execute(task)
    
    @staticmethod
    async def compensate(task, compensation_tasks):
        """补偿策略"""
        try:
            result = await task.execute()
            return result
        except Exception as e:
            # 执行补偿任务
            for comp_task in compensation_tasks:
                await comp_task.execute()
            raise
```

### 4.3 完整的Pipeline示例

```python
# example_pipeline.py
import asyncio
from datetime import datetime

class MorningBriefingPipeline:
    """
    每日晨报Pipeline
    自动收集信息并生成摘要
    """
    
    def __init__(self):
        self.agents = {
            'news': NewsAgent(),
            'weather': WeatherAgent(),
            'calendar': CalendarAgent(),
            'writer': SummaryWriterAgent()
        }
    
    async def run(self, user_id: str) -> str:
        """执行完整Pipeline"""
        
        # Phase 1: 并行收集信息
        gather_tasks = [
            self.agents['news'].get_headlines(category='tech'),
            self.agents['weather'].get_forecast(user_id),
            self.agents['calendar'].get_today_events(user_id)
        ]
        
        news, weather, events = await asyncio.gather(
            *gather_tasks, 
            return_exceptions=True
        )
        
        # Phase 2: 处理结果（容错）
        data = {}
        if not isinstance(news, Exception):
            data['news'] = news
        if not isinstance(weather, Exception):
            data['weather'] = weather
        if not isinstance(events, Exception):
            data['events'] = events
        
        # Phase 3: 生成摘要
        summary = await self.agents['writer'].write(
            template='morning_briefing',
            data=data
        )
        
        # Phase 4: 存储结果
        await self._store_result(user_id, summary)
        
        return summary
    
    async def schedule_daily(self, user_id: str, time: str = "08:00"):
        """设置为每日定时任务"""
        scheduler = TaskScheduler()
        scheduler.register(
            f"morning_briefing_{user_id}",
            lambda: self.run(user_id)
        )
        await scheduler.schedule(
            f"morning_briefing_{user_id}",
            trigger=f"cron:0 8 * * *"  # 每天8点
        )

# 使用示例
pipeline = MorningBriefingPipeline()
result = asyncio.run(pipeline.run(user_id="user_123"))
```

---

## 五、关键设计原则

### 5.1 Agent协作原则

1. **单一职责**
   - 每个Agent专注于一个领域
   - 避免功能重叠导致的冲突

2. **显式通信**
   - Agent间通过定义好的接口通信
   - 避免隐式状态共享

3. **容错设计**
   - 单个Agent失败不导致整体失败
   - 提供降级和补偿机制

4. **可观测性**
   - 完整的执行日志
   - 状态可视化
   - 性能指标监控

### 5.2 安全与权限

```yaml
security_model:
  agent_permissions:
    research:
      allowed: [web_search, web_fetch, file_read]
      denied: [file_write, shell_exec]
    
    code:
      allowed: [file_read, file_write, code_exec_sandbox]
      denied: [shell_exec_production]
    
    execution:
      allowed: []
      requires_approval: [shell_exec, file_delete]
      audit_all: true

  data_isolation:
    - 用户A的数据对用户B不可见
    - Agent间敏感数据脱敏传输
    - 临时数据自动清理
```

---

## 六、实践建议与下一步

### 6.1 渐进式实施路线图

**Phase 1: 单Agent优化（1-2周）**
- 优化单个Agent的提示词和工具
- 建立Agent评估基准
- [ ] 实现研究Agent原型

**Phase 2: 双Agent协作（2-3周）**
- 实现最简单的两Agent工作流
- 建立Agent间通信协议
- [ ] 研究Agent + 写作Agent组合

**Phase 3: 多Agent系统（3-4周）**
- 实现完整的多Agent架构
- 搭建Pipeline基础设施
- [ ] 完整的任务分解和调度

**Phase 4: 自动化与优化（持续）**
- 自动化常见工作流
- 性能监控和优化
- [ ] 自动化研究报告生成

### 6.2 评估指标

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| 任务完成率 | > 90% | 成功完成的任务/总任务 |
| 平均执行时间 | < 30s | 端到端执行时间 |
| 人工干预率 | < 20% | 需要人工介入的任务比例 |
| 用户满意度 | > 4.0/5 | 用户评分 |
| 成本效率 | 优化中 | 每任务API调用成本 |

---

**下一步行动：**
- [ ] 选择CrewAI作为试点框架
- [ ] 实现研究Agent原型
- [ ] 设计Agent间通信协议
- [ ] 搭建Pipeline基础设施
- [ ] 建立评估基准

---

*设计完成时间：2026-02-12*  
*参考：IBM Developer, CrewAI Docs, LangGraph Docs*
