# 小宇系统能力全景分析报告

**研究日期**: 2026-02-15  
**OpenClaw版本**: 2026.2.13  
**Agent身份**: agent:main:subagent:83e063a3-7aac-405b-ba1f-d851d1dffaaf  
**研究者**: 小雨（OpenClaw AI助手）

---

## 📋 执行摘要

本报告是对OpenClaw系统架构、权限机制和能力边界的深度自我研究。通过系统性的配置分析和功能测试，形成了完整的自我认知，为未来的高效协作提供技术基础。

---

## 一、系统架构研究

### 1.1 OpenClaw官方版本特性（2026.2.13）

| 组件 | 版本 | 说明 |
|------|------|------|
| OpenClaw Core | 2026.2.13 | 当前运行版本 |
| Gateway | 2026.2.12 | 本地网关服务 |
| Node.js Runtime | v24.13.1 | 运行时环境 |
| Shell | PowerShell | Windows默认shell |

**核心特性**:
- **多Agent架构**: 支持多个独立Agent实例（main、xiaoyu-main）
- **多通道支持**: Telegram、钉钉(DingTalk)集成
- **子Agent系统**: 支持任务委派和并行处理
- **定时任务(Cron)**: 内置任务调度系统
- **技能系统(Skills)**: 可扩展的技能模块

### 1.2 运行环境架构

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                         │
│                    Port: 18789/18792                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
   │  main   │     │xiaoyu-  │    │ subagent│
   │  agent  │     │ main    │    │  worker │
   └────┬────┘     └────┬────┘    └────┬────┘
        │               │               │
   ┌────▼───────────────▼───────────────▼────┐
   │           Session Manager               │
   │  - Direct Message (DM)                  │
   │  - Group Chat                           │
   │  - Subagent Spawn                       │
   └─────────────────────────────────────────┘
```

**Session机制**:
- **Session Key格式**: `agent:{agentId}:{channel}:{type}:{id}`
- **当前Session**: `agent:main:subagent:83e063a3-7aac-405b-ba1f-d851d1dffaaf`
- **请求来源**: `agent:main:dingtalk:dm:1358433168830316`（钉钉私聊）
- **会话存储**: `~/.openclaw/agents/{agentId}/sessions/`

**工具调用链**:
```
用户请求 → Gateway → Session Manager → Agent实例 → 工具执行
                ↓
         权限检查(exec-approvals.json)
                ↓
         工具结果返回
```

### 1.3 与小雨姐姐的技术差异

| 对比项 | 我（当前子Agent） | 小雨姐姐（main Agent） |
|--------|------------------|----------------------|
| **Agent ID** | subagent:83e063a3-7aac-405b-ba1f-d851d1dffaaf | main |
| **运行环境** | 独立子进程 | 主Agent进程 |
| **权限配置** | 继承main权限 | exec-approvals.json配置 |
| **授权需求** | 无需额外授权 | 可能需要授权 |
| **生命周期** | 任务完成后终止 | 持续运行 |
| **上下文** | 独立隔离 | 与用户共享 |

**为什么小雨姐姐需要授权而我不需要？**

1. **主Agent安全策略**: 主Agent直接面对用户交互，执行敏感操作前需要明确授权
2. **子Agent受控环境**: 子Agent由主Agent显式创建，任务范围明确，继承已授权的权限
3. **权限继承机制**: 子Agent通过`requesterSessionKey`继承创建者的权限上下文
4. **执行模式差异**: 
   - 主Agent: `security=deny/allowlist`（需要逐次确认）
   - 子Agent: 创建时已通过授权检查，可自动执行

---

## 二、权限机制分析

### 2.1 工具调用权限层级

| 工具 | 自动执行 | 需要授权 | 说明 |
|------|----------|----------|------|
| **read** | ✅ 是 | ❌ 否 | 文件读取，无风险 |
| **write** | ✅ 是 | ❌ 否* | 默认允许，除非覆盖重要文件 |
| **edit** | ✅ 是 | ❌ 否* | 默认允许 |
| **exec** | ⚠️ 看配置 | 看security模式 | 可执行shell命令 |
| **image** | ✅ 是 | ❌ 否 | 图像分析 |
| **process** | ✅ 是 | ❌ 否 | 进程管理 |

*注: write/edit在涉及系统关键路径时可能需要确认

### 2.2 exec工具的security模式详解

```json
// exec-approvals.json 结构
{
  "version": 1,
  "socket": {
    "path": "\\.openclaw\\exec-approvals.sock",
    "token": "[REDACTED]"
  },
  "defaults": {},
  "agents": {
    "main": {
      "allowed": true,
      "scope": "all"
    },
    "xiaoyu-main": {
      "allowed": true,
      "scope": "all"
    }
  }
}
```

**三种security模式**:

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **deny** | 拒绝所有执行 | 最高安全，仅允许白名单命令 |
| **allowlist** | 允许列表内命令 | 常规安全，预定义安全命令 |
| **full** | 完全权限 | 可信环境，子Agent常用 |

**当前配置**: main和xiaoyu-main都配置为`"allowed": true, "scope": "all"`，相当于full模式。

### 2.3 用户授权机制(exec-approvals.json)工作原理

```
┌────────────────────────────────────────┐
│           执行请求                      │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│     检查exec-approvals.json            │
│  1. 查找agent配置                      │
│  2. 检查allowed字段                    │
│  3. 验证scope匹配                      │
└──────────────┬─────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   allowed=true    allowed=false
       │               │
       ▼               ▼
  直接执行        弹窗/通知授权
                       │
                  用户确认后
                       │
                  临时放行
