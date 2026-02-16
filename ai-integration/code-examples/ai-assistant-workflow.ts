# 完整AI助手工作流设计

## 1. 核心工作流架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI助手工作流引擎                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   输入层                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  • 语音输入 (Whisper)    • 文本输入                                  │   │
│   │  • 文档上传 (OCR)        • 图片输入 (Vision)                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   理解层                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │   │
│   │  │  意图识别    │───►│  实体提取    │───►│  上下文管理  │          │   │
│   │  │  Intent      │    │  NER         │    │  Context     │          │   │
│   │  └──────────────┘    └──────────────┘    └──────────────┘          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   决策层                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │   │
│   │  │  任务路由    │───►│  模型选择    │───►│  工具规划    │          │   │
│   │  │  Router      │    │  Selector    │    │  Planner     │          │   │
│   │  └──────────────┘    └──────────────┘    └──────────────┘          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   执行层                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│   │  │ 云端API  │ │ 本地LLM  │ │ 企业系统 │ │ 知识检索 │ │ 代码执行 │  │   │
│   │  │ Claude   │ │ Ollama   │ │ SAP/OA   │ │ RAG      │ │ Python   │  │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                          │
│                                   ▼                                          │
│   输出层                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  • 文本回复            • 语音合成 (TTS)                              │   │
│   │  • 结构化数据          • 可视化图表                                  │   │
│   │  • 文档生成            • 操作执行结果                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 工作流引擎实现

