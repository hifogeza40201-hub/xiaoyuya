#!/usr/bin/env node
/**
 * Capability Evolver - 小宇每日任务执行检查 + 错误自修复
 * 任务导向型AI的自我优化工具（增强版）
 */

const fs = require('fs');
const path = require('path');

const WORKSPACE = process.env.WORKSPACE || 'C:\\Users\\Admin\\.openclaw\\workspace';
const MEMORY_DIR = path.join(WORKSPACE, 'memory');
const TASKS_DIR = path.join(MEMORY_DIR, 'tasks');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '─'.repeat(50));
  log(`⛰️  ${title}`, 'bright');
  console.log('─'.repeat(50));
}

function getDateInfo() {
  const now = new Date();
  return {
    dateStr: now.toISOString().split('T')[0],
    dayOfWeek: now.toLocaleDateString('zh-CN', { weekday: 'long' }),
    timeStr: now.toLocaleTimeString('zh-CN')
  };
}

// ========== 任务系统 ==========

function checkTaskSystem() {
  const results = [];
  const checks = [
    { path: MEMORY_DIR, name: '记忆目录' },
    { path: TASKS_DIR, name: '任务目录' }
  ];

  checks.forEach(check => {
    if (!fs.existsSync(check.path)) {
      try {
        fs.mkdirSync(check.path, { recursive: true });
        results.push({ status: 'created', msg: `✓ ${check.name} 已创建` });
      } catch (e) {
        results.push({ status: 'error', msg: `✗ ${check.name} 创建失败` });
      }
    } else {
      results.push({ status: 'ok', msg: `✓ ${check.name} 就绪` });
    }
  });

  return results;
}

function checkTodayTasks() {
  const { dateStr } = getDateInfo();
  const todayFile = path.join(MEMORY_DIR, `${dateStr}.md`);
  
  if (!fs.existsSync(todayFile)) {
    return { completed: 0, pending: 0, total: 0 };
  }

  const content = fs.readFileSync(todayFile, 'utf-8');
  const completed = (content.match(/\[x\]/gi) || []).length;
  const pending = (content.match(/\[ \]/g) || []).length;
  
  return { completed, pending, total: completed + pending };
}

function checkEfficiency() {
  const recentDays = [];
  
  if (!fs.existsSync(MEMORY_DIR)) return recentDays;

  const files = fs.readdirSync(MEMORY_DIR)
    .filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/))
    .sort()
    .reverse()
    .slice(0, 7);

  files.forEach(f => {
    const filePath = path.join(MEMORY_DIR, f);
    const content = fs.readFileSync(filePath, 'utf-8');
    const completed = (content.match(/\[x\]/gi) || []).length;
    const pending = (content.match(/\[ \]/g) || []).length;
    
    recentDays.push({
      date: f.replace('.md', ''),
      completed,
      pending,
      rate: pending + completed > 0 ? Math.round((completed / (pending + completed)) * 100) : 0
    });
  });

  return recentDays;
}

// ========== 错误分析系统 ==========

const ERROR_PATTERNS = [
  { pattern: /error|Error|ERROR/, type: 'error', desc: '执行错误' },
  { pattern: /exception|Exception/, type: 'error', desc: '异常' },
  { pattern: /fail|Fail|FAILURE/, type: 'error', desc: '失败' },
  { pattern: /timeout|Timeout/, type: 'warning', desc: '超时' },
  { pattern: /invalid|Invalid/, type: 'error', desc: '无效参数' },
  { pattern: /not found|404/, type: 'error', desc: '未找到' },
  { pattern: /permission|denied/, type: 'error', desc: '权限拒绝' },
  { pattern: /undefined|cannot read/, type: 'error', desc: '空值错误' }
];

function analyzeErrors() {
  const errors = [];
  const recentFiles = [];

  // 扫描近3天的memory文件
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
      ERROR_PATTERNS.forEach(({ pattern, type, desc }) => {
        if (pattern.test(line)) {
          errors.push({
            date: file.date,
            line: idx + 1,
            type,
            desc,
            content: line.trim().slice(0, 80)
          });
        }
      });
    });
  });

  return errors;
}

function generateFixes(errors) {
  const fixes = [];
  const errorTypes = new Set(errors.map(e => e.desc));

  errorTypes.forEach(type => {
    switch(type) {
      case '权限拒绝':
        fixes.push({
          issue: '权限不足',
          fix: '检查文件/目录权限，使用管理员权限运行或修改ACL'
        });
        break;
      case '未找到':
        fixes.push({
          issue: '路径或文件不存在',
          fix: '验证路径正确性，确保前置步骤已创建所需资源'
        });
        break;
      case '空值错误':
        fixes.push({
          issue: '访问了未定义的变量/属性',
          fix: '添加空值检查，使用可选链操作符 ?. 或默认值'
        });
        break;
      case '超时':
        fixes.push({
          issue: '操作超时',
          fix: '增加超时时间，检查网络/资源可用性，添加重试逻辑'
        });
        break;
      case '无效参数':
        fixes.push({
          issue: '参数校验失败',
          fix: '检查输入参数格式，添加参数校验逻辑'
        });
        break;
    }
  });

  return fixes;
}

// ========== 记忆系统 ==========

