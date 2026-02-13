-- ============================================
-- 示例脚本 1: 电商订单分析
-- 场景：分析用户购买行为、销售额统计、热门商品
-- ============================================

-- 创建示例表
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    city TEXT,
    register_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE DEFAULT CURRENT_DATE,
    total_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 插入示例数据
INSERT OR IGNORE INTO customers (id, name, email, city, register_date) VALUES
(1, '张三', 'zhangsan@example.com', '北京', '2024-01-10'),
(2, '李四', 'lisi@example.com', '上海', '2024-02-15'),
(3, '王五', 'wangwu@example.com', '广州', '2024-03-20'),
(4, '赵六', 'zhaoliu@example.com', '北京', '2024-04-05'),
(5, '钱七', 'qianqi@example.com', '上海', '2024-05-12');

INSERT OR IGNORE INTO products (id, name, category, price, stock) VALUES
(1, 'iPhone 15', '手机', 5999.00, 100),
(2, 'MacBook Pro', '电脑', 12999.00, 50),
(3, 'AirPods Pro', '耳机', 1899.00, 200),
(4, 'iPad Air', '平板', 4799.00, 80),
(5, '小米14', '手机', 3999.00, 150);

INSERT OR IGNORE INTO orders (id, customer_id, order_date, total_amount, status) VALUES
(1, 1, '2024-06-01', 7888.00, 'completed'),
(2, 2, '2024-06-02', 12999.00, 'completed'),
(3, 1, '2024-06-10', 1899.00, 'completed'),
(4, 3, '2024-06-15', 5999.00, 'completed'),
(5, 4, '2024-06-20', 8798.00, 'pending'),
(6, 2, '2024-06-25', 3999.00, 'completed'),
(7, 5, '2024-07-01', 14898.00, 'completed');

INSERT OR IGNORE INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1, 5999.00),
(2, 1, 3, 1, 1899.00),
(3, 2, 2, 1, 12999.00),
(4, 3, 3, 1, 1899.00),
(5, 4, 1, 1, 5999.00),
(6, 5, 1, 1, 5999.00),
(7, 5, 3, 1, 1899.00),
(8, 5, 4, 1, 900.00),
(9, 6, 5, 1, 3999.00),
(10, 7, 2, 1, 12999.00),
(11, 7, 3, 1, 1899.00);

-- ============================================
-- 实用查询 1: 销售统计报表
-- ============================================

-- 按月份统计销售额
SELECT 
    STRFTIME('%Y-%m', order_date) as 月份,
    COUNT(*) as 订单数,
    SUM(total_amount) as 销售额,
    ROUND(AVG(total_amount), 2) as 平均订单金额
FROM orders
WHERE status = 'completed'
GROUP BY STRFTIME('%Y-%m', order_date)
ORDER BY 月份 DESC;

-- 按城市统计客户数量和消费总额
SELECT 
    c.city as 城市,
    COUNT(DISTINCT c.id) as 客户数,
    COUNT(o.id) as 订单数,
    ROUND(SUM(o.total_amount), 2) as 消费总额,
    ROUND(AVG(o.total_amount), 2) as 人均消费
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
GROUP BY c.city
ORDER BY 消费总额 DESC;

-- ============================================
-- 实用查询 2: 热门商品分析
-- ============================================

-- 商品销量排行榜
SELECT 
    p.name as 商品名称,
    p.category as 分类,
    SUM(oi.quantity) as 销量,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) as 销售额
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id AND o.status = 'completed'
GROUP BY p.id
ORDER BY 销量 DESC;

-- 分类销售统计
SELECT 
    p.category as 分类,
    COUNT(DISTINCT p.id) as 商品种类,
    SUM(oi.quantity) as 总销量,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) as 总销售额
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id AND o.status = 'completed'
GROUP BY p.category
ORDER BY 总销售额 DESC;

-- ============================================
-- 实用查询 3: 客户价值分析 (RFM模型简化版)
-- ============================================

-- 找出高价值客户（消费金额高、购买次数多）
SELECT 
    c.name as 客户姓名,
    c.city as 城市,
    c.email as 邮箱,
    COUNT(o.id) as 购买次数,
    ROUND(SUM(o.total_amount), 2) as 累计消费,
    MAX(o.order_date) as 最后购买日期,
    JULIANDAY('now') - JULIANDAY(MAX(o.order_date)) as 距今天数
FROM customers c
JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
GROUP BY c.id
HAVING 累计消费 > 5000  -- 消费超过5000
ORDER BY 累计消费 DESC
LIMIT 10;

-- 客户分层统计
SELECT 
    CASE 
        WHEN total_spent >= 10000 THEN 'VIP客户'
        WHEN total_spent >= 5000 THEN '高价值客户'
        WHEN total_spent >= 1000 THEN '普通客户'
        ELSE '新客户'
    END as 客户等级,
    COUNT(*) as 人数,
    ROUND(AVG(total_spent), 2) as 平均消费
FROM (
    SELECT customer_id, SUM(total_amount) as total_spent
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
GROUP BY 客户等级
ORDER BY 平均消费 DESC;

-- ============================================
-- 实用查询 4: 库存预警
-- ============================================

-- 库存不足商品（库存 < 100）
SELECT 
    name as 商品名称,
    category as 分类,
    stock as 库存,
    price as 单价,
    CASE 
        WHEN stock = 0 THEN '缺货'
        WHEN stock < 50 THEN '严重缺货'
        WHEN stock < 100 THEN '库存紧张'
        ELSE '正常'
    END as 库存状态
FROM products
WHERE stock < 100
ORDER BY stock ASC;

-- ============================================
-- 实用查询 5: 订单详情联表查询
-- ============================================

-- 查看某个订单的完整信息
SELECT 
    o.id as 订单号,
    o.order_date as 下单日期,
    c.name as 客户姓名,
    c.city as 城市,
    p.name as 商品,
    oi.quantity as 数量,
    oi.unit_price as 单价,
    oi.quantity * oi.unit_price as 小计,
    o.total_amount as 订单总额,
    o.status as 状态
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.id = 1;

-- 查看所有待处理订单
SELECT 
    o.id as 订单号,
    o.order_date as 下单日期,
    c.name as 客户,
    c.email as 联系邮箱,
    o.total_amount as 金额,
    JULIANDAY('now') - JULIANDAY(o.order_date) as 待处理天数
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending'
ORDER BY o.order_date;
