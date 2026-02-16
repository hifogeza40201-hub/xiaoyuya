#!/usr/bin/env node
/**
 * Learning Evolver - 每日学习任务优化
 * 整合 capability-evolver 的错误分析能力到学习流程
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const WORKSPACE = process.env.WORKSPACE || 'C:\\Users\\Admin\\.openclaw\\workspace';
const MEMORY_DIR = path.join(WORKSPACE, 'memory');
const LEARNING_DIR = path.join(WORKSPACE, 'learning');
const REPORTS_DIR = path.join(WORKSPACE, 'reports');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title, icon = '📚') {
  console.log('\n' + '─'.repeat(50));
  log(`${icon}  ${title}`, 'bright');
  console.log('─'.repeat(50));
}

function getDateInfo() {
  const now = new Date();
  return {
    dateStr: now.toISOString().split('T')[0],
    dayOfWeek: now.toLocaleDateString('zh-CN', { weekday: 'long' }),
    timeStr: now.toLocaleTimeString('zh-CN'),
    hour: now.getHours()
  };
}

// ========== 学习错误模式 ==========

const LEARNING_ERROR_PATTERNS = [
  { pattern: /cron.*error|定时任务.*失败|schedule.*fail/i, type: 'critical', desc: 'Cron任务失败', category: '调度' },
  { pattern: /spawn.*error|sub-agent.*fail|agent.*error/i, type: 'error', desc: '子Agent执行失败', category: '执行' },
  { pattern: /timeout|超时|exceed.*time/i, type: 'warning', desc: '学习超时', category: '性能' },
  { pattern: /memory.*error|out of memory|内存不足/i, type: 'critical', desc: '内存不足', category: '资源' },
  { pattern: /network.*error|connection|网络|连接/i, type: 'warning', desc: '网络问题', category: '网络' },
  { pattern: /api.*error|rate.*limit|token.*exceed/i, type: 'error', desc: 'API限制', category: 'API' },
  { pattern: /file.*not.*found|目录.*不存在|path.*error/i, type: 'error', desc: '文件/路径错误', category: '文件' },
  { pattern: /parse.*error|json.*error|格式.*错误/i, type: 'warning', desc: '解析错误', category: '数据' },
  { pattern: /学习.*失败|任务.*中断|未完成/i, type: 'error', desc: '学习任务中断', category: '任务' }
];

// ========== 学习状态检查 ==========

function checkLearningSystem() {
  const results = [];
  const checks = [
    { path: LEARNING_DIR, name: '学习笔记目录' },
    { path: REPORTS_DIR, name: '学习报告目录' },
    { path: MEMORY_DIR, name: '记忆目录' }
  ];

  checks.forEach(check => {
    if (!fs.existsSync(check.path)) {
      try {
        fs.mkdirSync(check.path, { recursive: true });
        results.push({ status: 'created', name: check.name, msg: `✓ ${check.name} 已创建` });
      } catch (e) {
        results.push({ status: 'error', name: check.name, msg: `✗ ${check.name} 创建失败: ${e.message}` });
      }
    } else {
      results.push({ status: 'ok', name: check.name, msg: `✓ ${check.name} 就绪` });
    }
  });

  return results;
}

function getTodayLearningStats() {
  const { dateStr } = getDateInfo();
  const todayFile = path.join(MEMORY_DIR, `${dateStr}.md`);
  
  let stats = {
    hasRecord: false,
    learningCount: 0,
    completedTasks: 0,
    errors: 0,
    topics: []
  };

  if (!fs.existsSync(todayFile)) {
    return stats;
  }

  const content = fs.readFileSync(todayFile, 'utf-8');
  stats.hasRecord = true;
  
  // 统计学习相关条目
  stats.learningCount = (content.match(/学习|learn|study|📚|⛰️/gi) || []).length;
  stats.completedTasks = (content.match(/\[x\].*学习|\[x\].*完成/gi) || []).length;
  stats.errors = (content.match(/error|失败|❌|异常/gi) || []).length;
  
  // 提取学习主题
  const topicMatches = content.match(/学习.*：.*$/gm) || [];
  stats.topics = topicMatches.map(t => t.replace(/.*学习.*：/, '').trim()).slice(0, 5);

  return stats;
}

function getLearningHistory(days = 7) {
  const history = [];
  
  if (!fs.existsSync(MEMORY_DIR)) return history;

  const files = fs.readdirSync(MEMORY_DIR)
    .filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/))
    .sort()
    .reverse()
    .slice(0, days);

  files.forEach(f => {
    const filePath = path.join(MEMORY_DIR, f);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    history.push({
      date: f.replace('.md', ''),
      learningCount: (content.match(/学习|learn|study|📚|⛰️/gi) || []).length,
      completed: (content.match(/\[x\].*学习|\[x\].*完成/gi) || []).length,
      errors: (content.match(/error|失败|❌|异常/gi) || []).length,
      hasLearning: /学习|learn|study/i.test(content)
    });
  });

  return history;
}

// ========== 学习错误分析 ==========

function analyzeLearningErrors() {
  const errors = [];
  const recentFiles = [];

  // 扫描近3天的记录
  if (fs.existsSync(MEMORY_DIR)) {
    const files = fs.readdirSync(MEMORY_DIR)
      .filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/))
      .sort()
      .reverse()
      .slice(0, 3);

    files.forEach(f => {
      const filePath = path.join(MEMORY_DIR, f);
      const content = fs.readFileSync(filePath, 'utf-8');
      recentFiles.push({ date: f.replace('.md', ''), content });
    });
  }

  // 分析错误
  recentFiles.forEach(file => {
    const lines = file.content.split('\n');
    lines.forEach((line, idx) => {
      LEARNING_ERROR_PATTERNS.forEach(({ pattern, type, desc, category }) => {
        if (pattern.test(line)) {
          errors.push({
            date: file.date,
            line: idx + 1,
            type,
            desc,
            category,
            content: line.trim().slice(0, 100)
          });
        }
      });
    });
  });

  return errors;
}

function generateLearningFixes(errors) {
  const fixes = [];
  const categories = new Set(errors.map(e => e.category));

  categories.forEach(cat => {
    switch(cat) {
      case '调度':
        fixes.push({
          priority: '高',
          issue: 'Cron定时任务执行失败',
          fix: '检查cron配置语法、确认网关运行状态、查看任务日志',
          action: 'gateway status && cron list'
        });
        break;
      case '执行':
        fixes.push({
          priority: '高',
          issue: '子Agent执行异常',
          fix: '检查Agent配置、减少并发数、增加超时时间',
          action: '调整 maxConcurrent 参数'
        });
        break;
      case '资源':
        fixes.push({
          priority: '中',
          issue: '系统资源不足',
          fix: '清理旧日志、限制并发Agent数、优化内存使用',
          action: '清理 workspace/logs/ 目录'
        });
        break;
      case '网络':
        fixes.push({
          priority: '中',
          issue: '网络连接问题',
          fix: '检查网络状态、添加重试机制、使用离线模式',
          action: '检查网络连通性'
        });
        break;
      case 'API':
        fixes.push({
          priority: '中',
          issue: 'API调用限制或错误',
          fix: '检查API配额、降低调用频率、切换备用模型',
          action: '检查API密钥状态'
        });
        break;
      case '文件':
        fixes.push({
          priority: '低',
          issue: '文件或目录访问错误',
          fix: '检查路径权限、创建缺失目录、验证文件存在性',
          action: 'mkdir -p 缺失目录'
        });
        break;
      case '任务':
        fixes.push({
          priority: '高',
          issue: '学习任务中断或未完成',
          fix: '检查任务中断原因、简化学习内容、调整执行时间',
          action: 'review 今日学习任务'
        });
        break;
    }
  });

  return fixes.sort((a, b) => {
    const p = { '高': 3, '中': 2, '低': 1 };
    return p[b.priority] - p[a.priority];
  });
}

// ========== 学习优化建议 ==========

function generateLearningOptimizations(stats, history, errors) {
  const suggestions = [];

  // 基于今日统计
  if (!stats.hasRecord) {
    suggestions.push({
      type: 'warning',
      msg: '今日无学习记录，建议检查Cron是否正常运行'
    });
  } else if (stats.learningCount === 0) {
    suggestions.push({
      type: 'warning',
      msg: '今日有记录但无学习条目，可能需要手动触发学习'
    });
  } else if (stats.errors > 0) {
    suggestions.push({
      type: 'error',
      msg: `今日学习出现 ${stats.errors} 个错误，建议优先处理`
    });
  }

  // 基于历史趋势
  const learningDays = history.filter(h => h.hasLearning).length;
  if (history.length >= 3 && learningDays < history.length * 0.5) {
    suggestions.push({
      type: 'warning',
      msg: `近${history.length}天只有${learningDays}天有学习记录，学习频率偏低`
    });
  }

  // 基于错误分析
  if (errors.length > 5) {
    suggestions.push({
      type: 'error',
      msg: `近3天累积 ${errors.length} 个错误，系统稳定性需要关注`
    });
  }

  // 学习质量建议
  if (stats.completedTasks === 0 && stats.hasRecord) {
    suggestions.push({
      type: 'info',
      msg: '今日暂无已完成的学习任务，可以启动新的学习轮次'
    });
  }

  return suggestions;
}

// ========== 报告生成 ==========

function generateLearningReport(stats, history, errors, fixes, suggestions) {
  const report = [];

  // 今日状态
  if (stats.hasRecord) {
    if (stats.errors === 0) {
      report.push(`✓ 今日学习正常，无错误记录`);
    } else {
      report.push(`! 今日学习有 ${stats.errors} 个问题需处理`);
    }
  } else {
    report.push(`! 今日暂无学习记录`);
  }

  // 频率统计
  const learningDays = history.filter(h => h.hasLearning).length;
  report.push(`→ 近${history.length}天学习打卡: ${learningDays}天`);

  // 错误汇总
  if (errors.length === 0) {
    report.push(`✓ 系统运行平稳`);
  } else {
    const critical = errors.filter(e => e.type === 'critical').length;
    if (critical > 0) {
      report.push(`! 发现 ${critical} 个严重错误`);
    } else {
      report.push(`○ 发现 ${errors.length} 个一般问题`);
    }
  }

  return report;
}

// ========== 主函数 ==========

async function runLearningCheck() {
  const { dateStr, dayOfWeek, timeStr, hour } = getDateInfo();

  console.log('\n');
  log('═══════════════════════════════════════════', 'magenta');
  log('     📚 小宇每日学习优化检查', 'bright');
  log('═══════════════════════════════════════════', 'magenta');
  log(`${dateStr} ${timeStr} | ${dayOfWeek}`, 'dim');

  // 1. 系统检查
  logSection('学习系统状态', '📁');
  const system = checkLearningSystem();
  system.forEach(s => log(s.msg, s.status === 'error' ? 'red' : 'green'));

  // 2. 今日学习统计
  logSection('今日学习概况', '📝');
  const stats = getTodayLearningStats();
  if (stats.hasRecord) {
    log(`学习条目: ${stats.learningCount} | 完成任务: ${stats.completedTasks} | 错误: ${stats.errors}`);
    if (stats.topics.length > 0) {
      log(`今日主题: ${stats.topics.join('、')}`, 'cyan');
    }
  } else {
    log('暂无今日学习记录', 'yellow');
  }

  // 3. 学习历史
  logSection('学习打卡 (近7天)', '📊');
  const history = getLearningHistory(7);
  if (history.length > 0) {
    history.forEach(h => {
      const icon = h.hasLearning ? '✓' : '○';
      const color = h.hasLearning ? 'green' : 'dim';
      const bar = h.hasLearning ? '█'.repeat(Math.min(h.learningCount, 10)) + '░'.repeat(Math.max(0, 10 - h.learningCount)) : '░░░░░░░░░░';
      log(`${icon} ${h.date} ${bar} ${h.hasLearning ? h.learningCount + '项' : '无'}`, color);
    });
  } else {
    log('无历史数据', 'dim');
  }

  // 4. 错误分析
  logSection('学习错误分析 (近3天)', '🔍');
  const errors = analyzeLearningErrors();
  if (errors.length > 0) {
    log(`发现 ${errors.length} 个问题:`, 'yellow');
    const grouped = {};
    errors.forEach(e => {
      if (!grouped[e.category]) grouped[e.category] = [];
      grouped[e.category].push(e);
    });
    
    Object.entries(grouped).slice(0, 3).forEach(([cat, items]) => {
      log(`  [${cat}] ${items.length}个`, items[0].type === 'critical' ? 'red' : 'yellow');
      items.slice(0, 2).forEach(e => {
        log(`    - ${e.desc}: ${e.content.slice(0, 40)}...`, 'dim');
      });
    });
  } else {
    log('✓ 系统运行平稳，无错误记录', 'green');
  }

  // 5. 修复建议
  if (errors.length > 0) {
    logSection('修复建议', '🔧');
    const fixes = generateLearningFixes(errors);
    fixes.slice(0, 5).forEach(f => {
      const pColor = f.priority === '高' ? 'red' : f.priority === '中' ? 'yellow' : 'dim';
      log(`[${f.priority}] ${f.issue}`, pColor);
      log(`  → ${f.fix}`, 'dim');
    });
  }

  // 6. 优化建议
  logSection('学习优化建议', '💡');
  const suggestions = generateLearningOptimizations(stats, history, errors);
  if (suggestions.length > 0) {
    suggestions.forEach(s => {
      const icon = s.type === 'error' ? '!' : s.type === 'warning' ? '○' : '→';
      const color = s.type === 'error' ? 'red' : s.type === 'warning' ? 'yellow' : 'cyan';
      log(`${icon} ${s.msg}`, color);
    });
  } else {
    log('✓ 学习状态良好，继续保持！', 'green');
  }

  // 7. 执行报告
  logSection('学习执行报告', '📋');
  const report = generateLearningReport(stats, history, errors, [], suggestions);
  report.forEach(r => log(r));

  // 总结
  console.log('\n' + '═'.repeat(50));
  const hasIssues = errors.length > 0 || suggestions.some(s => s.type === 'error');
  const summary = hasIssues 
    ? '检查完成。发现问题，建议优先处理后再继续学习。📚'
    : '检查完成。学习系统运行良好，继续保持！📚';
  log(summary, hasIssues ? 'yellow' : 'bright');
  console.log('═'.repeat(50) + '\n');

  // 返回检查结果（供其他脚本调用）
  return {
    stats,
    errors: errors.length,
    hasIssues,
    timestamp: new Date().toISOString()
  };
}

// CLI
const args = process.argv.slice(2);
if (args[0] === 'check') {
  runLearningCheck()
    .then(result => {
      if (result.hasIssues) {
        process.exit(1); // 有问题的退出码
      }
    })
    .catch(err => {
      console.error('检查失败:', err.message);
      process.exit(2);
    });
} else {
  console.log(`
📚 小宇学习优化检查工具

用法:
  node learning-evolver.js check    执行学习系统检查

功能:
  • 学习追踪：每日学习统计
  • 打卡分析：7天学习趋势
  • 错误检测：Cron/Agent/资源问题
  • 修复建议：自动生成解决方案
  • 优化建议：学习质量提升
`);
}

module.exports = { runLearningCheck, analyzeLearningErrors };
