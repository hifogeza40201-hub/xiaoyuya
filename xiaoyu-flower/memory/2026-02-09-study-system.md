# OpenClaw 系统架构与 Agent 设计模式学习笔记

> **学习时间**: 2026-02-09  
> **学习时长**: 1 小时  
> **资料来源**: OpenClaw 官方文档、本地技能文件、网络资源

---

## 一、OpenClaw 架构概述（核心组件）

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Chat Apps + Plugins                          │
│  (WhatsApp, Telegram, Discord, iMessage, Mattermost, etc.)         │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Gateway (核心网关)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Session    │  │    Agent     │  │   Channel    │              │
│  │   Manager    │  │    Runner    │  │   Router     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Plugin     │  │    Hook      │  │   Memory     │              │
│  │   System     │  │   System     │  │   System     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │    Pi     │    │    CLI    │    │  Web UI   │
            │   Agent   │    │           │    │ Control   │
            └───────────┘    └───────────┘    └───────────┘
```

### 1.2 核心组件详解

#### 1.2.1 Gateway（网关）
- **角色**: 单一真相源（Single Source of Truth）
- **职责**: 会话管理、路由、频道连接
- **特点**: 自托管、多频道同时服务

#### 1.2.2 Agent（代理）
- **定义**: 一个完全隔离的"大脑"，拥有独立的：
  - Workspace（工作空间）
  - AgentDir（状态目录）
  - Session Store（会话存储）
  - Auth Profiles（认证配置）
- **多代理支持**: 可在单个 Gateway 上运行多个隔离的代理

#### 1.2.3 Session（会话）
- **会话键格式**: `agent:<agentId>:<sessionKey>`
- **主会话**: `agent:main:main`（默认）
- **隔离级别**:
  - `dmScope: "main"` - 所有私信共享主会话（连续性）
  - `dmScope: "per-peer"` - 按发送者隔离
  - `dmScope: "per-channel-peer"` - 按频道+发送者隔离
  - `dmScope: "per-account-channel-peer"` - 按账户+频道+发送者隔离

#### 1.2.4 Channel（频道）
- 支持的频道: WhatsApp、Telegram、Discord、iMessage 等
- 插件扩展: Mattermost、Teams、Matrix、Nostr、Zalo 等
- 每个频道可有多个账号（如多个 WhatsApp 号码）

---

## 二、Agent 设计模式总结

### 2.1 核心设计原则

#### 2.1.1 隔离性（Isolation）
- **工作空间隔离**: 每个代理有独立的工作目录
- **认证隔离**: 每个代理有自己的 `auth-profiles.json`
- **会话隔离**: 独立的会话存储，无跨代理干扰

#### 2.1.2 路由绑定（Bindings）
```json
{
  "bindings": [
    {
      "agentId": "home",
      "match": { 
        "channel": "whatsapp", 
        "accountId": "personal" 
      }
    },
    {
      "agentId": "work", 
      "match": { 
        "channel": "whatsapp", 
        "accountId": "biz",
        "peer": { "kind": "group", "id": "..." }
      }
    }
  ]
}
```
**路由优先级**: peer > guildId > teamId > accountId > channel > default

#### 2.1.3 沙盒模式（Sandbox）
| 模式 | 说明 |
|------|------|
| `off` | 不沙盒，直接运行在主机 |
| `non-main` | 非主会话使用沙盒（默认）|
| `all` | 所有会话都使用沙盒 |

**作用域**: 
- `session` - 每个会话一个容器
- `agent` - 每个代理一个容器
- `shared` - 多个代理共享容器

### 2.2 多代理架构模式

#### 2.2.1 个人+工作分离模式
```
┌─────────────────────────────────────┐
│           Gateway                   │
│  ┌─────────┐     ┌─────────┐       │
│  │  home   │     │  work   │       │
│  │ 代理    │     │ 代理    │       │
│  │ 私人助理 │     │ 工作助理 │       │
│  └────┬────┘     └────┬────┘       │
│       │               │            │
│       ▼               ▼            │
│  WhatsApp          WhatsApp        │
│  personal          biz             │
│  账号              账号            │
└─────────────────────────────────────┘
```

#### 2.2.2 按频道分工模式
- WhatsApp → 日常聊天代理（轻量级模型）
- Telegram → 深度工作代理（Opus 模型）

#### 2.2.3 按群组/DM 路由模式
- 大部分消息 → 日常代理
- 特定群组/DM → 专业代理

### 2.3 Agent Loop（代理循环）

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Loop 流程                           │
└─────────────────────────────────────────────────────────────────┘

消息进入
   │
   ▼
┌─────────────┐
│  会话解析   │ ──► 确定 sessionKey、agentId
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  队列序列化 │ ──► 每会话串行执行，防止竞态
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  上下文组装 │ ──► 系统提示 + 技能 + 历史记录
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  模型推理   │ ──► LLM 生成响应/工具调用
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  工具执行   │ ──► 执行工具、获取结果
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  流式回复   │ ──► 向用户发送响应
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  状态持久化 │ ──► 保存会话历史
└─────────────┘
```