function checkMemoryHealth() {
  const memoryPath = path.join(WORKSPACE, 'MEMORY.md');
  if (!fs.existsSync(memoryPath)) {
    return { exists: false, sections: 0, size: 0 };
  }

  const content = fs.readFileSync(memoryPath, 'utf-8');
  const sections = (content.match(/^##\s+/gm) || []).length;
  
  return {
    exists: true,
    sections,
    size: (content.length / 1024).toFixed(1)
  };
}

// ========== 执行报告 ==========

function generateReport(tasks, efficiency, errors, fixes) {
  const report = [];
  
  // 今日任务
  if (tasks.total > 0) {
    const rate = Math.round((tasks.completed / tasks.total) * 100);
    if (rate >= 80) {
      report.push(`✓ 今日执行率 ${rate}% - 高效！`);
    } else if (rate >= 50) {
      report.push(`○ 今日执行率 ${rate}% - 还有空间`);
    } else {
      report.push(`! 今日执行率 ${rate}% - 需要加速`);
    }
  } else {
    report.push(`! 今日无任务记录 - 建议查看待办`);
  }
  
  // 待办提醒
  if (tasks.pending > 0) {
    report.push(`→ 剩余 ${tasks.pending} 项待办`);
  }
  
  // 错误状态
  if (errors.length > 0) {
    report.push(`! 发现 ${errors.length} 个错误/异常 - 需关注`);
  } else {
    report.push(`✓ 近3天无错误记录`);
  }
  
  // 平均效率
  if (efficiency.length >= 3) {
    const avgRate = Math.round(
      efficiency.reduce((sum, d) => sum + d.rate, 0) / efficiency.length
    );
    report.push(`→ 近7天平均完成率 ${avgRate}%`);
  }
  
  return report;
}

// ========== 主函数 ==========

async function runCheck() {
  const { dateStr, dayOfWeek, timeStr } = getDateInfo();

  console.log('\n');
  log('═══════════════════════════════════════════', 'cyan');
  log('     ⛰️  小宇每日任务执行检查', 'bright');
  log('═══════════════════════════════════════════', 'cyan');
  log(`${dateStr} ${timeStr} | ${dayOfWeek}`, 'dim');

  // 1. 系统检查
  logSection('系统状态');
  const system = checkTaskSystem();
  system.forEach(s => log(s.msg, s.status === 'error' ? 'red' : 'green'));

  // 2. 今日任务
  logSection('今日任务');
  const tasks = checkTodayTasks();
  if (tasks.total > 0) {
    log(`完成: ${tasks.completed} | 待办: ${tasks.pending} | 总计: ${tasks.total}`, 'green');
  } else {
    log('暂无今日任务记录', 'yellow');
  }

  // 3. 执行效率
  logSection('执行效率 (近7天)');
  const efficiency = checkEfficiency();
  if (efficiency.length > 0) {
    efficiency.forEach(d => {
      const bar = '█'.repeat(d.rate / 10) + '░'.repeat(10 - d.rate / 10);
      log(`${d.date} ${bar} ${d.rate}%`, d.rate >= 70 ? 'green' : 'yellow');
    });
  } else {
    log('无历史数据', 'dim');
  }

  // 4. 错误分析
  logSection('错误分析 (近3天)');
  const errors = analyzeErrors();
  if (errors.length > 0) {
    log(`发现 ${errors.length} 个问题:`, 'yellow');
    errors.slice(0, 5).forEach(e => {
      log(`  [${e.date}] ${e.desc}: ${e.content}`, e.type === 'error' ? 'red' : 'yellow');
    });
    if (errors.length > 5) {
      log(`  ... 还有 ${errors.length - 5} 个`, 'dim');
    }
  } else {
    log('✓ 运行平稳，无错误记录', 'green');
  }

  // 5. 修复建议
  if (errors.length > 0) {
    logSection('修复建议');
    const fixes = generateFixes(errors);
    fixes.forEach(f => {
      log(`• ${f.issue}`, 'yellow');
      log(`  → ${f.fix}`, 'dim');
    });
  }

  // 6. 记忆系统
  logSection('记忆系统');
  const memory = checkMemoryHealth();
  if (memory.exists) {
    log(`✓ MEMORY.md 正常 (${memory.size}KB, ${memory.sections}节)`);
  } else {
    log(`✗ MEMORY.md 缺失`, 'red');
  }

  // 7. 执行报告
  logSection('执行报告');
  const report = generateReport(tasks, efficiency, errors, []);
  report.forEach(r => log(r));

  // 总结
  console.log('\n' + '═'.repeat(50));
  const hasErrors = errors.length > 0;
  const summary = hasErrors 
    ? '检查完成。发现错误，建议优先处理。⛰️'
    : '检查完成。运行良好，保持高效。⛰️';
  log(summary, hasErrors ? 'yellow' : 'bright');
  console.log('═'.repeat(50) + '\n');
}

// CLI
const args = process.argv.slice(2);
if (args[0] === 'run' && args.includes('--review')) {
  runCheck().catch(err => {
    console.error('检查失败:', err.message);
    process.exit(1);
  });
} else {
  console.log(`
⛰️ 小宇任务执行检查工具（增强版）

用法:
  node index.js run --review    执行每日检查

功能:
  • 任务追踪：完成/待办统计
  • 效率分析：7天完成率趋势
  • 错误扫描：近3天错误检测
  • 修复建议：自动推荐解决方案
`);
}
