/**
 * 自动备份检查脚本
 * 检查本地文件是否已同步到 GitHub
 * 未同步时自动执行 git push
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// 配置
const CONFIG = {
    // 要检查的Git仓库目录（默认为上级目录）
    repos: [
        path.join(__dirname, '..')
    ],
    
    // 需要检查的文件/目录模式
    watchPatterns: [
        'memory/',
        'scripts/',
        'reports/',
        'AGENTS.md',
        'USER.md',
        'TOOLS.md'
    ],
    
    // 日志文件
    logFile: path.join(__dirname, '..', 'data', 'backup-check.log'),
    lastBackupFile: path.join(__dirname, '..', 'data', 'last-backup.timestamp'),
    
    // 自动推送设置
    autoPush: true,
    pushBranch: 'main'  // 或 'master'
};

// 确保数据目录存在
const dataDir = path.dirname(CONFIG.logFile);
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// 日志函数
function log(level, message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level}] ${message}\n`;
    
    console.log(logEntry.trim());
    fs.appendFileSync(CONFIG.logFile, logEntry);
}

// 执行命令并返回Promise
function execPromise(command, cwd) {
    return new Promise((resolve, reject) => {
        const options = { 
            encoding: 'utf8',
            cwd: cwd || process.cwd()
        };
        
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject({ error, stdout, stderr });
            } else {
                resolve(stdout.trim());
            }
        });
    });
}

// 检查Git仓库状态
async function checkGitStatus(repoPath) {
    const repoName = path.basename(repoPath);
    log('INFO', `📁 检查仓库: ${repoName}`);
    
    try {
        // 检查是否是git仓库
        try {
            await execPromise('git rev-parse --git-dir', repoPath);
        } catch (e) {
            log('WARN', `⚠️ ${repoName} 不是Git仓库`);
            return { status: 'not-git', path: repoPath };
        }
        
        // 获取仓库状态
        const status = await execPromise('git status --porcelain', repoPath);
        const branch = await execPromise('git branch --show-current', repoPath);
        
        // 检查是否有未提交的更改
        const hasUncommitted = status.length > 0;
        
        // 检查是否有未推送的提交
        let hasUnpushed = false;
        try {
            const aheadBehind = await execPromise(`git rev-list --left-right --count origin/${branch}...${branch}`, repoPath);
            const [behind, ahead] = aheadBehind.split('\t').map(n => parseInt(n.trim()));
            hasUnpushed = ahead > 0;
        } catch (e) {
            // 可能还没有远程分支
            hasUnpushed = true;
        }
        
        // 检查远程URL
        let remoteUrl = '';
        try {
            remoteUrl = await execPromise('git remote get-url origin', repoPath);
        } catch (e) {
            log('WARN', `⚠️ ${repoName} 没有配置远程仓库`);
        }
        
        return {
            status: 'ok',
            path: repoPath,
            name: repoName,
            branch,
            remoteUrl,
            hasUncommitted,
            hasUnpushed,
            uncommittedFiles: status.split('\n').filter(line => line.trim()),
            needsSync: hasUncommitted || hasUnpushed
        };
        
    } catch (error) {
        log('ERROR', `❌ 检查 ${repoName} 失败: ${error.error?.message || error.message}`);
        return { status: 'error', path: repoPath, error: error.error?.message || error.message };
    }
}

// 自动提交和推送
async function autoSync(repo) {
    log('INFO', `🔄 开始自动同步: ${repo.name}`);
    
    try {
        // 配置Git用户信息（如果没有）
        try {
            await execPromise('git config user.name', repo.path);
        } catch (e) {
            await execPromise('git config user.name "OpenClaw Bot"', repo.path);
            await execPromise('git config user.email "bot@openclaw.local"', repo.path);
        }
        
        // 添加所有更改
        if (repo.hasUncommitted) {
            log('INFO', `📦 添加 ${repo.uncommittedFiles.length} 个更改的文件`);
            await execPromise('git add -A', repo.path);
            
            // 提交更改
            const commitMsg = `Auto backup: ${new Date().toISOString()}`;
            await execPromise(`git commit -m "${commitMsg}"`, repo.path);
            log('INFO', `✅ 已提交: ${commitMsg}`);
        }
        
        // 推送到远程
        if (repo.hasUnpushed || repo.hasUncommitted) {
            log('INFO', `📤 推送到远程仓库...`);
            await execPromise(`git push origin ${repo.branch}`, repo.path);
            log('INFO', `✅ 推送成功`);
        }
        
        // 更新最后备份时间
        fs.writeFileSync(CONFIG.lastBackupFile, Date.now().toString());
        
        return { success: true };
        
    } catch (error) {
        log('ERROR', `❌ 自动同步失败: ${error.stderr || error.error?.message}`);
        return { success: false, error: error.stderr || error.error?.message };
    }
}

// 生成备份报告
function generateReport(results) {
    const now = new Date().toLocaleString('zh-CN');
    let report = `# 📦 自动备份检查报告\n\n**时间:** ${now}\n\n`;
    
    let needsSyncCount = 0;
    let syncedCount = 0;
    let errorCount = 0;
    
    results.forEach(repo => {
        if (repo.status === 'error') {
            errorCount++;
            report += `## ❌ ${path.basename(repo.path)}\n\n`;
            report += `- **状态:** 检查失败\n`;
            report += `- **错误:** ${repo.error}\n\n`;
        } else if (repo.status === 'not-git') {
            report += `## ⚠️ ${path.basename(repo.path)}\n\n`;
            report += `- **状态:** 不是Git仓库\n\n`;
        } else if (repo.needsSync) {
            needsSyncCount++;
            report += `## 🔄 ${repo.name}\n\n`;
            report += `- **分支:** ${repo.branch}\n`;
            report += `- **远程:** ${repo.remoteUrl || '未配置'}\n`;
            report += `- **未提交文件:** ${repo.uncommittedFiles.length}\n`;
            if (repo.uncommittedFiles.length > 0) {
                report += `  - ${repo.uncommittedFiles.slice(0, 5).join('\n  - ')}\n`;
                if (repo.uncommittedFiles.length > 5) {
                    report += `  - ... 还有 ${repo.uncommittedFiles.length - 5} 个文件\n`;
                }
            }
            report += `- **未推送提交:** ${repo.hasUnpushed ? '是' : '否'}\n\n`;
        } else {
            syncedCount++;
            report += `## ✅ ${repo.name}\n\n`;
            report += `- **分支:** ${repo.branch}\n`;
            report += `- **状态:** 已同步\n\n`;
        }
    });
    
    report += `---\n\n**统计:** ✅ ${syncedCount} 个已同步 | 🔄 ${needsSyncCount} 个需要同步 | ❌ ${errorCount} 个错误\n`;
    
    return { report, needsSyncCount, syncedCount, errorCount };
}

// 主函数
async function main() {
    console.log('='.repeat(60));
    console.log('📦 自动备份检查');
    console.log('='.repeat(60));
    
    log('INFO', '🚀 开始备份检查');
    
    // 检查所有配置的仓库
    const results = [];
    for (const repoPath of CONFIG.repos) {
        const result = await checkGitStatus(repoPath);
        results.push(result);
    }
    
    // 生成报告
    const { report, needsSyncCount } = generateReport(results);
    
    console.log('\n' + '='.repeat(60));
    console.log(report);
    console.log('='.repeat(60));
    
    // 保存报告
    const reportFile = path.join(dataDir, `backup-report-${new Date().toISOString().split('T')[0]}.md`);
    fs.writeFileSync(reportFile, report);
    
    // 自动同步需要同步的仓库
    if (CONFIG.autoPush && needsSyncCount > 0) {
        console.log('\n🔄 开始自动同步...\n');
        
        for (const repo of results) {
            if (repo.needsSync) {
                const syncResult = await autoSync(repo);
                if (syncResult.success) {
                    log('INFO', `✅ ${repo.name} 同步成功`);
                } else {
                    log('ERROR', `❌ ${repo.name} 同步失败: ${syncResult.error}`);
                }
            }
        }
    } else if (needsSyncCount > 0) {
        log('INFO', `⚠️ 发现 ${needsSyncCount} 个仓库需要同步，但自动推送已禁用`);
    }
    
    log('INFO', '✅ 备份检查完成');
    
    // 返回结果（供其他脚本调用）
    return {
        timestamp: new Date().toISOString(),
        needsSync: needsSyncCount > 0,
        results
    };
}

// 运行
main().then(result => {
    process.exit(result.needsSync ? 1 : 0);
}).catch(error => {
    log('ERROR', `脚本异常: ${error.message}`);
    process.exit(1);
});
