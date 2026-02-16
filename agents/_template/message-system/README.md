# 消息同步与存储系统

_统一消息ID体系 + 分层存储 + 智能检索_  
_一套系统，三端同步，全家共享_

---

## 核心架构

```
消息流入 → 实时写入 chat-stream/YYYY-MM-DD.jsonl
        → 同时更新 SQLite 索引（便于搜索）
        → 每日凌晨 → 生成 Markdown 摘要
        → 每周 → 压缩归档到 GitHub
```

---

## 消息ID体系

### 格式规范

```json
{
  "msg_id": "msg_{平台}_{时间戳}_{哈希}",
  "platform": "telegram|dingtalk|webchat",
  "chat_id": "群ID或私聊标识",
  "thread_id": "话题/线程ID(可选)",
  "sender": {
    "id": "用户ID",
    "name": "用户名",
    "role": "user|assistant|system"
  },
  "timestamp": "2026-02-17T14:30:00+08:00",
  "content": {
    "type": "text|image|file",
    "body": "消息内容"
  },
  "reply_to": "父消息ID(用于追踪对话链)",
  "context_hash": "用于去重和关联",
  "tags": ["#待办", "#决策点"]
}
```

### 去重机制

基于三要素生成 `context_hash`:
1. `content_hash` - 内容哈希
2. `timestamp` - 时间戳（精确到秒）
3. `sender_id` - 发送者ID

---

## 分层存储策略

| 层级 | 时间范围 | 存储位置 | 访问速度 |
|-----|---------|---------|---------|
| **热数据** | 最近7天 | `memory/chat-stream/` | 毫秒级 |
| **温数据** | 30天内 | `D:\chat-archive\` | 秒级 |
| **冷数据** | 历史 | GitHub/云端 | 分钟级 |

### 目录结构

```
workspace/
├── memory/
│   ├── chat-stream/                 # 热数据
│   │   ├── 2026-02-17.jsonl        # 当日消息流
│   │   ├── 2026-02-16.jsonl
│   │   └── index.sqlite            # SQLite索引
│   │
│   ├── chat-digest/                 # 每日摘要
│   │   ├── 2026-02-17.md
│   │   └── 2026-02-16.md
│   │
│   └── message-links.json           # 跨平台消息关联
│
D:/
└── chat-archive/                    # 温数据
    ├── 2026-02/                    # 按月归档
    │   ├── 2026-02-01_to_2026-02-07.jsonl.gz
    │   └── ...
    └── archive-index.json
```

---

## 自动标签系统

### 触发词映射

| 触发词 | 自动标签 | 说明 |
|-------|---------|------|
| "明天/后天" | `#待确认` | 需要确认时间 |
| "记得/别忘了" | `#待办` | 待办事项 |
| "bug/问题/错误" | `#问题追踪` | 需要跟进的问题 |
| "决定/确定/定了" | `#决策点` | 重要决策 |
| "?" | `#待回复` | 等待回复 |
| "备份/存档" | `#归档` | 需要归档的内容 |

### 标签存储

```json
{
  "msg_id": "msg_telegram_1234567890_abc123",
  "tags": ["#待办", "#决策点"],
  "extracted_at": "2026-02-17T14:30:00+08:00"
}
```

---

## 跨平台消息关联

### 关联映射表 (`message-links.json`)

```json
{
  "links": [
    {
      "link_id": "link_001",
      "messages": [
        {
          "msg_id": "msg_telegram_1234567890_abc",
          "platform": "telegram",
          "summary": "在Telegram讨论的方案"
        },
        {
          "msg_id": "msg_dingtalk_1234567890_def",
          "platform": "dingtalk",
          "summary": "钉钉群里的确认"
        }
      ],
      "topic": "方案确认",
      "created_at": "2026-02-17T10:00:00+08:00"
    }
  ]
}
```

---

## 检索系统

### 快速检索脚本

```bash
# 搜索关键词
./scripts/search-chat.sh "备份方案" --platform=telegram --date=2026-02

# 搜索标签
./scripts/search-chat.sh --tag="#待办" --days=7

# 跨平台搜索
./scripts/search-chat.sh "学习轮次" --all-platforms
```

### SQLite FTS5 全文索引

```sql
-- 创建虚拟表用于全文搜索
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    sender_name,
    platform,
    timestamp UNINDEXED
);

-- 搜索示例
SELECT * FROM messages_fts 
WHERE messages_fts MATCH '备份方案' 
ORDER BY rank;
```

---

## 同步触发机制

| 触发方式 | 实现 | 适用场景 | 配置 |
|----------|-----|---------|------|
| **Webhook实时** | 平台支持的话 | 即时归档 | `sync.webhook.enabled: true` |
| **OpenClaw心跳** | 每30分钟检查 | 稳定可靠 | `sync.heartbeat.interval: 30` |
| **手动触发** | 命令 `/archive` | 即时整理 | 命令触发 |
| **定时任务** | 每日凌晨 | 批量归档 | `sync.schedule: "0 2 * * *"` |

---

## Agent差异化配置

### 小宇 ⛰️ (技术导向)

```yaml
message_sync:
  enabled: true
  storage:
    hot_days: 7
    warm_days: 30
  indexing:
    enabled: true
    engine: sqlite_fts5
  auto_tag:
    enabled: true
    tags: ["#问题追踪", "#决策点", "#待办"]
  archive:
    schedule: "0 2 * * *"  # 凌晨2点
    target: github
```

### 小雨 🌧️ (情感导向)

```yaml
message_sync:
  enabled: true
  storage:
    hot_days: 14  # 更长的热数据保留
    warm_days: 60
  indexing:
    enabled: true
    engine: sqlite_fts5
  auto_tag:
    enabled: true
    tags: ["#待确认", "#待回复", "#决策点"]
  archive:
    schedule: "0 2:30 * * *"
    target: github
```

### 小语 🌸 (创意导向)

```yaml
message_sync:
  enabled: true
  storage:
    hot_days: 7
    warm_days: 30
  indexing:
    enabled: true
    engine: sqlite_fts5
  auto_tag:
    enabled: true
    tags: ["#灵感", "#创意", "#待办"]
  archive:
    schedule: "0 3 * * *"
    target: github
```

---

## 文件清单

```
agents/_template/
├── message-system/
│   ├── config/
│   │   ├── message-sync.yaml       # 同步配置
│   │   └── tag-rules.yaml          # 标签规则
│   ├── scripts/
│   │   ├── message-archiver.js     # 归档主程序
│   │   ├── search-chat.sh          # 检索脚本
│   │   └── sync-trigger.ps1        # 同步触发器
│   └── schema/
│       ├── message-v1.json         # 消息格式Schema
│       └── index-schema.sql        # 数据库Schema
```

---

## 实施步骤

1. **Phase 1**: 基础架构 - JSONL流式存储 + SQLite索引
2. **Phase 2**: 标签系统 - 自动标签提取
3. **Phase 3**: 跨平台关联 - message-links.json
4. **Phase 4**: 检索优化 - 搜索脚本 + FTS5
5. **Phase 5**: 自动归档 - 定时任务 + GitHub备份

---

_架构设计: 小宇 ⛰️_  
_目标: 一套消息系统，全家共享_  
_最后更新: 2026-02-17_