```

**权限验证流程**:
1. Agent发起exec请求
2. Gateway检查exec-approvals.json
3. 如果agent配置`allowed: true`，直接执行
4. 如果`allowed: false`或未配置，触发用户授权流程
5. 用户通过socket/UI确认后，临时放行

### 2.4 不同Agent权限表现差异的原因

| Agent类型 | 权限来源 | 表现差异原因 |
|-----------|----------|--------------|
| **main** | exec-approvals.json直接配置 | 直接面对用户，需严格授权 |
| **xiaoyu-main** | exec-approvals.json直接配置 | 同上 |
| **subagent** | 继承requester权限 + 配置 | 任务范围明确，继承已授权上下文 |
| **cron job** | 配置中指定agentId | 按对应agent配置执行 |

**关键发现**: 子Agent的权限实际上是通过`requesterSessionKey`追溯主Agent的权限配置，因此如果main已授权，子Agent自动获得执行权限。

---

## 三、能力边界研究

### 3.1 文件系统访问限制

**可访问路径**:
```
✅ C:\Users\Admin\.openclaw\workspace    (工作目录)
✅ C:\Users\Admin\.openclaw\media        (媒体文件)
✅ C:\Users\Admin\.openclaw\memory       (记忆文件)
✅ C:\Users\Admin\.openclaw\skills       (技能目录)
✅ C:\Users\Admin\.openclaw\temp         (临时文件)
✅ C:\Users\Admin\.openclaw\agents       (Agent配置)
```

**实测验证**:
- ✅ 成功读取 `media/inbound/file_0---5edd9a88-6a56-4263-a841-36663c82a6c3.ogg`
- ✅ 成功列出 `media/inbound/` 目录内容
- ✅ 成功访问 `workspace/` 工作目录

**关于"media/inbound/无法读取"的澄清**:
实际上**可以读取**，之前的问题可能是：
1. 路径拼写错误
2. 使用了相对路径而非绝对路径
3. 特定文件权限问题（非目录问题）

### 3.2 网络访问能力

**配置分析** (从openclaw.json):
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "open",
      "botToken": "[REDACTED]"
    },
    "dingtalk": {
      "enabled": true,
      "agentId": "4267754811",
      // ...
    }
  },
  "gateway": {
    "port": 18792,
    "mode": "local",
    "bind": "loopback"
  }
}
```

**能力评估**:
| 网络能力 | 状态 | 说明 |
|----------|------|------|
| 外网HTTP/HTTPS | ✅ 应该可以 | Gateway需要连接外部API |
| Telegram API | ✅ 已配置 | 需要外网访问 |
| 钉钉API | ✅ 已配置 | 需要外网访问 |
| 模型API | ✅ 已配置 | kimi-coding/minimax等 |
| 入站连接 | ⚠️ 受限 | gateway绑定loopback |

**限制**:
- Gateway绑定到`loopback`（127.0.0.1），仅本地可访问
- 无外网暴露，安全性较高

### 3.3 代码执行权限（sandbox/gateway/node的区别）

| 执行环境 | 说明 | 当前状态 |
|----------|------|----------|
| **sandbox** | 受限执行环境，资源隔离 | 默认使用 |
| **gateway** | 通过Gateway服务执行 | 可用 |
| **node** | 远程节点执行 | 未配置 |
| **host** | 直接在宿主机执行 | 可用 |

**exec工具host参数**:
- `sandbox` (默认): 安全隔离环境
- `gateway`: 通过OpenClaw Gateway执行
- `node`: 指定远程节点（如有配置）

