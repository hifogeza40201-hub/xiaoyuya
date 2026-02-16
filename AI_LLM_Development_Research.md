# AI大模型应用开发深度研究报告

## 目录
1. [大模型API集成与调用优化](#一大模型api集成与调用优化)
2. [提示词工程高级技巧](#二提示词工程prompt-engineering高级技巧)
3. [RAG检索增强生成系统构建](#三rag检索增强生成系统构建)
4. [大模型微调与定制化](#四大模型微调与定制化)
5. [AI Agent设计与实现](#五ai-agent设计与实现)

---

## 一、大模型API集成与调用优化

### 1.1 主流API架构对比

```
┌─────────────────────────────────────────────────────────────────┐
│                    大模型API架构对比                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│    提供商        │    特点         │         适用场景             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ OpenAI (GPT-4)  │ 功能全面,稳定    │ 通用对话,复杂推理,代码生成    │
│ Claude (Anthropic)│ 长上下文,安全   │ 文档分析,长文本处理,企业应用  │
│ Gemini (Google) │ 多模态,实时性    │ 多媒体处理,搜索增强           │
│ 文心一言(百度)   │ 中文优化,合规    │ 国内应用,政务,金融            │
│ 通义千问(阿里)   │ 开源生态,低成本  │ 企业内部,开发者社区           │
│ DeepSeek        │ 推理强,性价比高  │ 代码生成,数学推理,科研        │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### 1.2 统一API抽象层设计

```python
# unified_llm_client.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"

@dataclass
class LLMConfig:
    provider: ModelProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2048

@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]
    latency_ms: float
    model: str
    finish_reason: Optional[str] = None

class BaseLLMClient(ABC):
    """LLM客户端抽象基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._semaphore = asyncio.Semaphore(100)  # 并发控制
        self._request_count = 0
        self._error_count = 0
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """同步生成"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """流式生成"""
        pass
    
    @asynccontextmanager
    async def _rate_limited_request(self):
        """速率限制上下文管理器"""
        async with self._semaphore:
            yield

# OpenAI实现示例
class OpenAIClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        import time
        start = time.time()
        
        async with self._rate_limited_request():
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                stream=False
            )
        
        latency = (time.time() - start) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            latency_ms=latency,
            model=response.model,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        async with self._rate_limited_request():
            stream = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

# 工厂模式
class LLMClientFactory:
    _clients: Dict[str, BaseLLMClient] = {}
    
    @classmethod
    def get_client(cls, config: LLMConfig) -> BaseLLMClient:
        cache_key = f"{config.provider.value}:{config.model_name}"
        if cache_key not in cls._clients:
            if config.provider == ModelProvider.OPENAI:
                cls._clients[cache_key] = OpenAIClient(config)
            # ... 其他provider
        return cls._clients[cache_key]
```

### 1.3 调用优化策略

#### 1.3.1 智能路由与负载均衡

```python
# smart_router.py
import random
from typing import List, Callable
from dataclasses import dataclass

@dataclass
class EndpointConfig:
    name: str
    client: BaseLLMClient
    weight: float = 1.0
    cost_per_1k: float = 0.0
    latency_target_ms: float = 1000.0
    failure_rate: float = 0.0

class SmartRouter:
    """智能路由 - 基于成本、延迟、质量的动态选择"""
    
    def __init__(self, endpoints: List[EndpointConfig]):
        self.endpoints = endpoints
        self.health_status = {e.name: True for e in endpoints}
        self.latency_history = {e.name: [] for e in endpoints}
    
    def route_by_strategy(
        self, 
        strategy: str = "balanced",
        prompt_complexity: float = 0.5
    ) -> EndpointConfig:
        """
        路由策略:
        - cost: 优先低成本
        - quality: 优先高质量
        - balanced: 平衡策略
        - latency: 优先低延迟
        """
        available = [e for e in self.endpoints if self.health_status[e.name]]
        
        if strategy == "cost":
            return min(available, key=lambda x: x.cost_per_1k)
        elif strategy == "quality":
            # 复杂任务用大模型
            if prompt_complexity > 0.7:
                return max(available, key=lambda x: x.weight)
            return random.choice(available)
        elif strategy == "latency":
            avg_latencies = {
                e.name: sum(self.latency_history[e.name]) / max(len(self.latency_history[e.name]), 1)
                for e in available
            }
            return min(available, key=lambda x: avg_latencies.get(x.name, float('inf')))
        else:  # balanced
            scores = []
            for e in available:
                score = (
                    e.weight * 0.4 +
                    (1 / (e.cost_per_1k + 0.01)) * 0.3 +
                    (1 / (sum(self.latency_history[e.name]) / max(len(self.latency_history[e.name]), 1) + 1)) * 0.3
                )
                scores.append((e, score))
            return max(scores, key=lambda x: x[1])[0]
```

#### 1.3.2 请求批处理与异步优化

```python
# batch_processor.py
import asyncio
from typing import List, Callable
from concurrent.futures import ThreadPoolExecutor

class BatchProcessor:
    """请求批处理器 - 减少API调用开销"""
    
    def __init__(self, client: BaseLLMClient, batch_size: int = 10):
        self.client = client
        self.batch_size = batch_size
        self._queue = asyncio.Queue()
        self._processing = False
    
    async def submit(self, prompt: str, callback: Callable = None) -> str:
        """提交单个请求"""
        future = asyncio.Future()
        await self._queue.put((prompt, future, callback))
        if not self._processing:
            asyncio.create_task(self._process_batch())
        return await future
    
    async def _process_batch(self):
        """批量处理队列中的请求"""
        self._processing = True
        batch = []
        
        while not self._queue.empty() and len(batch) < self.batch_size:
            try:
                item = self._queue.get_nowait()
                batch.append(item)
            except asyncio.QueueEmpty:
                break
        
        if batch:
            # 并行处理批量请求
            tasks = [self._execute_single(prompt, future, callback) 
                    for prompt, future, callback in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self._processing = False
    
    async def _execute_single(self, prompt: str, future: asyncio.Future, callback: Callable):
        """执行单个请求"""
        try:
            response = await self.client.generate(prompt)
            future.set_result(response.content)
            if callback:
                callback(response)
        except Exception as e:
            future.set_exception(e)

# 使用示例
async def optimized_api_calls():
    processor = BatchProcessor(client, batch_size=5)
    
    # 并发提交多个请求
    prompts = ["问题1", "问题2", "问题3", "问题4", "问题5"]
    tasks = [processor.submit(p) for p in prompts]
    results = await asyncio.gather(*tasks)
    return results
```

#### 1.3.3 缓存策略

```python
# cache_manager.py
import hashlib
import json
from typing import Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

class LLMCache:
    """多级缓存系统"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.local_cache = {}  # L1: 内存缓存
        self.redis = redis.from_url(redis_url) if redis_url else None  # L2: Redis
        self.local_ttl = 300  # 5分钟
        self.redis_ttl = 3600  # 1小时
    
    def _generate_key(self, prompt: str, model: str, params: dict) -> str:
        """生成缓存键"""
        content = f"{prompt}:{model}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(self, prompt: str, model: str, params: dict) -> Optional[str]:
        """获取缓存结果"""
        key = self._generate_key(prompt, model, params)
        
        # L1缓存
        if key in self.local_cache:
            entry = self.local_cache[key]
            if datetime.now() < entry['expires']:
                return entry['value']
            del self.local_cache[key]
        
        # L2缓存
        if self.redis:
            value = await self.redis.get(f"llm:{key}")
            if value:
                # 回填L1
                self.local_cache[key] = {
                    'value': value.decode(),
                    'expires': datetime.now() + timedelta(seconds=self.local_ttl)
                }
                return value.decode()
        
        return None
    
    async def set(self, prompt: str, model: str, params: dict, value: str):
        """设置缓存"""
        key = self._generate_key(prompt, model, params)
        
        # L1缓存
        self.local_cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=self.local_ttl)
        }
        
        # L2缓存
        if self.redis:
            await self.redis.setex(
                f"llm:{key}",
                self.redis_ttl,
                value
            )
```

### 1.4 性能优化最佳实践

| 优化维度 | 策略 | 预期效果 |
|---------|------|---------|
| **连接池** | 复用HTTP连接,避免重复握手 | 减少30-50%延迟 |
| **流式响应** | 首Token快速返回,提升用户体验 | TTFT < 500ms |
| **压缩传输** | 启用gzip/brotli压缩 | 减少40%带宽 |
| **智能重试** | 指数退避+抖动,避免雪崩 | 提升可用性至99.9% |
| **边缘部署** | CDN+边缘计算就近处理 | 减少跨区域延迟 |
| **模型蒸馏** | 复杂任务用大模型,简单任务用小模型 | 成本降低70% |

---

## 二、提示词工程(Prompt Engineering)高级技巧

### 2.1 核心方法论

```
                    提示词工程金字塔
                    
                        ▲
                       /│\     Level 5: 元提示/自动优化
                      / │ \         (Meta-prompting, APE)
                     /  │  \
                    /───┼───\   Level 4: 思维链/多步推理
                   /    │    \      (Chain-of-Thought, ToT)
                  /     │     \
                 /──────┼──────\ Level 3: 结构化/上下文学习
                /       │       \    (Few-shot, Structured)
               /        │        \
              /─────────┼─────────\ Level 2: 角色设定/系统提示
             /          │          \   (Role, System Prompt)
            /           │           \
           ─────────────┴───────────── Level 1: 基础指令
                                         (Zero-shot, Direct)
```

### 2.2 高级提示词模板

```python
# advanced_prompts.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import json

@dataclass
class PromptTemplate:
    system_prompt: str
    user_template: str
    examples: List[Dict[str, str]] = None
    output_format: Optional[str] = None

class AdvancedPromptEngine:
    """高级提示词引擎"""
    
    # ============== 1. Chain-of-Thought (思维链) ==============
    COT_TEMPLATE = """请逐步思考以下问题,展示完整的推理过程:

问题: {question}

要求:
1. 先分析问题的前提条件
2. 列出可能的解决思路
3. 逐一评估各思路
4. 给出最终答案

请按照以下格式回答:
思考过程:
[你的详细推理]

最终答案:
[简洁的结论]"""

    # ============== 2. Tree of Thoughts (思维树) ==============
    TOT_TEMPLATE = """你需要探索多个解决思路来回答这个问题。

问题: {question}

请按照思维树的方式:
1. 生成3个不同的初步思路
2. 对每个思路进行评估(1-10分)
3. 选择最有前景的思路深入展开
4. 继续分解子问题直到得出答案

格式:
思路1: [描述]
评估: [分数和理由]

思路2: [描述]
评估: [分数和理由]

思路3: [描述]
评估: [分数和理由]

最优路径深入:
[详细展开]

最终答案: [结论]"""

    # ============== 3. ReAct (推理+行动) ==============
    REACT_TEMPLATE = """你是一个智能助手,可以调用工具解决问题。
可用工具: {tools_description}

请按照"思考 -> 行动 -> 观察"的循环来解决问题:
问题: {question}

格式要求:
思考[1]: [分析当前状态]
行动[1]: [选择工具] 参数: {...}
观察[1]: [工具返回结果]
思考[2]: [基于观察的分析]
...
直到得出答案。

最终答案: [你的结论]"""

    # ============== 4. 结构化输出提示 ==============
    STRUCTURED_TEMPLATE = """请分析以下内容并以JSON格式输出:

输入: {input_content}

输出格式:
{{
    "sentiment": "positive|neutral|negative",
    "confidence": 0.0-1.0,
    "key_points": ["要点1", "要点2"],
    "entities": [
        {{"name": "实体名", "type": "类型", "relevance": 0.0-1.0}}
    ],
    "summary": "一句话总结"
}}

请确保输出是有效的JSON格式。"""

    # ============== 5. 少样本学习模板 ==============
    FEW_SHOT_TEMPLATE = """请参考以下示例,完成类似任务:

示例1:
输入: {example1_input}
输出: {example1_output}

示例2:
输入: {example2_input}
输出: {example2_output}

示例3:
输入: {example3_input}
输出: {example3_output}

现在请处理:
输入: {target_input}
输出:"""

    @classmethod
    def build_cot_prompt(cls, question: str) -> str:
        """构建思维链提示"""
        return cls.COT_TEMPLATE.format(question=question)
    
    @classmethod
    def build_react_prompt(cls, question: str, tools: List[Dict]) -> str:
        """构建ReAct提示"""
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}" 
            for t in tools
        ])
        return cls.REACT_TEMPLATE.format(
            question=question,
            tools_description=tools_desc
        )
    
    @classmethod
    def build_few_shot_prompt(
        cls, 
        examples: List[Dict[str, str]], 
        target: str,
        n_shots: int = 3
    ) -> str:
        """构建少样本提示"""
        template_vars = {}
        for i, ex in enumerate(examples[:n_shots], 1):
            template_vars[f"example{i}_input"] = ex['input']
            template_vars[f"example{i}_output"] = ex['output']
        template_vars['target_input'] = target
        
        return cls.FEW_SHOT_TEMPLATE.format(**template_vars)
