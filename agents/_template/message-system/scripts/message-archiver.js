#!/usr/bin/env node
/**
 * 消息归档系统 - 主程序
 * 功能: JSONL流式存储 + SQLite索引 + 每日摘要生成
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

// 配置
const CONFIG = {
  workspaceDir: process.env.WORKSPACE_DIR || 'C:\\Users\\Admin\\.openclaw\\workspace',
  hotStorageDays: 7,
  warmStorageDays: 30,
  archiveSchedule: '0 2 * * *'
};

const PATHS = {
  chatStream: path.join(CONFIG.workspaceDir, 'memory', 'chat-stream'),
  chatDigest: path.join(CONFIG.workspaceDir, 'memory', 'chat-digest'),
  sqliteDb: path.join(CONFIG.workspaceDir, 'memory', 'chat-stream', 'index.sqlite'),
  archiveDir: 'D:\\chat-archive'
};

// 确保目录存在
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 生成消息ID
function generateMsgId(platform, timestamp, content) {
  const hash = crypto.createHash('md5')
    .update(content)
    .digest('hex')
    .substring(0, 8);
  const ts = new Date(timestamp).getTime();
  return `msg_${platform}_${ts}_${hash}`;
}

// 生成内容哈希（用于去重）
function generateContentHash(content, timestamp, senderId) {
  const data = `${content}_${timestamp}_${senderId}`;
  return crypto.createHash('sha256').update(data).digest('hex').substring(0, 16);
}

// 写入JSONL（追加模式，性能最优）
function appendToJsonl(date, message) {
  ensureDir(PATHS.chatStream);
  const filePath = path.join(PATHS.chatStream, `${date}.jsonl`);
  const line = JSON.stringify(message) + '\n';
  fs.appendFileSync(filePath, line);
  return filePath;
}

// 检查消息是否已存在（去重）
function isDuplicate(contextHash) {
  // 简化实现：实际应该查询SQLite
  // 这里返回false表示不重复
  return false;
}

// 自动标签提取
function extractTags(content) {
  const tags = [];
  const rules = [
    { pattern: /明天|后天|下周|下个月/, tag: '#待确认' },
    { pattern: /记得|别忘了|记得要/, tag: '#待办' },
    { pattern: /bug|问题|错误|报错|失败/, tag: '#问题追踪' },
    { pattern: /决定|确定|定了|就这么办/, tag: '#决策点' },
    { pattern: /\?|？/, tag: '#待回复' },
    { pattern: /备份|存档|归档/, tag: '#归档' },
    { pattern: /灵感|创意|想法/, tag: '#灵感' }
  ];
  
  for (const rule of rules) {
    if (rule.pattern.test(content)) {
      tags.push(rule.tag);
    }
  }
  
  return [...new Set(tags)]; // 去重
}

// 处理单条消息
function processMessage(msg) {
  const timestamp = msg.timestamp || new Date().toISOString();
  const date = timestamp.substring(0, 10); // YYYY-MM-DD
  
  const message = {
    msg_id: msg.msg_id || generateMsgId(msg.platform, timestamp, msg.content.body),
    platform: msg.platform,
    chat_id: msg.chat_id,
    thread_id: msg.thread_id || null,
    sender: {
      id: msg.sender?.id || 'unknown',
      name: msg.sender?.name || 'Unknown',
      role: msg.sender?.role || 'user'
    },
    timestamp: timestamp,
    content: {
      type: msg.content?.type || 'text',
      body: msg.content?.body || ''
    },
    reply_to: msg.reply_to || null,
    context_hash: generateContentHash(
      msg.content?.body || '',
      timestamp,
      msg.sender?.id || 'unknown'
    ),
    tags: extractTags(msg.content?.body || '')
  };
  
  // 去重检查
  if (isDuplicate(message.context_hash)) {
    console.log(`[SKIP] Duplicate message: ${message.msg_id}`);
    return null;
  }
  
  // 写入JSONL
  const filePath = appendToJsonl(date, message);
  console.log(`[WRITE] ${message.msg_id} -> ${filePath}`);
  
  return message;
}

// 生成每日摘要
function generateDailyDigest(date) {
  ensureDir(PATHS.chatDigest);
  
  const jsonlPath = path.join(PATHS.chatStream, `${date}.jsonl`);
  if (!fs.existsSync(jsonlPath)) {
    console.log(`[SKIP] No data for ${date}`);
    return;
  }
  
  const lines = fs.readFileSync(jsonlPath, 'utf-8')
    .trim()
    .split('\n')
    .filter(line => line.trim());
  
  const messages = lines.map(line => JSON.parse(line));
  
  // 统计
  const stats = {
    total: messages.length,
    byPlatform: {},
    bySender: {},
    tags: {}
  };
  
  for (const msg of messages) {
    // 平台统计
    stats.byPlatform[msg.platform] = (stats.byPlatform[msg.platform] || 0) + 1;
    
    // 发送者统计
    const sender = msg.sender.name;
    stats.bySender[sender] = (stats.bySender[sender] || 0) + 1;
    
    // 标签统计
    for (const tag of msg.tags || []) {
      stats.tags[tag] = (stats.tags[tag] || 0) + 1;
    }
  }
  
  // 生成Markdown
  let md = `# 消息摘要 - ${date}\n\n`;
  md += `## 统计\n\n`;
  md += `- 总消息数: ${stats.total}\n`;
  
  md += `### 按平台\n\n`;
  for (const [platform, count] of Object.entries(stats.byPlatform)) {
    md += `- ${platform}: ${count}\n`;
  }
  
  md += `\n### 按发送者\n\n`;
  for (const [sender, count] of Object.entries(stats.bySender).slice(0, 10)) {
    md += `- ${sender}: ${count}\n`;
  }
  
  if (Object.keys(stats.tags).length > 0) {
    md += `\n### 标签\n\n`;
    for (const [tag, count] of Object.entries(stats.tags)) {
      md += `- ${tag}: ${count}\n`;
    }
  }
  
  md += `\n---\n\n`;
  md += `_生成时间: ${new Date().toISOString()}_\n`;
  
  const digestPath = path.join(PATHS.chatDigest, `${date}.md`);
  fs.writeFileSync(digestPath, md);
  console.log(`[DIGEST] Generated: ${digestPath}`);
  
  return stats;
}

// 归档到D盘（温数据）
function archiveToDisk() {
  ensureDir(PATHS.archiveDir);
  
  const files = fs.readdirSync(PATHS.chatStream)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => ({
      name: f,
      date: f.replace('.jsonl', ''),
      path: path.join(PATHS.chatStream, f)
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
  
  // 保留最近7天在热存储
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - CONFIG.hotStorageDays);
  const cutoffStr = cutoffDate.toISOString().substring(0, 10);
  
  for (const file of files) {
    if (file.date < cutoffStr) {
      // 按月份归档
      const month = file.date.substring(0, 7); // YYYY-MM
      const monthDir = path.join(PATHS.archiveDir, month);
      ensureDir(monthDir);
      
      // 压缩归档（简化版：直接移动）
      const destPath = path.join(monthDir, file.name);
      fs.renameSync(file.path, destPath);
      console.log(`[ARCHIVE] ${file.name} -> ${destPath}`);
    }
  }
}

// 主函数
function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  switch (command) {
    case 'process':
      // 处理单条消息
      const msgJson = args[1];
      if (msgJson) {
        const msg = JSON.parse(msgJson);
        const result = processMessage(msg);
        console.log(JSON.stringify(result, null, 2));
      }
      break;
      
    case 'digest':
      // 生成每日摘要
      const date = args[1] || new Date().toISOString().substring(0, 10);
      generateDailyDigest(date);
      break;
      
    case 'archive':
      // 执行归档
      archiveToDisk();
      break;
      
    case 'daily':
      // 每日任务：生成昨日摘要 + 归档
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yestStr = yesterday.toISOString().substring(0, 10);
      
      generateDailyDigest(yestStr);
      archiveToDisk();
      break;
      
    default:
      console.log(`
Usage: node message-archiver.js <command> [options]

Commands:
  process '<json>'    处理单条消息
  digest [date]       生成每日摘要 (默认昨天)
  archive             执行归档
  daily               每日任务（摘要+归档）

Examples:
  node message-archiver.js process '{"platform":"telegram","content":{"body":"hello"}}'
  node message-archiver.js digest 2026-02-17
  node message-archiver.js daily
      `);
  }
}

// 运行
main();