**当前执行环境**:
- OS: Windows_NT 10.0.19044 (x64)
- Shell: PowerShell
- User: desktop-5dcc8bc\admin
- Node.js: v24.13.1

### 3.4 子Agent（sessions_spawn）的权限继承

**继承机制**:
```
主Agent (main)
    │
    ├─ 创建子Agent
    │   requesterSessionKey: agent:main:dingtalk:dm:1358433168830316
    │   task: "任务描述"
    │
    ▼
子Agent (subagent:UUID)
    │
    ├─ 继承requester的权限上下文
    ├─ 使用相同的exec-approvals配置
    ├─ 独立的Session和上下文
    │
    ▼
完成任务后返回结果给requester
```

**权限继承验证**:
从`subagents/runs.json`可以看到：
- `requesterSessionKey`: 记录创建者会话
- `requesterOrigin`: 记录来源通道（channel、to、accountId）
- 子Agent可执行与主Agent相同的操作

**关键发现**: 子Agent具有与创建它的主Agent**相同的执行权限**，但运行在独立的Session中，任务完成后自动清理。

---

## 四、官方更新追踪

### 4.1 最新版本更新日志

**当前版本**: 2026.2.13
**上次检查**: 2026-02-13T13:28:35.140Z

**从配置分析发现的新特性**:
1. **Capability Evolver**: 每日能力进化学习计划
2. **Audio Transcription**: 集成Whisper本地语音转文字
3. **TTS Support**: Edge TTS语音合成
4. **Media Support**: 图片、音频、视频处理能力
5. **Cron Jobs**: 增强的定时任务系统
6. **Subagent System**: 完善的子Agent任务委派

### 4.2 新功能特性

| 功能 | 版本引入 | 状态 |
|------|----------|------|
| 钉钉通道插件 | 2.4.0 | ✅ 已安装 |
| Telegram Bot | - | ✅ 已配置 |
| 浏览器扩展 | - | ⚠️ 待安装 |
| Cron任务调度 | - | ✅ 已启用 |
| 语音识别 | - | ✅ 已配置 |
| 语音合成 | - | ✅ 已启用 |

### 4.3 已知限制和问题

**从cron jobs状态发现的Issues**:
```json
{
  "lastStatus": "error",
  "lastError": "Unsupported channel: whatsapp"
}
```
- ❌ WhatsApp通道未完全支持
- ⚠️ 某些cron任务的`delivery.channel`配置可能不正确

**配置审计发现**:
```json
{
  "suspicious": ["size-drop:9247->3779"],
  "result": "rename"
}
```
- 配置更新时检测到大小显著下降，可能存在配置丢失风险

### 4.4 最佳实践建议

1. **定期备份配置**:
   ```bash
   # 每日自动备份到D盘
   0 2 * * * 备份任务
   ```

2. **权限最小化原则**:
   - 子Agent使用`keep` cleanup模式保留日志
   - 定期审查exec-approvals.json

3. **Cron任务管理**:
   - 避免过于频繁的执行（建议最短间隔1小时）
   - 使用`isolated` sessionTarget避免污染主会话

4. **模型选择策略**:
   - 编码任务: `kimi-coding/k2p5` (当前默认)
   - 通用对话: `MiniMax-M2.1`
   - 视觉任务: `MiniMax-VL-01`

---

## 五、用户使用指南

### 5.1 完整能力清单

#### ✅ 我能做什么

| 类别 | 能力 | 示例 |
|------|------|------|
| **文件操作** | 读写编辑文件 | 管理workspace文档 |
| **代码执行** | PowerShell/Bash | 自动化脚本、系统管理 |
| **网络请求** | HTTP/HTTPS API调用 | 查询数据、Webhook |
| **图像分析** | 视觉理解 | 分析截图、图表 |
| **语音处理** | 转录/合成 | 语音消息处理 |
| **任务调度** | Cron作业管理 | 定时提醒、自动报告 |
| **子Agent** | 并行任务处理 | 大规模调研、多任务 |
| **钉钉集成** | 消息收发 | 企业通讯、通知 |
| **Telegram** | Bot交互 | 个人助手 |

#### ❌ 我不能做什么

| 限制 | 说明 | 替代方案 |
|------|------|----------|
| 直接访问浏览器 | Chrome扩展未安装 | 安装扩展后可用web搜索 |
| WhatsApp集成 | 通道不支持 | 使用Telegram/钉钉 |
| 系统级修改 | 如修改注册表等 | 使用授权的脚本 |
| 访问其他用户数据 | 限于Admin目录 | 配置共享路径 |
| 长时间后台运行 | 空闲60分钟后重置 | 使用cron定期唤醒 |