```

### 2.3 动态提示词优化 (APE)

```python
# automatic_prompt_engineering.py
class AutomaticPromptEngineer:
    """自动提示词优化器"""
    
    def __init__(self, client: BaseLLMClient):
        self.client = client
        self.meta_prompt = """你是一个提示词优化专家。

任务: 为以下目标生成最优的提示词
目标: {objective}

当前提示词: {current_prompt}
性能评分: {score}/10

请生成一个改进版本的提示词,要求:
1. 更清晰的指令
2. 更具体的约束
3. 更好的示例(如适用)
4. 明确的输出格式

只返回优化后的提示词内容,不要解释。"""

    async def optimize_prompt(
        self, 
        objective: str,
        initial_prompt: str,
        eval_function: Callable,
        iterations: int = 5
    ) -> str:
        """
        自动优化提示词
        
        Args:
            objective: 任务目标描述
            initial_prompt: 初始提示词
            eval_function: 评估函数,返回0-10的分数
            iterations: 优化轮数
        """
        best_prompt = initial_prompt
        best_score = await eval_function(initial_prompt)
        
        for i in range(iterations):
            # 生成候选提示词
            meta_input = self.meta_prompt.format(
                objective=objective,
                current_prompt=best_prompt,
                score=best_score
            )
            
            response = await self.client.generate(meta_input)
            candidate_prompt = response.content.strip()
            
            # 评估候选
            candidate_score = await eval_function(candidate_prompt)
            
            # 更新最优
            if candidate_score > best_score:
                best_prompt = candidate_prompt
                best_score = candidate_score
                print(f"迭代 {i+1}: 找到更好的提示词,得分 {best_score}")
        
        return best_prompt

# 使用示例
async def demo_ape():
    ape = AutomaticPromptEngineer(client)
    
    async def eval_prompt(prompt: str) -> float:
        """评估提示词效果"""
        test_cases = [
            ("中国的首都是哪里？", "北京"),
            ("法国的首都是哪里？", "巴黎"),
        ]
        correct = 0
        for input_text, expected in test_cases:
            full_prompt = f"{prompt}\n问题: {input_text}\n答案:"
            response = await client.generate(full_prompt)
            if expected in response.content:
                correct += 1
        return (correct / len(test_cases)) * 10
    
    optimized = await ape.optimize_prompt(
        objective="回答简单的地理问题",
        initial_prompt="请回答问题:",
        eval_function=eval_prompt,
        iterations=3
    )
    return optimized
```

### 2.4 提示词版本管理与A/B测试

```python
# prompt_management.py
from datetime import datetime
from typing import Dict, List, Any
import sqlite3

