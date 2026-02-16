# 云端API集成代码示例

## 1. 统一模型客户端 (TypeScript)

```typescript
// src/clients/UnifiedAIClient.ts

import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
}

interface CompletionRequest {
  messages: Message[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
  tools?: any[];
  stream?: boolean;
}

interface CompletionResponse {
  content: string;
  usage: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  toolCalls?: any[];
  model: string;
}

export class UnifiedAIClient {
  private claudeClient: Anthropic;
  private grokClient: OpenAI;
  private config: {
    defaultModel: string;
    fallbackEnabled: boolean;
    timeout: number;
  };

  constructor(config: {
    claudeApiKey: string;
    grokApiKey: string;
    defaultModel?: string;
    fallbackEnabled?: boolean;
    timeout?: number;
  }) {
    this.claudeClient = new Anthropic({
      apiKey: config.claudeApiKey,
    });

    this.grokClient = new OpenAI({
      apiKey: config.grokApiKey,
      baseURL: 'https://api.x.ai/v1',
    });

    this.config = {
      defaultModel: config.defaultModel || 'claude-3-5-sonnet-20241022',
      fallbackEnabled: config.fallbackEnabled ?? true,
      timeout: config.timeout || 60000,
    };
  }

  /**
   * 统一的聊天完成接口
   */
  async chatComplete(request: CompletionRequest): Promise<CompletionResponse> {
    const model = request.model || this.config.defaultModel;
    
    try {
      if (model.startsWith('claude')) {
        return await this.callClaude(request);
      } else if (model.startsWith('grok')) {
        return await this.callGrok(request);
      } else {
        throw new Error(`Unsupported model: ${model}`);
      }
    } catch (error) {
      if (this.config.fallbackEnabled) {
        console.log(`Primary model failed, trying fallback...`);
        return this.tryFallback(request, model);
      }
      throw error;
    }
  }

  /**
   * 调用Claude API
   */
  private async callClaude(request: CompletionRequest): Promise<CompletionResponse> {
    const systemMessage = request.messages.find(m => m.role === 'system')?.content as string;
    const conversationMessages = request.messages.filter(m => m.role !== 'system');

    const response = await this.claudeClient.messages.create({
      model: request.model || 'claude-3-5-sonnet-20241022',
      max_tokens: request.maxTokens || 4096,
      temperature: request.temperature || 0.7,
      system: systemMessage,
      messages: conversationMessages.map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content as string,
      })),
      tools: request.tools,
      stream: request.stream || false,
    });

    return {
      content: response.content[0]?.type === 'text' ? response.content[0].text : '',
      usage: {
        inputTokens: response.usage.input_tokens,
        outputTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens,
      },
      toolCalls: response.stop_reason === 'tool_use' 
        ? response.content.filter(c => c.type === 'tool_use')
        : undefined,
      model: response.model,
    };
  }

  /**
   * 调用Grok API
   */
  private async callGrok(request: CompletionRequest): Promise<CompletionResponse> {
    const response = await this.grokClient.chat.completions.create({
      model: request.model || 'grok-3',
      messages: request.messages as any,
      temperature: request.temperature || 0.7,
      max_tokens: request.maxTokens || 4096,
      tools: request.tools,
      stream: request.stream || false,
    });

    const choice = response.choices[0];
    
    return {
      content: choice.message.content || '',
      usage: {
        inputTokens: response.usage?.prompt_tokens || 0,
        outputTokens: response.usage?.completion_tokens || 0,
        totalTokens: response.usage?.total_tokens || 0,
      },
      toolCalls: choice.message.tool_calls,
      model: response.model,
    };
  }

  /**
   * 故障转移逻辑
   */
  private async tryFallback(request: CompletionRequest, failedModel: string): Promise<CompletionResponse> {
    const fallbackModel = failedModel.startsWith('claude') ? 'grok-3' : 'claude-3-5-sonnet-20241022';
    console.log(`Falling back to ${fallbackModel}`);
    
    return this.chatComplete({
      ...request,
      model: fallbackModel,
    });
  }

  /**
   * 流式输出
   */
  async *streamChat(request: CompletionRequest): AsyncGenerator<string> {
    const model = request.model || this.config.defaultModel;
    
    if (model.startsWith('claude')) {
      const stream = await this.claudeClient.messages.create({
        model: request.model || 'claude-3-5-sonnet-20241022',
        max_tokens: request.maxTokens || 4096,
        temperature: request.temperature || 0.7,
        messages: request.messages.filter(m => m.role !== 'system').map(m => ({
          role: m.role as 'user' | 'assistant',
          content: m.content as string,
        })),
        stream: true,
      });

      for await (const chunk of stream) {
        if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
          yield chunk.delta.text;
        }
      }
    } else {
      const stream = await this.grokClient.chat.completions.create({
        model: request.model || 'grok-3',
        messages: request.messages as any,
        temperature: request.temperature || 0.7,
        max_tokens: request.maxTokens || 4096,
        stream: true,
      });

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content;
        if (content) {
          yield content;
        }
      }
    }
  }
}

// 使用示例
async function example() {
  const client = new UnifiedAIClient({
    claudeApiKey: process.env.CLAUDE_API_KEY!,
    grokApiKey: process.env.GROK_API_KEY!,
    defaultModel: 'claude-3-5-sonnet-20241022',
  });

  // 普通调用
  const response = await client.chatComplete({
    messages: [
      { role: 'system', content: '你是一位专业的数据分析师' },
      { role: 'user', content: '分析今年Q3销售数据趋势' },
    ],
    temperature: 0.5,
  });

  console.log('Response:', response.content);
  console.log('Tokens used:', response.usage);

  // 流式调用
  for await (const chunk of client.streamChat({
    messages: [{ role: 'user', content: '写一篇关于AI发展趋势的文章' }],
  })) {
    process.stdout.write(chunk);
  }
}
```

