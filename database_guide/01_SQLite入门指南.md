# SQLite 数据库设计入门指南

> 一份面向初学者的数据库基础教程，涵盖SQLite安装、SQL语法（增删改查）和数据库设计原则。

---

## 目录

1. [什么是SQLite？](#什么是sqlite)
2. [SQLite 安装与基础操作](#sqlite-安装与基础操作)
3. [SQL 基础语法 - CRUD](#sql-基础语法---crud)
4. [数据库设计原则](#数据库设计原则)
5. [常用数据类型](#常用数据类型)
6. [进阶技巧](#进阶技巧)

---

## 什么是SQLite？

SQLite 是一个**嵌入式关系型数据库**，特点：

| 特性 | 说明 |
|------|------|
| 零配置 | 无需安装服务器，直接使用 |
| 单文件存储 | 整个数据库存储在一个 `.db` 文件中 |
| 轻量级 | 体积小（<1MB），速度快 |
| 跨平台 | Windows、Mac、Linux、移动端都支持 |
| 标准SQL | 支持大部分标准SQL语法 |

**适用场景**：
- 小型应用/网站
- 移动APP本地存储
- 桌面应用程序
- 数据分析与原型开发
- 学习SQL语法

---

## SQLite 安装与基础操作

### 安装方法

**Windows:**
```bash
# 方法1：官网下载 https://sqlite.org/download.html
# 方法2：使用包管理器
scoop install sqlite
# 或
choco install sqlite
```

**Mac:**
```bash
brew install sqlite3
```

**Linux:**
```bash
sudo apt-get install sqlite3    # Debian/Ubuntu
sudo yum install sqlite3        # CentOS/RHEL
```

### 基础命令

```bash
# 打开/创建数据库文件
sqlite3 mydatabase.db

# SQLite 提示符下的常用命令
.help          # 显示帮助
.tables        # 列出所有表
.schema table  # 显示表结构
.quit          # 退出
.databases     # 列出所有数据库
```

---

## SQL 基础语法 - CRUD

CRUD = **C**reate(创建) + **R**ead(读取) + **U**pdate(更新) + **D**elete(删除)

### 1. Create - 创建表和插入数据

#### 创建表 (CREATE TABLE)

```sql
-- 基本语法
CREATE TABLE 表名 (
    列名1 数据类型 约束条件,
    列名2 数据类型 约束条件,
    ...
);

-- 示例：创建用户表
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- 主键，自增
    username    TEXT NOT NULL,                       -- 非空
    email       TEXT UNIQUE,                         -- 唯一
    age         INTEGER CHECK(age >= 0),             -- 检查约束
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP   -- 默认值
);

-- 创建订单表（外键示例）
CREATE TABLE orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    product     TEXT NOT NULL,
    amount      REAL DEFAULT 0.0,
    order_date  DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)       -- 外键关联
);
```

#### 插入数据 (INSERT)

```sql
-- 插入单行
INSERT INTO users (username, email, age) 
VALUES ('张三', 'zhangsan@example.com', 25);

-- 插入多行
INSERT INTO users (username, email, age) VALUES
    ('李四', 'lisi@example.com', 30),
    ('王五', 'wangwu@example.com', 28),
    ('赵六', 'zhaoliu@example.com', 35);

-- 插入时省略自增ID
INSERT INTO users (username, email) 
VALUES ('钱七', 'qianqi@example.com');

-- 从另一个表插入
INSERT INTO users_backup SELECT * FROM users WHERE age > 25;
```

---

### 2. Read - 查询数据 (SELECT)

```sql
-- 基础查询
SELECT * FROM users;                           -- 查询所有列
SELECT username, email FROM users;             -- 查询指定列

-- 条件查询 (WHERE)
SELECT * FROM users WHERE age > 25;            -- 大于
SELECT * FROM users WHERE age BETWEEN 20 AND 30;  -- 范围
SELECT * FROM users WHERE username = '张三';    -- 等于
SELECT * FROM users WHERE email LIKE '%@example.com';  -- 模糊匹配
SELECT * FROM users WHERE age IN (25, 30, 35); -- 在列表中

-- 排序 (ORDER BY)
SELECT * FROM users ORDER BY age ASC;          -- 升序
SELECT * FROM users ORDER BY age DESC;         -- 降序
SELECT * FROM users ORDER BY age DESC, username ASC;  -- 多字段排序

-- 限制结果 (LIMIT)
SELECT * FROM users LIMIT 10;                  -- 前10条
SELECT * FROM users LIMIT 10 OFFSET 20;        -- 分页：第21-30条
SELECT * FROM users LIMIT 20, 10;              -- MySQL风格分页

-- 聚合函数
SELECT COUNT(*) FROM users;                    -- 总数
SELECT AVG(age) FROM users;                    -- 平均值
SELECT MAX(age), MIN(age) FROM users;          -- 最大最小
SELECT SUM(amount) FROM orders;                -- 求和

-- 分组 (GROUP BY)
SELECT age, COUNT(*) as count FROM users GROUP BY age;
SELECT user_id, SUM(amount) as total FROM orders GROUP BY user_id;

-- 分组过滤 (HAVING)
SELECT user_id, COUNT(*) as order_count 
FROM orders 
GROUP BY user_id 
HAVING order_count > 5;

-- 去重 (DISTINCT)
SELECT DISTINCT age FROM users;

-- 联表查询 (JOIN)
-- INNER JOIN：只返回匹配的记录
SELECT u.username, o.product, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- LEFT JOIN：返回左表所有记录，右表不匹配则为NULL
SELECT u.username, o.product
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- 子查询
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100);
SELECT * FROM users WHERE age > (SELECT AVG(age) FROM users);
```

---

### 3. Update - 更新数据

```sql
-- 基础更新
UPDATE users SET age = 26 WHERE username = '张三';

-- 更新多个字段
UPDATE users 
SET age = 27, email = 'newemail@example.com' 
WHERE id = 1;

-- 批量更新（慎用！）
UPDATE users SET age = age + 1;  -- 所有人年龄+1

-- 带条件的批量更新
UPDATE orders 
SET amount = amount * 0.9 
WHERE order_date < '2024-01-01';

-- 使用子查询更新
UPDATE users 
SET status = 'VIP' 
WHERE id IN (SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*) > 10);
```

**⚠️ 重要提醒**：UPDATE 必须加 WHERE 条件！不加 WHERE 会更新所有行！

---

### 4. Delete - 删除数据

```sql
-- 删除指定记录
DELETE FROM users WHERE id = 5;

-- 删除满足条件的记录
DELETE FROM users WHERE age < 18;

-- 删除所有数据（保留表结构）
DELETE FROM users;

-- 清空表并重置自增ID（更快）
DELETE FROM users;
DELETE FROM sqlite_sequence WHERE name = 'users';  -- 重置自增计数器

-- 或者使用
DROP TABLE users;  -- 删除整个表（包括结构和数据）
```

**⚠️ 重要提醒**：DELETE 必须加 WHERE 条件！不加 WHERE 会删除所有数据！

---

## 数据库设计原则

### 1. 命名规范

```sql
-- 表名：小写，复数形式，下划线分隔
users           ✓
user            ✗
UserTable       ✗

-- 列名：小写，下划线分隔
created_at      ✓
createdAt       ✗ (除非团队约定)
CreatedAt       ✗

-- 主键：通常用 id 或 表名_id
id              ✓
user_id         ✓ (关联时)
```

### 2. 三大范式 (Normalization)

**第一范式 (1NF)**：每个字段都是原子值，不可再分

```sql
-- ❌ 不好的设计
CREATE TABLE bad_orders (
    id INTEGER PRIMARY KEY,
    customer_info TEXT  -- 存储 "张三,13800138000,北京市"
);

-- ✅ 好的设计
CREATE TABLE good_orders (
    id INTEGER PRIMARY KEY,
    customer_name TEXT,
    customer_phone TEXT,
    customer_address TEXT
);
```

**第二范式 (2NF)**：在满足1NF基础上，非主键字段必须完全依赖于主键

```sql
-- ❌ 不好的设计（联合主键部分依赖）
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    product_name TEXT,    -- 只依赖 product_id，不依赖 order_id
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);

-- ✅ 好的设计（拆分成两个表）
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

**第三范式 (3NF)**：在满足2NF基础上，非主键字段不能传递依赖于主键

```sql
-- ❌ 不好的设计（存在传递依赖：id → department_id → department_name）
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department_id INTEGER,
    department_name TEXT  -- 可通过 department_id 关联获得
);

-- ✅ 好的设计
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

### 3. 常用字段设计

```sql
-- 每个表建议都有的字段
CREATE TABLE example (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自增主键
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新时间
    is_deleted  INTEGER DEFAULT 0                    -- 软删除标记
);

-- 更新时间的触发器
CREATE TRIGGER update_example_timestamp 
AFTER UPDATE ON example
BEGIN
    UPDATE example SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### 4. 索引设计

```sql
-- 主键自动创建索引
-- 外键建议创建索引
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 常用查询字段创建索引
CREATE INDEX idx_users_email ON users(email);

-- 复合索引（最左前缀原则）
CREATE INDEX idx_orders_date_user ON orders(order_date, user_id);

-- 唯一索引
CREATE UNIQUE INDEX idx_users_username ON users(username);

-- 删除索引
DROP INDEX idx_users_email;
```

**索引原则**：
- WHERE、JOIN、ORDER BY 频繁使用的字段考虑加索引
- 索引不是越多越好（写操作会变慢）
- 小表（<1000行）不需要索引
- 区分度低的字段（如性别）不适合索引

---

## 常用数据类型

| SQLite类型 | 说明 | 示例 |
|-----------|------|------|
| `INTEGER` | 整数 | 1, 100, -50 |
| `REAL` | 浮点数 | 3.14, -0.5 |
| `TEXT` | 字符串 | 'hello', '中文' |
| `BLOB` | 二进制数据 | 图片、文件 |
| `NUMERIC` | 数值/日期 | 自动转换 |
| `BOOLEAN` | 布尔值 | 0(假), 1(真) |

**日期时间存储建议**：
```sql
-- 方法1：TEXT 存储 ISO8601 格式
created_at TEXT DEFAULT (datetime('now', 'localtime'))
-- 存储为 '2024-01-15 09:30:00'

-- 方法2：INTEGER 存储时间戳（推荐，效率高）
created_at INTEGER DEFAULT (strftime('%s', 'now'))
-- 存储为 1705315800
```

---

## 进阶技巧

### 1. 事务处理

```sql
-- 保证多条SQL要么全部成功，要么全部失败
BEGIN TRANSACTION;

-- 执行多条操作
INSERT INTO accounts (user_id, balance) VALUES (1, 100);
UPDATE accounts SET balance = balance - 50 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 50 WHERE user_id = 2;

-- 提交或回滚
COMMIT;     -- 全部成功，提交
-- 或
ROLLBACK;   -- 出现问题，回滚所有操作
```

### 2. 视图 (VIEW)

```sql
-- 创建视图（虚拟表，方便查询）
CREATE VIEW user_order_summary AS
SELECT 
    u.id,
    u.username,
    COUNT(o.id) as order_count,
    COALESCE(SUM(o.amount), 0) as total_amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;

-- 使用视图
SELECT * FROM user_order_summary WHERE total_amount > 1000;

-- 删除视图
DROP VIEW user_order_summary;
```

### 3. 常用函数

```sql
-- 字符串函数
SELECT UPPER('hello');           -- 'HELLO'
SELECT LOWER('WORLD');           -- 'world'
SELECT LENGTH('hello');          -- 5
SELECT SUBSTR('hello', 1, 3);    -- 'hel'
SELECT REPLACE('hello world', 'world', 'SQL');  -- 'hello SQL'

-- 数学函数
SELECT ROUND(3.14159, 2);        -- 3.14
SELECT ABS(-10);                 -- 10
SELECT RANDOM() % 100;           -- 0-99随机数

-- 日期函数
SELECT DATE('now');              -- '2024-01-15'
SELECT DATETIME('now');          -- '2024-01-15 09:30:00'
SELECT STRFTIME('%Y-%m', 'now'); -- '2024-01'
SELECT DATE('now', '+7 days');   -- 7天后

-- 条件函数
SELECT IFNULL(NULL, '默认值');    -- '默认值'
SELECT COALESCE(NULL, NULL, 'a', 'b');  -- 'a'
SELECT CASE 
    WHEN age < 18 THEN '未成年'
    WHEN age < 60 THEN '成年'
    ELSE '老年'
END as age_group
FROM users;
```

---

## 学习资源

- **SQLite 官方文档**：https://sqlite.org/docs.html
- **SQL 练习**：https://sqlbolt.com/
- **可视化工具**：DB Browser for SQLite (免费)

---

*本指南版本：v1.0 | 最后更新：2024年*
