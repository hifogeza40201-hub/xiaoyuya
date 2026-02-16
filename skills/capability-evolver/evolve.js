#!/usr/bin/env node
/**
 * Capability Evolver - 统一入口
 * 小宇每日任务 + 学习优化 整合检查
 */

const path = require('path');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function printBanner() {
  console.log('\n');
  log('╔═══════════════════════════════════════════╗', 'cyan');
  log('║     ⛰️  小宇每日进化检查系统         ║', 'bright');
  log('╚═══════════════════════════════════════════╝', 'cyan');
  console.log('');
}

function printFooter() {
  console.log('\n');
  log('═══════════════════════════════════════════', 'cyan');
  log('检查完成。持续进化，永不止步。⛰️📚', 'bright');
  log('═══════════════════════════════════════════', 'cyan');
  console.log('');
}

// 运行任务检查
async function runTaskCheck() {
  log('📋 正在执行每日任务检查...', 'cyan');
  console.log('');
  
  try {
    const taskModule = require('./index.js');
    // 模拟运行（因为原脚本设计为CLI直接运行）
    require('child_process').execSync('node index.js run --review', {
      cwd: __dirname,
      stdio: 'inherit'
    });
    return { success: true };
  } catch (e) {
    // 即使有错误也继续
    return { success: false, error: e.message };
  }
}

// 运行学习检查
async function runLearningCheck() {
  log('\n📚 正在执行学习优化检查...', 'magenta');
  console.log('');
  
  try {
    const { runLearningCheck } = require('./learning-evolver.js');
    return await runLearningCheck();
  } catch (e) {
    console.error('学习检查失败:', e.message);
    return { success: false, error: e.message };
  }
}

// 主函数
async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || 'all';

  if (mode === '--help' || mode === '-h') {
    console.log(`
⛰️ 小宇每日进化检查系统

用法:
  node evolve.js              执行全部检查（任务+学习）
  node evolve.js task         仅执行每日任务检查
  node evolve.js learning     仅执行学习优化检查
  node evolve.js --help       显示帮助

模式说明:
  task      - 检查今日任务完成情况、效率趋势
  learning  - 检查学习系统状态、错误分析、优化建议
  all       - 同时执行两种检查（默认）
`);
    return;
  }

  printBanner();

  let taskResult, learningResult;

  if (mode === 'all' || mode === 'task') {
    taskResult = await runTaskCheck();
  }

  if (mode === 'all' || mode === 'learning') {
    learningResult = await runLearningCheck();
  }

  printFooter();

  // 汇总状态
  const hasIssues = (taskResult && !taskResult.success) || 
                    (learningResult && learningResult.hasIssues);
  
  process.exit(hasIssues ? 1 : 0);
}

main().catch(err => {
  console.error('执行失败:', err);
  process.exit(2);
});