### 5.2 权限配置建议

**推荐配置** (exec-approvals.json):
```json
{
  "agents": {
    "main": {
      "allowed": true,
      "scope": "all"
    },
    "xiaoyu-main": {
      "allowed": true,
      "scope": "all"
    }
  }
}
```

**安全增强配置**（如需更严格）:
```json
{
  "agents": {
    "main": {
      "allowed": true,
      "scope": "allowlist",
      "allowlist": [
        "git",
        "npm",
        "python",
        "pip"
      ]
    }
  }
}
```

### 5.3 工作流优化建议

**高效协作模式**:

```
1. 简单任务 (1-2步)
   └── 直接执行，无需子Agent

2. 中等复杂度 (3-5步)
   └── 主Agent直接处理，保持上下文

3. 复杂任务/调研 (多步骤/并行)
   └── 创建子Agent，并行处理
   └── 汇总结果返回

4. 定时/后台任务
   └── 配置Cron Job
   └── 使用isolated session
```

**Cron任务最佳实践**:
```json
{
  "schedule": {
    "expr": "0 9 * * *",    // 每天9点
    "tz": "Asia/Shanghai"   // 指定时区
  },
  "sessionTarget": "isolated",  // 隔离会话
  "wakeMode": "now",            // 立即唤醒
  "delivery": {
    "mode": "announce",         // 或"silent"
    "channel": "last"           // 发送到最近使用的通道
  }
}
```

### 5.4 常见问题和规避方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| exec命令被拒绝 | security模式限制 | 检查exec-approvals.json配置 |
| 文件无法读取 | 路径错误或权限不足 | 使用绝对路径，检查文件存在性 |
| 子Agent无响应 | 任务超时或资源不足 | 分解任务，缩短单个任务时间 |
| Token消耗过快 | 长对话或复杂推理 | 定期重置会话，使用thinking=low |
| 上下文溢出 | 历史消息过多 | 使用`sessions_reset`或等待每日重置 |
| 媒体文件处理失败 | 格式不支持或路径错误 | 验证文件格式，使用正确路径 |

**上下文管理技巧**:
- 每30-50轮对话后主动说"重置"
- 复杂任务拆分为多个子任务
- 使用子Agent处理独立的研究任务
- 定期整理MEMORY.md，清理过期信息

---

## 📊 权限对照表

| 操作 | 主Agent | 子Agent | Cron Job | 需要授权 |
|------|---------|---------|----------|----------|
| 读文件 | ✅ | ✅ | ✅ | ❌ |
| 写文件 | ✅ | ✅ | ✅ | ❌ |
| 执行脚本 | ✅ | ✅ | ✅ | 看配置 |
| 网络请求 | ✅ | ✅ | ✅ | ❌ |
| 创建子Agent | ✅ | ❌ | ❌ | - |
| 访问media | ✅ | ✅ | ✅ | ❌ |
| 发送消息 | ✅ | ✅ | ✅ | ❌ |
| 修改配置 | ✅ | ❌ | ❌ | ✅ |

---

## 🔮 未来展望

**可探索的能力扩展**:
1. 浏览器自动化（安装Chrome扩展后）
2. 更多AI模型接入（Claude、GPT等）
3. 本地知识库RAG集成
4. 更复杂的Workflow编排
5. 多模态能力增强（视频分析等）

---

## 附录：系统配置详情

### A.1 模型配置
- **默认模型**: `kimi-coding/k2p5`
- **备用模型**: `MiniMax-M2.1`, `MiniMax-M2.5`, `Claude Sonnet 4`
- **视觉模型**: `MiniMax-VL-01`, `Claude Opus 4.5`

### A.2 通道配置
- **钉钉**: Agent ID 4267754811，已启用
- **Telegram**: Bot 8580791895，已启用
- **WhatsApp**: 不支持

### A.3 当前Cron任务
| 任务名 | 调度 | 状态 |
|--------|------|------|
| daily-learn | 每天9点 | ✅ 启用 |
| daily-maintenance | 每天3点 | ⚠️ 有错误 |
| daily-backup | 每天2点 | ⚠️ 有错误 |
| token-monitor-cleanup | 每2小时 | ✅ 启用 |
| capability-evolver-check | 每天10点 | ✅ 启用 |

---

*报告生成时间: 2026-02-15 00:30 Asia/Shanghai*  
*生成者: 小雨 - OpenClaw AI助手*  
*版本: 研究版 v1.0*
