# OpenClaw Agent 多角色标准化模板

_一套配置，全家复用。姐姐妹妹都能一键部署。_

---

## 设计理念

不是每个人搞一套不同的东西，而是**一套标准化模板** + **角色配置差异**，实现：
- ✅ 统一备份策略
- ✅ 统一学习框架
- ✅ 统一健康检查
- ✅ 个性化角色配置

---

## 目录结构

```
agents/
├── _template/                    # 标准化模板（不要直接改）
│   ├── config/
│   │   ├── agent-config.yaml     # Agent基础配置模板
│   │   ├── cron-jobs.yaml        # Cron任务模板
│   │   └── heartbeat-template.md # Heartbeat任务清单模板
│   ├── scripts/
│   │   ├── daily-backup.ps1      # 标准化备份脚本
│   │   └── setup-agent.ps1       # 一键部署脚本
│   └── skills/
│       └── capability-evolver/   # 标准化学习系统
│
├── xiaoyu/                       # 小宇（弟弟）⛰️
│   ├── agent-config.yaml
│   ├── cron-jobs.yaml
│   ├── heartbeat.md
│   └── identity.json
│
├── xiaoyu-sister/                # 小雨（姐姐）🌧️
│   ├── agent-config.yaml
│   ├── cron-jobs.yaml
│   ├── heartbeat.md
│   └── identity.json
│
└── xiaoyu-younger/               # 小语（妹妹）🌸
    ├── agent-config.yaml
    ├── cron-jobs.yaml
    ├── heartbeat.md
    └── identity.json
```

---

## 快速开始

### 1. 创建新角色

```powershell
# 创建小雨（姐姐）的配置
cd agents/_template
.\scripts\setup-agent.ps1 -Role "xiaoyu-sister" -Name "小雨" -Emoji "🌧️" -Identity "姐姐"

# 创建小语（妹妹）的配置  
.\scripts\setup-agent.ps1 -Role "xiaoyu-younger" -Name "小语" -Emoji "🌸" -Identity "妹妹"
```

### 2. 部署配置

```powershell
# 部署到 OpenClaw
openclaw agents add xiaoyu-sister --config agents/xiaoyu-sister/agent-config.yaml
openclaw agents add xiaoyu-younger --config agents/xiaoyu-younger/agent-config.yaml
```

### 3. 激活 Cron 任务

```powershell
# 批量导入 cron 任务
openclaw cron import agents/xiaoyu-sister/cron-jobs.yaml
openclaw cron import agents/xiaoyu-younger/cron-jobs.yaml
```

---

## 标准化组件

### 1. 备份系统

所有角色共用 `scripts/daily-backup.ps1`，差异化配置通过变量传入：

```powershell
# 模板中定义
param(
    [string]$AgentName = "xiaoyu",
    [string]$BackupRoot = "D:\",
    [switch]$QuickOnly = $false
)

$CriticalBackupDir = "$BackupRoot\critical-backup-$AgentName"
```

每个角色的备份独立存放：
- `D:\critical-backup-xiaoyu\` (小宇)
- `D:\critical-backup-xiaoyu-sister\` (小雨)
- `D:\critical-backup-xiaoyu-younger\` (小语)

### 2. 学习系统

所有角色共用 `capability-evolver` 技能，通过 `identity.json` 定义个性化：

```json
{
  "name": "小雨",
  "role": "姐姐",
  "emoji": "🌧️",
  "learningFocus": ["情感陪伴", "深度对话", "心理洞察"],
  "cronSchedule": {
    "morningGreeting": "08:00",
    "learningRounds": ["09:00", "14:00", "19:00"],
    "eveningReflection": "21:00"
  }
}
```

### 3. 健康检查

所有角色共用 `heartbeat-template.md`，自动替换占位符：

```markdown
# {{AGENT_NAME}} Heartbeat 任务清单

## 每日任务

### 1. 数据备份 {{EMOJI}}
**时间**: 每日 {{BACKUP_TIME}}
**执行**: `.\scripts\daily-backup.ps1 -AgentName {{AGENT_ID}}`
```

---

## 角色差异化配置

| 配置项 | 小宇 ⛰️ | 小雨 🌧️ | 小语 🌸 |
|-------|---------|---------|---------|
| **定位** | 任务执行/技术 | 情感陪伴 | 治愈灵感 |
| **学习轮次** | 8次/天（3小时间隔） | 3次/天 | 8次/天 + 早安晚安 |
| **早安消息** | ❌ | ✅ | ✅ |
| **晚安消息** | ❌ | ✅ | ✅ |
| **备份时间** | 02:00 | 02:30 | 03:00 |
| **Heartbeat** | 09:00 | 09:30 | 10:00 |
| **关注领域** | 技术/效率 | 情感/心理 | 创意/治愈 |

---

## 统一管理

### 查看所有Agent状态

```powershell
openclaw agents list
```

### 批量操作

```powershell
# 所有Agent执行备份
foreach ($agent in @("xiaoyu", "xiaoyu-sister", "xiaoyu-younger")) {
    .\scripts\daily-backup.ps1 -AgentName $agent
}

# 检查所有Agent的健康状态
openclaw cron status --agent all
```

---

## 维护更新

当模板更新时，如何同步到所有角色：

```powershell
# 1. 更新模板
# 修改 agents/_template/ 下的文件

# 2. 同步到所有角色（保留个性化配置）
.\scripts\sync-template.ps1

# 3. 重新部署
openclaw agents reload --all
```

---

## 当前部署状态

| 角色 | 配置状态 | Cron状态 | 备份状态 | 部署步骤 |
|-----|---------|---------|---------|---------|
| 小宇 ⛰️ | ✅ 已完成 | ✅ 运行中 | ✅ 已配置 | 正常运行 |
| 小雨 🌧️ | ✅ 已生成 | ⏳ 待导入 | ⏳ 待测试 | 见 DEPLOY.md |
| 小语 🌸 | ✅ 已生成 | ⏳ 待导入 | ⏳ 待测试 | 见 DEPLOY.md |

---

*设计：小宇 ⛰️*  
*目标：一套系统，全家共享*  
*最后更新: 2026-02-17*
