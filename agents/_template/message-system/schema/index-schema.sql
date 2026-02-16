-- SQLite FTS5 全文索引Schema
-- 用于消息快速检索

-- 主消息表
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    msg_id TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    chat_id TEXT,
    thread_id TEXT,
    sender_id TEXT,
    sender_name TEXT,
    sender_role TEXT,
    timestamp TEXT NOT NULL,
    content_type TEXT,
    content_body TEXT,
    reply_to TEXT,
    context_hash TEXT UNIQUE,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 全文搜索虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content_body,
    sender_name,
    platform,
    timestamp UNINDEXED,
    content='messages',
    content_rowid='id'
);

-- 标签表
CREATE TABLE IF NOT EXISTS message_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    extracted_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (msg_id) REFERENCES messages(msg_id),
    UNIQUE(msg_id, tag)
);

-- 跨平台链接表
CREATE TABLE IF NOT EXISTS message_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id TEXT UNIQUE NOT NULL,
    topic TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS message_link_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id TEXT NOT NULL,
    msg_id TEXT NOT NULL,
    platform TEXT,
    summary TEXT,
    FOREIGN KEY (link_id) REFERENCES message_links(link_id),
    FOREIGN KEY (msg_id) REFERENCES messages(msg_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_platform ON messages(platform);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_tags_msg ON message_tags(msg_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON message_tags(tag);

-- 触发器: 插入消息时自动更新FTS索引
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content_body, sender_name, platform, timestamp)
    VALUES (new.id, new.content_body, new.sender_name, new.platform, new.timestamp);
END;

-- 触发器: 删除消息时自动清理FTS索引
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content_body, sender_name, platform, timestamp)
    VALUES ('delete', old.id, old.content_body, old.sender_name, old.platform, old.timestamp);
END;