```typescript
// src/workflow/AIAssistantWorkflow.ts

import { EventEmitter } from 'events';
import { UnifiedAIClient } from '../clients/UnifiedAIClient';
import { ModelRouter } from '../services/ModelRouter';
import { WhisperService } from '../services/whisper_service';
import { ChatTTSService } from '../services/tts_service';
import { OllamaService } from '../services/local_llm_service';

// 工作流状态
enum WorkflowState {
  IDLE = 'idle',
  PROCESSING = 'processing',
  WAITING_TOOL = 'waiting_tool',
  COMPLETED = 'completed',
  ERROR = 'error',
}

// 意图类型
enum IntentType {
  CHAT = 'chat',
  DATA_QUERY = 'data_query',
  DOCUMENT_ANALYSIS = 'document_analysis',
  CODE_GENERATION = 'code_generation',
  WORKFLOW_EXECUTION = 'workflow_execution',
  KNOWLEDGE_RETRIEVAL = 'knowledge_retrieval',
}

// 消息类型
interface WorkflowMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

// 工作流上下文
interface WorkflowContext {
  sessionId: string;
  messages: WorkflowMessage[];
  currentIntent?: IntentType;
  extractedEntities?: Record<string, any>;
  toolResults?: any[];
  userPreferences?: Record<string, any>;
}

export class AIAssistantWorkflow extends EventEmitter {
  private state: WorkflowState = WorkflowState.IDLE;
  private context: WorkflowContext;
  private cloudClient: UnifiedAIClient;
  private localLLM: OllamaService;
  private modelRouter: ModelRouter;
  private whisper: WhisperService | null = null;
  private tts: ChatTTSService | null = null;
  
  // 工具注册表
  private tools: Map<string, Function> = new Map();
  
  constructor(config: {
    sessionId: string;
    cloudClient: UnifiedAIClient;
    localLLM: OllamaService;
    enableVoice?: boolean;
  }) {
    super();
    
    this.context = {
      sessionId: config.sessionId,
      messages: [],
    };
    
    this.cloudClient = config.cloudClient;
    this.localLLM = config.localLLM;
    this.modelRouter = new ModelRouter();
    
    this.initializeTools();
  }

  /**
   * 初始化工具
   */
  private initializeTools() {
    // 数据查询工具
    this.tools.set('query_database', this.queryDatabase.bind(this));
    this.tools.set('query_sap', this.querySAP.bind(this));
    
    // 文档工具
    this.tools.set('analyze_document', this.analyzeDocument.bind(this));
    this.tools.set('summarize_text', this.summarizeText.bind(this));
    
    // 代码工具
    this.tools.set('execute_code', this.executeCode.bind(this));
    this.tools.set('generate_code', this.generateCode.bind(this));
    
    // 工作流工具
    this.tools.set('create_approval', this.createApproval.bind(this));
    this.tools.set('send_notification', this.sendNotification.bind(this));
    
    // 知识工具
    this.tools.set('search_knowledge', this.searchKnowledge.bind(this));
    this.tools.set('semantic_search', this.semanticSearch.bind(this));
  }

  /**
   * 处理用户输入
   */
  async processInput(
    input: string | Buffer,
    options: {
      inputType?: 'text' | 'voice' | 'image';
      useVoiceOutput?: boolean;
      context?: Record<string, any>;
    } = {}
  ): Promise<WorkflowMessage> {
    this.state = WorkflowState.PROCESSING;
    this.emit('stateChange', this.state);

    try {
      let userContent = input;
      
      // 语音输入处理
      if (options.inputType === 'voice' && Buffer.isBuffer(input)) {
        userContent = await this.transcribeVoice(input);
      }

      // 添加上下文信息
      if (options.context) {
        this.context.extractedEntities = {
          ...this.context.extractedEntities,
          ...options.context,
        };
      }

      // 添加用户消息
      const userMessage: WorkflowMessage = {
        id: this.generateId(),
        role: 'user',
        content: userContent as string,
        timestamp: new Date(),
      };
      this.context.messages.push(userMessage);

      // 意图识别
      const intent = await this.recognizeIntent(userContent as string);
      this.context.currentIntent = intent;

      // 根据意图路由处理
      let response: WorkflowMessage;
      
      switch (intent) {
        case IntentType.DATA_QUERY:
          response = await this.handleDataQuery(userContent as string);
          break;
        case IntentType.DOCUMENT_ANALYSIS:
          response = await this.handleDocumentAnalysis(userContent as string);
          break;
        case IntentType.CODE_GENERATION:
          response = await this.handleCodeGeneration(userContent as string);
          break;
        case IntentType.WORKFLOW_EXECUTION:
          response = await this.handleWorkflowExecution(userContent as string);
          break;
        case IntentType.KNOWLEDGE_RETRIEVAL:
          response = await this.handleKnowledgeRetrieval(userContent as string);
          break;
        default:
          response = await this.handleGeneralChat(userContent as string);
      }

      // 语音输出
      if (options.useVoiceOutput && this.tts) {
        const audioBuffer = await this.synthesizeVoice(response.content);
        response.metadata = { ...response.metadata, audioBuffer };
      }

      this.context.messages.push(response);
      this.state = WorkflowState.COMPLETED;
      this.emit('stateChange', this.state);
      this.emit('message', response);

      return response;
    } catch (error) {
      this.state = WorkflowState.ERROR;
      this.emit('stateChange', this.state);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * 意图识别
   */
  private async recognizeIntent(text: string): Promise<IntentType> {
    const prompt = `分析以下用户输入的意图类型，只返回类型名称：

输入："${text}"

可选类型：
- chat: 一般聊天对话
- data_query: 数据查询分析
- document_analysis: 文档分析处理
- code_generation: 代码生成
- workflow_execution: 流程执行
- knowledge_retrieval: 知识检索

