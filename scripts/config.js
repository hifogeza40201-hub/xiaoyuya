/**
 * 自动化工作流配置文件
 * 小雨的自动化工作流配置
 */

const path = require('path');

module.exports = {
    // ==================== 每日信息聚合 ====================
    newsAggregator: {
        enabled: true,
        // 输出目录
        outputDir: path.join(__dirname, '..', 'reports'),
        // 获取数量
        hackerNewsLimit: 10,
        githubTrendingLimit: 10,
        aiNewsLimit: 5,
        // 运行时间 (用于日志)
        schedule: '每天 08:00'
    },
    
    // ==================== 系统健康监控 ====================
    healthMonitor: {
        enabled: true,
        // 钉钉机器人配置
        // 获取方法: 钉钉群 -> 群设置 -> 智能群助手 -> 添加机器人 -> 自定义
        dingtalkWebhook: process.env.DINGTALK_WEBHOOK || '',
        dingtalkSecret: process.env.DINGTALK_SECRET || '',
        
        // 报警阈值
        thresholds: {
            diskUsagePercent: 85,      // 磁盘使用超过85%报警
            memoryUsagePercent: 90,    // 内存使用超过90%报警
            cpuLoadPercent: 90,        // CPU负载超过90%报警
            gatewayTimeoutMs: 5000     // 网关响应超时时间
        },
        
        // 报警冷却时间 (分钟)
        alertCooldownMinutes: 15,
        
        // 运行时间
        schedule: '每4小时'
    },
    
    // ==================== 自动备份检查 ====================
    backupCheck: {
        enabled: true,
        // 要检查的Git仓库目录
        repos: [
            path.join(__dirname, '..')
        ],
        
        // 自动推送设置
        autoPush: true,
        defaultBranch: 'main',
        
        // 提交信息模板
        commitMessageTemplate: 'Auto backup: {{date}}',
        
        // 运行时间
        schedule: '每天 22:00'
    },
    
    // ==================== 学习进度追踪 ====================
    learningTracker: {
        enabled: true,
        // 数据目录
        dataDir: path.join(__dirname, '..', 'data', 'learning'),
        
        // 周报输出目录
        weeklyReportDir: path.join(__dirname, '..', 'reports'),
        
        // 学习分类
        categories: [
            '编程开发',
            '人工智能',
            '英语',
            '阅读',
            '技术文档',
            '项目实践',
            '其他'
        ],
        
        // 周报生成时间 (周日晚上)
        weeklyReportSchedule: '每周日 21:00'
    },
    
    // ==================== 通用配置 ====================
    general: {
        // 时区
        timezone: 'Asia/Shanghai',
        
        // 日志级别: debug, info, warn, error
        logLevel: 'info',
        
        // 数据保留天数
        dataRetentionDays: 30
    }
};
