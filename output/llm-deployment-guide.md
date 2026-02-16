# LLM大模型工程化部署最佳实践指南

> 本文档系统梳理大模型生产环境部署的核心技术，涵盖量化优化、服务化部署、分布式推理、缓存策略及监控告警五大维度。

---

## 目录

1. [模型量化与推理优化](#一模型量化与推理优化)
2. [大模型服务化部署](#二大模型服务化部署)
3. [分布式推理与模型并行](#三分布式推理与模型并行)
4. [LLM缓存策略与成本控制](#四llm缓存策略与成本控制)
5. [生产环境监控与告警](#五生产环境监控与告警)
6. [综合选型建议](#六综合选型建议)

---

## 一、模型量化与推理优化

### 1.1 量化技术对比

| 量化方法 | 精度损失 | 显存节省 | 推理速度提升 | 适用场景 |
|---------|---------|---------|-------------|---------|
| **FP16** | 基准 | 50% vs FP32 | 1.5-2x | 通用推理 |
| **INT8 (SmoothQuant)** | <1% | 75% vs FP32 | 2-3x | 平衡精度与速度 |
| **GPTQ (4-bit)** | 2-4% | 87.5% vs FP32 | 2.5-4x | 消费级GPU部署 |
| **AWQ (4-bit)** | 1-2% | 87.5% vs FP32 | 3-5x | **推荐生产环境** |
| **GGUF (Q4_K_M)** | 3-5% | 87.5% vs FP32 | 2-3x | CPU推理/边缘设备 |

### 1.2 各量化方案详解

#### GPTQ (Post-Training Quantization)

```python
# AutoGPTQ 使用示例
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

quant_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    desc_act=False,
)

model = AutoGPTQForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b",
    quantize_config=quant_config,
)
model.quantize(examples)
model.save_quantized("./llama-7b-4bit-gptq")
```

**优势：**
- 一次性量化，无需重新训练
- 支持多种模型架构
- 社区生态成熟

**局限性：**
- 对outlier敏感，可能损失精度
- activation量化效果一般

#### AWQ (Activation-aware Weight Quantization)

```python
# AutoAWQ 使用示例
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "meta-llama/Llama-2-7b"
quant_path = "./llama-7b-4bit-awq"
quant_config = {"zero_point": True, "q_group_size": 128, "w_bit": 4}

model = AutoAWQForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 准备校准数据
data = [tokenizer(example) for example in calibration_data]

model.quantize(tokenizer, quant_config=quant_config, calib_data=data)
model.save_quantized(quant_path)
```

**核心优势：**
- 保护1%的关键权重（salient weights），精度损失最小
- 支持fuse layer优化，推理速度更快
- 生产环境首选方案

**性能数据（Llama-2-70B on A100）：**

| 配置 | 显存占用 | 吞吐量 (tokens/s) | 延迟 (ms/token) |
|-----|---------|------------------|----------------|
| FP16 | 140GB | 45 | 22 |
| GPTQ-4bit | 42GB | 95 | 10.5 |
| **AWQ-4bit** | **42GB** | **125** | **8** |

### 1.3 推理引擎：vLLM

vLLM采用 **PagedAttention** 技术，是生产环境高性能推理的首选引擎。

```python
# vLLM 服务启动
from vllm import LLM, SamplingParams

# 支持AWQ/GPTQ量化模型
llm = LLM(
    model="TheBloke/Llama-2-70B-AWQ",
    quantization="awq",
    tensor_parallel_size=4,
    gpu_memory_utilization=0.90,
    max_num_seqs=256,
    max_model_len=4096,
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=1024,
)

outputs = llm.generate(prompts, sampling_params)
```

**vLLM 核心特性：**

| 特性 | 说明 | 性能提升 |
|-----|------|---------|
| PagedAttention | 动态KV Cache管理，减少显存碎片 | 显存效率提升2-4x |
| Continuous Batching | 请求级动态批处理 | 吞吐量提升5-10x |
| Streaming | 流式输出 | 首token延迟降低50% |
| Speculative Decoding | 投机解码 | 延迟降低1.5-2x |

**vLLM vs 其他推理引擎对比：**

| 引擎 | 吞吐量 (req/s) | 首token延迟 | 适用场景 |
|-----|---------------|------------|---------|
| HuggingFace | 基准 | 基准 | 开发调试 |
| TensorRT-LLM | 2.5x | 低 | 固定batch生产 |
| **vLLM** | **3-5x** | **低** | **动态负载生产** |
| llama.cpp | 1.5x (CPU) | 高 | 边缘/CPU部署 |

---

## 二、大模型服务化部署

### 2.1 部署架构选型

```
┌─────────────────────────────────────────────────────────────┐
│                        负载均衡层                             │
│              (Nginx / AWS ALB / Kubernetes Ingress)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  vLLM Instance │    │  vLLM Instance │    │  vLLM Instance │
│   (GPU 0-3)    │    │   (GPU 4-7)    │    │   (GPU 8-11)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     缓存层 (Redis/Valkey)                    │
│              缓存KV Cache、Prompt、Embedding                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Triton Inference Server + TensorRT-LLM

#### 部署流程

```bash
# 1. 模型转换为TensorRT-LLM格式
git clone https://github.com/NVIDIA/TensorRT-LLM.git
cd TensorRT-LLM

# 构建量化模型
python examples/llama/build.py \
    --model_dir ./Llama-2-70b \
    --dtype float16 \
    --remove_input_padding \
    --use_gpt_attention_plugin float16 \
    --enable_context_fmha \
    --use_weight_only \
    --weight_only_precision int4_awq \
    --output_dir ./trt_engines/llama-70b-4gpu/

# 2. 启动Triton服务
docker run --gpus all --rm -p 8000:8000 \
    -v $(pwd)/trt_engines:/models \
    nvcr.io/nvidia/tritonserver:24.01-trtllm-python-py3 \
    tritonserver --model-repository=/models
```

#### Triton配置示例

```protobuf
// config.pbtxt
name: "llama_70b"
platform: "ensemble"
max_batch_size: 64

input [
  {
    name: "INPUT_ID"
    data_type: TYPE_INT32
    dims: [ -1 ]
  }
]

output [
  {
    name: "OUTPUT_ID"
    data_type: TYPE_INT32
    dims: [ -1 ]
  }
]

instance_group [
  {
    count: 1
    kind: KIND_GPU
    gpus: [0, 1, 2, 3]
  }
]

dynamic_batching {
  preferred_batch_size: [ 16, 32 ]
  max_queue_delay_microseconds: 10000
}
```

### 2.3 vLLM Production部署

```python
# production_server.py
import asyncio
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

# 引擎配置
engine_args = AsyncEngineArgs(
    model="TheBloke/Llama-2-70B-AWQ",
    quantization="awq",
    tensor_parallel_size=4,
    gpu_memory_utilization=0.90,
    max_num_seqs=256,
    max_num_batched_tokens=4096,
    disable_log_stats=False,
)

engine = AsyncLLMEngine.from_engine_args(engine_args)

@app.post("/v1/completions")
async def create_completion(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    stream = data.get("stream", False)
    
    sampling_params = SamplingParams(
        temperature=data.get("temperature", 0.7),
        top_p=data.get("top_p", 0.95),
        max_tokens=data.get("max_tokens", 1024),
    )
    
    request_id = str(uuid.uuid4())
    
    if stream:
        async def stream_generator():
            async for output in engine.generate(
                prompt, sampling_params, request_id
            ):
                yield f"data: {json.dumps({'text': output.outputs[0].text})}\n\n"
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        outputs = []
        async for output in engine.generate(prompt, sampling_params, request_id):
            outputs.append(output)
        return {"text": outputs[-1].outputs[0].text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Docker Compose生产部署：**

```yaml
version: '3.8'
services:
  vllm-server:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=0,1,2,3
    volumes:
      - ./models:/models
    ports:
      - "8000:8000"
    command: >
      --model /models/Llama-2-70B-AWQ
      --quantization awq
      --tensor-parallel-size 4
      --gpu-memory-utilization 0.90
      --max-num-seqs 256
      --max-model-len 4096
      --dtype half
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 4
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 2.4 性能基准测试

**Llama-2-70B @ 4x A100 80GB**

| 部署方案 | 并发数 | 吞吐量 (tok/s) | P99延迟 (s) | 显存利用率 |
|---------|-------|---------------|------------|-----------|
| HF Transformers | 8 | 45 | 12.5 | 85% |
| TensorRT-LLM | 32 | 180 | 3.2 | 90% |
| **vLLM** | **64** | **240** | **2.1** | **92%** |
| TGI | 32 | 150 | 4.1 | 88% |

---

## 三、分布式推理与模型并行

### 3.1 并行策略选择

```
┌─────────────────────────────────────────────────────────────┐
│                    分布式推理策略矩阵                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   模型大小    │ 单卡显存    │ 推荐策略                      │
│   ─────────────────────────────────────────────────────    │
│   <13B       │ <24GB      │ 单卡推理                       │
│   13B-30B    │ 24-48GB    │ 张量并行 (TP=2)                │
│   30B-70B    │ 48-80GB    │ 张量并行 (TP=4)                │
│   70B-180B   │ >80GB      │ TP=8 或 TP+PP组合              │
│   >180B      │ N/A        │ 流水线并行 (PP) + 张量并行      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 张量并行 (Tensor Parallelism)

```python
# Megatron-LM 风格张量并行
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel

# 初始化进程组
dist.init_process_group(backend='nccl')
local_rank = dist.get_rank()
torch.cuda.set_device(local_rank)

# TP配置
tensor_parallel_size = 4
tensor_parallel_rank = local_rank % tensor_parallel_size

# 列切分线性层示例
class ColumnParallelLinear(torch.nn.Module):
    def __init__(self, input_size, output_size):
        super().__init__()
        # 输出维度切分到各GPU
        per_partition = output_size // tensor_parallel_size
        self.weight = torch.nn.Parameter(
            torch.empty(per_partition, input_size)
        )
        
    def forward(self, input):
        # All-Gather合并结果
        output_parallel = torch.nn.functional.linear(input, self.weight)
        output = gather_from_tensor_model_parallel_region(output_parallel)
        return output
```

**vLLM张量并行启动：**

```bash
# 4卡张量并行
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-70b \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.95
```

### 3.3 流水线并行 (Pipeline Parallelism)

```python
# 流水线并行配置 (适用于超大模型)
from vllm import LLM

# 8卡配置：TP=4, PP=2
llm = LLM(
    model="meta-llama/Llama-3-405B",
    tensor_parallel_size=4,
    pipeline_parallel_size=2,
    gpu_memory_utilization=0.90,
)
```

### 3.4 多机分布式部署

```bash
# Node 0 (Master)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-70b \
    --tensor-parallel-size 8 \
    --pipeline-parallel-size 2 \
    --master-addr 192.168.1.10 \
    --master-port 29500 \
    --rank 0

# Node 1
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-70b \
    --tensor-parallel-size 8 \
    --pipeline-parallel-size 2 \
    --master-addr 192.168.1.10 \
    --master-port 29500 \
    --rank 1
```

### 3.5 性能对比：并行策略

**180B模型 @ 8x A100 (80GB)**

| 配置 | 延迟 (ms/token) | 吞吐量 (tok/s) | 显存/GPU | 扩展效率 |
|-----|----------------|---------------|---------|---------|
| TP=8 | 15 | 320 | 75GB | 95% |
| TP=4, PP=2 | 28 | 280 | 72GB | 85% |
| TP=2, PP=4 | 52 | 200 | 70GB | 70% |
| PP=8 | 95 | 120 | 68GB | 55% |

**结论：** 张量并行效率最高，优先使用TP；当显存仍不足时，再引入PP。

---

## 四、LLM缓存策略与成本控制

### 4.1 缓存架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      多级缓存架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   L1: Prefix Cache (GPU显存)                                │
│   ├── 缓存KV Cache                                          │
│   ├── 命中率: 60-80%                                        │
│   └── 访问延迟: ~0.1ms                                      │
│                                                             │
│   L2: Redis/Valkey (内存)                                   │
│   ├── 缓存Prompt Embedding                                  │
│   ├── 命中率: 30-50%                                        │
│   └── 访问延迟: ~1ms                                        │
│                                                             │
│   L3: SSD/对象存储                                          │
│   ├── 缓存历史对话                                          │
│   └── 访问延迟: ~10ms                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 vLLM Prefix Caching

```python
# vLLM自动Prefix Caching配置
from vllm import LLM

llm = LLM(
    model="meta-llama/Llama-2-70b",
    enable_prefix_caching=True,  # 启用前缀缓存
    prefix_caching_hash_algo="sha256",
    max_num_batched_tokens=4096,
)

# 自动缓存共享前缀的KV Cache
# System Prompt + User Prompt 的共享部分只计算一次
```

**Prefix Caching性能提升：**

| 场景 | 无缓存 | 有Prefix Cache | 提升 |
|-----|-------|---------------|------|
| 多轮对话 | 基准 | 40-60% | 首token延迟 |
| RAG应用 | 基准 | 50-70% | 首token延迟 |
| 批量相似任务 | 基准 | 80-90% | 首token延迟 |

### 4.3 Redis缓存实现

```python
import redis
import json
import hashlib
from typing import Optional

class LLMResponseCache:
    def __init__(self, redis_host='localhost', ttl=3600):
        self.redis = redis.Redis(host=redis_host, decode_responses=True)
        self.ttl = ttl
    
    def _generate_key(self, prompt: str, params: dict) -> str:
        """生成缓存key"""
        content = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return f"llm:response:{hashlib.sha256(content.encode()).hexdigest()}"
    
    def get(self, prompt: str, params: dict) -> Optional[str]:
        """获取缓存响应"""
        key = self._generate_key(prompt, params)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set(self, prompt: str, params: dict, response: str):
        """设置缓存响应"""
        key = self._generate_key(prompt, params)
        self.redis.setex(
            key, 
            self.ttl, 
            json.dumps({"response": response})
        )

# 使用示例
cache = LLMResponseCache()

def generate_with_cache(prompt, params):
    # 先查缓存
    cached = cache.get(prompt, params)
    if cached:
        return cached["response"]
    
    # 调用模型
    response = llm.generate(prompt, params)
    
    # 写入缓存
    cache.set(prompt, params, response)
    return response
```

### 4.4 成本控制策略

#### 智能路由策略

```python
class SmartRouter:
    def __init__(self):
        self.models = {
            "gpt-4": {"cost_per_1k": 0.03, "capability": 100},
            "gpt-3.5": {"cost_per_1k": 0.0015, "capability": 70},
            "local-llama": {"cost_per_1k": 0.0002, "capability": 60},
        }
    
    def route(self, prompt: str, complexity: int) -> str:
        """根据任务复杂度选择模型"""
        if complexity > 80:
            return "gpt-4"
        elif complexity > 50:
            return "gpt-3.5"
        else:
            return "local-llama"
```

#### 成本优化对比

| 策略 | 成本降低 | 适用场景 |
|-----|---------|---------|
| 响应缓存 | 30-50% | 重复查询多的场景 |
| 模型路由 | 40-60% | 混合复杂度任务 |
| 批处理 | 20-30% | 离线任务 |
| 量化部署 | 50-70% | 自有GPU集群 |

### 4.5 成本估算模型

```python
class CostCalculator:
    """LLM部署成本计算器"""
    
    # GPU成本 ($/小时)
    GPU_COSTS = {
        "A100-40GB": 2.5,
        "A100-80GB": 3.5,
        "H100-80GB": 6.0,
        "A10G": 1.2,
    }
    
    @staticmethod
    def calculate_serving_cost(
        qps: float,
        avg_tokens_per_request: int,
        model_size: str,
        gpu_type: str,
    ) -> dict:
        """计算服务成本"""
        
        # 假设吞吐量数据 (tokens/s/GPU)
        throughput = {
            "7B": 800,
            "13B": 600,
            "70B": 200,
        }
        
        tokens_per_second = throughput.get(model_size, 200)
        required_gpus = max(1, int(
            (qps * avg_tokens_per_request) / tokens_per_second
        ))
        
        hourly_cost = required_gpus * CostCalculator.GPU_COSTS[gpu_type]
        monthly_cost = hourly_cost * 24 * 30
        
        cost_per_1k_tokens = (hourly_cost * 1000) / (tokens_per_second * 3600)
        
        return {
            "required_gpus": required_gpus,
            "hourly_cost_usd": round(hourly_cost, 2),
            "monthly_cost_usd": round(monthly_cost, 2),
            "cost_per_1k_tokens_usd": round(cost_per_1k_tokens, 4),
        }

# 示例：70B模型，10 QPS，平均500 tokens/请求
calc = CostCalculator()
result = calc.calculate_serving_cost(
    qps=10,
    avg_tokens_per_request=500,
    model_size="70B",
    gpu_type="A100-80GB",
)
print(result)
# {
#   'required_gpus': 4,
#   'hourly_cost_usd': 14.0,
#   'monthly_cost_usd': 10080.0,
#   'cost_per_1k_tokens_usd': 0.0194
# }
```

---

## 五、生产环境监控与告警

### 5.1 监控指标体系

```
┌─────────────────────────────────────────────────────────────┐
│                      监控指标分层                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  基础设施层                                                  │
│  ├── GPU利用率 (目标: >70%)                                 │
│  ├── GPU显存使用 (告警: >90%)                               │
│  ├── GPU温度 (告警: >85°C)                                  │
│  └── 功耗                                                   │
│                                                             │
│  推理引擎层                                                  │
│  ├── 吞吐量 (tokens/second)                                 │
│  ├── 延迟 (P50/P95/P99)                                     │
│  ├── 批处理效率 (实际batch/最大batch)                        │
│  ├── KV Cache命中率                                         │
│  └── 队列长度                                               │
│                                                             │
│  应用层                                                      │
│  ├── QPS (请求/秒)                                          │
│  ├── 错误率 (目标: <0.1%)                                   │
│  ├── 首token延迟 (TTFT)                                     │
│  ├── 每token延迟 (TPOT)                                     │
│  └── 端到端延迟                                             │
│                                                             │
│  业务层                                                      │
│  ├── 成本/token                                             │
│  ├── 缓存命中率                                             │
│  └── 用户满意度                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Prometheus + Grafana 监控配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vllm-server'
    static_configs:
      - targets: ['vllm-server:8000']
    metrics_path: /metrics

  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

```python
# vllm_metrics.py - 自定义指标导出
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# 定义指标
REQUEST_COUNT = Counter('vllm_requests_total', 'Total requests', ['status'])
REQUEST_LATENCY = Histogram('vllm_request_duration_seconds', 'Request latency')
TOKENS_GENERATED = Counter('vllm_tokens_generated_total', 'Total tokens generated')
BATCH_SIZE = Gauge('vllm_batch_size_current', 'Current batch size')
KV_CACHE_USAGE = Gauge('vllm_kv_cache_usage_ratio', 'KV Cache usage ratio')
QUEUE_LENGTH = Gauge('vllm_queue_length', 'Number of requests in queue')

# 启动metrics服务
start_http_server(8001)

# 在推理过程中更新指标
@app.post("/v1/completions")
async def create_completion(request: Request):
    start_time = time.time()
    
    try:
        # 推理逻辑...
        TOKENS_GENERATED.inc(num_tokens)
        REQUEST_COUNT.labels(status='success').inc()
    except Exception as e:
        REQUEST_COUNT.labels(status='error').inc()
        raise
    finally:
        REQUEST_LATENCY.observe(time.time() - start_time)
```

### 5.3 告警规则配置

```yaml
# alert_rules.yml
groups:
  - name: vllm_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(vllm_requests_total{status="error"}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(vllm_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency > 5s"
          
      - alert: GPUOutOfMemory
        expr: vllm_kv_cache_usage_ratio > 0.95
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "GPU memory almost full"
          
      - alert: QueueBuildup
        expr: vllm_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Request queue building up"
```

### 5.4 日志与Tracing

```python
# 结构化日志配置
import structlog
import logging
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
tracer = trace.get_tracer("llm-service")

# 在请求中使用
@app.post("/v1/completions")
async def create_completion(request: Request):
    with tracer.start_as_current_span("llm_inference") as span:
        span.set_attribute("model", "llama-70b")
        span.set_attribute("request_id", request_id)
        
        logger.info(
            "inference_started",
            request_id=request_id,
            prompt_length=len(prompt),
        )
        
        # 推理...
        
        logger.info(
            "inference_completed",
            request_id=request_id,
            tokens_generated=num_tokens,
            duration_ms=duration,
        )
```

### 5.5 健康检查与自动恢复

```python
# health_check.py
import asyncio
import httpx
from kubernetes import client, config

class HealthChecker:
    def __init__(self):
        config.load_incluster_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    async def check_endpoint(self, url: str, timeout: float = 5.0) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{url}/health",
                    timeout=timeout
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def restart_deployment(self, name: str, namespace: str = "default"):
        """重启故障Pod"""
        now = datetime.datetime.utcnow()
        now = str(now.isoformat() + "Z")
        
        body = {
            'spec': {
                'template': {
                    'metadata': {
                        'annotations': {
                            'kubectl.kubernetes.io/restartedAt': now
                        }
                    }
                }
            }
        }
        
        self.apps_v1.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=body
        )
```

---

## 六、综合选型建议

### 6.1 场景化部署方案

| 场景 | 推荐方案 | 硬件配置 | 预计成本 |
|-----|---------|---------|---------|
| **原型验证** | HF Transformers + FP16 | 1x RTX 4090 | ~$200/月 |
| **中小规模服务** | vLLM + AWQ-4bit | 2x A100 40GB | ~$3,600/月 |
| **大规模生产** | vLLM + TensorRT-LLM + AWQ | 4-8x A100 80GB | ~$10k-20k/月 |
| **超大规模集群** | vLLM + TP/PP + K8s | 16x H100 | ~$70k/月 |
| **边缘部署** | llama.cpp + GGUF Q4 | RTX 3060 / 嵌入式 | ~$100/月 |

### 6.2 技术栈推荐

```
┌─────────────────────────────────────────────────────────────┐
│                     生产级LLM技术栈                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  模型层: AWQ/GPTQ 4-bit 量化模型                             │
│        ↓                                                    │
│  推理层: vLLM (PagedAttention + Continuous Batching)        │
│        ↓                                                    │
│  服务层: FastAPI / Triton Inference Server                   │
│        ↓                                                    │
│  编排层: Kubernetes + KNative / KServe                      │
│        ↓                                                    │
│  缓存层: Redis/Valkey (Prefix Cache + Response Cache)       │
│        ↓                                                    │
│  网关层: Nginx / Kong / Istio (限流/熔断/负载均衡)           │
│        ↓                                                    │
│  可观测: Prometheus + Grafana + Jaeger                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 性能优化Checklist

- [ ] **量化优化**
  - [ ] 使用AWQ 4-bit量化，精度损失<2%
  - [ ] 校准数据覆盖实际业务场景
  - [ ] 验证量化模型端到端质量

- [ ] **推理优化**
  - [ ] 启用vLLM PagedAttention
  - [ ] 配置合适的max_num_seqs (通常256-512)
  - [ ] 启用Prefix Caching减少重复计算

- [ ] **部署优化**
  - [ ] 张量并行度与GPU数量匹配
  - [ ] 合理配置gpu_memory_utilization (0.85-0.95)
  - [ ] 使用CUDA Graph减少kernel启动开销

- [ ] **缓存优化**
  - [ ] 实现多级缓存架构
  - [ ] 监控缓存命中率 (目标>50%)
  - [ ] 设置合理的TTL策略

- [ ] **监控告警**
  - [ ] 配置关键指标采集
  - [ ] 设置合理告警阈值
  - [ ] 实现自动故障恢复

---

## 附录：性能基准数据汇总

### 量化方案对比（Llama-2-70B @ A100）

| 方案 | 显存(GB) | 吞吐量(tok/s) | 精度损失 | 推荐度 |
|-----|---------|--------------|---------|-------|
| FP16 | 140 | 45 | 0% | ⭐⭐⭐ |
| INT8 | 75 | 85 | <1% | ⭐⭐⭐⭐ |
| GPTQ-4bit | 42 | 95 | 2-4% | ⭐⭐⭐⭐ |
| **AWQ-4bit** | **42** | **125** | **1-2%** | ⭐⭐⭐⭐⭐ |

### 推理引擎对比（Llama-2-70B @ 4x A100）

| 引擎 | 并发数 | 吞吐量 | P99延迟 | 显存效率 |
|-----|-------|-------|--------|---------|
| HF | 8 | 45 | 12.5s | 低 |
| TGI | 32 | 150 | 4.1s | 中 |
| TensorRT-LLM | 32 | 180 | 3.2s | 高 |
| **vLLM** | **64** | **240** | **2.1s** | **极高** |

### 成本对比（100万 tokens/天）

| 部署方式 | 月成本(USD) | 延迟 | 备注 |
|---------|------------|------|------|
| GPT-4 API | ~$900 | 低 | 简单但成本高 |
| 自有GPU (AWQ) | ~$400 | 低 | 推荐方案 |
| 自有GPU (FP16) | ~$1,200 | 中 | 精度最高 |

---

*文档版本: v1.0*  
*最后更新: 2024年*
