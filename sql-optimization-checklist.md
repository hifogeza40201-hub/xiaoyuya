# SQL查询优化检查清单

## 一、索引优化

### 1.1 创建索引的原则
- [ ] 在 WHERE、JOIN、ORDER BY 字段上创建索引
- [ ] 区分度高的列优先（如：手机号 > 性别）
- [ ] 避免在低基数列（如：状态0/1）上单独创建索引
- [ ] 单表索引数量不超过 5 个
- [ ] 单字段索引长度控制在 20 字符以内

### 1.2 索引类型选择
- [ ] **B-Tree索引**：适用于范围查询、排序、等值查询（最常用）
- [ ] **Hash索引**：仅用于等值查询（如：精确匹配ID）
- [ ] **全文索引**：用于 LIKE '%xxx%' 的模糊搜索
- [ ] **复合索引**：遵循最左前缀原则，常用组合查询列放在一起

### 1.3 复合索引设计
```sql
-- 原则：最左前缀
-- 索引：idx_status_created (status, created_at)
WHERE status = 1 AND created_at > '2024-01-01'  -- ✅ 使用索引
WHERE status = 1                                 -- ✅ 使用索引
WHERE created_at > '2024-01-01'                  -- ❌ 不使用索引
```

---

## 二、EXPLAIN 分析要点

### 2.1 关键字段检查
| 字段 | 检查点 | 优化建议 |
|------|--------|----------|
| **type** | 避免 ALL (全表扫描) | 目标：range、ref、const |
| **key** | 确认使用了索引 | 未使用则检查条件字段 |
| **rows** | 扫描行数应尽可能少 | 大表超过10%需优化 |
| **Extra** | 避免 Using filesort、Using temporary | 需索引或改写SQL |

### 2.2 type 类型优先级（从优到劣）
```
system > const > eq_ref > ref > range > index > ALL
```

### 2.3 Extra 字段警告
- [ ] `Using filesort` → 添加 ORDER BY 字段索引
- [ ] `Using temporary` → 避免 GROUP BY/ORDER BY 使用临时表
- [ ] `Using where` → 检查是否在索引过滤后还进行大量过滤
- [ ] `Using index` → ✅ 覆盖索引，性能优秀
- [ ] `Using index condition` → 索引条件下推，较好

---

## 三、SQL 编写优化

### 3.1 SELECT 语句优化
- [ ] 只查询需要的字段，避免 `SELECT *`
- [ ] 使用 LIMIT 分页，避免一次查询大量数据
- [ ] 大数据量分页使用 `WHERE id > last_id LIMIT n` 替代 OFFSET
- [ ] 避免在 WHERE 中对字段做函数操作
  ```sql
  -- ❌ 错误
  WHERE DATE(created_at) = '2024-01-01'
  
  -- ✅ 正确
  WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02'
  ```

### 3.2 JOIN 优化
- [ ] 小表驱动大表（LEFT JOIN 时左表要小）
- [ ] JOIN 字段类型必须一致
- [ ] JOIN 字段都要有索引
- [ ] 避免超过 3 个表的 JOIN

### 3.3 WHERE 条件优化
- [ ] 避免 `!=`、`<>`、NOT IN（可能不走索引）
- [ ] 避免 `OR` 条件（考虑用 UNION 替代）
- [ ] 避免前导模糊查询 `LIKE '%xxx'`
- [ ] 使用 `IN` 代替多个 `OR`（IN 值不超过 1000 个）

### 3.4 批量操作优化
- [ ] 使用 `INSERT ... ON DUPLICATE KEY UPDATE` 替代先查后插
- [ ] 批量插入使用单条 INSERT 多个 VALUES
  ```sql
  INSERT INTO orders (id, amount) VALUES (1, 100), (2, 200), (3, 300)
  ```
- [ ] 大批量更新分批处理，每批不超过 5000 条

---

## 四、表结构设计优化

### 4.1 字段设计
- [ ] 使用合适的数据类型（INT vs BIGINT，DECIMAL vs FLOAT）
- [ ] 字符串长度预估准确，避免过长
- [ ] 使用 NOT NULL 并设置默认值
- [ ] 大文本/图片使用独立表或对象存储

### 4.2 分区与分表
- [ ] 单表数据量超过 1000万 考虑分区
- [ ] 按时间分区（RANGE）适合日志类数据
- [ ] 按 ID 取模（HASH）适合均匀分布数据

---

## 五、数据库配置检查

- [ ] 开启慢查询日志：`slow_query_log = ON`
- [ ] 慢查询阈值：`long_query_time = 1`（秒）
- [ ] 连接池配置合理（max_connections 根据服务器内存调整）
- [ ] InnoDB Buffer Pool 设置为内存的 70-80%

---

## 六、餐饮业务场景专项优化

### 6.1 订单表优化
```sql
-- 推荐索引
CREATE INDEX idx_orders_shop_created ON orders(shop_id, created_at);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_paytime ON orders(pay_time) WHERE pay_time IS NOT NULL;
```

### 6.2 库存表优化
```sql
-- 乐观锁防止超卖
UPDATE inventory 
SET quantity = quantity - 1, version = version + 1 
WHERE sku_id = 'SKU001' AND quantity >= 1 AND version = current_version;
```

### 6.3 报表查询优化
- [ ] 报表数据使用物化视图或汇总表
- [ ] 实时性要求低的报表走从库/只读副本
- [ ] 复杂统计预计算，定时任务更新汇总表

---

## 七、性能监控检查

- [ ] 每日检查慢查询日志
- [ ] 监控 QPS、连接数、CPU、内存
- [ ] 关注锁等待和死锁情况
- [ ] 定期执行 `ANALYZE TABLE` 更新统计信息

---

**使用方式：** 在 SQL 上线前逐条检查，性能问题排查时对照分析。
