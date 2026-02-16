"""
AI大模型API集成与优化 - 完整代码库
可直接用于生产环境的API优化工具集
"""

import asyncio
import hashlib
import json
import random
import re
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple, TypeVar

T = TypeVar('T')

# =============================================================================
# 1. 性能基准测试模块
# =============================================================================

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    model: str
    latency_first_token: float
    latency_total: float
    tokens_per_second: float
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)


class ModelBenchmark:
    """大模型API性能基准测试器"""
    
    TEST_PROMPTS = {
        'short': '解释什么是机器学习',
        'medium': '详细说明深度学习在计算机视觉中的应用，包括CNN、RNN和Transformer架构',
        'long_code': '''请实现一个高效的LRU缓存类，要求：
1. 线程安全
2. O(1)时间复杂度的get和put操作
3. 支持过期时间设置
4. 提供使用示例''',
        'chinese': '请分析中国古代诗词中月亮意象的象征意义，并举例说明',
        'reasoning': '如果一个池塘里的莲花每天翻倍，第30天铺满池塘，那么什么时候铺满半个池塘？'
    }
    
    def __init__(self, api_clients: Dict[str, Any]):
        """
        Args:
            api_clients: 模型名称到API客户端的映射
        """
        self.clients = api_clients
        self.results: List[BenchmarkResult] = []
    
    async def run_benchmark(
        self, 
        models: List[str] = None,
        prompts: Dict[str, str] = None,
        iterations: int = 3
    ) -> List[BenchmarkResult]:
        """运行基准测试"""
        
        models = models or list(self.clients.keys())
        prompts = prompts or self.TEST_PROMPTS
        
        for model_name in models:
            if model_name not in self.clients:
                print(f"跳过 {model_name}: 未配置客户端")
                continue
            
            client = self.clients[model_name]
            
            for prompt_name, prompt in prompts.items():
                print(f"测试 {model_name} - {prompt_name}...")
                
                try:
                    result = await self._benchmark_single(
                        model_name, client, prompt, iterations
                    )
                    self.results.append(result)
                except Exception as e:
                    print(f"  错误: {e}")
        
        return self.results
    
    async def _benchmark_single(
        self, 
        model_name: str, 
        client: Any,
        prompt: str,
        iterations: int
    ) -> BenchmarkResult:
        """单模型单提示词测试"""
        
        latencies = []
        first_token_times = []
        token_counts = []
        
        for _ in range(iterations):
            start = time.time()
            first_token_time = None
            total_tokens = 0
            full_response = ""
            
            # 流式测试
            if hasattr(client, 'stream_generate'):
                async for chunk in client.stream_generate(prompt):
                    if first_token_time is None:
                        first_token_time = time.time() - start
                    content = chunk.get('content', '')
                    full_response += content
                    total_tokens += chunk.get('tokens', len(content) // 4)
            else:
                response = await client.generate(prompt)
                full_response = response
                first_token_time = time.time() - start
                total_tokens = len(full_response) // 4
            
            total_time = time.time() - start
            latencies.append(total_time)
            first_token_times.append(first_token_time or total_time)
            token_counts.append(total_tokens)
        
        # 计算统计值
        avg_latency = statistics.mean(latencies)
        avg_first = statistics.mean(first_token_times)
        avg_tokens = statistics.mean(token_counts)
        
        # 估算成本
        cost = self._estimate_cost(model_name, len(prompt) // 4, int(avg_tokens))
        
        return BenchmarkResult(
            model=model_name,
            latency_first_token=avg_first,
            latency_total=avg_latency,
            tokens_per_second=avg_tokens / avg_latency if avg_latency > 0 else 0,
            input_tokens=len(prompt) // 4,
            output_tokens=int(avg_tokens),
            cost=cost
        )
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """估算成本"""
        pricing = {
            'gpt-4o': (0.005, 0.015),
            'gpt-4o-mini': (0.00015, 0.0006),
            'claude-3-5-sonnet': (0.003, 0.015),
            'kimi': (0.0008, 0.0008),
        }
        
        input_price, output_price = pricing.get(model, (0.01, 0.03))
        return (input_tokens / 1000 * input_price + 
                output_tokens / 1000 * output_price)
    
    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.results:
            return "暂无测试结果"
        
        lines = ["\n" + "="*80, "性能基准测试报告", "="*80]
        
        # 按模型分组
        by_model = defaultdict(list)
        for r in self.results:
            by_model[r.model].append(r)
        
        for model, results in by_model.items():
            lines.append(f"\n【{model}】")
            lines.append(f"  平均首token延迟: {statistics.mean([r.latency_first_token for r in results]):.3f}s")
            lines.append(f"  平均总延迟: {statistics.mean([r.latency_total for r in results]):.3f}s")
            lines.append(f"  平均生成速度: {statistics.mean([r.tokens_per_second for r in results]):.1f} tokens/s")
            lines.append(f"  平均成本: ${statistics.mean([r.cost for r in results]):.4f}")
        
        return '\n'.join(lines)


# =============================================================================
# 2. 批处理与流式优化
# =============================================================================

@dataclass
class BatchConfig:
    """批处理配置"""
    max_batch_size: int = 10
    max_wait_time: float = 0.1
    max_tokens_per_batch: int = 8000
    enable_priority: bool = True


class BatchProcessor:
    """智能批处理器"""
    
    def __init__(self, api_client, config: Optional[BatchConfig] = None):
        self.client = api_client
        self.config = config or BatchConfig()
        self.request_queue: List[Dict] = []
        self._lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    async def submit(
        self, 
        request_id: str, 
        prompt: str, 
        priority: int = 1,
        **kwargs
    ) -> str:
        """提交请求到批处理队列"""
        
        if self._shutdown:
            raise RuntimeError("Processor is shutting down")
        
        future = asyncio.get_event_loop().create_future()
        
        async with self._lock:
            self.request_queue.append({
                'id': request_id,
                'prompt': prompt,
                'priority': priority,
                'future': future,
                'timestamp': time.time(),
                'kwargs': kwargs
            })
            
            if self.config.enable_priority:
                self.request_queue.sort(
                    key=lambda x: (-x['priority'], x['timestamp'])
                )
        
        # 启动批处理
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self):
        """处理批量请求"""
        await asyncio.sleep(self.config.max_wait_time)
        
        async with self._lock:
            if not self.request_queue:
                return
            
            batch = self.request_queue[:self.config.max_batch_size]
            self.request_queue = self.request_queue[self.config.max_batch_size:]
        
        try:
            # 并行处理
            tasks = [
                self._execute_single(item) 
                for item in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 分发结果
            for item, result in zip(batch, results):
                if not item['future'].done():
                    if isinstance(result, Exception):
                        item['future'].set_exception(result)
                    else:
                        item['future'].set_result(result)
                        
        except Exception as e:
            # 批量失败时逐个重试
            for item in batch:
                try:
                    result = await self._execute_single(item)
                    if not item['future'].done():
                        item['future'].set_result(result)
                except Exception as e2:
                    if not item['future'].done():
                        item['future'].set_exception(e2)
    
    async def _execute_single(self, item: Dict) -> str:
        """执行单个请求"""
        return await self.client.generate(
            item['prompt'], 
            **item.get('kwargs', {})
        )
    
    async def shutdown(self):
        """优雅关闭"""
        self._shutdown = True
        
        # 等待队列处理完成
        while self.request_queue:
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_batch())
            await asyncio.sleep(0.1)
        
        if self._batch_task:
            await self._batch_task


class StreamingOptimizer:
    """流式输出优化器"""
    
    def __init__(
        self, 
        min_chunk_size: int = 10,
        max_chunk_delay: float = 0.05,
        natural_break_chars: str = '。，.!\n'
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_delay = max_chunk_delay
        self.natural_break_chars = natural_break_chars
        self.buffer = ""
        self.last_emit_time = 0
    
    async def optimize_stream(
        self,
        raw_stream: AsyncIterator[str],
        on_token: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """优化流式输出"""
        
        self.buffer = ""
        self.last_emit_time = time.time()
        
        async for chunk in raw_stream:
            self.buffer += chunk
            current_time = time.time()
            
            should_emit = (
                len(self.buffer) >= self.min_chunk_size or
                (current_time - self.last_emit_time) >= self.max_chunk_delay or
                any(c in self.buffer for c in self.natural_break_chars)
            )
            
            if should_emit:
                if on_token:
                    on_token(self.buffer)
                yield self.buffer
                self.buffer = ""
                self.last_emit_time = current_time
        
        # 刷新剩余内容
        if self.buffer:
            if on_token:
                on_token(self.buffer)
            yield self.buffer


# =============================================================================
# 3. 错误重试与熔断机制
# =============================================================================

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_errors: Tuple = (TimeoutError, ConnectionError, Exception)


@dataclass
class CircuitConfig:
    """熔断配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 3


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, name: str = "default", config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """执行带熔断保护的调用"""
        
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    print(f"[{self.name}] 熔断器进入半开状态")
                else:
                    raise CircuitBreakerOpen(f"Circuit '{self.name}' is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    print(f"[{self.name}] 熔断器关闭")
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                print(f"[{self.name}] 熔断器打开(半开状态失败)")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"[{self.name}] 熔断器打开(失败次数: {self.failure_count})")
    
    def get_state(self) -> str:
        return self.state.value


class CircuitBreakerOpen(Exception):
    pass


class RetryWithBackoff:
    """指数退避重试"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """执行带重试的调用"""
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not isinstance(e, self.config.retryable_errors):
                    raise
                
                if attempt == self.config.max_retries:
                    break
                
                # 计算退避时间
                delay = min(
                    self.config.base_delay * (self.config.exponential_base ** attempt),
                    self.config.max_delay
                )
                delay *= (0.5 + random.random())  # 添加抖动
                
                print(f"重试 {attempt + 1}/{self.config.max_retries}, 等待 {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        raise last_exception


# =============================================================================
# 4. 提示词工程工具
# =============================================================================

class TaskType(Enum):
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    ANALYSIS = "analysis"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    REASONING = "reasoning"
    CREATIVE = "creative"


class PromptLibrary:
    """提示词模板库"""
    
    TEMPLATES = {
        # 摘要类
        'summary_concise': {
            'system': '你是专业的文本摘要专家。提供简洁准确的摘要。',
            'template': '''请对以下文本进行摘要：

【原文】
{text}

【要求】
- 摘要控制在 {max_words} 字以内
- 保留核心观点和关键数据
- 语言简洁明了

【摘要】'''
        },
        
        'summary_bullet': {
            'system': '你是信息提炼专家。',
            'template': '''请提炼以下文本的关键信息：

{text}

请以要点形式输出（最多{bullet_count}条）：
- '''
        },
        
        # 代码类
        'code_generate': {
            'system': '你是资深软件工程师，编写高质量、可维护的代码。',
            'template': '''请根据以下需求编写代码：

【需求】
{requirement}

【技术栈】
- 语言: {language}
- 框架: {framework}

【要求】
1. 包含必要的注释
2. 处理边界情况
3. 遵循最佳实践
4. 提供使用示例

【代码】
```{language}
'''
        },
        
        'code_review': {
            'system': '你是代码审查专家。',
            'template': '''请审查以下代码：

```{language}
{code}
```

【审查维度】
1. 代码质量和可读性
2. 潜在Bug和安全问题
3. 性能优化建议
4. 最佳实践遵循

【审查结果】
评分: _/10
主要问题:
改进建议:'''
        },
        
        # 分析类
        'sentiment_analysis': {
            'system': '你是情感分析专家。',
            'template': '''请分析以下文本的情感倾向：

【文本】
{text}

请输出JSON格式：
{{
    "sentiment": "positive/negative/neutral",
    "confidence": 0.0-1.0,
    "keywords": ["..."],
    "explanation": "..."
}}'''
        },
        
        'data_analysis': {
            'system': '你是数据分析师。',
            'template': '''请分析以下数据：

【数据】
{data}

【分析目标】
{goal}

请提供：
1. 数据概览
2. 关键发现
3. 趋势分析
4. 建议'''
        },
        
        # 推理类
        'chain_of_thought': {
            'system': '你是逻辑推理专家，擅长逐步分析问题。',
            'template': '''请逐步思考并回答：

【问题】
{question}

【思考过程】
1. 理解问题：...
2. 分析关键信息：...
3. 推理过程：...
4. 验证：...

【答案】'''
        },
        
        # 创意类
        'creative_writing': {
            'system': '你是创意写作专家。',
            'template': '''请创作以下内容：

【类型】{genre}
【主题】{theme}
【风格】{style}
【字数】约{word_count}字

【要求】
{requirements}

【创作】'''
        }
    }
    
    @classmethod
    def get(cls, name: str, **kwargs) -> Dict[str, str]:
        """获取提示词模板"""
        template = cls.TEMPLATES.get(name)
        if not template:
            raise ValueError(f"Unknown template: {name}")
        
        return {
            'system': template.get('system', ''),
            'prompt': template['template'].format(**kwargs)
        }
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """列出所有模板"""
        return list(cls.TEMPLATES.keys())


class PromptOptimizer:
    """提示词优化器"""
    
    @staticmethod
    def compress(prompt: str, max_chars: int = 2000) -> str:
        """压缩提示词"""
        if len(prompt) <= max_chars:
            return prompt
        
        # 移除多余空白
        prompt = re.sub(r'\s+', ' ', prompt)
        
        # 简化标记
        prompt = prompt.replace('```python', '```py')
        
        # 如果仍超长，保留核心部分
        if len(prompt) > max_chars:
            lines = prompt.split('\n')
            core_lines = [
                l for l in lines 
                if any(k in l.lower() for k in ['任务', '要求', 'input:', 'output:'])
            ]
            prompt = '\n'.join(core_lines[:10])
        
        return prompt[:max_chars]
    
    @staticmethod
    def add_few_shot(base_prompt: str, examples: List[Dict], max_examples: int = 3) -> str:
        """添加Few-shot示例"""
        if not examples:
            return base_prompt
        
        few_shot = '\n\n【示例】\n'
        for i, ex in enumerate(examples[:max_examples], 1):
            few_shot += f'\n示例{i}:\n'
            few_shot += f'输入: {ex.get("input", "")}\n'
            few_shot += f'输出: {ex.get("output", "")}\n'
        
        few_shot += '\n请按照上述格式回答。\n'
        return base_prompt + few_shot


# =============================================================================
# 5. 成本优化工具
# =============================================================================

class TokenOptimizer:
    """Token优化器"""
    
    @staticmethod
    def estimate(text: str, language: str = 'mixed') -> int:
        """估算token数量"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        
        # 中文约2 tokens/字，英文约0.25 tokens/字符
        return chinese_chars * 2 + int(other_chars * 0.25)
    
    @staticmethod
    def truncate_history(
        messages: List[Dict],
        max_tokens: int = 4000,
        keep_system: bool = True
    ) -> List[Dict]:
        """智能截断对话历史"""
        
        if not messages:
            return messages
        
        result = []
        current_tokens = 0
        
        # 先添加系统消息
        if keep_system:
            system_msgs = [m for m in messages if m.get('role') == 'system']
            for m in system_msgs:
                tokens = TokenOptimizer.estimate(m.get('content', ''))
                if current_tokens + tokens <= max_tokens * 0.3:  # 系统消息最多30%
                    result.append(m)
                    current_tokens += tokens
        
        # 从后往前添加用户和助手消息
        other_msgs = [m for m in messages if m.get('role') != 'system']
        for m in reversed(other_msgs):
            tokens = TokenOptimizer.estimate(m.get('content', ''))
            if current_tokens + tokens <= max_tokens:
                result.insert(len(result), m)  # 保持原有顺序
                current_tokens += tokens
            else:
                break
        
        return result


class SmartCache:
    """智能缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
    
    def _key(self, prompt: str, model: str, params: Dict) -> str:
        """生成缓存键"""
        data = f"{prompt}:{model}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, params: Dict = None) -> Tuple[bool, Any]:
        """获取缓存"""
        key = self._key(prompt, model, params or {})
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['time'] < self.ttl:
                self.access_count[key] += 1
                return True, entry['value']
            else:
                del self.cache[key]
                del self.access_count[key]
        
        return False, None
    
    def set(self, prompt: str, model: str, value: Any, params: Dict = None):
        """设置缓存"""
        # LRU清理
        if len(self.cache) >= self.max_size:
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        key = self._key(prompt, model, params or {})
        self.cache[key] = {'value': value, 'time': time.time()}
        self.access_count[key] = 1
    
    def stats(self) -> Dict:
        """获取统计信息"""
        hits = sum(self.access_count.values())
        return {
            'size': len(self.cache),
            'hits': hits,
            'hit_rate': hits / max(len(self.access_count), 1)
        }


class CostTracker:
    """成本追踪器"""
    
    PRICING = {
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'claude-3-5-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-5-haiku': {'input': 0.00025, 'output': 0.00125},
        'kimi': {'input': 0.0008, 'output': 0.0008},
    }
    
    def __init__(self):
        self.usage: List[Dict] = []
    
    def log(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str = ''
    ) -> float:
        """记录使用"""
        pricing = self.PRICING.get(model, {'input': 0.01, 'output': 0.03})
        
        cost = (
            input_tokens / 1000 * pricing['input'] +
            output_tokens / 1000 * pricing['output']
        )
        
        self.usage.append({
            'time': datetime.now(),
            'model': model,
            'input': input_tokens,
            'output': output_tokens,
            'cost': cost,
            'task': task_type
        })
        
        return cost
    
    def summary(self) -> Dict:
        """使用摘要"""
        by_model = defaultdict(lambda: {'tokens': 0, 'cost': 0, 'calls': 0})
        
        for u in self.usage:
            m = u['model']
            by_model[m]['tokens'] += u['input'] + u['output']
            by_model[m]['cost'] += u['cost']
            by_model[m]['calls'] += 1
        
        return {
            'total_cost': sum(u['cost'] for u in self.usage),
            'total_tokens': sum(u['input'] + u['output'] for u in self.usage),
            'total_calls': len(self.usage),
            'by_model': dict(by_model)
        }


# =============================================================================
# 6. 多模型路由
# =============================================================================

@dataclass
class ModelSpec:
    """模型规格"""
    name: str
    context_length: int
    cost_input: float
    cost_output: float
    strengths: List[str]
    quality_score: float


class ModelRouter:
    """智能模型路由器"""
    
    MODELS = {
        'gpt-4o-mini': ModelSpec(
            name='gpt-4o-mini',
            context_length=128000,
            cost_input=0.00015,
            cost_output=0.0006,
            strengths=['speed', 'cost'],
            quality_score=7.5
        ),
        'gpt-4o': ModelSpec(
            name='gpt-4o',
            context_length=128000,
            cost_input=0.005,
            cost_output=0.015,
            strengths=['vision', 'code', 'reasoning'],
            quality_score=9.0
        ),
        'claude-3-5-sonnet': ModelSpec(
            name='claude-3-5-sonnet',
            context_length=200000,
            cost_input=0.003,
            cost_output=0.015,
            strengths=['long_context', 'creative', 'analysis'],
            quality_score=9.0
        ),
        'kimi': ModelSpec(
            name='kimi',
            context_length=200000,
            cost_input=0.0008,
            cost_output=0.0008,
            strengths=['chinese', 'long_context', 'cost'],
            quality_score=8.0
        ),
    }
    
    def __init__(self, clients: Dict[str, Any], budget_weight: float = 0.3):
        """
        Args:
            clients: 模型名称到客户端的映射
            budget_weight: 成本权重 (0-1)，越高越重视成本
        """
        self.clients = clients
        self.budget_weight = budget_weight
        self.circuit_breakers = {
            name: CircuitBreaker(name) 
            for name in clients.keys()
        }
        self.cost_tracker = CostTracker()
    
    def select_model(self, prompt: str, task_type: str = '') -> str:
        """选择最合适的模型"""
        
        prompt_len = len(prompt)
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in prompt)
        
        candidates = []
        
        for name, spec in self.MODELS.items():
            if name not in self.clients:
                continue
            if prompt_len > spec.context_length:
                continue
            
            score = spec.quality_score
            
            # 中文内容加分
            if has_chinese and 'chinese' in spec.strengths:
                score *= 1.2
            
            # 成本调整
            avg_cost = (spec.cost_input + spec.cost_output) / 2
            cost_factor = 1 - (avg_cost / 0.01) * self.budget_weight
            score *= max(0.5, cost_factor)
            
            candidates.append((name, score, spec))
        
        if not candidates:
            return list(self.clients.keys())[0]
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        fallback_models: List[str] = None,
        **kwargs
    ) -> Dict:
        """带熔断和降级的生成"""
        
        if model is None:
            model = self.select_model(prompt)
        
        fallback_models = fallback_models or ['gpt-4o-mini']
        models_to_try = [model] + [m for m in fallback_models if m != model]
        
        for m in models_to_try:
            if m not in self.clients:
                continue
            
            cb = self.circuit_breakers.get(m)
            client = self.clients[m]
            
            try:
                start = time.time()
                
                if cb:
                    response = await cb.call(client.generate, prompt, **kwargs)
                else:
                    response = await client.generate(prompt, **kwargs)
                
                latency = time.time() - start
                
                # 记录成本
                input_tokens = TokenOptimizer.estimate(prompt)
                output_tokens = TokenOptimizer.estimate(response)
                cost = self.cost_tracker.log(m, input_tokens, output_tokens)
                
                return {
                    'success': True,
                    'model': m,
                    'response': response,
                    'latency': latency,
                    'cost': cost
                }
                
            except CircuitBreakerOpen:
                print(f"模型 {m} 熔断器打开，跳过")
                continue
            except Exception as e:
                print(f"模型 {m} 调用失败: {e}")
                continue
        
        return {
            'success': False,
            'error': 'All models failed'
        }
    
    async def ensemble(
        self,
        prompt: str,
        models: List[str] = None,
        strategy: str = 'vote'
    ) -> Dict:
        """多模型集成"""
        
        models = models or list(self.clients.keys())[:3]
        
        # 并行调用
        tasks = [
            self._safe_generate(m, prompt) 
            for m in models if m in self.clients
        ]
        results = await asyncio.gather(*tasks)
        
        valid = [(m, r) for m, r in zip(models, results) if r is not None]
        
        if not valid:
            return {'success': False, 'error': 'All models failed'}
        
        if strategy == 'vote':
            # 选择最常见的响应
            from collections import Counter
            responses = [r for _, r in valid]
            most_common = Counter(responses).most_common(1)[0][0]
            
        elif strategy == 'best':
            # 使用质量最高的模型
            best_model = max(valid, key=lambda x: self.MODELS.get(x[0], ModelSpec('',0,0,0,[],0)).quality_score)
            most_common = best_model[1]
        
        else:
            most_common = valid[0][1]
        
        return {
            'success': True,
            'response': most_common,
            'all_responses': dict(valid),
            'models_used': [m for m, _ in valid]
        }
    
    async def _safe_generate(self, model: str, prompt: str) -> Optional[str]:
        """安全生成"""
        try:
            client = self.clients[model]
            cb = self.circuit_breakers.get(model)
            
            if cb:
                return await cb.call(client.generate, prompt)
            return await client.generate(prompt)
        except Exception:
            return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'cost': self.cost_tracker.summary(),
            'circuits': {n: cb.get_state() for n, cb in self.circuit_breakers.items()}
        }


# =============================================================================
# 使用示例
# =============================================================================

async def demo():
    """演示用法"""
    
    # 1. 批处理示例
    print("=== 批处理示例 ===")
    
    class MockClient:
        async def generate(self, prompt: str) -> str:
            await asyncio.sleep(0.1)
            return f"Response to: {prompt[:20]}..."
    
    client = MockClient()
    processor = BatchProcessor(client, BatchConfig(max_batch_size=5))
    
    # 提交多个请求
    tasks = [
        processor.submit(f"req_{i}", f"Question {i}")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    print(f"批处理结果: {len(results)} 个响应")
    
    await processor.shutdown()
    
    # 2. 提示词模板示例
    print("\n=== 提示词模板示例 ===")
    
    prompt_data = PromptLibrary.get(
        'summary_concise',
        text='这是一段需要摘要的长文本...',
        max_words=100
    )
    print(f"系统提示: {prompt_data['system'][:50]}...")
    print(f"用户提示: {prompt_data['prompt'][:100]}...")
    
    # 3. 成本追踪示例
    print("\n=== 成本追踪示例 ===")
    
    tracker = CostTracker()
    tracker.log('gpt-4o', 1000, 500, 'summary')
    tracker.log('gpt-4o-mini', 1000, 500, 'simple')
    tracker.log('claude-3-5-sonnet', 2000, 1000, 'analysis')
    
    summary = tracker.summary()
    print(f"总成本: ${summary['total_cost']:.4f}")
    print(f"总Token: {summary['total_tokens']}")
    print(f"调用次数: {summary['total_calls']}")
    
    # 4. 模型路由示例
    print("\n=== 模型路由示例 ===")
    
    clients = {
        'gpt-4o-mini': MockClient(),
        'gpt-4o': MockClient(),
        'kimi': MockClient(),
    }
    
    router = ModelRouter(clients, budget_weight=0.5)
    
    # 测试不同内容的路由选择
    test_prompts = [
        "解释什么是机器学习",  # 中文 -> Kimi
        "Write a Python function",  # 代码 -> GPT-4o
        "Summarize this quickly",  # 简单任务 -> GPT-4o-mini
    ]
    
    for prompt in test_prompts:
        selected = router.select_model(prompt)
        print(f"提示: {prompt[:30]}... -> 选择模型: {selected}")
    
    print("\n演示完成!")


if __name__ == '__main__':
    asyncio.run(demo())