class PromptRegistry:
    """提示词注册表 - 版本管理与A/B测试"""
    
    def __init__(self, db_path: str = "prompts.db"):
        self.db = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, version)
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS prompt_metrics (
                id INTEGER PRIMARY KEY,
                prompt_id INTEGER,
                latency_ms REAL,
                token_count INTEGER,
                user_rating REAL,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(prompt_id) REFERENCES prompts(id)
            )
        """)
        self.db.commit()
    
    def register(
        self, 
        name: str, 
        content: str, 
        version: str = None,
        metadata: Dict = None
    ):
        """注册新提示词版本"""
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.db.execute(
            """INSERT INTO prompts (name, version, content, metadata)
               VALUES (?, ?, ?, ?)""",
            (name, version, content, json.dumps(metadata or {}))
        )
        self.db.commit()
        return version
    
    def activate(self, name: str, version: str):
        """激活指定版本"""
        self.db.execute(
            "UPDATE prompts SET is_active = 0 WHERE name = ?",
            (name,)
        )
        self.db.execute(
            """UPDATE prompts SET is_active = 1 
               WHERE name = ? AND version = ?""",
            (name, version)
        )
        self.db.commit()
    
    def get_active(self, name: str) -> Dict:
        """获取当前激活的提示词"""
        cursor = self.db.execute(
            """SELECT version, content, metadata FROM prompts
               WHERE name = ? AND is_active = 1""",
            (name,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "version": row[0],
                "content": row[1],
                "metadata": json.loads(row[2])
            }
        return None
    
    def get_ab_test_candidates(self, name: str, n: int = 2) -> List[Dict]:
        """获取A/B测试候选"""
        cursor = self.db.execute(
            """SELECT version, content FROM prompts
               WHERE name = ? ORDER BY created_at DESC LIMIT ?""",
            (name, n)
        )
        return [{"version": r[0], "content": r[1]} for r in cursor.fetchall()]
    
    def record_metric(
        self, 
        name: str, 
        version: str, 
        metrics: Dict[str, Any]
    ):
        """记录性能指标"""
        cursor = self.db.execute(
            "SELECT id FROM prompts WHERE name = ? AND version = ?",
            (name, version)
        )
        prompt_id = cursor.fetchone()[0]
        
        self.db.execute(
            """INSERT INTO prompt_metrics 
               (prompt_id, latency_ms, token_count, user_rating, success)
               VALUES (?, ?, ?, ?, ?)""",
            (
                prompt_id,
                metrics.get('latency_ms'),
                metrics.get('token_count'),
                metrics.get('user_rating'),
                metrics.get('success')
            )
        )
        self.db.commit()
    
    def get_performance_report(self, name: str) -> Dict:
        """获取性能报告"""
        cursor = self.db.execute("""
            SELECT p.version, 
                   AVG(pm.latency_ms) as avg_latency,
                   AVG(pm.user_rating) as avg_rating,
                   SUM(CASE WHEN pm.success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                   COUNT(*) as total_calls
            FROM prompts p
            LEFT JOIN prompt_metrics pm ON p.id = pm.prompt_id
            WHERE p.name = ?
            GROUP BY p.version
            ORDER BY p.created_at DESC
        """, (name,))
        
        return {
            row[0]: {
                "avg_latency_ms": row[1],
                "avg_rating": row[2],
                "success_rate": row[3],
                "total_calls": row[4]
            }
            for row in cursor.fetchall()
        }
```

### 2.5 提示词工程最佳实践清单

```
┌─────────────────────────────────────────────────────────────────┐
│                    提示词工程最佳实践清单                          │
├─────────────────────────────────────────────────────────────────┤
│ ✅ 设计原则                                                      │
│    □ 明确性: 指令具体,避免歧义                                    │
│    □ 结构化: 使用Markdown/JSON格式                               │
│    □ 分隔符: 用XML标签或###区分不同部分                           │
│    □ 示例优先: 用few-shot展示期望输出                             │
│                                                                 │
│ ✅ 优化技巧                                                      │
│    □ 角色设定: "你是一位资深XXX专家..."                           │
│    □ 思维链: 复杂任务要求逐步推理                                 │
│    □ 自一致性: 多次采样投票取多数                                 │
│    □ 反思机制: 让模型自我检查并修正                               │
│                                                                 │
│ ✅ 安全防护                                                      │
│    □ 输出约束: 限定格式和长度                                     │
│    □ 内容过滤: 添加安全提示词                                     │
│    □ 输入验证: 预处理敏感内容                                     │
│    □ 人工审核: 关键内容人工确认                                   │
│                                                                 │
│ ✅ 性能优化                                                      │
│    □ 提示压缩: 移除不必要的token                                  │
│    □ 缓存复用: 相似提示词结果缓存                                 │
│    □ 版本管理: 追踪提示词变更和效果                               │
│    □ A/B测试: 对比不同提示词效果                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、RAG(检索增强生成)系统构建

### 3.1 RAG架构全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RAG系统架构图                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                 │
│  │   文档加载    │────▶│   文档处理    │────▶│   向量化     │                 │
│  │  Document    │     │  Processing  │     │  Embedding   │                 │
│  │   Loaders    │     │              │     │              │                 │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                 │
│        │                                          │                          │
│        │  ┌───────────────────────────────────────┘                          │
│        │  │                                                                  │
│        ▼  ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────┐                 │
│  │                    向量数据库                             │                 │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │                 │
│  │  │   Chunk 1   │  │   Chunk 2   │  │     Chunk N     │  │                 │
│  │  │ [向量,元数据] │  │ [向量,元数据] │  │  [向量,元数据]   │  │                 │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │                 │
│  └────────────────────┬────────────────────────────────────┘                 │
│                       │                                                      │
│                       │ 相似度检索                                            │
│                       ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐                 │
│  │                      查询处理                             │                 │
│  │  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │                 │
│  │  │ Query理解    │───▶│ Query扩展    │───▶│ 向量化    │  │                 │
│  │  │ 意图识别     │    │ 同义词/重写  │    │ Embedding │  │                 │
│  │  └──────────────┘    └──────────────┘    └─────┬─────┘  │                 │
│  └─────────────────────────────────────────────────┼────────┘                 │
│                                                    │                         │
│                       检索结果                      │                         │
│  ┌─────────────────────────────────────────────────┼────────┐                 │
│  │                    重排序层                      │        │                 │
│  │  ┌───────────────────────────────────────────────┘        │                 │
│  │  │  • 向量相似度排序                                       │                 │
│  │  │  • BM25关键词匹配                                       │                 │
│  │  │  • Cross-Encoder重排序                                  │                 │
│  │  │  • 多样性/MMR算法                                       │                 │
│  │  └──────────────────────────────────────────────┘         │                 │
│  └───────────────────────┬───────────────────────────────────┘                 │
│                          │                                                   │
│                          ▼ Top-K 文档                                        │
│  ┌──────────────────────────────────────────────────────────┐                │
│  │                      提示词组装                            │                │
│  │  系统提示 + 上下文文档 + 用户查询 ─────────────────────▶   │                │
│  └──────────────────────────────────────────────────────────┘                │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐                │
│  │                      LLM生成                              │                │
│  │                    [大语言模型]                            │                │
│  └──────────────────────────────────────────────────────────┘                │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐                │
│  │                      后处理                               │                │
│  │  • 答案验证  • 引用溯源  • 安全过滤  • 格式化输出           │                │
│  └──────────────────────────────────────────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 完整RAG实现代码

```python
# rag_system.py
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import numpy as np
from enum import Enum
import hashlib

@dataclass
class Document:
    """文档数据结构"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None

@dataclass
class RetrievedChunk:
    """检索结果"""
    document: Document
    score: float
    rank: int

@dataclass
class RAGResponse:
    """RAG响应"""
    answer: str
    sources: List[RetrievedChunk]
    latency_ms: float
    tokens_used: int

class DocumentProcessor:
    """文档处理器 - 分块与预处理"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        splitter_type: str = "recursive"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter_type = splitter_type
    
    def split_text(self, text: str) -> List[str]:
        """文本分块"""
        if self.splitter_type == "recursive":
            return self._recursive_split(text)
        elif self.splitter_type == "fixed":
            return self._fixed_split(text)
        elif self.splitter_type == "semantic":
            return self._semantic_split(text)
        return [text]
    
    def _recursive_split(self, text: str) -> List[str]:
        """递归分块 - 优先按语义边界分割"""
        separators = ["\n\n", "\n", "。", ". ", " ", ""]
        chunks = []
        
        for separator in separators:
            if len(text) <= self.chunk_size:
                chunks.append(text)
                break
            
            parts = text.split(separator)
            current_chunk = ""
            
            for part in parts:
                if len(current_chunk) + len(part) + len(separator) <= self.chunk_size:
                    current_chunk += part + separator
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = part + separator
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            if all(len(c) <= self.chunk_size for c in chunks):
                break
            text = separator.join(chunks)
            chunks = []
        
        return chunks or [text]
    
    def _fixed_split(self, text: str) -> List[str]:
        """固定长度分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        return chunks
    
    def _semantic_split(self, text: str) -> List[str]:
        """语义分块 - 基于句子嵌入的相似度"""
        # 简化的实现,实际应使用句子嵌入模型
        sentences = text.replace("。", ".").split(".")
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            if current_length + len(sent) > self.chunk_size and current_chunk:
                chunks.append(". ".join(current_chunk) + ".")
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sent)
            current_length += len(sent)
        
        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
        
        return chunks
    
    def process_document(
        self, 
        content: str, 
        metadata: Dict = None
    ) -> List[Document]:
        """处理完整文档"""
        chunks = self.split_text(content)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(
                f"{metadata.get('source', '')}:{i}:{chunk[:50]}".encode()
            ).hexdigest()
            
            documents.append(Document(
                id=doc_id,
                content=chunk,
                metadata={
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_length": len(chunk)
                }
            ))
        
        return documents


