# 小雨的自动化工作流

## 📁 目录结构

```
workspace/
├── scripts/                    # 自动化脚本
│   ├── config.js              # 配置文件
│   ├── daily-news-aggregator.js   # 每日信息聚合
│   ├── system-health-monitor.js   # 系统健康监控
│   ├── auto-backup-check.js       # 自动备份检查
│   └── learning-tracker.js        # 学习进度追踪
├── reports/                    # 生成的报告
│   ├── daily-tech-brief-YYYY-MM-DD.md
│   └── learning-weekly-YYYY-MM-DD.md
├── data/                       # 数据存储
│   ├── learning/              # 学习记录数据
│   ├── health-monitor.log     # 健康监控日志
│   └── backup-check.log       # 备份检查日志
└── setup-windows-scheduler.ps1 # Windows计划任务设置脚本
```

## 🚀 快速开始

### 1. 安装依赖

所有脚本使用Node.js内置模块，无需额外安装依赖。

确保已安装 Node.js (建议 v16+):
```bash
node --version
```

### 2. 配置钉钉机器人 (可选)

如需系统异常时发送钉钉通知:

1. 在钉钉群中创建自定义机器人
2. 复制 Webhook 地址
3. 设置环境变量:
```powershell
[Environment]::SetEnvironmentVariable("DINGTALK_WEBHOOK", "https://oapi.dingtalk.com/robot/send?access_token=xxx", "User")
```

### 3. 设置 Windows 计划任务

**方法1: 使用 PowerShell 脚本 (推荐)**
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-windows-scheduler.ps1
```

**方法2: 手动设置**

打开 任务计划程序 (taskschd.msc)，创建以下任务:

| 任务名称 | 触发器 | 操作 |
|---------|--------|------|
| DailyNews | 每天 8:00 | `node "C:\Users\Admin\.openclaw\workspace\scripts\daily-news-aggregator.js"` |
| HealthMonitor | 每4小时 | `node "C:\Users\Admin\.openclaw\workspace\scripts\system-health-monitor.js"` |
| BackupCheck | 每天 22:00 | `node "C:\Users\Admin\.openclaw\workspace\scripts\auto-backup-check.js"` |
| WeeklyLearning | 每周日 21:00 | `node "C:\Users\Admin\.openclaw\workspace\scripts\learning-tracker.js" week` |

## 📜 脚本说明

### 1. 每日信息聚合 (daily-news-aggregator.js)

**功能:**
- 自动收集 Hacker News 热门文章
- 获取 GitHub Trending 项目
- 汇总 AI 新闻源

**输出:** `reports/daily-tech-brief-YYYY-MM-DD.md`

**手动运行:**
```bash
node scripts/daily-news-aggregator.js
```

### 2. 系统健康监控 (system-health-monitor.js)

**功能:**
- 检查 OpenClaw 网关状态
- 监控磁盘空间使用
- 监控内存使用
- 监控 CPU 负载
- 异常时发送钉钉通知

**输出:** 
- 控制台日志
- `data/health-check-YYYY-MM-DD.json`
- `data/health-monitor.log`

**手动运行:**
```bash
node scripts/system-health-monitor.js
```

### 3. 自动备份检查 (auto-backup-check.js)

**功能:**
- 检查 Git 仓库同步状态
- 自动提交未提交的更改
- 自动推送到远程仓库

**输出:**
- `data/backup-report-YYYY-MM-DD.md`
- `data/backup-check.log`

**手动运行:**
```bash
node scripts/auto-backup-check.js
```

### 4. 学习进度追踪 (learning-tracker.js)

**功能:**
- 记录每天学习时间和内容
- 按分类统计
- 生成周报

**用法:**
```bash
# 添加学习记录
node scripts/learning-tracker.js add "编程开发" "学习Node.js异步编程" 60

# 交互式添加
node scripts/learning-tracker.js interactive

# 查看今日记录
node scripts/learning-tracker.js today

# 生成本周报告
node scripts/learning-tracker.js week
```

**输出:**
- `data/learning/YYYY-MM-DD.json` - 每日数据
- `reports/learning-weekly-YYYY-MM-DD.md` - 周报

## ⚙️ 配置说明

编辑 `scripts/config.js` 修改配置:

```javascript
module.exports = {
    healthMonitor: {
        // 钉钉 webhook
        dingtalkWebhook: 'your-webhook-url',
        
        // 报警阈值
        thresholds: {
            diskUsagePercent: 85,
            memoryUsagePercent: 90
        }
    },
    
    backupCheck: {
        // 要监控的仓库
        repos: [
            'C:\\Users\\Admin\\.openclaw\\workspace'
        ],
        autoPush: true
    }
};
```

## 📝 手动运行所有脚本

```powershell
# 每日简报
node scripts/daily-news-aggregator.js

# 系统健康检查
node scripts/system-health-monitor.js

# 备份检查
node scripts/auto-backup-check.js

# 学习记录
node scripts/learning-tracker.js interactive
```

## 🔧 故障排除

### 脚本无法运行
- 检查 Node.js 是否安装: `node --version`
- 检查文件路径是否正确

### 钉钉通知不生效
- 确认 Webhook URL 正确
- 检查环境变量是否设置: `$env:DINGTALK_WEBHOOK`

### Git 推送失败
- 检查 Git 身份配置
- 确认有远程仓库权限
- 检查网络连接

## 📊 查看报告

所有报告保存在 `reports/` 目录:
- `daily-tech-brief-*.md` - 每日科技简报
- `learning-weekly-*.md` - 学习周报

## 🎉 完成!

自动化工作流已配置完成！系统将按设定时间自动运行各任务。
