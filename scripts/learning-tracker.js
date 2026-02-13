/**
 * 学习进度追踪脚本
 * 记录每天学习时间、学习内容
 * 输出周报统计
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// 配置
const CONFIG = {
    dataDir: path.join(__dirname, '..', 'data', 'learning'),
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
    ]
};

// 确保目录存在
[CONFIG.dataDir, CONFIG.weeklyReportDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// 获取今天的日期
function getToday() {
    return new Date().toISOString().split('T')[0];
}

// 获取当前周的起始日期（周一）
function getWeekStart(date = new Date()) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff)).toISOString().split('T')[0];
}

// 读取今天的学习记录
function getTodayRecord() {
    const todayFile = path.join(CONFIG.dataDir, `${getToday()}.json`);
    if (fs.existsSync(todayFile)) {
        return JSON.parse(fs.readFileSync(todayFile, 'utf8'));
    }
    return {
        date: getToday(),
        entries: [],
        totalMinutes: 0
    };
}

// 保存今天的学习记录
function saveTodayRecord(record) {
    const todayFile = path.join(CONFIG.dataDir, `${getToday()}.json`);
    fs.writeFileSync(todayFile, JSON.stringify(record, null, 2));
}

// 添加学习记录
function addEntry(category, content, minutes) {
    const record = getTodayRecord();
    
    const entry = {
        id: Date.now(),
        time: new Date().toLocaleTimeString('zh-CN'),
        category,
        content,
        minutes: parseInt(minutes)
    };
    
    record.entries.push(entry);
    record.totalMinutes += entry.minutes;
    
    saveTodayRecord(record);
    
    console.log(`\n✅ 已记录学习:`);
    console.log(`   📚 分类: ${category}`);
    console.log(`   📝 内容: ${content}`);
    console.log(`   ⏱️  时长: ${minutes}分钟`);
    console.log(`   📊 今日总计: ${record.totalMinutes}分钟\n`);
}

// 获取本周所有记录
function getWeekRecords() {
    const weekStart = getWeekStart();
    const records = [];
    
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(date.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        const filePath = path.join(CONFIG.dataDir, `${dateStr}.json`);
        
        if (fs.existsSync(filePath)) {
            records.push(JSON.parse(fs.readFileSync(filePath, 'utf8')));
        }
    }
    
    return records;
}

// 生成本周报告
function generateWeeklyReport() {
    const records = getWeekRecords();
    const weekStart = getWeekStart();
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    
    if (records.length === 0) {
        console.log('\n📭 本周暂无学习记录\n');
        return null;
    }
    
    // 统计数据
    const stats = {
        totalMinutes: 0,
        totalEntries: 0,
        byCategory: {},
        byDay: {}
    };
    
    records.forEach(record => {
        stats.totalMinutes += record.totalMinutes;
        stats.totalEntries += record.entries.length;
        
        // 按分类统计
        record.entries.forEach(entry => {
            if (!stats.byCategory[entry.category]) {
                stats.byCategory[entry.category] = 0;
            }
            stats.byCategory[entry.category] += entry.minutes;
        });
        
        // 按天统计
        stats.byDay[record.date] = record.totalMinutes;
    });
    
    // 生成 Markdown 报告
    const weekStartStr = weekStart;
    const weekEndStr = weekEnd.toISOString().split('T')[0];
    
    let md = `# 📚 学习周报 (${weekStartStr} ~ ${weekEndStr})

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总学习时长 | ${Math.floor(stats.totalMinutes / 60)}小时${stats.totalMinutes % 60}分钟 |
| 学习天数 | ${records.length}天 |
| 记录条数 | ${stats.totalEntries}条 |
| 平均每天 | ${Math.round(stats.totalMinutes / records.length)}分钟 |

## 📈 分类统计

| 分类 | 时长 | 占比 |
|------|------|------|
`;
    
    const sortedCategories = Object.entries(stats.byCategory)
        .sort((a, b) => b[1] - a[1]);
    
    sortedCategories.forEach(([category, minutes]) => {
        const percent = ((minutes / stats.totalMinutes) * 100).toFixed(1);
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        md += `| ${category} | ${hours}h${mins}m | ${percent}% |\n`;
    });
    
    md += `\n## 📅 每日详情\n\n`;
    
    records.forEach(record => {
        const date = new Date(record.date);
        const dayName = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()];
        const hours = Math.floor(record.totalMinutes / 60);
        const mins = record.totalMinutes % 60;
        
        md += `### ${record.date} ${dayName} (${hours}h${mins}m)\n\n`;
        
        record.entries.forEach(entry => {
            md += `- **${entry.time}** [${entry.category}] ${entry.content} (${entry.minutes}分钟)\n`;
        });
        
        md += '\n';
    });
    
    md += `---\n*Generated by OpenClaw Learning Tracker*\n`;
    
    // 保存报告
    const reportFile = path.join(CONFIG.weeklyReportDir, `learning-weekly-${weekStartStr}.md`);
    fs.writeFileSync(reportFile, md);
    
    console.log('\n📊 本周学习统计:');
    console.log(`   总时长: ${Math.floor(stats.totalMinutes / 60)}小时${stats.totalMinutes % 60}分钟`);
    console.log(`   学习天数: ${records.length}天`);
    console.log(`   平均每天: ${Math.round(stats.totalMinutes / records.length)}分钟`);
    console.log(`\n📄 周报已保存: ${reportFile}\n`);
    
    return { stats, reportFile };
}

// 显示今日记录
function showToday() {
    const record = getTodayRecord();
    
    console.log(`\n📅 今日学习记录 (${record.date})`);
    console.log('=' .repeat(50));
    
    if (record.entries.length === 0) {
        console.log('暂无记录\n');
        return;
    }
    
    record.entries.forEach((entry, index) => {
        console.log(`${index + 1}. [${entry.time}] ${entry.category}`);
        console.log(`   内容: ${entry.content}`);
        console.log(`   时长: ${entry.minutes}分钟`);
        console.log('');
    });
    
    const hours = Math.floor(record.totalMinutes / 60);
    const mins = record.totalMinutes % 60;
    console.log(`总计: ${hours}小时${mins}分钟\n`);
}

// 交互式添加记录
async function interactiveAdd() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    const question = (prompt) => new Promise(resolve => rl.question(prompt, resolve));
    
    console.log('\n📝 添加学习记录\n');
    console.log('可选分类:');
    CONFIG.categories.forEach((cat, i) => console.log(`  ${i + 1}. ${cat}`));
    console.log('');
    
    const categoryIdx = await question('选择分类 (1-7): ');
    const category = CONFIG.categories[parseInt(categoryIdx) - 1] || '其他';
    
    const content = await question('学习内容: ');
    const minutes = await question('学习时长 (分钟): ');
    
    rl.close();
    
    addEntry(category, content, parseInt(minutes));
}

// 显示帮助
function showHelp() {
    console.log(`
📚 学习进度追踪工具

用法: node learning-tracker.js [命令] [参数]

命令:
  add <分类> <内容> <分钟>    添加学习记录
  today                       显示今日记录
  week                        生成本周报告
  interactive                 交互式添加记录

示例:
  node learning-tracker.js add "编程开发" "学习Node.js" 60
  node learning-tracker.js today
  node learning-tracker.js week
`);
}

// 主函数
async function main() {
    const args = process.argv.slice(2);
    const command = args[0];
    
    switch (command) {
        case 'add':
            if (args.length < 4) {
                console.log('❌ 参数不足。用法: add <分类> <内容> <分钟>');
                process.exit(1);
            }
            addEntry(args[1], args[2], args[3]);
            break;
            
        case 'today':
            showToday();
            break;
            
        case 'week':
            generateWeeklyReport();
            break;
            
        case 'interactive':
        case 'i':
            await interactiveAdd();
            break;
            
        case 'help':
        case '--help':
        case '-h':
        default:
            showHelp();
            break;
    }
}

// 运行
main().catch(console.error);