class VectorStore:
    """向量存储 - 支持多种后端"""
    
    def __init__(self, embedding_func: Callable, backend: str = "memory"):
        self.embedding_func = embedding_func
        self.backend = backend
        self.documents: Dict[str, Document] = {}
        self.vectors: np.ndarray = None
        self.ids: List[str] = []
        
        if backend == "chroma":
            import chromadb
            self.client = chromadb.Client()
            self.collection = self.client.create_collection("rag_docs")
    
    async def add_documents(self, documents: List[Document]):
        """添加文档"""
        # 计算嵌入
        texts = [doc.content for doc in documents]
        embeddings = await self.embedding_func(texts)
        
        for doc, emb in zip(documents, embeddings):
            doc.embedding = emb
            self.documents[doc.id] = doc
        
        # 更新向量矩阵
        if self.vectors is None:
            self.vectors = np.array(embeddings)
            self.ids = [doc.id for doc in documents]
        else:
            self.vectors = np.vstack([self.vectors, embeddings])
            self.ids.extend([doc.id for doc in documents])
        
        # 持久化到Chroma
        if self.backend == "chroma":
            self.collection.add(
                ids=[doc.id for doc in documents],
                documents=[doc.content for doc in documents],
                embeddings=embeddings,
                metadatas=[doc.metadata for doc in documents]
            )
    
    async def similarity_search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_dict: Dict = None
    ) -> List[RetrievedChunk]:
        """相似度检索"""
        # 计算查询向量
        query_embedding = (await self.embedding_func([query]))[0]
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        # 计算余弦相似度
        similarities = cosine_similarity(query_vec, self.vectors)[0]
        
        # 过滤与排序
        results = []
        for idx, score in enumerate(similarities):
            doc_id = self.ids[idx]
            doc = self.documents[doc_id]
            
            if filter_dict:
                if not all(doc.metadata.get(k) == v for k, v in filter_dict.items()):
                    continue
            
            results.append((doc, float(score)))
        
        # 取Top-K
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [
            RetrievedChunk(document=doc, score=score, rank=i+1)
            for i, (doc, score) in enumerate(results[:top_k])
        ]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """计算余弦相似度"""
    norm_a = np.linalg.norm(a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(b, axis=1, keepdims=True)
    return np.dot(a, b.T) / (norm_a * norm_b.T + 1e-8)


class Reranker:
    """重排序器 - 提升检索质量"""
    
    def __init__(self, method: str = "cross_encoder"):
        self.method = method
    
    async def rerank(
        self, 
        query: str, 
        chunks: List[RetrievedChunk],
        top_n: int = 3
    ) -> List[RetrievedChunk]:
        """重排序候选文档"""
        if self.method == "cross_encoder":
            return await self._cross_encoder_rerank(query, chunks, top_n)
        elif self.method == "mmr":
            return self._mmr_rerank(query, chunks, top_n)
        return chunks[:top_n]
    
    async def _cross_encoder_rerank(
        self, 
        query: str, 
        chunks: List[RetrievedChunk],
        top_n: int
    ) -> List[RetrievedChunk]:
        """使用Cross-Encoder重排序"""
        # 实际实现应使用专门的cross-encoder模型
        # 这里简化为基于关键词的评分
        query_terms = set(query.lower().split())
        scored = []
        
        for chunk in chunks:
            content = chunk.document.content.lower()
            term_matches = sum(1 for term in query_terms if term in content)
            # 结合原始相似度分数
            combined_score = chunk.score * 0.6 + (term_matches / len(query_terms)) * 0.4
            scored.append((chunk, combined_score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [
            RetrievedChunk(
                document=c.document,
                score=s,
                rank=i+1
            )
            for i, (c, s) in enumerate(scored[:top_n])
        ]
    
    def _mmr_rerank(
        self, 
        query: str, 
        chunks: List[RetrievedChunk],
        top_n: int,
        lambda_param: float = 0.5
    ) -> List[RetrievedChunk]:
        """MMR (Maximal Marginal Relevance) - 平衡相关性与多样性"""
        selected = []
        candidates = chunks.copy()
        
        while len(selected) < top_n and candidates:
            if not selected:
                # 第一个选择最相关的
                best = max(candidates, key=lambda x: x.score)
            else:
                # MMR评分
                def mmr_score(chunk):
                    relevance = chunk.score
                    # 计算与已选文档的最大相似度
                    max_sim = max(
                        cosine_similarity(
                            np.array(chunk.document.embedding).reshape(1, -1),
                            np.array(s.document.embedding).reshape(1, -1)
                        )[0][0]
                        for s in selected
                    ) if selected else 0
                    return lambda_param * relevance - (1 - lambda_param) * max_sim
                
                best = max(candidates, key=mmr_score)
            
            selected.append(best)
            candidates.remove(best)
        
        return [
            RetrievedChunk(document=c.document, score=c.score, rank=i+1)
            for i, c in enumerate(selected)
        ]


class RAGSystem:
    """完整的RAG系统"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        embedding_func: Callable,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[Reranker] = None,
        config: Dict = None
    ):
        self.llm = llm_client
        self.embedding_func = embedding_func
        self.vector_store = vector_store or VectorStore(embedding_func)
        self.reranker = reranker or Reranker()
        self.doc_processor = DocumentProcessor()
        self.config = config or {}
    
    async def index_document(self, content: str, metadata: Dict = None):
        """索引文档"""
        # 分块处理
        documents = self.doc_processor.process_document(content, metadata)
        
        # 添加到向量存储
        await self.vector_store.add_documents(documents)
        
        return len(documents)
    
    async def query(
        self, 
        question: str,
        top_k: int = 5,
        rerank_top_n: int = 3,
        system_prompt: str = None
    ) -> RAGResponse:
        """执行RAG查询"""
        import time
        start_time = time.time()
        
        # 1. 检索相关文档
        retrieved = await self.vector_store.similarity_search(
            question, 
            top_k=top_k
        )
        
        # 2. 重排序
        if self.reranker:
            retrieved = await self.reranker.rerank(
                question, 
                retrieved, 
                top_n=rerank_top_n
            )
        
        # 3. 构建上下文
        context = self._build_context(retrieved)
        
        # 4. 组装提示词
        prompt = self._build_rag_prompt(
            question, 
            context,
            system_prompt
        )
        
        # 5. 生成答案
        response = await self.llm.generate(prompt)
        
        latency = (time.time() - start_time) * 1000
        
        return RAGResponse(
            answer=response.content,
            sources=retrieved,
            latency_ms=latency,
            tokens_used=response.usage.get('total_tokens', 0)
        )
    
    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        """构建上下文字符串"""
        context_parts = []
        for chunk in chunks:
            source = chunk.document.metadata.get('source', 'Unknown')
            context_parts.append(
                f"[Source: {source} - Relevance: {chunk.score:.2f}]\n"
                f"{chunk.document.content}\n"
            )
        return "\n---\n".join(context_parts)
    
    def _build_rag_prompt(
        self, 
        question: str, 
        context: str,
        system_prompt: str = None
    ) -> str:
        """构建RAG提示词"""
        default_system = """你是一个专业的问答助手。基于提供的参考资料回答用户问题。
请遵循以下规则:
1. 仅使用提供的参考资料回答问题
2. 如果资料不足以回答,请明确说明
3. 在回答中引用相关资料的来源
4. 保持回答简洁准确"""
        
        system = system_prompt or default_system
        
        return f"""{system}

参考资料:
{context}

用户问题: {question}

请基于以上资料回答问题,并引用来源:"""
```

### 3.3 高级RAG技术

```python
# advanced_rag.py

class AdvancedRAG(RAGSystem):
    """高级RAG - 包含更多优化技术"""
    
    async def query_with_hyde(
        self, 
        question: str,
        **kwargs
    ) -> RAGResponse:
        """
        HyDE (Hypothetical Document Embeddings)
        生成假设答案,用假设答案做检索
        """
        # 1. 生成假设答案
        hyde_prompt = f"""基于以下问题,生成一个假设的理想答案:
问题: {question}

假设答案:"""
        
        hyde_response = await self.llm.generate(hyde_prompt)
        hypothetical_answer = hyde_response.content
        
        # 2. 用假设答案检索(结合原始问题)
        query_embedding = await self.embedding_func([question, hypothetical_answer])
        # ... 执行检索
        
        return await self.query(question, **kwargs)
    
    async def query_with_step_back(
        self, 
        question: str,
        **kwargs
    ) -> RAGResponse:
        """
        Step-Back Prompting
        先检索抽象概念的文档,再检索具体信息
        """
        # 1. 生成抽象问题
        step_back_prompt = f"""将以下具体问题抽象为更通用的概念性问题:
具体问题: {question}

概念性问题:"""
        
        abstract_response = await self.llm.generate(step_back_prompt)
        abstract_question = abstract_response.content
        
        # 2. 同时检索抽象和具体层次
        abstract_results = await self.vector_store.similarity_search(
            abstract_question, 
            top_k=3
        )
        specific_results = await self.vector_store.similarity_search(
            question, 
            top_k=3
        )
        
        # 3. 合并结果
        all_results = self._deduplicate_results(
            abstract_results + specific_results
        )
        
        # 4. 生成答案
        return await self._generate_with_context(question, all_results)
    
    async def query_recursive(
        self, 
        question: str,
        max_iterations: int = 3,
        **kwargs
    ) -> RAGResponse:
        """
        递归RAG - 如果答案不充分,自动补充检索
        """
        all_contexts = []
        
        for iteration in range(max_iterations):
            # 检索
            results = await self.vector_store.similarity_search(
                question,
                top_k=5
            )
            all_contexts.extend(results)
            
            # 生成并评估
            response = await self._generate_with_context(
                question, 
                all_contexts
            )
            
            # 检查是否需要补充检索
            follow_up = await self._check_completeness(
                question, 
                response.content
            )
            
            if follow_up.get('is_complete', True):
                return response
            
            # 用跟进问题继续检索
            question = follow_up.get('follow_up_question', question)
        
        return response
    
    async def _check_completeness(
        self, 
        question: str, 
        answer: str
    ) -> Dict:
        """检查答案是否完整"""
        check_prompt = f"""评估以下答案是否完整回答了问题:

问题: {question}
答案: {answer}

评估:
1. 答案是否完整? (yes/no)
2. 如有遗漏,提出跟进问题以获取缺失信息

以JSON格式输出:
{{"is_complete": boolean, "follow_up_question": string or null}}"""
        
        response = await self.llm.generate(check_prompt)
        try:
            return json.loads(response.content)
        except:
            return {"is_complete": True, "follow_up_question": None}
    
    def _deduplicate_results(
        self, 
        results: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """去重检索结果"""
        seen_ids = set()
        unique = []
        for r in results:
            if r.document.id not in seen_ids:
                seen_ids.add(r.document.id)
                unique.append(r)
        return unique
```

### 3.4 RAG评估框架

```python
# rag_evaluation.py
from typing import List, Callable
from dataclasses import dataclass
import statistics

@dataclass
class RAGMetrics:
    """RAG评估指标"""
    faithfulness: float  # 忠实度 - 答案是否基于检索内容
    answer_relevance: float  # 答案相关性
    context_precision: float  # 上下文精确率
    context_recall: float  # 上下文召回率
    latency_ms: float
    
class RAGEvaluator:
    """RAG系统评估器"""
    
    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client
    
    async def evaluate_faithfulness(
        self, 
        question: str,
        answer: str,
        contexts: List[str]
    ) -> float:
        """评估忠实度"""
        eval_prompt = f"""评估以下答案是否忠实于提供的上下文:

上下文:
{' '.join(contexts)}

答案: {answer}

请判断:
1. 答案中的每个声明是否都能在上下文中找到支持
2. 是否有幻觉或无法验证的内容

评分标准 (0-1):
- 1.0: 完全忠实,所有声明都有上下文支持
- 0.5: 部分忠实,有一些无法验证的内容
- 0.0: 完全不忠实,包含大量幻觉

只返回数字评分:"""
        
        response = await self.llm.generate(eval_prompt)
        try:
            return float(response.content.strip())
        except:
            return 0.5
    
    async def evaluate_answer_relevance(
        self,
        question: str,
        answer: str
    ) -> float:
        """评估答案相关性"""
        eval_prompt = f"""评估以下答案与问题的相关程度:

问题: {question}
答案: {answer}

评分标准 (0-1):
- 1.0: 直接且完整地回答了问题
- 0.5: 部分相关但未完全回答
- 0.0: 完全不相关

只返回数字评分:"""
        
        response = await self.llm.generate(eval_prompt)
        try:
            return float(response.content.strip())
        except:
            return 0.5
    
    async def evaluate(
        self,
        test_cases: List[Dict]
    ) -> Dict[str, float]:
        """批量评估"""
        metrics = {
            "faithfulness": [],
            "answer_relevance": [],
            "context_precision": [],
            "context_recall": []
        }
        
        for case in test_cases:
            # 执行RAG查询
            response = await self.rag.query(case['question'])
            contexts = [c.document.content for c in response.sources]
            
            # 评估各项指标
            faith = await self.evaluate_faithfulness(
                case['question'],
                response.answer,
                contexts
            )
            rel = await self.evaluate_answer_relevance(
                case['question'],
                response.answer
            )
            
            metrics['faithfulness'].append(faith)
            metrics['answer_relevance'].append(rel)
        
        return {
            k: statistics.mean(v) if v else 0
            for k, v in metrics.items()
        }
```

---

## 四、大模型微调与定制化

### 4.1 微调技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       大模型微调技术架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        微调方法选择                                  │    │
│  ├─────────────────┬─────────────────┬────────────────────────────────┤    │
│  │   Full Fine-tuning              │   Parameter-Efficient Fine-tuning │    │
│  │   (全参数微调)                   │   (参数高效微调)                   │    │
│  ├─────────────────┼─────────────────┼────────────────────────────────┤    │
│  │ • 预训练 → 微调  │ • LoRA          │ • Prompt Tuning                │    │
│  │ • 需要大量计算   │ • QLoRA (量化)   │ • Prefix Tuning                │    │
│  │ • 容易过拟合    │ • AdaLoRA       │ • P-Tuning v2                  │    │
│  │ • 灾难性遗忘    │ • DoRA          │ • IA³                          │    │
│  └─────────────────┴─────────────────┴────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      典型微调流程                                     │    │
│  │                                                                      │    │
│  │   数据准备 ──▶ 数据预处理 ──▶ 模型选择 ──▶ 配置训练参数              │    │
│  │      │           │            │            │                         │    │
│  │      ▼           ▼            ▼            ▼                         │    │
│  │   原始数据    清洗/标注    Base Model    LoRA配置                     │    │
│  │   领域数据    Tokenization  7B/13B/70B   Rank=64                      │    │
│  │   指令数据    数据增强      量化版本      Learning Rate               │    │
│  │                                                                      │    │
│  │   训练执行 ──▶ 评估验证 ──▶ 模型合并 ──▶ 部署推理                     │    │
│  │      │           │            │            │                         │    │
│  │      ▼           ▼            ▼            ▼                         │    │
│  │   GPU/TPU     验证集测试    LoRA +      vLLM/                        │    │
│  │   分布式训练   指标评估     Base模型    TGI推理                       │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 LoRA/QLoRA微调完整实现

```python
# llm_finetuning.py
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset
import json
from typing import List, Dict, Optional

class LLMFinetuner:
    """大语言模型微调器"""
    
    def __init__(
        self,
        base_model_path: str,
        output_dir: str,
        use_qlora: bool = True
    ):
        self.base_model_path = base_model_path
        self.output_dir = output_dir
        self.use_qlora = use_qlora
        self.model = None
        self.tokenizer = None
        
    def setup_model_and_tokenizer(self):
        """设置模型和分词器"""
        # QLoRA配置 - 4bit量化
        if self.use_qlora:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        else:
            bnb_config = None
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if not self.use_qlora else None
        )
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # 准备模型用于训练
        if self.use_qlora:
            self.model = prepare_model_for_kbit_training(self.model)
    
    def setup_lora(
        self,
        r: int = 64,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        target_modules: List[str] = None
    ):
        """配置LoRA"""
        # 自动识别目标模块
        if target_modules is None:
            target_modules = self._find_target_modules()
        
        lora_config = LoraConfig(
            r=r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
            # 新增选项
            use_rslora=True,  # 使用Rank-Stabilized LoRA
            init_lora_weights="gaussian"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        return lora_config
    
    def _find_target_modules(self) -> List[str]:
        """自动查找可训练的模块"""
        # 常见的注意力模块名称
        target_modules = []
        module_names = [name for name, _ in self.model.named_modules()]
        
        patterns = ["q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj"]
        
        for pattern in patterns:
            if any(pattern in name for name in module_names):
                target_modules.append(pattern)
        
        return target_modules or ["q_proj", "v_proj"]
    
    def prepare_dataset(
        self,
        data: List[Dict[str, str]],
        max_length: int = 2048,
        template: str = "alpaca"
    ) -> Dataset:
        """准备数据集"""
        
        def format_alpaca(example):
            """Alpaca格式模板"""
            if example.get('input'):
                prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
            else:
                prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Response:
{example['output']}"""
            return prompt
        
        def format_chatml(example):
            """ChatML格式模板"""
            messages = [
                {"role": "system", "content": example.get('system', 'You are a helpful assistant.')},
                {"role": "user", "content": example['instruction']},
                {"role": "assistant", "content": example['output']}
            ]
            return self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=False
            )
        
        # 选择模板
        formatter = format_chatml if template == "chatml" else format_alpaca
        
        # 格式化数据
        formatted_data = []
        for item in data:
            text = formatter(item)
            formatted_data.append({"text": text})
        
        dataset = Dataset.from_list(formatted_data)
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length"
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset
    
    def train(
        self,
        train_dataset: Dataset,
        eval_dataset: Dataset = None,
        num_epochs: int = 3,
        batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_ratio: float = 0.03,
        logging_steps: int = 10,
        save_steps: int = 500,
        **kwargs
    ):
        """执行训练"""
        
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            optim="paged_adamw_8bit" if self.use_qlora else "adamw_torch",
            save_steps=save_steps,
            logging_steps=logging_steps,
            learning_rate=learning_rate,
            weight_decay=0.001,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            max_grad_norm=0.3,
            max_steps=-1,
            warmup_ratio=warmup_ratio,
            group_by_length=True,
            lr_scheduler_type="cosine",
            report_to="tensorboard",
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=save_steps if eval_dataset else None,
            load_best_model_at_end=True if eval_dataset else False,
            **kwargs
        )
        
        # 数据整理器
        data_collator = DataCollatorForSeq2Seq(
            self.tokenizer,
            pad_to_multiple_of=8,
            return_tensors="pt",
            padding=True,
            label_pad_token_id=-100
        )
        
        # 训练器
        from trl import SFTTrainer
        
        trainer = SFTTrainer(
            model=self.model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            args=training_args,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
            max_seq_length=2048
        )
        
        # 训练
        trainer.train()
        
        # 保存模型
        trainer.save_model(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        return trainer


# 使用示例
async def demo_finetuning():
    """演示微调流程"""
    
    # 准备训练数据
    train_data = [
        {
            "instruction": "将以下中文翻译成英文",
            "input": "人工智能正在改变世界",
            "output": "Artificial intelligence is changing the world."
        },
        {
            "instruction": "总结以下段落的主要观点",
            "input": "机器学习是人工智能的一个分支...",
            "output": "主要观点: 1. 机器学习是AI分支 2. 通过数据学习模式 3. 应用广泛"
        }
        # ... 更多数据
    ]
    
    # 初始化微调器
    finetuner = LLMFinetuner(
        base_model_path="meta-llama/Llama-2-7b-hf",
        output_dir="./finetuned_model",
        use_qlora=True
    )
    
    # 设置
    finetuner.setup_model_and_tokenizer()
    finetuner.setup_lora(r=64, lora_alpha=16)
    
    # 准备数据
    train_dataset = finetuner.prepare_dataset(
        train_data,
        max_length=2048,
        template="alpaca"
    )
    
    # 训练
    trainer = finetuner.train(
        train_dataset=train_dataset,
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4
    )
    
    return trainer
```

### 4.3 微调最佳实践

```python
# finetuning_best_practices.py

class FinetuningBestPractices:
    """微调最佳实践指南"""
    
    # 不同规模模型的推荐配置
    RECOMMENDED_CONFIGS = {
        "7B": {
            "lora_r": 64,
            "lora_alpha": 16,
            "batch_size": 4,
            "learning_rate": 2e-4,
            "max_length": 2048,
            "gpu_memory": "16GB"
        },
        "13B": {
            "lora_r": 128,
            "lora_alpha": 32,
            "batch_size": 2,
            "learning_rate": 1e-4,
            "max_length": 2048,
            "gpu_memory": "24GB"
        },
        "70B": {
            "lora_r": 256,
            "lora_alpha": 64,
            "batch_size": 1,
            "learning_rate": 5e-5,
            "max_length": 4096,
            "gpu_memory": "80GB"
        }
    }
    
    @staticmethod
    def prepare_instruction_data(
        raw_data: List[Dict],
        task_type: str
    ) -> List[Dict]:
        """
        准备指令微调数据
        
        Args:
            raw_data: 原始数据
            task_type: 任务类型 (qa/summarization/classification/...)
        """
        formatted = []
        
        for item in raw_data:
            if task_type == "qa":
                formatted.append({
                    "instruction": item.get('question', ''),
                    "input": item.get('context', ''),
                    "output": item.get('answer', '')
                })
            elif task_type == "summarization":
                formatted.append({
                    "instruction": "请总结以下文本:",
                    "input": item['text'],
                    "output": item['summary']
                })
            elif task_type == "classification":
                formatted.append({
                    "instruction": f"请将以下文本分类为: {item.get('labels', '')}",
                    "input": item['text'],
                    "output": item['label']
                })
        
        return formatted
    
    @staticmethod
    def estimate_training_cost(
        num_samples: int,
        avg_length: int,
        model_size: str,
        num_epochs: int
    ) -> Dict:
        """估算训练成本"""
        
        # 粗略估算token数量
        tokens_per_sample = avg_length * 1.3  # 中文字符到token的转换
        total_tokens = num_samples * tokens_per_sample * num_epochs
        
        # 不同模型的训练速度 (tokens/second, A100)
        speed_map = {
            "7B": 2000,
            "13B": 1200,
            "70B": 300
        }
        
        speed = speed_map.get(model_size, 1000)
        training_time_hours = total_tokens / speed / 3600
        
        # A100每小时成本 (约$2-3)
        estimated_cost = training_time_hours * 2.5
        
        return {
            "total_tokens": int(total_tokens),
            "estimated_hours": round(training_time_hours, 2),
            "estimated_cost_usd": round(estimated_cost, 2),
            "gpu_recommendation": f"{int(training_time_hours / 10) + 1}x A100"
        }
    
    @staticmethod
    def validate_dataset(data: List[Dict]) -> Dict:
        """验证数据集质量"""
        issues = []
        stats = {
            "total_samples": len(data),
            "avg_instruction_length": 0,
            "avg_output_length": 0,
            "duplicate_inputs": 0
        }
        
        seen_inputs = set()
        inst_lengths = []
        output_lengths = []
        
        for item in data:
            # 检查必需字段
            if 'instruction' not in item or 'output' not in item:
                issues.append(f"缺少必需字段: {item}")
                continue
            
            # 检查空值
            if not item['instruction'].strip() or not item['output'].strip():
                issues.append(f"空值内容: {item}")
            
            # 统计长度
            inst_lengths.append(len(item['instruction']))
            output_lengths.append(len(item['output']))
            
            # 检查重复
            input_key = item.get('input', '') + item['instruction']
            if input_key in seen_inputs:
                stats["duplicate_inputs"] += 1
            seen_inputs.add(input_key)
        
        if inst_lengths:
            stats["avg_instruction_length"] = sum(inst_lengths) / len(inst_lengths)
        if output_lengths:
            stats["avg_output_length"] = sum(output_lengths) / len(output_lengths)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues[:10],  # 只显示前10个问题
            "stats": stats
        }
```

### 4.4 模型评估与合并

```python
# model_evaluation.py
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
import json

class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, base_model_path: str, adapter_path: str = None):
        self.base_model_path = base_model_path
        self.adapter_path = adapter_path
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """加载模型(合并adapter)"""
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        
        if self.adapter_path:
            self.model = PeftModel.from_pretrained(
                base_model,
                self.adapter_path
            )
            # 合并权重以便推理
            self.model = self.model.merge_and_unload()
        else:
            self.model = base_model
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
    
    async def evaluate_on_benchmark(
        self, 
        benchmark: str = "ceval",
        num_samples: int = None
    ) -> Dict:
        """在基准测试上评估"""
        
        if benchmark == "ceval":
            return await self._evaluate_ceval(num_samples)
        elif benchmark == "mmlu":
            return await self._evaluate_mmlu(num_samples)
        
        return {"error": f"Unknown benchmark: {benchmark}"}
    
    async def _evaluate_ceval(self, num_samples: int = None) -> Dict:
        """评估中文C-Eval基准"""
        from datasets import load_dataset
        
        dataset = load_dataset("ceval/ceval-exam", name="all")
        
        correct = 0
        total = 0
        results_by_subject = {}
        
        for item in dataset["validation"]:
            if num_samples and total >= num_samples:
                break
            
            # 构建提示
            prompt = f"""以下是中国关于{item['subject']}考试的单项选择题,请选出正确答案。

{item['question']}

A. {item['A']}
B. {item['B']}
C. {item['C']}
D. {item['D']}

答案:"""
            
            # 生成答案
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1,
                do_sample=False
            )
            
            answer = self.tokenizer.decode(outputs[0][-1:], skip_special_tokens=True)
            predicted = answer.strip().upper()
            
            is_correct = predicted == item['answer']
            if is_correct:
                correct += 1
            total += 1
            
            # 按科目统计
            subject = item['subject']
            if subject not in results_by_subject:
                results_by_subject[subject] = {"correct": 0, "total": 0}
            results_by_subject[subject]["total"] += 1
            if is_correct:
                results_by_subject[subject]["correct"] += 1
        
        return {
            "overall_accuracy": correct / total if total > 0 else 0,
            "correct": correct,
            "total": total,
            "by_subject": {
                k: {"accuracy": v["correct"] / v["total"]} 
                for k, v in results_by_subject.items()
            }
        }
    
    def merge_and_save(self, output_path: str):
        """合并LoRA权重并保存完整模型"""
        if self.model is None:
            self.load_model()
        
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        print(f"合并后的模型已保存到: {output_path}")


