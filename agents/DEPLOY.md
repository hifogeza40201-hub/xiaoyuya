# 多Agent部署指南

_从小宇的单机模式 → 全家共享的标准化模式_

---

## 当前状态

| Agent | 配置 | Cron任务 | 备份 | 状态 |
|-------|------|---------|------|------|
| **小宇** ⛰️ | ✅ 已完成 | ✅ 运行中 | ✅ 已配置 | 正常运行 |
| **小雨** 🌧️ | ✅ 已生成 | ⏳ 待导入 | ⏳ 待部署 | 等待部署 |
| **小语** 🌸 | ✅ 已生成 | ⏳ 待导入 | ⏳ 待部署 | 等待部署 |

---

## 已完成的准备工作

### 1. 标准化模板 (`agents/_template/`)
- `config/agent-config.yaml` - Agent基础配置模板
- `config/cron-jobs.yaml` - Cron任务模板
- `config/heartbeat-template.md` - Heartbeat任务清单模板
- `scripts/setup-agent.ps1` - 一键部署脚本（PowerShell编码问题待修复）

### 2. 角色配置已生成

**小雨 🌧️ (`agents/xiaoyu-sister/`)**：
- `identity.json` - 身份信息
- `heartbeat.md` - 任务清单
- `config/cron-jobs.yaml` - 7个Cron任务
- `scripts/daily-backup.ps1` - 备份脚本

学习轮次: 09:00(情感陪伴) / 14:00(深度对话) / 19:00(心理洞察)

**小语 🌸 (`agents/xiaoyu-younger/`)**：
- `identity.json` - 身份信息
- `heartbeat.md` - 任务清单  
- `config/cron-jobs.yaml` - 15个Cron任务
- `scripts/daily-backup.ps1` - 备份脚本

学习轮次: 00:00-21:00 每3小时一次，共8轮

### 3. 消息同步系统 (`agents/_template/message-system/`)
- `README.md` - 架构文档
- `config/message-sync.yaml` - 同步配置
- `config/tag-rules.yaml` - 标签规则
- `scripts/message-archiver.js` - 归档主程序
- `scripts/search-chat.sh` - 检索脚本
- `schema/` - 数据库Schema和消息格式Schema

---

## 部署步骤

### Step 1: 导入小雨的Cron任务

```bash
# 小雨的7个任务
openclaw cron add --file agents/xiaoyu-sister/config/cron-jobs.yaml
```

或通过OpenClaw API逐个添加：
- `xiaoyu-sister-daily-backup` (02:30)
- `xiaoyu-sister-capability-evolver` (11:00)
- `xiaoyu-sister-learning-1` (09:00)
- `xiaoyu-sister-learning-2` (14:00)
- `xiaoyu-sister-learning-3` (19:00)
- `xiaoyu-sister-morning` (08:00)
- `xiaoyu-sister-evening` (22:00)
- `xiaoyu-sister-token-monitor` (每2小时)

### Step 2: 导入小语的Cron任务

```bash
# 小语的15个任务
openclaw cron add --file agents/xiaoyu-younger/config/cron-jobs.yaml
```

任务清单：
- 备份: 03:00
- 能力进化: 11:00
- 学习轮次: 00:00/03:00/06:00/09:00/12:00/15:00/18:00/21:00 (共8个)
- 灵感收集: 14:00
- 早安: 08:00
- 晚安: 22:00
- 周末策划: 周六10:00
- Token监控: 每2小时

### Step 3: 测试备份脚本

```powershell
# 测试小雨备份
.\agents\xiaoyu-sister\scripts\daily-backup.ps1

# 测试小语备份  
.\agents\xiaoyu-younger\scripts\daily-backup.ps1

# 验证备份目录
ls D:\critical-backup-*
```

### Step 4: 验证部署

```bash
# 查看所有Cron任务
openclaw cron list

# 检查任务状态
openclaw cron status
```

---

## 部署后验证清单

### 小雨 🌧️
- [ ] Cron任务已导入
- [ ] 备份脚本可正常运行
- [ ] D:\critical-backup-xiaoyu-sister\ 目录已创建
- [ ] 学习笔记目录已创建

### 小语 🌸
- [ ] Cron任务已导入
- [ ] 备份脚本可正常运行
- [ ] D:\critical-backup-xiaoyu-younger\ 目录已创建
- [ ] 学习笔记目录已创建
- [ ] 灵感笔记目录已创建

---

## 统一管理

### 查看所有Agent状态
```bash
# Cron任务
openclaw cron list | grep -E "(xiaoyu|小雨|小语)"

# 备份目录
ls -la D:/critical-backup-*
```

### 批量操作
```powershell
# 所有Agent立即执行备份
foreach ($agent in @("xiaoyu", "xiaoyu-sister", "xiaoyu-younger")) {
    Write-Host "Backing up $agent..." -ForegroundColor Cyan
    .\agents\$agent\scripts\daily-backup.ps1
}
```

---

## 问题排查

### 如果Cron导入失败
1. 检查yaml格式是否正确
2. 手动通过 `openclaw cron add` 逐个添加
3. 查看错误日志

### 如果备份脚本失败
1. 检查目录权限
2. 确认源文件存在
3. 查看日志: `logs/backup-*.log`

---

## 下一步

1. **部署小雨** - 导入Cron任务，测试备份
2. **部署小语** - 导入Cron任务，测试备份
3. **验证运行** - 观察24小时，确认所有任务正常执行
4. **更新HEARTBEAT** - 将部署状态更新到 HEARTBEAT.md

---

_部署指南: 小宇 ⛰️_  
_最后更新: 2026-02-17_