---

## 三、工具调用机制详解

### 3.1 工具层次结构

```
┌─────────────────────────────────────────────────────────────────┐
│                     工具调用决策链                               │
└─────────────────────────────────────────────────────────────────┘

1. 工具配置 (tools.profile)
   │
   ├── profile: "coding"    → read, write, edit, apply_patch, exec
   ├── profile: "messaging" → sessions_list, sessions_send, message
   ├── profile: "minimal"   → read only
   └── profile: "all"       → 所有工具
   │
   ▼
2. 全局工具策略 (tools.allow / tools.deny)
   │
   ▼
3. 提供商工具策略 (tools.byProvider[provider].allow/deny)
   │
   ▼
4. 代理特定工具策略 (agents.list[].tools.allow/deny)
   │
   ▼
5. 沙盒工具策略 (tools.sandbox.tools)
   │
   ▼
6. 子代理工具策略 (tools.subagents.tools)
   │
   ▼
7. 特权模式 (tools.elevated) ← 需要显式授权
```

**规则**: 每个级别只能进一步限制，不能恢复已拒绝的工具

### 3.2 工具组速查

| 工具组 | 包含工具 |
|--------|----------|
| `group:runtime` | exec, bash, process |
| `group:fs` | read, write, edit, apply_patch |
| `group:sessions` | sessions_list, sessions_send, etc. |
| `group:memory` | memory_search, memory_get |
| `group:ui` | browser, canvas |
| `group:automation` | cron, gateway |
| `group:messaging` | message |
| `group:nodes` | nodes |
| `group:openclaw` | 所有内置工具 |

### 3.3 工具调用流程

```typescript
// 伪代码示例
interface ToolCall {
  type: 'tool';
  tool: string;
  params: Record<string, any>;
}

async function executeTool(call: ToolCall, context: Context) {
  // 1. 权限检查
  if (!isToolAllowed(call.tool, context.agentId)) {
    throw new Error(`Tool ${call.tool} not allowed for agent ${context.agentId}`);
  }
  
  // 2. 沙盒检查
  if (context.sandbox && !isSandboxTool(call.tool)) {
    throw new Error(`Tool ${call.tool} not available in sandbox`);
  }
  
  // 3. 执行工具
  const result = await toolRegistry.execute(call.tool, call.params);
  
  // 4. 结果处理
  return sanitizeResult(result);
}
```

### 3.4 特权模式（Elevated Mode）

- 基于发送者的白名单机制
- 默认关闭，需要显式启用
- 可与沙盒配置叠加使用

---

## 四、记忆系统工作原理