## 2. Python版本统一客户端

```python
# src/clients/unified_ai_client.py

import os
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import anthropic
import openai
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class Message:
    role: str
    content: str | List[Dict[str, Any]]


@dataclass
class CompletionResponse:
    content: str
    usage: Dict[str, int]
    model: str
    tool_calls: Optional[List[Dict]] = None


class UnifiedAIClient:
    """统一的AI模型客户端"""
    
    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        grok_api_key: Optional[str] = None,
        default_model: str = "claude-3-5-sonnet-20241022",
        fallback_enabled: bool = True,
        timeout: int = 60
    ):
        self.claude_client = anthropic.AsyncAnthropic(
            api_key=claude_api_key or os.getenv("CLAUDE_API_KEY")
        )
        self.grok_client = openai.AsyncOpenAI(
            api_key=grok_api_key or os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
            timeout=timeout
        )
        self.default_model = default_model
        self.fallback_enabled = fallback_enabled
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> CompletionResponse:
        """统一的聊天完成接口"""
        model = model or self.default_model
        
        try:
            if model.startswith("claude"):
                return await self._call_claude(
                    messages, model, temperature, max_tokens, tools, stream
                )
            elif model.startswith("grok"):
                return await self._call_grok(
                    messages, model, temperature, max_tokens, tools, stream
                )
            else:
                raise ValueError(f"Unsupported model: {model}")
        except Exception as e:
            if self.fallback_enabled:
                print(f"Primary model failed: {e}, trying fallback...")
                fallback_model = "grok-3" if model.startswith("claude") else "claude-3-5-sonnet-20241022"
                return await self.chat_complete(
                    messages, fallback_model, temperature, max_tokens, tools, stream
                )
            raise

    async def _call_claude(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict]],
        stream: bool
    ) -> CompletionResponse:
        """调用Claude API"""
        system_msg = next((m.content for m in messages if m.role == "system"), None)
        conversation = [m for m in messages if m.role != "system"]
        
        response = await self.claude_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=[
                {"role": m.role, "content": m.content}
                for m in conversation
            ],
            tools=tools,
            stream=stream
        )
        
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })
        
        return CompletionResponse(
            content=content,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            model=response.model,
            tool_calls=tool_calls if tool_calls else None
        )

    async def _call_grok(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict]],
        stream: bool
    ) -> CompletionResponse:
        """调用Grok API"""
        response = await self.grok_client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=stream
        )
        
        choice = response.choices[0]
        
        return CompletionResponse(
            content=choice.message.content or "",
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            },
            model=response.model,
            tool_calls=choice.message.tool_calls
        )

    async def stream_chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口"""
        model = model or self.default_model
        
        if model.startswith("claude"):
            async with self.claude_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": m.role, "content": m.content}
                    for m in messages if m.role != "system"
                ]
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        else:
            response = await self.grok_client.chat.completions.create(
                model=model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content


# 使用示例
async def main():
    client = UnifiedAIClient()
    
    # 普通调用
    response = await client.chat_complete(
        messages=[
            Message(role="system", content="你是一位专业的数据分析师"),
            Message(role="user", content="分析今年Q3销售数据趋势")
        ],
        temperature=0.5
    )
    
    print(f"Response: {response.content}")
    print(f"Tokens: {response.usage}")
    
    # 流式调用
    async for chunk in client.stream_chat(
        messages=[Message(role="user", content="写一篇关于AI发展趋势的文章")]
    ):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

## 3. 模型路由服务

```typescript
// src/services/ModelRouter.ts

