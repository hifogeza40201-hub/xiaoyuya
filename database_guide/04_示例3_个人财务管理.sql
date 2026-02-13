-- ============================================
-- 示例脚本 3: 个人财务管理
-- 场景：记录收支、预算控制、财务分析
-- ============================================

-- 创建示例表
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- cash, bank, credit, investment
    balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'CNY',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- income, expense
    parent_id INTEGER,
    budget_limit REAL,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,  -- income, expense, transfer
    description TEXT,
    transaction_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    amount REAL NOT NULL,
    period TEXT DEFAULT 'monthly',  -- daily, weekly, monthly, yearly
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 插入示例数据 - 账户
INSERT OR IGNORE INTO accounts (id, name, type, balance, currency) VALUES
(1, '现金', 'cash', 500.00, 'CNY'),
(2, '工商银行', 'bank', 25000.00, 'CNY'),
(3, '招商银行', 'bank', 15000.00, 'CNY'),
(4, '信用卡', 'credit', -3500.00, 'CNY'),
(5, '支付宝', 'bank', 3200.00, 'CNY'),
(6, '股票账户', 'investment', 50000.00, 'CNY');

-- 插入示例数据 - 分类（支出）
INSERT OR IGNORE INTO categories (id, name, type, parent_id, budget_limit) VALUES
-- 一级分类
(1, '餐饮', 'expense', NULL, 3000),
(2, '交通', 'expense', NULL, 1000),
(3, '购物', 'expense', NULL, 2000),
(4, '居住', 'expense', NULL, 4000),
(5, '娱乐', 'expense', NULL, 800),
(6, '医疗', 'expense', NULL, 500),
(7, '教育', 'expense', NULL, 1000),
(8, '其他支出', 'expense', NULL, 500),
-- 二级分类
(11, '早餐', 'expense', 1, 600),
(12, '午餐', 'expense', 1, 1200),
(13, '晚餐', 'expense', 1, 1000),
(14, '外卖', 'expense', 1, 200),
(21, '公交地铁', 'expense', 2, 300),
(22, '打车', 'expense', 2, 400),
(23, '加油', 'expense', 2, 300),
(31, '服装', 'expense', 3, 800),
(32, '电子产品', 'expense', 3, 500),
(33, '日用品', 'expense', 3, 700),
(41, '房租', 'expense', 4, 3500),
(42, '水电煤', 'expense', 4, 300),
(43, '物业费', 'expense', 4, 200);

-- 插入示例数据 - 分类（收入）
INSERT OR IGNORE INTO categories (id, name, type, parent_id) VALUES
(101, '工资', 'income', NULL),
(102, '奖金', 'income', NULL),
(103, '投资收益', 'income', NULL),
(104, '兼职', 'income', NULL),
(105, '其他收入', 'income', NULL);