class ContinuousLearningPipeline:
    """持续学习管道 - 在线学习与人反馈"""
    
    def __init__(self, base_model_path: str, adapter_path: str):
        self.base_model_path = base_model_path
        self.adapter_path = adapter_path
        self.feedback_buffer = []
    
    def collect_feedback(
        self, 
        prompt: str, 
        response: str, 
        rating: float,
        improved_response: str = None
    ):
        """收集用户反馈"""
        self.feedback_buffer.append({
            "prompt": prompt,
            "response": response,
            "rating": rating,
            "improved_response": improved_response,
            "timestamp": datetime.now().isoformat()
        })
    
    async def incremental_update(self, min_feedback: int = 100):
        """增量更新模型"""
        if len(self.feedback_buffer) < min_feedback:
            return {"status": "insufficient_feedback", "count": len(self.feedback_buffer)}
        
        # 筛选高质量反馈
        good_feedback = [
            f for f in self.feedback_buffer 
            if f["rating"] >= 4 or f["improved_response"]
        ]
        
        # 转换为训练数据
        train_data = []
        for fb in good_feedback:
            if fb.get("improved_response"):
                train_data.append({
                    "instruction": fb["prompt"],
                    "output": fb["improved_response"]
                })
        
        # 执行增量训练
        finetuner = LLMFinetuner(
            base_model_path=self.base_model_path,
            output_dir=f"{self.adapter_path}_updated",
            use_qlora=True
        )
        
        # ... 执行训练流程
        
        # 清空已使用的反馈
        self.feedback_buffer = []
        
        return {"status": "updated", "samples_used": len(train_data)}