意图类型：`;

    const response = await this.localLLM.generate(prompt, {
      temperature: 0.1,
      num_predict: 20,
    });

    const intentMap: Record<string, IntentType> = {
      'chat': IntentType.CHAT,
      'data_query': IntentType.DATA_QUERY,
      'document_analysis': IntentType.DOCUMENT_ANALYSIS,
      'code_generation': IntentType.CODE_GENERATION,
      'workflow_execution': IntentType.WORKFLOW_EXECUTION,
      'knowledge_retrieval': IntentType.KNOWLEDGE_RETRIEVAL,
    };

    const detectedIntent = Object.keys(intentMap).find(key => 
      response.content.toLowerCase().includes(key)
    );

    return detectedIntent ? intentMap[detectedIntent] : IntentType.CHAT;
  }

  /**
   * 一般聊天处理
   */
  private async handleGeneralChat(userMessage: string): Promise<WorkflowMessage> {
    // 构建消息历史
    const messages = this.buildMessageHistory();
    
    // 智能路由选择模型
    const routeDecision = await this.modelRouter.route({
      messages,
      complexity: this.estimateComplexity(userMessage),
    });

    let response: string;
    
    if (routeDecision.provider === 'ollama') {
      // 使用本地模型
      const result = await this.localLLM.chat(messages);
      response = result.content;
    } else {
      // 使用云端API
      const result = await this.cloudClient.chatComplete({
        messages: messages.map(m => ({
          role: m.role,
          content: m.content,
        })),
        model: routeDecision.name,
      });
      response = result.content;
    }

    return {
      id: this.generateId(),
      role: 'assistant',
      content: response,
      timestamp: new Date(),
      metadata: { model: routeDecision.name },
    };
  }

  /**
   * 数据查询处理
   */
  private async handleDataQuery(userMessage: string): Promise<WorkflowMessage> {
    // 提取查询参数
    const extractionPrompt = `从以下查询中提取关键参数(时间范围、指标、维度等)：
"${userMessage}"

以JSON格式返回：`;

    const extraction = await this.localLLM.generate(extractionPrompt, {
      temperature: 0.1,
    });

    let queryParams: any = {};
    try {
      queryParams = JSON.parse(extraction.content);
    } catch {
      // 使用默认参数
    }

    // 执行数据查询
    const queryResult = await this.tools.get('query_database')!({
      ...queryParams,
      ...this.context.extractedEntities,
    });

    // 使用云端模型分析数据
    const analysisPrompt = `基于以下数据提供分析洞察：

查询：${userMessage}
数据结果：${JSON.stringify(queryResult)}

请提供：
1. 数据概览
2. 关键发现
3. 趋势分析
4. 建议`;

    const analysis = await this.cloudClient.chatComplete({
      messages: [{ role: 'user', content: analysisPrompt }],
      model: 'claude-3-5-sonnet-20241022',
    });

    return {
      id: this.generateId(),
      role: 'assistant',
      content: analysis.content,
      timestamp: new Date(),
      metadata: { 
        queryResult,
        dataVisualization: this.generateChartConfig(queryResult),
      },
    };
  }

  /**
   * 知识检索处理
   */
  private async handleKnowledgeRetrieval(userMessage: string): Promise<WorkflowMessage> {
    // 生成查询向量
    const queryEmbedding = await this.localLLM.embeddings([userMessage]);
    
    // 语义检索
    const searchResults = await this.tools.get('semantic_search')!({
      vector: queryEmbedding[0],
      topK: 5,
    });

    // 构建RAG上下文
    const context = searchResults.map((r: any) => r.content).join('\n\n');
    
    const ragPrompt = `基于以下参考资料回答问题：

参考资料：
${context}

问题：${userMessage}

请基于以上资料回答，如果资料不足请说明：`;

    const response = await this.cloudClient.chatComplete({
      messages: [{ role: 'user', content: ragPrompt }],
      model: 'claude-3-5-sonnet-20241022',
    });

    return {
      id: this.generateId(),
      role: 'assistant',
      content: response.content,
      timestamp: new Date(),
      metadata: { 
        sources: searchResults.map((r: any) => r.source),
        confidence: searchResults[0]?.score,
      },
    };
  }

  /**
   * 代码生成处理
   */
  private async handleCodeGeneration(userMessage: string): Promise<WorkflowMessage> {
    const codePrompt = `根据以下需求生成代码：

需求：${userMessage}

要求：
1. 代码简洁高效
2. 包含详细注释
3. 考虑边界情况
4. 提供使用示例