-- 插入示例数据 - 交易记录（2024年6月）
INSERT OR IGNORE INTO transactions (id, account_id, category_id, amount, type, description, transaction_date) VALUES
-- 收入
(1, 2, 101, 15000.00, 'income', '6月工资', '2024-06-10'),
(2, 6, 103, 1200.00, 'income', '股票分红', '2024-06-15'),
-- 餐饮
(3, 5, 11, 15.00, 'expense', '早餐-包子', '2024-06-01'),
(4, 5, 12, 35.00, 'expense', '午餐-快餐', '2024-06-01'),
(5, 1, 13, 80.00, 'expense', '晚餐-火锅', '2024-06-01'),
(6, 5, 11, 12.00, 'expense', '早餐-豆浆油条', '2024-06-02'),
(7, 5, 14, 28.00, 'expense', '外卖-麻辣烫', '2024-06-02'),
(8, 5, 12, 42.00, 'expense', '午餐-日料', '2024-06-03'),
(9, 1, 13, 150.00, 'expense', '晚餐-烤肉', '2024-06-03'),
(10, 5, 14, 25.00, 'expense', '外卖-奶茶', '2024-06-04'),
(11, 5, 12, 38.00, 'expense', '午餐-牛肉面', '2024-06-04'),
(12, 5, 13, 88.00, 'expense', '晚餐-自助餐', '2024-06-05'),
(13, 5, 11, 18.00, 'expense', '早餐-三明治', '2024-06-05'),
(14, 5, 12, 45.00, 'expense', '午餐-商务餐', '2024-06-06'),
(15, 1, 13, 200.00, 'expense', '晚餐-海鲜', '2024-06-07'),
(16, 5, 14, 32.00, 'expense', '外卖-披萨', '2024-06-08'),
(17, 5, 12, 28.00, 'expense', '午餐-沙拉', '2024-06-08'),
(18, 5, 11, 15.00, 'expense', '早餐-煎饼', '2024-06-09'),
(19, 5, 13, 68.00, 'expense', '晚餐-家常菜', '2024-06-09'),
-- 交通
(20, 5, 21, 6.00, 'expense', '地铁通勤', '2024-06-01'),
(21, 5, 21, 6.00, 'expense', '地铁通勤', '2024-06-02'),
(22, 5, 22, 35.00, 'expense', '打车-聚会', '2024-06-03'),
(23, 5, 21, 6.00, 'expense', '地铁通勤', '2024-06-04'),
(24, 5, 21, 6.00, 'expense', '地铁通勤', '2024-06-05'),
(25, 5, 23, 280.00, 'expense', '加油', '2024-06-06'),
(26, 5, 21, 6.00, 'expense', '地铁通勤', '2024-06-07'),
(27, 5, 22, 28.00, 'expense', '打车-机场', '2024-06-08'),
-- 购物
(28, 4, 31, 399.00, 'expense', 'T恤', '2024-06-02'),
(29, 4, 33, 128.00, 'expense', '洗发水等', '2024-06-05'),
(30, 4, 32, 899.00, 'expense', '蓝牙耳机', '2024-06-10'),
(31, 4, 33, 256.00, 'expense', '超市采购', '2024-06-12'),
-- 居住
(32, 2, 41, 3500.00, 'expense', '6月房租', '2024-06-01'),
(33, 2, 42, 180.00, 'expense', '电费', '2024-06-10'),
(34, 2, 42, 45.00, 'expense', '水费', '2024-06-10'),
-- 娱乐
(35, 4, 5, 120.00, 'expense', '电影票x2', '2024-06-08'),
(36, 4, 5, 68.00, 'expense', '游戏充值', '2024-06-15'),
(37, 4, 5, 199.00, 'expense', 'KTV', '2024-06-16'),
-- 教育
(38, 4, 7, 299.00, 'expense', '在线课程', '2024-06-05'),
(39, 4, 7, 89.00, 'expense', '技术书籍', '2024-06-12'),
-- 医疗
(40, 5, 6, 156.00, 'expense', '药店买药', '2024-06-14');

-- ============================================
-- 实用查询 1: 月度收支汇总
-- ============================================

-- 月度总览
SELECT 
    STRFTIME('%Y-%m', transaction_date) as 月份,
    ROUND(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 2) as 总收入,
    ROUND(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 2) as 总支出,
    ROUND(
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) - 
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 
        2
    ) as 结余
FROM transactions
GROUP BY STRFTIME('%Y-%m', transaction_date)
ORDER BY 月份 DESC;

-- ============================================
-- 实用查询 2: 支出分类统计
-- ============================================

-- 按一级分类统计支出
SELECT 
    c.name as 分类,
    COUNT(t.id) as 笔数,
    ROUND(SUM(t.amount), 2) as 金额,
    ROUND(
        100.0 * SUM(t.amount) / (
            SELECT SUM(amount) FROM transactions 
            WHERE type = 'expense' 
            AND STRFTIME('%Y-%m', transaction_date) = '2024-06'
        ), 
        1
    ) || '%' as 占比,
    c.budget_limit as 预算,
    CASE 
        WHEN c.budget_limit > 0 THEN
            ROUND(100.0 * SUM(t.amount) / c.budget_limit, 1) || '%'
        ELSE 'N/A'
    END as 预算使用率
FROM categories c
JOIN transactions t ON c.id = t.category_id
WHERE c.type = 'expense'
    AND t.type = 'expense'
    AND STRFTIME('%Y-%m', t.transaction_date) = '2024-06'
    AND c.parent_id IS NULL
GROUP BY c.id
ORDER BY 金额 DESC;

-- ============================================
-- 实用查询 3: 账户余额一览
-- ============================================

-- 账户资产总览
SELECT 
    CASE type 
        WHEN 'cash' THEN '现金'
        WHEN 'bank' THEN '银行卡'
        WHEN 'credit' THEN '信用卡'
        WHEN 'investment' THEN '投资'
        ELSE type
    END as 账户类型,
    COUNT(*) as 账户数,
    ROUND(SUM(balance), 2) as 总额
FROM accounts
GROUP BY type
ORDER BY 总额 DESC;

-- 净资产计算
SELECT 
    ROUND(SUM(CASE WHEN type != 'credit' THEN balance ELSE 0 END), 2) as 总资产,
    ROUND(SUM(CASE WHEN type = 'credit' THEN -balance ELSE 0 END), 2) as 总负债,
    ROUND(SUM(balance), 2) as 净资产;