```

---

## 五、AI Agent设计与实现

### 5.1 Agent架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI Agent系统架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Agent核心层                                  │    │
│  │                                                                      │    │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐  │    │
│  │   │    规划模块      │    │    记忆系统      │    │   行动执行器   │  │    │
│  │   │   (Planning)    │◀──▶│    (Memory)     │◀──▶│  (Action)     │  │    │
│  │   │                 │    │                 │    │               │  │    │
│  │   │ • 任务分解      │    │ • 短期记忆      │    │ • 工具调用    │  │    │
│  │   │ • 策略选择      │    │ • 长期记忆      │    │ • API执行     │  │    │
│  │   │ • 反思迭代      │    │ • 工作记忆      │    │ • 代码执行    │  │    │
│  │   │ • 多步推理      │    │ • 向量检索      │    │ • 界面操作    │  │    │
│  │   └────────┬────────┘    └────────┬────────┘    └───────┬───────┘  │    │
│  │            │                      │                      │          │    │
│  │            └──────────────────────┼──────────────────────┘          │    │
│  │                                   │                                 │    │
│  │                        ┌──────────▼──────────┐                      │    │
│  │                        │      推理引擎        │                      │    │
│  │                        │   (Reasoning Engine) │                      │    │
│  │                        │                      │                      │    │
│  │                        │  ReAct / CoT / ToT   │                      │    │
│  │                        └──────────────────────┘                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         工具层 (Tools)                               │    │
│  │                                                                      │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │   │  搜索    │ │  代码    │ │  数据库  │ │   API    │ │  浏览器  │  │    │
│  │   │ Search   │ │  Code    │ │   DB     │ │   Call   │ │ Browser  │  │    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  │                                                                      │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │   │  计算    │ │  文件    │ │  向量    │ │  知识    │ │   LLM    │  │    │
│  │   │  Math    │ │  File    │ │  Vector  │ │   Graph  │ │  Call    │  │    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      观测与反馈层                                     │    │
│  │                                                                      │    │
│  │   用户输入 ◀──▶ Agent处理循环 ◀──▶ 环境观测 ◀──▶ 结果反馈           │    │
│  │                 (Observation → Thought → Action)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 ReAct Agent完整实现

```python
# react_agent.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import re

class ActionType(Enum):
    """行动类型"""
    THINK = "think"
    TOOL_CALL = "tool_call"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"

@dataclass
class Thought:
    """思考步骤"""
    step: int
    observation: str
    thought: str
    action: str
    action_input: Dict
    action_output: str = ""

@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict
    function: Callable
    
    def to_schema(self) -> str:
        """转换为函数调用模式"""
        return f"""{self.name}: {self.description}
参数: {json.dumps(self.parameters, ensure_ascii=False, indent=2)}"""

class BaseAgent(ABC):
    """Agent基类"""
    
    @abstractmethod
    async def run(self, query: str, max_iterations: int = 10) -> str:
        pass