请直接输出代码：`;

    const response = await this.cloudClient.chatComplete({
      messages: [{ role: 'user', content: codePrompt }],
      model: 'claude-3-opus-20240229', // 使用最强模型
      temperature: 0.2,
    });

    // 提取代码块
    const codeMatch = response.content.match(/```[\w]*\n?([\s\S]*?)```/);
    const code = codeMatch ? codeMatch[1].trim() : response.content;

    return {
      id: this.generateId(),
      role: 'assistant',
      content: response.content,
      timestamp: new Date(),
      metadata: { 
        code,
        language: this.detectLanguage(code),
      },
    };
  }

  // 辅助方法
  private buildMessageHistory(): any[] {
    return this.context.messages.slice(-10).map(m => ({
      role: m.role,
      content: m.content,
    }));
  }

  private estimateComplexity(text: string): string {
    if (text.length > 500 || text.includes('分析') || text.includes('设计')) {
      return 'high';
    }
    if (text.length > 200) {
      return 'medium';
    }
    return 'low';
  }

  private generateId(): string {
    return Math.random().toString(36).substring(2, 15);
  }

  // 工具方法占位
  private async queryDatabase(params: any) { return { data: [] }; }
  private async querySAP(params: any) { return { data: [] }; }
  private async analyzeDocument(params: any) { return { text: '' }; }
  private async summarizeText(params: any) { return { summary: '' }; }
  private async executeCode(params: any) { return { output: '' }; }
  private async generateCode(params: any) { return { code: '' }; }
  private async createApproval(params: any) { return { id: '' }; }
  private async sendNotification(params: any) { return { sent: true }; }
  private async searchKnowledge(params: any) { return { results: [] }; }
  private async semanticSearch(params: any) { return { results: [] }; }
  private async transcribeVoice(buffer: Buffer): Promise<string> { return ''; }
  private async synthesizeVoice(text: string): Promise<Buffer> { return Buffer.from([]); }
  private generateChartConfig(data: any): any { return {}; }
  private detectLanguage(code: string): string { return 'typescript'; }

  // Getters
  getState(): WorkflowState { return this.state; }
  getContext(): WorkflowContext { return { ...this.context }; }
  getMessages(): WorkflowMessage[] { return [...this.context.messages]; }
}
```

## 3. 多Agent协作系统

```typescript
// src/workflow/MultiAgentSystem.ts

interface Agent {
  name: string;
  role: string;
  expertise: string[];
  execute: (task: Task, context: SharedContext) => Promise<TaskResult>;
}

interface Task {
  id: string;
  type: string;
  description: string;
  dependencies: string[];
  priority: number;
}

interface TaskResult {
  success: boolean;
  output: any;
  agent: string;
  timestamp: Date;
}

interface SharedContext {
  originalQuery: string;
  intermediateResults: Map<string, any>;
  conversationHistory: WorkflowMessage[];
}

export class MultiAgentOrchestrator {
  private agents: Map<string, Agent> = new Map();
  private taskQueue: Task[] = [];
  private sharedContext: SharedContext;

  constructor() {
    this.sharedContext = {
      originalQuery: '',
      intermediateResults: new Map(),
      conversationHistory: [],
    };
    this.initializeAgents();
  }

  private initializeAgents() {
    // 分析师Agent
    this.agents.set('analyst', {
      name: 'Data Analyst',
      role: '数据分析专家',
      expertise: ['sql', 'statistics', 'visualization'],
      execute: this.analystExecute.bind(this),
    });

    // 研究员Agent
    this.agents.set('researcher', {
      name: 'Researcher',
      role: '信息检索专家',
      expertise: ['search', 'synthesis', 'summarization'],
      execute: this.researcherExecute.bind(this),
    });

    // 程序员Agent
    this.agents.set('coder', {
      name: 'Software Engineer',
      role: '软件开发专家',
      expertise: ['coding', 'debugging', 'architecture'],
      execute: this.coderExecute.bind(this),
    });

    // 业务专家Agent
    this.agents.set('business', {
      name: 'Business Expert',
      role: '业务顾问',
      expertise: ['domain_knowledge', 'workflow', 'best_practices'],
      execute: this.businessExecute.bind(this),
    });
  }

  /**
   * 执行复杂任务
   */
  async executeComplexTask(query: string): Promise<any> {
    this.sharedContext.originalQuery = query;
    
    // 1. 任务分解
    const subtasks = await this.decomposeTask(query);
    
    // 2. 任务调度
    const executionPlan = this.scheduleTasks(subtasks);
    
    // 3. 并行执行
    const results = await this.executePlan(executionPlan);
    
    // 4. 结果聚合
    const finalAnswer = await this.synthesizeResults(results);
    
    return finalAnswer;
  }

  /**
   * 任务分解
   */
  private async decomposeTask(query: string): Promise<Task[]> {
    const decompositionPrompt = `将以下复杂任务分解为子任务：