### 4.1 认知记忆系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     上下文窗口 (始终加载)                             │
│  ├─ 系统提示 (~4-5K tokens)                                          │
│  ├─ 核心记忆 MEMORY.md (~3K tokens)  ◄── 始终在上下文中                │
│  └─ 对话 + 工具 (~185K+ tokens)                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     记忆存储 (按需检索)                               │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   Episodic      │    Semantic     │   Procedural    │    Vault      │
│   情景记忆      │    语义记忆     │    程序记忆     │   保险库      │
├─────────────────┼─────────────────┼─────────────────┼───────────────┤
│ • 时间线事件    │ • 知识图谱      │ • 工作流模板    │ • 用户固定    │
│ • 每日日志      │ • 实体关系      │ • 学习模式      │ • 永不衰减    │
│ • 对话历史      │ • 概念网络      │ • 最佳实践      │               │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
```

### 4.2 四大记忆存储

#### 4.2.1 Episodic（情景记忆）
- **内容**: 按时间顺序的事件日志
- **存储**: `memory/episodes/YYYY-MM-DD.md`
- **特点**: 只追加，不修改

#### 4.2.2 Semantic（语义记忆）
- **内容**: 知识图谱
- **存储**: 
  - `memory/graph/index.md` - 实体注册表
  - `memory/graph/entities/` - 实体文件
  - `memory/graph/relations.md` - 关系定义
- **特点**: 实体+关系的网络化存储

#### 4.2.3 Procedural（程序记忆）
- **内容**: 学习的工作流和模式
- **存储**: `memory/procedures/`
- **特点**: 可复用的操作模板

#### 4.2.4 Vault（保险库）
- **内容**: 用户固定的记忆
- **存储**: `memory/vault/`
- **特点**: 永不自动衰减

### 4.3 记忆衰减模型

```
relevance(t) = base × e^(-0.03 × days_since_access) × log2(access_count + 1) × type_weight
```

| 分数范围 | 状态 | 行为 |
|----------|------|------|
| 1.0–0.5 | Active | 完全可搜索 |
| 0.5–0.2 | Fading | 降低优先级 |
| 0.2–0.05 | Dormant | 仅显式搜索 |
| < 0.05 | Archived | 隐藏 |

**类型权重**: core=1.5, episodic=0.8, semantic=1.2, procedural=1.0, vault=∞

### 4.4 触发系统

**记住触发词**:
- "remember", "don't forget", "keep in mind"
- "note that", "important:", "for future reference"
- "save this"

**遗忘触发词**:
- "forget about", "never mind", "disregard"
- "scratch that", "remove from memory"

### 4.5 反思机制（Reflection）

```
┌─────────────────────────────────────────────────────────────────────┐
│                        反思流程                                      │
└─────────────────────────────────────────────────────────────────────┘

1. 触发确认
   ├─ 立即触发: "reflect" / "let's reflect"
   └─ 软触发: "going to sleep" → 询问用户
   │
   ▼
2. 代币请求 (可选)
   ├─ 基线: 8,000 tokens
   ├─ 额外请求: +[N] tokens
   └─ 自罚: -[N] tokens
   │
   ▼
3. 执行反思 (用户批准后)
   ├─ 范围: 上次反思以来的 episodes + decay > 0.3 的实体
   ├─ 格式: 内心独白 (第三人称)
   └─ 元素: 5-8 个随机选择
   │
   ▼
4. 记录结果
   ├─ 完整反思 → reflections/YYYY-MM-DD.md
   ├─ 摘要 → reflection-log.md
   ├─ [Self-Awareness] → IDENTITY.md
   └─ 更新 decay-scores.json
```

### 4.6 多代理记忆访问

**模型**: 共享读取，门控写入

| 代理类型 | 读取权限 | 写入权限 |
|----------|----------|----------|
| Main Agent | 所有存储 | 直接写入 |
| Sub-agent | 所有存储 | 提议 → pending-memories.md |

---

## 五、子代理与任务分发机制

### 5.1 子代理概念

子代理（Sub-agent）是专门用于处理特定任务的轻量级代理实例：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     主代理 vs 子代理                                 │
├─────────────────────────────────────────────────────────────────────┤
│  主代理 (Main Agent)           │  子代理 (Sub-agent)                │
├────────────────────────────────┼────────────────────────────────────┤
│  • 长期运行                    │  • 任务生命周期                    │
│  • 完整上下文                  │  • 有限上下文                      │
│  • 直接记忆写入                │  • 提议式记忆写入                  │
│  • 完整工具访问                │  • 受限工具访问                    │
│  • 用户直接交互                │  • 由主代理委派                    │
└────────────────────────────────┴────────────────────────────────────┘
```

### 5.2 子代理工具策略

```json
{
  "tools": {
    "subagents": {
      "tools": {
        "allow": ["read", "web_search", "web_fetch"],
        "deny": ["write", "edit", "exec", "browser"]
      }
    }
  }
}
```

### 5.3 任务分发模式

#### 5.3.1 简单委派模式
```
用户请求 ──► 主代理分析 ──► 识别子任务 ──► 创建子代理 ──► 子代理执行
                                              │
                                              ▼
用户 ◄── 整合结果 ◄── 主代理 ◄── 返回结果 ◄──┘
```

#### 5.3.2 并行任务模式
```
用户请求 ──► 主代理分析 ──┬─► 子代理 A (任务 1) ──┐
                        ├─► 子代理 B (任务 2) ──┼─► 主代理整合
                        └─► 子代理 C (任务 3) ──┘
```

#### 5.3.3 流水线模式
```
用户请求 ──► 子代理 A (研究) ──► 子代理 B (分析) ──► 子代理 C (总结) ──► 用户
```

### 5.4 会话管理