interface ModelConfig {
  name: string;
  provider: 'anthropic' | 'xai' | 'openai';
  priority: number;
  costPer1kTokens: number;
  capabilities: string[];
  maxTokens: number;
  rateLimit: {
    requestsPerMinute: number;
    tokensPerMinute: number;
  };
}

interface RoutingRule {
  condition: (request: any) => boolean;
  targetModel: string;
  priority: number;
}

export class ModelRouter {
  private models: Map<string, ModelConfig> = new Map();
  private rules: RoutingRule[] = [];
  private usageStats: Map<string, { tokens: number; cost: number }> = new Map();

  constructor() {
    this.initializeModels();
    this.initializeRules();
  }

  private initializeModels() {
    this.models.set('claude-3-5-sonnet', {
      name: 'claude-3-5-sonnet-20241022',
      provider: 'anthropic',
      priority: 1,
      costPer1kTokens: 3.0,
      capabilities: ['reasoning', 'coding', 'analysis', 'vision'],
      maxTokens: 8192,
      rateLimit: { requestsPerMinute: 100, tokensPerMinute: 40000 },
    });

    this.models.set('claude-3-opus', {
      name: 'claude-3-opus-20240229',
      provider: 'anthropic',
      priority: 2,
      costPer1kTokens: 15.0,
      capabilities: ['reasoning', 'coding', 'analysis', 'vision', 'complex-tasks'],
      maxTokens: 4096,
      rateLimit: { requestsPerMinute: 50, tokensPerMinute: 20000 },
    });

    this.models.set('grok-3', {
      name: 'grok-3',
      provider: 'xai',
      priority: 3,
      costPer1kTokens: 5.0,
      capabilities: ['reasoning', 'coding', 'realtime', 'x-data'],
      maxTokens: 8192,
      rateLimit: { requestsPerMinute: 60, tokensPerMinute: 30000 },
    });
  }

  private initializeRules() {
    // 根据任务复杂度路由
    this.rules.push({
      condition: (req) => req.complexity === 'high' || req.codeTask === true,
      targetModel: 'claude-3-opus',
      priority: 1,
    });

    // 根据成本敏感度路由
    this.rules.push({
      condition: (req) => req.costSensitive === true,
      targetModel: 'claude-3-5-sonnet',
      priority: 2,
    });

    // 根据实时性需求路由
    this.rules.push({
      condition: (req) => req.realtime === true,
      targetModel: 'grok-3',
      priority: 3,
    });

    // 默认路由
    this.rules.push({
      condition: () => true,
      targetModel: 'claude-3-5-sonnet',
      priority: 999,
    });

    // 按优先级排序
    this.rules.sort((a, b) => a.priority - b.priority);
  }