任务：${query}

要求：
1. 每个子任务明确具体
2. 标注任务间的依赖关系
3. 估算任务优先级

以JSON数组格式返回子任务列表：`;

    // 使用本地模型进行快速分解
    const result = await localLLM.generate(decompositionPrompt);
    
    try {
      return JSON.parse(result.content);
    } catch {
      // 返回默认分解
      return [{
        id: '1',
        type: 'analysis',
        description: query,
        dependencies: [],
        priority: 1,
      }];
    }
  }

  /**
   * 任务调度
   */
  private scheduleTasks(tasks: Task[]): Map<string, Agent> {
    const assignment = new Map<string, Agent>();
    
    for (const task of tasks) {
      const bestAgent = this.selectBestAgent(task);
      assignment.set(task.id, bestAgent);
    }
    
    return assignment;
  }

  /**
   * 选择最佳Agent
   */
  private selectBestAgent(task: Task): Agent {
    const taskType = task.type.toLowerCase();
    
    for (const [name, agent] of this.agents) {
      if (agent.expertise.some(e => taskType.includes(e))) {
        return agent;
      }
    }
    
    return this.agents.get('business')!;
  }

  /**
   * 执行计划
   */
  private async executePlan(
    plan: Map<string, Agent>
  ): Promise<Map<string, TaskResult>> {
    const results = new Map<string, TaskResult>();
    const tasks = Array.from(plan.entries());
    
    // 按依赖分组并行执行
    const batches = this.groupByDependencies(tasks);
    
    for (const batch of batches) {
      const batchResults = await Promise.all(
        batch.map(async ([taskId, agent]) => {
          const task = this.taskQueue.find(t => t.id === taskId)!;
          const result = await agent.execute(task, this.sharedContext);
          this.sharedContext.intermediateResults.set(taskId, result);
          return [taskId, result] as [string, TaskResult];
        })
      );
      
      batchResults.forEach(([id, result]) => results.set(id, result));
    }
    
    return results;
  }

  /**
   * 结果合成
   */
  private async synthesizeResults(
    results: Map<string, TaskResult>
  ): Promise<string> {
    const synthesisPrompt = `综合以下各Agent的执行结果，提供完整回答：

原始问题：${this.sharedContext.originalQuery}

子任务结果：
${Array.from(results.entries())
  .map(([id, r]) => `[${id}] ${r.agent}: ${JSON.stringify(r.output)}`)
  .join('\n')}