class ReActAgent(BaseAgent):
    """ReAct (Reasoning + Acting) Agent"""
    
    REACT_PROMPT_TEMPLATE = """你是一个智能助手,可以调用工具来解决问题。

可用工具:
{tools_schema}

请按照以下格式回答:

Question: 需要回答的问题
Thought: 思考当前情况,决定下一步行动
Action: 要采取的行动(必须是上述工具之一,或"Final Answer")
Action Input: 行动的输入参数(JSON格式)
Observation: 行动的结果
... (这个Thought/Action/Observation循环可以重复多次)
Thought: 我现在知道最终答案
Final Answer: 对原始问题的最终回答

现在开始:

Question: {query}

Thought:"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        tools: List[Tool] = None,
        max_iterations: int = 10
    ):
        self.llm = llm_client
        self.tools = {t.name: t for t in (tools or [])}
        self.max_iterations = max_iterations
        self.conversation_history = []
    
    def _build_tools_schema(self) -> str:
        """构建工具模式描述"""
        return "\n\n".join([t.to_schema() for t in self.tools.values()])
    
    def _parse_action(self, text: str) -> tuple:
        """解析行动和输入"""
        # 匹配 Action: xxx
        action_match = re.search(r'Action:\s*(\w+)', text, re.IGNORECASE)
        if not action_match:
            return None, None
        
        action = action_match.group(1).strip()
        
        # 匹配 Action Input: {...} 或 Action Input: ...
        input_match = re.search(
            r'Action Input:\s*(\{[^}]*\}|.+?)(?=\n|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        action_input = {}
        if input_match:
            try:
                input_str = input_match.group(1).strip()
                action_input = json.loads(input_str)
            except json.JSONDecodeError:
                action_input = {"input": input_match.group(1).strip()}
        
        return action, action_input
    
    def _extract_thought(self, text: str) -> str:
        """提取思考内容"""
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', text, re.DOTALL | re.IGNORECASE)
        return thought_match.group(1).strip() if thought_match else ""
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """执行工具"""
        if tool_name == "Final Answer":
            return tool_input.get("answer", "")
        
        if tool_name not in self.tools:
            return f"错误: 未知工具 '{tool_name}'"
        
        tool = self.tools[tool_name]
        try:
            result = await tool.function(**tool_input) if asyncio.iscoroutinefunction(tool.function) else tool.function(**tool_input)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    async def run(self, query: str) -> str:
        """执行ReAct循环"""
        # 初始化提示词
        prompt = self.REACT_PROMPT_TEMPLATE.format(
            tools_schema=self._build_tools_schema(),
            query=query
        )
        
        thoughts_history = []
        
        for iteration in range(self.max_iterations):
            # 生成下一步
            response = await self.llm.generate(prompt)
            content = response.content
            
            # 解析思考
            thought_text = self._extract_thought(content)
            
            # 解析行动
            action, action_input = self._parse_action(content)
            
            if not action:
                # 没有明确的行动,可能是最终答案
                if "Final Answer:" in content:
                    return content.split("Final Answer:")[-1].strip()
                prompt += f"\n{content}\nObservation: 请明确你的下一步行动 (Action)"
                continue
            
            # 执行行动
            observation = await self._execute_tool(action, action_input)
            
            # 记录
            thoughts_history.append({
                "step": iteration + 1,
                "thought": thought_text,
                "action": action,
                "action_input": action_input,
                "observation": observation
            })
            
            # 检查是否完成
            if action == "Final Answer":
                return observation
            
            # 更新提示词继续循环
            prompt += f"\n{content}\nObservation: {observation}\nThought:"
        
        # 达到最大迭代次数
        return f"达到最大迭代次数。当前进展:\n{json.dumps(thoughts_history, ensure_ascii=False, indent=2)}"


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def register_function(
        self,
        name: str = None,
        description: str = None
    ):
        """装饰器方式注册"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""
            
            # 通过类型注解推断参数
            import inspect
            sig = inspect.signature(func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in sig.parameters.items():
                param_info = {"type": "string"}  # 默认字符串
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_info["type"] = "integer"
                    elif param.annotation == float:
                        param_info["type"] = "number"
                    elif param.annotation == bool:
                        param_info["type"] = "boolean"
                
                parameters["properties"][param_name] = param_info
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            
            tool = Tool(
                name=tool_name,
                description=tool_desc,
                parameters=parameters,
                function=func
            )
            self.register(tool)
            return func
        return decorator
    
    def get_tools(self) -> List[Tool]:
        return list(self._tools.values())


# 创建工具示例
registry = ToolRegistry()

@registry.register_function(
    name="web_search",
    description="搜索网络获取信息"
)
async def web_search(query: str, top_k: int = 5) -> str:
    """模拟搜索工具"""
    # 实际实现应调用搜索API
    return f"搜索结果: 关于'{query}'的{top_k}条结果"

@registry.register_function(
    name="calculator",
    description="执行数学计算"
)
def calculator(expression: str) -> str:
    """计算器工具"""
    try:
        # 注意: eval有安全风险,生产环境应使用ast.literal_eval或安全计算库
        import ast
        node = ast.parse(expression, mode='eval')
        
        # 只允许安全操作
        allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num,
                        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
                        ast.Load)
        
        if not all(isinstance(n, allowed_nodes) for n in ast.walk(node)):
            return "错误: 不支持的表达式"
        
        result = eval(compile(node, '<string>', 'eval'), {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

@registry.register_function(
    name="get_weather",
    description="获取指定城市的天气信息"
)
async def get_weather(city: str, date: str = "today") -> str:
    """天气查询工具"""
    # 实际实现应调用天气API
    return f"{city} {date} 的天气: 晴, 25°C"
```

### 5.3 多Agent协作系统

```python
# multi_agent_system.py
from typing import List, Set
import asyncio

class AgentRole(Enum):
    """Agent角色"""
    PLANNER = "planner"      # 规划者
    EXECUTOR = "executor"    # 执行者
    CRITIC = "critic"        # 批评者
    RESEARCHER = "researcher" # 研究员
    WRITER = "writer"        # 撰写者

@dataclass
class Agent:
    """Agent定义"""
    name: str
    role: AgentRole
    system_prompt: str
    llm_client: BaseLLMClient
    tools: List[Tool] = field(default_factory=list)

class MultiAgentSystem:
    """多Agent协作系统"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_bus: asyncio.Queue = asyncio.Queue()
        self.shared_memory: Dict = {}
    
    def register_agent(self, agent: Agent):
        """注册Agent"""
        self.agents[agent.name] = agent
    
    async def broadcast(
        self, 
        sender: str, 
        message: str, 
        recipients: List[str] = None
    ):
        """广播消息"""
        recipients = recipients or list(self.agents.keys())
        await self.message_bus.put({
            "sender": sender,
            "recipients": recipients,
            "content": message,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def run_collaborative_task(
        self,
        task: str,
        max_rounds: int = 5
    ) -> str:
        """
        执行协作任务
        
        示例流程: Plan -> Execute -> Review -> Refine
        """
        
        # 初始化任务上下文
        context = {
            "original_task": task,
            "current_plan": None,
            "execution_results": [],
            "critiques": [],
            "iterations": 0
        }
        
        for round_num in range(max_rounds):
            context["iterations"] = round_num + 1
            
            # 1. 规划阶段
            if round_num == 0 or context.get("need_replan"):
                plan = await self._run_planner(task, context)
                context["current_plan"] = plan
                await self.broadcast("system", f"新计划: {plan}")
            
            # 2. 执行阶段
            results = await self._run_executor(context["current_plan"], context)
            context["execution_results"].append(results)
            
            # 3. 评审阶段
            critique = await self._run_critic(results, context)
            context["critiques"].append(critique)
            
            # 4. 判断是否完成
            if critique.get("is_satisfactory", False):
                break
            
            context["need_replan"] = critique.get("suggestions")
        
        # 生成最终答案
        final_answer = await self._synthesize_answer(context)
        return final_answer
    
    async def _run_planner(self, task: str, context: Dict) -> str:
        """运行规划Agent"""
        planner = self.agents.get("planner")
        if not planner:
            return f"直接执行: {task}"
        
        prompt = f"""你是一个任务规划专家。请将以下任务分解为可执行的步骤。

任务: {task}
历史上下文: {json.dumps(context, ensure_ascii=False)}

请以JSON格式输出执行计划:
{{
    "steps": [
        {{"step": 1, "action": "具体行动", "expected_output": "预期结果"}},
        ...
    ],
    "estimated_complexity": "low/medium/high"
}}"""
        
        response = await planner.llm_client.generate(prompt)
        return response.content
    
    async def _run_executor(self, plan: str, context: Dict) -> str:
        """运行执行Agent"""
        executor = self.agents.get("executor")
        if not executor:
            return "无执行Agent可用"
        
        # 创建ReAct agent执行任务
        react_agent = ReActAgent(
            llm_client=executor.llm_client,
            tools=executor.tools
        )
        
        result = await react_agent.run(f"执行计划: {plan}")
        return result
    
    async def _run_critic(self, results: str, context: Dict) -> Dict:
        """运行批评Agent"""
        critic = self.agents.get("critic")
        if not critic:
            return {"is_satisfactory": True}
        
        prompt = f"""你是一个质量评审专家。请评估以下执行结果。

原始任务: {context['original_task']}
执行计划: {context['current_plan']}
执行结果: {results}

请评估:
1. 结果是否满足任务要求? (yes/no)
2. 有哪些问题或不足?
3. 改进建议

以JSON格式输出:
{{
    "is_satisfactory": boolean,
    "score": 1-10,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}"""
        
        response = await critic.llm_client.generate(prompt)
        try:
            return json.loads(response.content)
        except:
            return {"is_satisfactory": True}
    
    async def _synthesize_answer(self, context: Dict) -> str:
        """综合所有结果生成最终答案"""
        writer = self.agents.get("writer")
        if not writer:
            return context["execution_results"][-1] if context["execution_results"] else "无结果"
        
        prompt = f"""基于以下执行过程,生成最终答案。

原始任务: {context['original_task']}

执行历史:
{json.dumps(context['execution_results'], ensure_ascii=False, indent=2)}

评审意见:
{json.dumps(context['critiques'], ensure_ascii=False, indent=2)}

请生成完整、准确的最终答案:"""
        
        response = await writer.llm_client.generate(prompt)
        return response.content


class AgentOrchestrator:
    """Agent编排器 - 动态Agent调度"""
    
    def __init__(self):
        self.available_agents: Dict[str, Agent] = {}
        self.task_history: List[Dict] = []
    
    async def route_task(self, task: str) -> str:
        """智能路由任务到合适的Agent"""
        
        # 分析任务类型
        routing_prompt = f"""分析以下任务,选择最合适的处理Agent类型:

任务: {task}

可选Agent类型:
- code_agent: 编程、代码相关任务
- research_agent: 研究、信息收集任务
- writing_agent: 写作、创作任务
- analysis_agent: 数据分析任务
- general_agent: 通用任务

请只返回Agent类型名称:"""
        
        # 使用通用LLM进行路由决策
        decision = await self.llm_client.generate(routing_prompt)
        agent_type = decision.content.strip().lower()
        
        # 查找对应Agent
        for name, agent in self.available_agents.items():
            if agent.role.value in agent_type or agent_type in name:
                # 执行
                react_agent = ReActAgent(agent.llm_client, agent.tools)
                result = await react_agent.run(task)
                
                self.task_history.append({
                    "task": task,
                    "routed_to": name,
                    "result": result
                })
                
                return result
        
        # 默认使用第一个可用Agent
        if self.available_agents:
            default_agent = list(self.available_agents.values())[0]
            react_agent = ReActAgent(default_agent.llm_client, default_agent.tools)
            return await react_agent.run(task)
        
        return "无可用Agent"
```

### 5.4 Agent记忆系统

```python
# agent_memory.py
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from collections import deque

class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"    # 短期记忆
    LONG_TERM = "long_term"      # 长期记忆
    EPISODIC = "episodic"        # 情景记忆
    SEMANTIC = "semantic"        # 语义记忆
    PROCEDURAL = "procedural"    # 程序记忆

@dataclass
class Memory:
    """记忆单元"""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    importance: float  # 0-1
    embeddings: Optional[List[float]] = None
    metadata: Dict = field(default_factory=dict)

class AgentMemory:
    """Agent记忆系统"""
    
    def __init__(
        self,
        embedding_func: Callable,
        short_term_limit: int = 10,
        importance_threshold: float = 0.5
    ):
        self.embedding_func = embedding_func
        self.short_term_limit = short_term_limit
        self.importance_threshold = importance_threshold
        
        # 不同记忆存储
        self.short_term: deque = deque(maxlen=short_term_limit)
        self.long_term: List[Memory] = []
        self.working_memory: Dict = {}
    
    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Dict = None
    ):
        """添加记忆"""
        memory_id = hashlib.md5(
            f"{content}:{datetime.now()}".encode()
        ).hexdigest()
        
        # 计算嵌入
        embeddings = await self.embedding_func([content])
        
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            embeddings=embeddings[0] if embeddings else None,
            metadata=metadata or {}
        )
        
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term.append(memory)
        else:
            self.long_term.append(memory)
        
        # 自动巩固重要记忆到长期记忆
        if importance >= self.importance_threshold and memory_type == MemoryType.SHORT_TERM:
            await self._consolidate_memory(memory)
    
    async def _consolidate_memory(self, memory: Memory):
        """巩固记忆到长期存储"""
        # 检查是否已存在相似记忆
        similar = await self.retrieve_similar(memory.content, top_k=1)
        
        if similar and similar[0][1] > 0.9:  # 相似度阈值
            # 合并记忆
            existing = similar[0][0]
            existing.content += f"\n[更新: {memory.timestamp}] {memory.content}"
            existing.importance = max(existing.importance, memory.importance)
        else:
            # 添加到长期记忆
            memory.memory_type = MemoryType.LONG_TERM
            self.long_term.append(memory)
    
    async def retrieve_similar(
        self,
        query: str,
        top_k: int = 5,
        memory_types: List[MemoryType] = None
    ) -> List[tuple]:
        """检索相关记忆"""
        query_emb = (await self.embedding_func([query]))[0]
        
        # 合并所有记忆
        all_memories = list(self.short_term) + self.long_term
        
        if memory_types:
            all_memories = [m for m in all_memories if m.memory_type in memory_types]
        
        # 计算相似度
        scored = []
        for memory in all_memories:
            if memory.embeddings:
                sim = cosine_similarity(
                    np.array(query_emb).reshape(1, -1),
                    np.array(memory.embeddings).reshape(1, -1)
                )[0][0]
                # 重要性加权
                weighted_score = sim * (0.7 + 0.3 * memory.importance)
                scored.append((memory, weighted_score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    async def get_context_for_query(
        self,
        query: str,
        max_memories: int = 5
    ) -> str:
        """获取查询相关的上下文记忆"""
        relevant = await self.retrieve_similar(query, top_k=max_memories)
        
        if not relevant:
            return ""
        
        context_parts = ["相关历史信息:"]
        for memory, score in relevant:
            time_ago = datetime.now() - memory.timestamp
            context_parts.append(
                f"- [{memory.memory_type.value}] {time_ago.days}天前 "
                f"(相关度: {score:.2f}): {memory.content[:200]}..."
            )
        
        return "\n".join(context_parts)
    
    def forget_old_memories(self, days: int = 30):
        """遗忘旧的不重要记忆"""
        cutoff = datetime.now() - timedelta(days=days)
        
        self.long_term = [
            m for m in self.long_term 
            if m.timestamp > cutoff or m.importance > 0.7
        ]
    
    def summarize_memory(self) -> str:
        """总结记忆状态"""
        return f"""记忆状态:
- 短期记忆: {len(self.short_term)} 条
- 长期记忆: {len(self.long_term)} 条
- 工作记忆: {len(self.working_memory)} 项
"""
```

---

## 六、性能优化策略汇总

### 6.1 全链路优化矩阵

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      大模型应用全链路优化矩阵                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  层级          优化目标              具体策略                    预期收益      │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  接入层        降低延迟              • 边缘部署/CDN              TTFT < 200ms │
│               提升吞吐               • 连接池复用                QPS +200%    │
│                                     • 负载均衡                                │
│                                     • 就近路由                                │
│                                                                              │
│  推理层        降低成本              • 模型量化(INT8/INT4)        显存 -75%    │
│               提升速度               • 批处理推理                吞吐 +300%   │
│                                     • vLLM/TGI                 延迟 -50%     │
│                                     • KV Cache优化                            │
│                                     • Speculative Decoding                    │
│                                                                              │
│  应用层        提升效率              • 提示词压缩                Token -30%   │
│               减少调用               • 多级缓存                  命中率 60%+   │
│                                     • 请求合并                                │
│                                     • 异步处理                                │
│                                                                              │
│  数据层        加速检索              • 向量索引优化              检索 -10ms    │
│               降低存储               • 分块策略优化                           │
│                                     • 近似最近邻                              │
│                                     • 冷热分离                                │
│                                                                              │
│  模型层        提升效果              • LoRA微调                  准确率 +15%   │
│               降低资源               • 蒸馏/剪枝                 模型 -90%     │
│                                     • MoE架构                                 │
│                                     • 动态路由                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 关键性能指标(KPI)

| 指标 | 描述 | 目标值 | 测量方法 |
|-----|------|-------|---------|
| **TTFT** | 首Token生成时间 | < 500ms | 请求开始到首Token |
| **TPOT** | 每Token生成时间 | < 50ms | 连续Token间隔 |
| **Throughput** | 系统吞吐量 | > 100 req/s | 单位时间完成请求 |
| **Cost/1K Tokens** | 每千Token成本 | <$0.01 | 总成本/Token数 |
| **Cache Hit Rate** | 缓存命中率 | > 60% | 命中/总请求 |
| **Accuracy** | 任务准确率 | > 90% | 正确回答/总回答 |

### 6.3 生产部署检查清单

```
┌─────────────────────────────────────────────────────────────────┐
│                  生产环境部署检查清单                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  □ 基础设施                                                      │
│    □ GPU资源充足,预留20%缓冲                                      │
│    □ 配置自动扩缩容(HPA)                                          │
│    □ 设置资源限制(requests/limits)                                │
│    □ 多可用区部署保证高可用                                        │
│                                                                 │
│  □ 安全                                                          │
│    □ API密钥轮转机制                                              │
│    □ 输入内容过滤(提示词注入防护)                                   │
│    □ 输出内容审核                                                 │
│    □ 访问日志审计                                                 │
│    □ 敏感信息脱敏                                                 │
│                                                                 │
│  □ 监控                                                          │
│    □ 模型推理延迟监控                                             │
│    □ Token用量监控                                               │
│    □ 错误率/异常监控                                              │
│    □ 成本监控与告警                                               │
│    □ 业务指标监控(准确率等)                                        │
│                                                                 │
│  □ 优化                                                          │
│    □ 启用推理优化(vLLM/TensorRT-LLM)                              │
│    □ 配置多级缓存                                                │
│    □ 批处理大小调优                                              │
│    □ 模型量化部署(INT8/INT4)                                      │
│                                                                 │
│  □ 容错                                                          │
│    □ 模型降级策略(大模型→小模型)                                   │
│    □ 熔断机制                                                    │
│    □ 超时重试策略                                                │
│    □  graceful shutdown                                         │
│                                                                 │
│  □ 运维                                                          │
│    □ 模型版本管理                                                │
│    □ A/B测试能力                                                 │
│    □ 快速回滚机制                                                │
│    □ 文档与运行手册                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 参考文献

1. OpenAI API Documentation - https://platform.openai.com/docs
2. Anthropic Claude API - https://docs.anthropic.com/
3. Hugging Face Transformers - https://huggingface.co/docs/transformers
4. LangChain Documentation - https://python.langchain.com/
5. LlamaIndex Documentation - https://docs.llamaindex.ai/
6. PEFT Library - https://huggingface.co/docs/peft
7. vLLM Documentation - https://docs.vllm.ai/
8. ReAct Paper - Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models"
9. LoRA Paper - Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models"
10. RAG Survey - Zhao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey"

---

*报告生成时间: 2025年2月*
*版本: v1.0*
