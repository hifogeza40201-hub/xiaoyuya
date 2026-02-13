/**
 * 系统健康监控脚本
 * 检查: OpenClaw网关状态、磁盘空间、内存使用
 * 异常时发送钉钉通知
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const https = require('https');

// 配置
const CONFIG = {
    // 钉钉机器人配置 (需要用户填写)
    dingtalkWebhook: process.env.DINGTALK_WEBHOOK || '',
    dingtalkSecret: process.env.DINGTALK_SECRET || '',
    
    // 阈值配置
    thresholds: {
        diskUsagePercent: 85,      // 磁盘使用超过85%报警
        memoryUsagePercent: 90,    // 内存使用超过90%报警
        gatewayTimeoutMs: 5000     // 网关响应超时时间
    },
    
    // 日志文件
    logFile: path.join(__dirname, '..', 'data', 'health-monitor.log'),
    alertCooldownFile: path.join(__dirname, '..', 'data', 'last-alert.timestamp')
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
    
    // 追加到日志文件
    fs.appendFileSync(CONFIG.logFile, logEntry);
}

// 执行命令并返回Promise
function execPromise(command) {
    return new Promise((resolve, reject) => {
        exec(command, { encoding: 'utf8' }, (error, stdout, stderr) => {
            if (error) {
                reject(error);
            } else {
                resolve(stdout.trim());
            }
        });
    });
}

// 检查 OpenClaw 网关状态
async function checkGateway() {
    log('INFO', '🔍 检查 OpenClaw 网关状态...');
    
    try {
        // 使用 openclaw gateway status 命令
        const output = await execPromise('openclaw gateway status');
        
        const isRunning = output.toLowerCase().includes('running') || 
                         output.toLowerCase().includes('online') ||
                         output.toLowerCase().includes('active');
        
        if (isRunning) {
            log('INFO', '✅ OpenClaw 网关运行正常');
            return { status: 'ok', message: 'Gateway is running', output };
        } else {
            log('WARN', '⚠️ OpenClaw 网关状态异常');
            return { status: 'warning', message: 'Gateway status unclear', output };
        }
    } catch (error) {
        log('ERROR', `❌ OpenClaw 网关检查失败: ${error.message}`);
        return { status: 'error', message: error.message, output: '' };
    }
}

// 检查磁盘空间
async function checkDiskSpace() {
    log('INFO', '💾 检查磁盘空间...');
    
    try {
        // Windows 使用 wmic 命令
        const output = await execPromise('wmic logicaldisk get size,freespace,caption /format:csv');
        
        const lines = output.split('\n').filter(line => line.trim());
        const results = [];
        
        for (let i = 1; i < lines.length; i++) {
            const parts = lines[i].split(',');
            if (parts.length >= 4) {
                const caption = parts[1].trim();
                const freeSpace = parseInt(parts[2].trim());
                const size = parseInt(parts[3].trim());
                
                if (size > 0) {
                    const usedSpace = size - freeSpace;
                    const usagePercent = Math.round((usedSpace / size) * 100);
                    const freeGB = (freeSpace / 1024 / 1024 / 1024).toFixed(2);
                    const totalGB = (size / 1024 / 1024 / 1024).toFixed(2);
                    
                    results.push({
                        drive: caption,
                        totalGB,
                        freeGB,
                        usagePercent,
                        status: usagePercent > CONFIG.thresholds.diskUsagePercent ? 'warning' : 'ok'
                    });
                }
            }
        }
        
        const warnings = results.filter(r => r.status === 'warning');
        
        if (warnings.length > 0) {
            log('WARN', `⚠️ 磁盘空间警告: ${warnings.map(w => `${w.drive} ${w.usagePercent}%`).join(', ')}`);
        } else {
            log('INFO', `✅ 磁盘空间正常: ${results.map(r => `${r.drive} ${r.usagePercent}%`).join(', ')}`);
        }
        
        return { status: warnings.length > 0 ? 'warning' : 'ok', drives: results };
    } catch (error) {
        log('ERROR', `❌ 磁盘空间检查失败: ${error.message}`);
        return { status: 'error', message: error.message };
    }
}

// 检查内存使用
async function checkMemory() {
    log('INFO', '🧠 检查内存使用...');
    
    try {
        // Windows 使用 wmic 命令
        const output = await execPromise('wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value');
        
        const lines = output.split('\n');
        let totalMemory = 0;
        let freeMemory = 0;
        
        for (const line of lines) {
            if (line.includes('TotalVisibleMemorySize')) {
                totalMemory = parseInt(line.split('=')[1].trim());
            }
            if (line.includes('FreePhysicalMemory')) {
                freeMemory = parseInt(line.split('=')[1].trim());
            }
        }
        
        if (totalMemory > 0) {
            const usedMemory = totalMemory - freeMemory;
            const usagePercent = Math.round((usedMemory / totalMemory) * 100);
            const totalGB = (totalMemory / 1024 / 1024).toFixed(2);
            const freeGB = (freeMemory / 1024 / 1024).toFixed(2);
            
            const status = usagePercent > CONFIG.thresholds.memoryUsagePercent ? 'warning' : 'ok';
            
            if (status === 'warning') {
                log('WARN', `⚠️ 内存使用过高: ${usagePercent}% (${freeGB}GB / ${totalGB}GB 可用)`);
            } else {
                log('INFO', `✅ 内存使用正常: ${usagePercent}% (${freeGB}GB / ${totalGB}GB 可用)`);
            }
            
            return { status, usagePercent, totalGB, freeGB };
        }
        
        return { status: 'error', message: '无法解析内存信息' };
    } catch (error) {
        log('ERROR', `❌ 内存检查失败: ${error.message}`);
        return { status: 'error', message: error.message };
    }
}

// 检查 CPU 负载
async function checkCPU() {
    log('INFO', '⚡ 检查 CPU 负载...');
    
    try {
        // Windows 使用 wmic 获取 CPU 负载
        const output = await execPromise('wmic cpu get loadpercentage /value');
        const match = output.match(/LoadPercentage=(\d+)/);
        
        if (match) {
            const load = parseInt(match[1]);
            const status = load > 90 ? 'warning' : 'ok';
            
            if (status === 'warning') {
                log('WARN', `⚠️ CPU 负载过高: ${load}%`);
            } else {
                log('INFO', `✅ CPU 负载正常: ${load}%`);
            }
            
            return { status, load };
        }
        
        return { status: 'ok', load: 0 };
    } catch (error) {
        log('ERROR', `❌ CPU 检查失败: ${error.message}`);
        return { status: 'error', message: error.message };
    }
}

// 发送钉钉通知
async function sendDingTalkAlert(message, details = []) {
    if (!CONFIG.dingtalkWebhook) {
        log('WARN', '⚠️ 未配置钉钉 Webhook，跳过通知');
        return false;
    }
    
    // 检查冷却时间 (15分钟内不重复发送相同类型的报警)
    const now = Date.now();
    let lastAlert = 0;
    try {
        if (fs.existsSync(CONFIG.alertCooldownFile)) {
            lastAlert = parseInt(fs.readFileSync(CONFIG.alertCooldownFile, 'utf8'));
        }
    } catch (e) {}
    
    if (now - lastAlert < 15 * 60 * 1000) {
        log('INFO', '⏱️  处于报警冷却期，跳过发送');
        return false;
    }
    
    log('INFO', '📤 发送钉钉通知...');
    
    const payload = {
        msgtype: 'markdown',
        markdown: {
            title: '🔔 系统健康报警',
            text: `## 🔔 系统健康报警\n\n**时间:** ${new Date().toLocaleString('zh-CN')}\n\n**消息:** ${message}\n\n${details.map(d => `- ${d}`).join('\n')}\n\n---\n*来自 OpenClaw 系统监控*`
        }
    };
    
    return new Promise((resolve) => {
        const url = new URL(CONFIG.dingtalkWebhook);
        const options = {
            hostname: url.hostname,
            path: url.pathname + url.search,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                log('INFO', '✅ 钉钉通知发送成功');
                // 记录发送时间
                fs.writeFileSync(CONFIG.alertCooldownFile, now.toString());
                resolve(true);
            });
        });
        
        req.on('error', (error) => {
            log('ERROR', `❌ 钉钉通知发送失败: ${error.message}`);
            resolve(false);
        });
        
        req.write(JSON.stringify(payload));
        req.end();
    });
}

// 主函数
async function main() {
    console.log('='.repeat(60));
    console.log('🔍 系统健康监控检查');
    console.log('='.repeat(60));
    
    const results = {
        timestamp: new Date().toISOString(),
        checks: {}
    };
    
    const alerts = [];
    
    // 执行各项检查
    results.checks.gateway = await checkGateway();
    if (results.checks.gateway.status === 'error') {
        alerts.push('OpenClaw 网关异常');
    }
    
    results.checks.disk = await checkDiskSpace();
    if (results.checks.disk.status === 'warning') {
        const warnings = results.checks.disk.drives.filter(d => d.status === 'warning');
        alerts.push(...warnings.map(w => `${w.drive}盘使用率 ${w.usagePercent}%`));
    }
    
    results.checks.memory = await checkMemory();
    if (results.checks.memory.status === 'warning') {
        alerts.push(`内存使用率 ${results.checks.memory.usagePercent}%`);
    }
    
    results.checks.cpu = await checkCPU();
    if (results.checks.cpu.status === 'warning') {
        alerts.push(`CPU 负载 ${results.checks.cpu.load}%`);
    }
    
    // 如果有异常，发送通知
    if (alerts.length > 0) {
        log('WARN', `⚠️ 发现 ${alerts.length} 个异常`);
        await sendDingTalkAlert('检测到系统异常', alerts);
    } else {
        log('INFO', '✅ 所有检查通过，系统健康');
    }
    
    // 保存检查结果
    const resultFile = path.join(dataDir, `health-check-${new Date().toISOString().split('T')[0]}.json`);
    fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));
    
    console.log('='.repeat(60));
    console.log(`✅ 监控完成，结果已保存: ${resultFile}`);
}

// 运行
main().catch(error => {
    log('ERROR', `监控脚本异常: ${error.message}`);
    process.exit(1);
});