  /**
   * 智能路由决策
   */
  async route(request: any): Promise<ModelConfig> {
    // 执行路由规则
    for (const rule of this.rules) {
      if (rule.condition(request)) {
        const model = this.models.get(rule.targetModel);
        if (model && await this.checkAvailability(model)) {
          return model;
        }
      }
    }

    // 如果指定了模型，直接返回
    if (request.model && this.models.has(request.model)) {
      return this.models.get(request.model)!;
    }

    // 默认返回优先级最高的可用模型
    return this.getDefaultModel();
  }

  /**
   * 检查模型可用性
   */
  private async checkAvailability(model: ModelConfig): Promise<boolean> {
    // TODO: 实现实际的限流检查
    return true;
  }

  /**
   * 获取默认模型
   */
  private getDefaultModel(): ModelConfig {
    const sortedModels = Array.from(this.models.values())
      .sort((a, b) => a.priority - b.priority);
    return sortedModels[0];
  }

  /**
   * 记录使用情况
   */
  recordUsage(modelName: string, tokens: number) {
    const model = Array.from(this.models.values()).find(m => m.name === modelName);
    if (!model) return;

    const cost = (tokens / 1000) * model.costPer1kTokens;
    const current = this.usageStats.get(modelName) || { tokens: 0, cost: 0 };
    
    this.usageStats.set(modelName, {
      tokens: current.tokens + tokens,
      cost: current.cost + cost,
    });
  }

  /**
   * 获取成本统计
   */
  getCostStats(): Record<string, { tokens: number; cost: number }> {
    return Object.fromEntries(this.usageStats);
  }
}
```

## 4. 使用示例

```typescript
// examples/api-integration-example.ts

import { UnifiedAIClient } from '../src/clients/UnifiedAIClient';
import { ModelRouter } from '../src/services/ModelRouter';

async function demonstrateIntegration() {
  // 初始化
  const client = new UnifiedAIClient({
    claudeApiKey: process.env.CLAUDE_API_KEY!,
    grokApiKey: process.env.GROK_API_KEY!,
  });

  const router = new ModelRouter();

  // 场景1: 复杂编程任务
  console.log('=== 场景1: 复杂编程任务 ===');
  const codingRequest = {
    complexity: 'high',
    codeTask: true,
    messages: [
      { role: 'system', content: '你是资深架构师' },
      { role: 'user', content: '设计一个分布式任务调度系统' },
    ],
  };
  
  const codingModel = await router.route(codingRequest);
  console.log(`路由到模型: ${codingModel.name}`);
  
  const codingResponse = await client.chatComplete({
    ...codingRequest,
    model: codingModel.name,
  });
  
  console.log(`Token使用: ${codingResponse.usage.totalTokens}`);
  router.recordUsage(codingResponse.model, codingResponse.usage.totalTokens);

  // 场景2: 成本敏感的数据分析
  console.log('\n=== 场景2: 成本敏感分析 ===');
  const analysisRequest = {
    costSensitive: true,
    messages: [
      { role: 'user', content: '总结这份销售报告的关键点' },
    ],
  };
  
  const analysisModel = await router.route(analysisRequest);
  console.log(`路由到模型: ${analysisModel.name}`);

  // 场景3: 带工具调用的对话
  console.log('\n=== 场景3: 工具调用 ===');
  const toolResponse = await client.chatComplete({
    messages: [
      { role: 'user', content: '查询本月销售额' },
    ],
    tools: [
      {
        name: 'query_sales',
        description: '查询销售数据',
        input_schema: {
          type: 'object',
          properties: {
            month: { type: 'string' },
            year: { type: 'number' },
          },
          required: ['month', 'year'],
        },
      },
    ],
  });

  if (toolResponse.toolCalls) {
    console.log('模型请求调用工具:', toolResponse.toolCalls);
  }

  // 成本统计
  console.log('\n=== 成本统计 ===');
  console.log(router.getCostStats());
}

demonstrateIntegration().catch(console.error);
```