请提供：
1. 综合分析
2. 关键发现
3. 行动建议`;

    const finalResponse = await cloudClient.chatComplete({
      messages: [{ role: 'user', content: synthesisPrompt }],
      model: 'claude-3-opus-20240229',
    });

    return finalResponse.content;
  }

  // Agent执行方法
  private async analystExecute(task: Task, context: SharedContext): Promise<TaskResult> {
    // 数据分析师执行逻辑
    return { success: true, output: {}, agent: 'analyst', timestamp: new Date() };
  }

  private async researcherExecute(task: Task, context: SharedContext): Promise<TaskResult> {
    // 研究员执行逻辑
    return { success: true, output: {}, agent: 'researcher', timestamp: new Date() };
  }

  private async coderExecute(task: Task, context: SharedContext): Promise<TaskResult> {
    // 程序员执行逻辑
    return { success: true, output: {}, agent: 'coder', timestamp: new Date() };
  }

  private async businessExecute(task: Task, context: SharedContext): Promise<TaskResult> {
    // 业务专家执行逻辑
    return { success: true, output: {}, agent: 'business', timestamp: new Date() };
  }

  private groupByDependencies(tasks: [string, Agent][]): [string, Agent][][] {
    // 按依赖关系分组
    return [tasks]; // 简化实现
  }
}
```

## 4. 工作流使用示例

```typescript
// examples/workflow-example.ts

import { AIAssistantWorkflow } from '../src/workflow/AIAssistantWorkflow';
import { UnifiedAIClient } from '../src/clients/UnifiedAIClient';
import { OllamaService } from '../src/services/local_llm_service';

async function runWorkflowExamples() {
  // 初始化服务
  const cloudClient = new UnifiedAIClient({
    claudeApiKey: process.env.CLAUDE_API_KEY!,
    grokApiKey: process.env.GROK_API_KEY!,
  });

  const localLLM = new OllamaService({
    baseUrl: 'http://localhost:11434',
    defaultModel: 'qwen2.5:14b',
  });

  // 创建工作流实例
  const workflow = new AIAssistantWorkflow({
    sessionId: 'demo-session-001',
    cloudClient,
    localLLM,
  });

  // 监听事件
  workflow.on('stateChange', (state) => {
    console.log(`工作流状态: ${state}`);
  });

  workflow.on('message', (message) => {
    console.log(`新消息: ${message.content.substring(0, 100)}...`);
  });

  // 示例1: 一般对话
  console.log('=== 示例1: 一般对话 ===');
  const response1 = await workflow.processInput(
    '你好，请介绍一下人工智能的发展趋势'
  );
  console.log('回复:', response1.content);

  // 示例2: 数据查询
  console.log('\n=== 示例2: 数据查询 ===');
  const response2 = await workflow.processInput(
    '查询上季度各区域的销售数据，并分析增长趋势',
    { context: { userRole: 'sales_manager', region: 'all' } }
  );
  console.log('回复:', response2.content);
  if (response2.metadata?.dataVisualization) {
    console.log('可视化配置:', response2.metadata.dataVisualization);
  }

  // 示例3: 代码生成
  console.log('\n=== 示例3: 代码生成 ===');
  const response3 = await workflow.processInput(
    '帮我写一个Python函数，用于处理CSV数据并生成统计报告'
  );
  console.log('回复:', response3.content);
  if (response3.metadata?.code) {
    console.log('提取的代码:', response3.metadata.code.substring(0, 200));
  }

  // 示例4: 知识检索
  console.log('\n=== 示例4: 知识检索 ===');
  const response4 = await workflow.processInput(
    '公司的远程办公政策是什么？'
  );
  console.log('回复:', response4.content);
  if (response4.metadata?.sources) {
    console.log('参考来源:', response4.metadata.sources);
  }

  // 示例5: 带语音输出
  console.log('\n=== 示例5: 语音输出 ===');
  const response5 = await workflow.processInput(
    '用简洁的语言总结今天的会议要点',
    { useVoiceOutput: true }
  );
  if (response5.metadata?.audioBuffer) {
    console.log('语音数据大小:', response5.metadata.audioBuffer.length, 'bytes');
  }

  // 打印会话历史
  console.log('\n=== 会话历史 ===');
  const messages = workflow.getMessages();
  messages.forEach((m, i) => {
    console.log(`${i + 1}. [${m.role}] ${m.content.substring(0, 50)}...`);
  });
}

runWorkflowExamples().catch(console.error);
```