**会话键格式**:
- 直接消息: `agent:<agentId>:<mainKey>` (默认 main)
- 按发送者: `agent:<agentId>:dm:<peerId>`
- 群组: `agent:<agentId>:<channel>:<groupId>`
- 定时任务: `cron:<name>`
- Webhook: `hook:<name>`

**会话重置策略**:
- 每日重置: 默认凌晨 4:00
- 空闲重置: `idleMinutes` 配置
- 手动重置: `/new` 或 `/reset` 命令

---

## 六、实践建议和应用场景

### 6.1 配置最佳实践

#### 6.1.1 单用户配置
```json
{
  "session": {
    "dmScope": "main"
  },
  "agents": {
    "defaults": {
      "sandbox": { "mode": "non-main" }
    }
  }
}
```

#### 6.1.2 多用户/共享收件箱配置
```json
{
  "session": {
    "dmScope": "per-channel-peer",
    "identityLinks": {
      "alice": ["telegram:123456789", "discord:987654321"]
    }
  },
  "agents": {
    "list": [
      { "id": "personal", "workspace": "~/.openclaw/workspace" },
      { "id": "family", "workspace": "~/.openclaw/workspace-family" }
    ]
  }
}
```

#### 6.1.3 安全工作代理配置
```json
{
  "agents": {
    "list": [
      {
        "id": "work",
        "workspace": "~/.openclaw/workspace-work",
        "sandbox": { "mode": "all", "scope": "agent" },
        "tools": {
          "allow": ["read", "write", "apply_patch"],
          "deny": ["exec", "browser", "gateway"]
        }
      }
    ]
  }
}
```

### 6.2 技能开发建议

1. **技能结构**: `skills/<name>/SKILL.md`
2. **文档优先**: SKILL.md 是技能的核心文档
3. **本地工具**: 在 TOOLS.md 中记录环境特定的配置
4. **版本控制**: 技能应与工作空间一起版本控制

### 6.3 Hook 使用场景

| Hook | 使用场景 |
|------|----------|
| `session-memory` | 保存会话上下文到记忆 |
| `command-logger` | 审计日志记录 |
| `boot-md` | 网关启动时自动执行 BOOT.md |
| `custom-hook` | 自定义自动化流程 |

### 6.4 插件开发场景

- **新频道**: 添加自定义消息渠道
- **新工具**: 扩展代理能力
- **新认证**: 添加模型提供商认证
- **后台服务**: 持续运行的自动化任务

### 6.5 安全建议

1. **启用安全 DM 模式**（多用户场景）
2. **使用沙盒**（不可信代码/多代理）
3. **工具白名单**（限制代理能力）
4. **定期审计**: `openclaw security audit`
5. **谨慎安装插件**: 插件在 Gateway 进程中运行

### 6.6 调试技巧

```bash
# 查看代理绑定
openclaw agents list --bindings

# 检查沙盒容器
docker ps --filter "name=openclaw-sbx-"

# 查看网关日志
openclaw logs --follow

# 诊断问题
openclaw doctor

# 开发者模式
OPENCLAW_PROFILE=dev openclaw gateway --dev
```

---

## 七、学习心得

### 7.1 架构亮点

1. **模块化设计**: Gateway-Agent-Session 三层架构清晰分离关注点
2. **多代理支持**: 真正的隔离，不是简单的命名空间
3. **灵活路由**: 基于绑定的细粒度消息路由
4. **记忆系统**: 类人的多存储记忆模型
5. **安全设计**: 沙盒+工具策略+特权模式的多层防护

### 7.2 可借鉴的设计模式

1. **隔离优先**: 安全敏感操作默认隔离
2. **渐进权限**: 工具访问可以层层限制
3. **事件驱动**: Hook 系统支持灵活扩展
4. **记忆分层**: 短期上下文 vs 长期存储分离
5. **反思机制**: 定期整理和自我进化

### 7.3 应用场景展望

- **个人知识管理**: 结合认知记忆系统构建个人知识库
- **团队协作**: 多代理分别服务不同角色
- **自动化工作流**: 子代理处理并行任务
- **安全沙盒执行**: 不可信代码的安全执行环境

---

## 参考资源

- OpenClaw 官方文档: https://docs.openclaw.ai
- 认知记忆系统: `skills/cognitive-memory/SKILL.md`
- 多代理沙盒配置: `docs/multi-agent-sandbox-tools.md`
- 会话管理: `docs/concepts/session`
- Agent Loop: `docs/concepts/agent-loop`

---

*学习完成时间: 2026-02-09*  
*下次复习建议: 一周后回顾核心概念，一个月后回顾实践场景*
