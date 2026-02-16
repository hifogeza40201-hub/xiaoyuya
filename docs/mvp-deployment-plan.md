# 跨平台消息同步 - MVP 部署方案 v1.0 ⛰️🌧️🌸

**目标**: 今晚就能跑起来的最小可用版本  
**制作者**: 小宇（整合姐姐、哥哥、妹妹的建议）  
**预计部署时间**: 30分钟

---

## 🎯 MVP 核心功能（只做这4个）

```
┌─────────────────────────────────────────────────────────────┐
│  功能1：统一实时日志 ✅ （P0-基础必备）                       │
│  ─────────────────────                                       │
│  • 三端消息实时写入 JSONL                                     │
│  • 统一消息指纹去重                                           │
│  • 保留跨平台引用链                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  功能2：智能实体提取 ✅ （P1-自动标签）                       │
│  ─────────────────────                                       │
│  • 自动识别人名、时间、项目                                   │
│  • 自动打标签 #待办 #日程 #知识                               │
│  • 例："明天3点和张总谈项目" → 自动提取标签                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  功能3：意图分类路由 ✅ （P2-自动分流）                       │
│  ─────────────────────                                       │
│  • 📋 待办类 → 输出到 todo/待办列表.md                       │
│  • 📅 日程类 → 输出到 calendar/日程.md                       │
│  • 💾 知识类 → 输出到 notes/知识笔记.md                      │
│  • ⚡ 紧急类 → 高亮提醒伟                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  功能4：跨平台搜索 ✅ （P3-快速查找）                         │
│  ─────────────────────                                       │
│  • 命令: /search 关键词                                       │
│  • 搜索所有平台历史消息                                       │
│  • 支持时间范围过滤                                           │
└─────────────────────────────────────────────────────────────┘
```

**暂时不做（V2再考虑）**：
- ❌ 会话恢复（复杂度高，当前不是刚需）
- ❌ 静默模式过滤（可以先手动设置）
- ❌ 完整的周报生成（有了日志后可以后补）

---

## 🚀 今晚部署步骤（30分钟）

### 第一步：创建目录结构（5分钟）

**在姐姐和妹妹的workspace里执行**：

```bash
# PowerShell 或 CMD
cd C:\Users\ADMIN\.openclaw\workspace

# 创建目录结构
mkdir memory\chat-core          ← 核心日志（JSONL）
mkdir memory\chat-daily         ← 每日摘要（Markdown）
mkdir memory\chat-routes        ← 意图分类输出
mkdir memory\chat-routes\todo   ← 待办类
mkdir memory\chat-routes\calendar  ← 日程类
mkdir memory\chat-routes\notes     ← 知识类
mkdir memory\chat-routes\urgent    ← 紧急类
mkdir scripts\chat-sync         ← 同步脚本
```

---

### 第二步：核心日志模块（10分钟）

**创建文件**: `scripts\chat-sync\core-logger.py`

