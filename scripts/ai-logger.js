const fs = require('fs');
const path = require('path');

/**
 * AI操作日志系统
 * 记录所有重要操作，确保安全可追溯
 */

const LOG_DIR = path.join(process.env.USERPROFILE || process.env.HOME, '.openclaw', 'workspace', 'logs');

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

function getLogFile() {
  const date = new Date().toISOString().split('T')[0];
  return path.join(LOG_DIR, `ai-actions-${date}.log`);
}

function formatTimestamp() {
  return new Date().toISOString();
}

/**
 * 记录AI操作
 * @param {string} action - 操作类型
 * @param {string} details - 操作详情
 * @param {string} result - 操作结果
 */
function logAction(action, details, result = 'pending') {
  const logEntry = {
    timestamp: formatTimestamp(),
    action,
    details,
    result,
    session: process.env.OPENCLAW_SESSION || 'unknown'
  };
  
  const logLine = JSON.stringify(logEntry) + '\n';
  fs.appendFileSync(getLogFile(), logLine);
  
  // 同时输出到控制台（便于调试）
  console.log(`[AI-LOG] ${action}: ${details}`);
}

/**
 * 记录软件安装
 */
function logSoftwareInstall(software, version, source) {
  logAction('SOFTWARE_INSTALL', `${software}@${version} from ${source}`, 'started');
}

/**
 * 记录服务管理
 */
function logServiceAction(service, action) {
  logAction('SERVICE_MANAGE', `${action} ${service}`, 'started');
}

/**
 * 记录文件操作
 */
function logFileOperation(operation, path, size) {
  logAction('FILE_OPERATION', `${operation}: ${path} (${size || 'unknown'} bytes)`);
}

/**
 * 记录网络请求
 */
function logNetworkRequest(url, method, status) {
  logAction('NETWORK_REQUEST', `${method} ${url}`, status);
}

/**
 * 获取今日日志统计
 */
function getTodayStats() {
  const logFile = getLogFile();
  if (!fs.existsSync(logFile)) {
    return { total: 0, actions: {} };
  }
  
  const content = fs.readFileSync(logFile, 'utf8');
  const lines = content.trim().split('\n').filter(line => line);
  
  const stats = { total: lines.length, actions: {} };
  
  lines.forEach(line => {
    try {
      const entry = JSON.parse(line);
      const action = entry.action;
      stats.actions[action] = (stats.actions[action] || 0) + 1;
    } catch (e) {
      // 忽略解析错误
    }
  });
  
  return stats;
}

/**
 * 生成日报
 */
function generateDailyReport() {
  const stats = getTodayStats();
  const date = new Date().toISOString().split('T')[0];
  
  const report = {
    date,
    summary: `今日共执行 ${stats.total} 项操作`,
    breakdown: stats.actions,
    generatedAt: formatTimestamp()
  };
  
  const reportPath = path.join(LOG_DIR, `daily-report-${date}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  return report;
}

module.exports = {
  logAction,
  logSoftwareInstall,
  logServiceAction,
  logFileOperation,
  logNetworkRequest,
  getTodayStats,
  generateDailyReport
};

// 如果直接运行，显示今日统计
if (require.main === module) {
  console.log('=== 今日AI操作统计 ===');
  console.log(JSON.stringify(getTodayStats(), null, 2));
}
