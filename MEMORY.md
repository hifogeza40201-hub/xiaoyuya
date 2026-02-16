

## 数据备份方案 (2026-02-17 确认执行)

**三重备份策略** ✅

| 位置 | 用途 | 保留周期 | 状态 |
|------|------|----------|------|
| 本地 C盘 | 工作区实时使用 | 持续 | ✅ |
| D盘 | 本地冗余备份 | 30天历史 | ✅ |
| GitHub | 远程容灾 | 365天 | ✅ |

### D盘备份结构

```
D:\critical-backup\          ← 快速恢复（总是最新）
├── openclaw-config/
│   ├── dingtalk.yaml
│   └── telegram-config.json
├── memory/
│   ├── MEMORY.md
│   └── IDENTITY.md
└── workspace/
    └── 重要项目文件

D:\backup-2026-02-17\         ← 历史版本（按日期）
D:\backup-2026-02-16\
...
```

### 备份内容清单

**重要文件（D:\critical-backup\）：**
- `MEMORY.md` - 长期记忆
- `IDENTITY.md` - 身份定义
- `SOUL.md` - 灵魂核心
- `USER.md` - 用户信息
- `dingtalk.yaml` - 钉钉配置（AgentID: 4267754811）
- `telegram-config.json` - 电报配置（群组: -5173207194）
- `gateway.yaml` - 网关配置
- `HEARTBEAT.md` - 每日任务

**完整备份（D:\backup-YYYY-MM-DD\）：**
- 整个 workspace/ 目录
- ~/.openclaw/ 配置
- 研究成果和项目文件

### 自动化脚本

**位置**: `scripts/daily-backup.ps1`

**功能**:
1. 复制关键文件到 `D:\critical-backup\`（覆盖更新）
2. 创建带日期的新备份 `D:\backup-YYYY-MM-DD\`
3. 清理30天前的旧备份
4. GitHub 推送（如配置了token）

**执行频率**: 每日一次（通过HEARTBEAT任务触发）

### 备份验证

- 每周抽查一次备份完整性
- 记录备份日志到 `logs/backup.log`
- 异常时通过Telegram报警

---

_最后更新: 2026-02-17