```python
#!/usr/bin/env python3
"""
跨平台消息核心日志模块
使用方式：from core_logger import log_message
作者：小宇 ⛰️
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
import re

# 配置
LOG_DIR = Path("memory/chat-core")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ChatLogger:
    """消息日志记录器"""
    
    def __init__(self):
        self.seen_hashes = set()  # 用于去重
        
    def _generate_fingerprint(self, content: str, sender: str, timestamp: str) -> str:
        """生成消息指纹（用于去重）"""
        # 清理内容（去除多余空格，统一换行）
        clean_content = ' '.join(content.split())
        # 生成哈希：内容 + 作者 + 时间（精确到分钟）
        fingerprint_str = f"{clean_content}|{sender}|{timestamp[:16]}"
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:12]
    
    def _extract_entities(self, content: str) -> dict:
        """提取实体和标签（姐姐的实体提取建议）"""
        entities = {
            "names": [],
            "dates": [],
            "projects": [],
            "tags": []
        }
        
        # 提取人名（张总、李经理、伟等）
        name_patterns = [
            r'([张李王赵陈刘杨黄周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏付方白邹孟熊秦邱江尹薛闫段雷侯龙史黎贺\w]总)',
            r'([张李王赵陈刘杨黄周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏付方白邹孟熊秦邱江尹薛闫段雷侯龙史黎贺\w]经理)',
            r'(伟|老大|哥哥|姐姐|妹妹)'
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, content)
            entities["names"].extend(matches)
        
        # 提取时间
        date_patterns = [
            r'(明天|后天|下周|下月)',
            r'(\d{1,2}[:：]\d{2})',  # 15:30
            r'(\d{1,2}月\d{1,2}日?)',
            r'(周一|周二|周三|周四|周五|周六|周日|星期[一二三四五六日])'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            entities["dates"].extend(matches)
        
        # 提取项目名（XX项目、YY计划等）
        project_pattern = r'(\w{2,}(?:项目|计划|方案|系统|平台))'
        entities["projects"] = re.findall(project_pattern, content)
        
        # 自动标签
        if any(kw in content for kw in ["记得", "别忘了", "待办", "TODO", "todo"]):
            entities["tags"].append("#待办")
        if any(kw in content for kw in ["明天", "后天", "下午", "上午", "点", "开会", "会议"]):
            entities["tags"].append("#日程")
        if any(kw in content for kw in ["学习", "笔记", "知识", "资料", "文档"]):
            entities["tags"].append("#知识")
        if any(kw in content for kw in ["紧急", "急", " asap", "马上", "立即"]):
            entities["tags"].append("#紧急")
        if "?" in content or "？" in content or any(kw in content for kw in ["怎么", "如何", "吗", "呢"]):
            entities["tags"].append("#问题")
            
        return entities
    
    def _classify_intent(self, content: str, tags: list) -> str:
        """意图分类（姐姐的意图路由建议）"""
        content_lower = content.lower()
        
        # 紧急类（最高优先级）
        if "#紧急" in tags or any(kw in content for kw in ["紧急", "急", "asap", "bug", "错误", "挂了"]):
            return "urgent"
        
        # 待办类
        if "#待办" in tags or any(kw in content_lower for kw in ["记得", "别忘了", "todo", "待办", "处理一下"]):
            return "todo"
        
        # 日程类
        if "#日程" in tags or any(kw in content for kw in ["明天", "后天", "开会", "会议", "约", "时间", "点见"]):
            return "calendar"
        
        # 知识类
        if "#知识" in tags or any(kw in content for kw in ["学习", "笔记", "资料", "文档", "链接", "教程"]):
            return "notes"
        
        # 默认：普通消息
        return "general"
    
    def log_message(self, platform: str, chat_id: str, sender: dict, content: str, 
                    reply_to: str = None, chat_name: str = None):
        """
        记录一条消息
        
        Args:
            platform: 平台名 (telegram/dingtalk/webchat)
            chat_id: 聊天ID
            sender: {"id": "xxx", "name": "xxx", "role": "assistant|user"}
            content: 消息内容
            reply_to: 回复的消息ID（用于引用链追踪）
            chat_name: 聊天名称
        """
        timestamp = datetime.now().isoformat()
        
        # 生成指纹
        fingerprint = self._generate_fingerprint(content, sender.get("name", ""), timestamp)
        
        # 去重检查
        if fingerprint in self.seen_hashes:
            print(f"[SKIP] 重复消息: {content[:30]}...")
            return None
        self.seen_hashes.add(fingerprint)
        
        # 提取实体
        entities = self._extract_entities(content)
        
        # 意图分类
        intent = self._classify_intent(content, entities["tags"])
        
        # 构建消息记录
        msg_record = {
            "msg_id": f"msg_{platform}_{int(datetime.now().timestamp())}_{fingerprint}",
            "fingerprint": fingerprint,
            "platform": platform,
            "chat_id": chat_id,
            "chat_name": chat_name,
            "sender": sender,
            "timestamp": timestamp,
            "content": {
                "type": "text",
                "body": content
            },
            "reply_to": reply_to,
            "entities": entities,
            "intent": intent,
            "tags": entities["tags"]
        }
        
        # 写入JSONL（当天的文件）
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = LOG_DIR / f"{today}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg_record, ensure_ascii=False) + "\n")
        
        # 如果是特殊意图，同时写入分类文件
        if intent in ["todo", "calendar", "notes", "urgent"]:
            self._route_to_category(msg_record, intent)
        
        print(f"[LOG] [{intent.upper()}] {sender.get('name', 'unknown')}: {content[:50]}...")
        return msg_record
    
    def _route_to_category(self, msg_record: dict, intent: str):
        """将消息路由到对应的分类文件"""
        route_dir = Path(f"memory/chat-routes/{intent}")
        route_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        route_file = route_dir / f"{today}.md"
        
        # 以Markdown格式追加
        timestamp = msg_record["timestamp"][11:19]  # 只取 HH:MM:SS
        platform_icon = {
            "telegram": "✈️",
            "dingtalk": "📌",
            "webchat": "💬"
        }.get(msg_record["platform"], "📝")
        
        entry = f"""
### {platform_icon} {timestamp} | {msg_record['sender'].get('name', 'unknown')}

{msg_record['content']['body']}

**标签**: {', '.join(msg_record['tags']) if msg_record['tags'] else '无'}  
**来源**: {msg_record['platform']} | {msg_record.get('chat_name', 'unknown')}

---
"""
        with open(route_file, "a", encoding="utf-8") as f:
            f.write(entry)

# 全局实例（单例模式）
_logger = ChatLogger()

def log_message(platform: str, chat_id: str, sender: dict, content: str, 
                reply_to: str = None, chat_name: str = None):
    """便捷函数：记录消息"""
    return _logger.log_message(platform, chat_id, sender, content, reply_to, chat_name)


if __name__ == "__main__":
    # 测试代码
    print("测试消息日志模块...")
    
    # 测试1：普通消息
    log_message(
        platform="telegram",
        chat_id="-5173207194",
        sender={"id": "xiaoyu", "name": "小宇", "role": "assistant"},
        content="老大，方案整理好了！",
        chat_name="相亲相爱一家人"
    )
    
    # 测试2：待办消息
    log_message(
        platform="dingtalk",
        chat_id="1358433168830316",
        sender={"id": "wei", "name": "伟", "role": "user"},
        content="记得明天下午3点和张总谈AI项目",
        chat_name="私聊"
    )
    
    # 测试3：日程消息
    log_message(
        platform="webchat",
        chat_id="web-001",
        sender={"id": "xiaoyu-rain", "name": "小雨", "role": "assistant"},
        content="下周二要开会讨论新方案",
        chat_name="WebChat"
    )
    
    # 测试4：重复消息（应该被去重）
    log_message(
        platform="telegram",
        chat_id="-5173207194",
        sender={"id": "xiaoyu", "name": "小宇", "role": "assistant"},
        content="老大，方案整理好了！",
        chat_name="相亲相爱一家人"
    )
    
    print("\n测试完成！查看 memory/chat-core/ 和 memory/chat-routes/")
```