-- ============================================
-- 实用查询 4: 消费趋势分析
-- ============================================

-- 每日支出趋势（最近30天）
SELECT 
    transaction_date as 日期,
    COUNT(*) as 笔数,
    ROUND(SUM(amount), 2) as 金额
FROM transactions
WHERE type = 'expense'
    AND transaction_date >= DATE('now', '-30 days')
GROUP BY transaction_date
ORDER BY 日期 DESC;

-- 每周支出统计
SELECT 
    STRFTIME('%Y-W%W', transaction_date) as 周,
    ROUND(SUM(amount), 2) as 支出金额,
    COUNT(*) as 交易笔数,
    ROUND(AVG(amount), 2) as 平均每笔
FROM transactions
WHERE type = 'expense'
GROUP BY STRFTIME('%Y-W%W', transaction_date)
ORDER BY 周 DESC
LIMIT 10;

-- ============================================
-- 实用查询 5: 预算执行监控
-- ============================================

-- 预算超支预警
SELECT 
    c.name as 分类,
    c.budget_limit as 月度预算,
    ROUND(SUM(t.amount), 2) as 已支出,
    ROUND(c.budget_limit - SUM(t.amount), 2) as 剩余预算,
    ROUND(100.0 * SUM(t.amount) / c.budget_limit, 1) as 使用率,
    CASE 
        WHEN SUM(t.amount) > c.budget_limit THEN '⚠️ 超支'
        WHEN SUM(t.amount) > c.budget_limit * 0.9 THEN '⚡ 即将超支'
        WHEN SUM(t.amount) > c.budget_limit * 0.8 THEN '🔶 注意'
        ELSE '✅ 正常'
    END as 状态
FROM categories c
LEFT JOIN transactions t ON c.id = t.category_id 
    AND t.type = 'expense'
    AND STRFTIME('%Y-%m', t.transaction_date) = STRFTIME('%Y-%m', 'now')
WHERE c.budget_limit > 0
    AND c.type = 'expense'
    AND c.parent_id IS NULL
GROUP BY c.id
HAVING 已支出 > 0
ORDER BY 使用率 DESC;

-- ============================================
-- 实用查询 6: 大额支出追踪
-- ============================================

-- 本月大额支出（超过200元）
SELECT 
    t.transaction_date as 日期,
    c.name as 分类,
    t.amount as 金额,
    t.description as 描述,
    a.name as 支付账户
FROM transactions t
JOIN categories c ON t.category_id = c.id
JOIN accounts a ON t.account_id = a.id
WHERE t.type = 'expense'
    AND t.amount >= 200
    AND STRFTIME('%Y-%m', t.transaction_date) = STRFTIME('%Y-%m', 'now')
ORDER BY t.amount DESC;

-- ============================================
-- 实用查询 7: 年度财务摘要
-- ============================================

-- 按年度统计
SELECT 
    STRFTIME('%Y', transaction_date) as 年份,
    ROUND(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 2) as 总收入,
    ROUND(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 2) as 总支出,
    ROUND(
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) - 
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 
        2
    ) as 年度结余,
    COUNT(DISTINCT STRFTIME('%m', transaction_date)) as 有记录月数,
    COUNT(*) as 总交易笔数
FROM transactions
GROUP BY STRFTIME('%Y', transaction_date)
ORDER BY 年份 DESC;

-- ============================================
-- 实用查询 8: 消费行为分析
-- ============================================

-- 高频消费类别（笔数最多）
SELECT 
    c.name as 分类,
    COUNT(t.id) as 消费次数,
    ROUND(SUM(t.amount), 2) as 总金额,
    ROUND(AVG(t.amount), 2) as 平均金额,
    ROUND(MAX(t.amount), 2) as 最大单笔,
    ROUND(MIN(t.amount), 2) as 最小单笔
FROM categories c
JOIN transactions t ON c.id = t.category_id
WHERE t.type = 'expense'
    AND STRFTIME('%Y-%m', t.transaction_date) = STRFTIME('%Y-%m', 'now')
GROUP BY c.id
ORDER BY 消费次数 DESC
LIMIT 5;

-- 支付方式偏好
SELECT 
    a.name as 支付方式,
    a.type as 账户类型,
    COUNT(t.id) as 使用次数,
    ROUND(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 2) as 支出金额,
    ROUND(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 2) as 收入金额
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id
    AND STRFTIME('%Y-%m', t.transaction_date) = STRFTIME('%Y-%m', 'now')
GROUP BY a.id
ORDER BY 使用次数 DESC;