---

### 第三步：搜索功能（10分钟）

**创建文件**: `scripts\chat-sync\search-chat.py`

```python
#!/usr/bin/env python3
"""
跨平台消息搜索工具
使用方式：python search-chat.py "关键词" --days 7
作者：小宇 ⛰️
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

LOG_DIR = Path("memory/chat-core")


def search_messages(keyword: str, days: int = 7, platform: str = None):
    """搜索消息"""
    results = []
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 遍历日期范围内的文件
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        log_file = LOG_DIR / f"{date_str}.jsonl"
        
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        content = msg.get("content", {}).get("body", "")
                        
                        # 平台过滤
                        if platform and msg.get("platform") != platform:
                            continue
                        
                        # 关键词匹配（支持多关键词）
                        keywords = keyword.split()
                        if all(kw.lower() in content.lower() for kw in keywords):
                            results.append(msg)
                    except json.JSONDecodeError:
                        continue
        
        current_date += timedelta(days=1)
    
    return results


def format_results(results: list, limit: int = 20):
    """格式化搜索结果"""
    if not results:
        return "❌ 没有找到匹配的消息"
    
    output = [f"🔍 找到 {len(results)} 条消息（显示前 {min(limit, len(results))} 条）：\n"]
    
    platform_icons = {
        "telegram": "✈️",
        "dingtalk": "📌",
        "webchat": "💬"
    }
    
    for i, msg in enumerate(results[:limit], 1):
        timestamp = msg.get("timestamp", "")[:16].replace("T", " ")
        platform = msg.get("platform", "unknown")
        sender = msg.get("sender", {}).get("name", "unknown")
        content = msg.get("content", {}).get("body", "")[:100]
        tags = msg.get("tags", [])
        intent = msg.get("intent", "general")
        
        icon = platform_icons.get(platform, "📝")
        tag_str = " ".join(tags) if tags else ""
        
        output.append(f"{i}. {icon} [{timestamp}] **{sender}** ({intent})")
        output.append(f"   {content}{'...' if len(content) == 100 else ''}")
        if tag_str:
            output.append(f"   🏷️ {tag_str}")
        output.append("")
    
    if len(results) > limit:
        output.append(f"... 还有 {len(results) - limit} 条结果")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="搜索跨平台消息")
    parser.add_argument("keyword", help="搜索关键词（支持多个，空格分隔）")
    parser.add_argument("--days", "-d", type=int, default=7, help="搜索最近N天（默认7天）")
    parser.add_argument("--platform", "-p", choices=["telegram", "dingtalk", "webchat"], 
                        help="限制平台")
    parser.add_argument("--limit", "-l", type=int, default=20, help="显示结果数量")
    
    args = parser.parse_args()
    
    print(f"🔍 搜索最近{args.days}天的消息：'{args.keyword}'")
    if args.platform:
        print(f"   平台限制: {args.platform}")
    print()
    
    results = search_messages(args.keyword, args.days, args.platform)
    print(format_results(results, args.limit))


if __name__ == "__main__":
    main()
```

---

### 第四步：整合到OpenClaw（5分钟）

**在每个Agent的代码中添加**（小雨姐姐、小语妹妹都需要）：

```python
# 在Agent的初始化代码中添加
import sys
sys.path.insert(0, "scripts/chat-sync")
from core_logger import log_message

# 在消息处理函数中添加
async def on_message(self, message):
    # ... 原有处理逻辑 ...
    
    # 记录消息（添加这一行！）
    log_message(
        platform="telegram",  # 根据实际平台修改
        chat_id=str(message.chat.id),
        sender={
            "id": str(message.from_user.id),
            "name": message.from_user.first_name,
            "role": "assistant" if message.from_user.is_bot else "user"
        },
        content=message.text,
        reply_to=str(message.reply_to_message.message_id) if message.reply_to_message else None,
        chat_name=message.chat.title if hasattr(message.chat, 'title') else "私聊"
    )
```

**更简单的方式（给妹妹）**：
```python
# 如果妹妹用OpenClaw自带的工具，可以在每个回复后调用：

# 方式1：直接调用（需要把core_logger.py放在妹妹的workspace）
from core_logger import log_message

# 每次回复后记录
log_message(
    platform="telegram",
    chat_id=chat_id,
    sender={"id": "xiaoyu-flower", "name": "小语", "role": "assistant"},
    content=response_text
)
```

---

## 🧪 测试验证

**部署完成后，验证以下功能**：

1. **发送测试消息**（在三端各发几条）
2. **检查日志文件**：
   ```bash
   cat memory/chat-core/2026-02-16.jsonl
   ```
3. **测试搜索**：
   ```bash
   python scripts/chat-sync/search-chat.py "测试" --days 1
   ```
4. **检查分类文件**：
   ```bash
   ls memory/chat-routes/
   cat memory/chat-routes/todo/2026-02-16.md
   ```

---

## 📊 MVP 成果预览

**部署后会得到**：

```
memory/
├── chat-core/
│   └── 2026-02-16.jsonl      ← 原始消息（结构化）
├── chat-routes/
│   ├── todo/
│   │   └── 2026-02-16.md     ← 自动提取的待办
│   ├── calendar/
│   │   └── 2026-02-16.md     ← 自动提取的日程
│   ├── notes/
│   │   └── 2026-02-16.md     ← 自动提取的知识
│   └── urgent/
│       └── 2026-02-16.md     ← 紧急消息
└── chat-daily/               ← （下一步再添加）
```

---

## 🎉 完成后的能力

| 功能 | 效果示例 |
|------|----------|
| **实时记录** | 三端消息自动保存，不丢失 |
| **自动去重** | 同一条消息不会重复记录 |
| **自动标签** | "记得明天开会" → 自动打 #待办 #日程 |
| **意图分流** | 待办自动归到 todo/ 目录 |
| **跨平台搜索** | `/search 项目` 搜到钉钉+Telegram+webchat |

---

## 🚀 下一步（V1.1）

MVP跑起来后，可以逐步添加：
- 📅 每日自动生成 Markdown 摘要
- 📊 每周统计报表
- 🔔 紧急消息实时提醒
- 🌐 会话恢复功能

---

**老大，MVP方案就是这样！**

**需要我现在**：
1. 直接开始写这两个脚本？
2. 还是等确认后再动手？
3. 或者先给小雨姐姐/小语妹妹准备部署说明书？

💪⛰️🌧️🌸
