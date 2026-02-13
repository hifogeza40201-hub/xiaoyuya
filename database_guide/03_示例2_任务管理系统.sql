-- ============================================
-- 示例脚本 2: 任务管理系统
-- 场景：团队协作任务跟踪、项目管理、工时统计
-- ============================================

-- 创建示例表
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    team_id INTEGER,
    role TEXT DEFAULT 'member',
    join_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'active',
    priority INTEGER DEFAULT 3  -- 1=最高, 5=最低
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assignee_id INTEGER,
    status TEXT DEFAULT 'todo',  -- todo, doing, review, done
    priority TEXT DEFAULT 'medium',  -- low, medium, high, urgent
    estimated_hours REAL,
    actual_hours REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (assignee_id) REFERENCES members(id)
);

CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    action TEXT,  -- created, updated, completed, etc.
    note TEXT,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (member_id) REFERENCES members(id)
);

-- 插入示例数据
INSERT OR IGNORE INTO teams (id, name, description) VALUES
(1, '前端组', '负责Web和移动端前端开发'),
(2, '后端组', '负责API和数据库开发'),
(3, '产品组', '负责产品设计和需求分析'),
(4, '测试组', '负责质量保证和测试');

INSERT OR IGNORE INTO members (id, name, email, team_id, role, join_date) VALUES
(1, '张伟', 'zhangwei@company.com', 1, 'leader', '2023-01-15'),
(2, '李娜', 'lina@company.com', 1, 'member', '2023-03-20'),
(3, '王强', 'wangqiang@company.com', 2, 'leader', '2023-01-10'),
(4, '刘洋', 'liuyang@company.com', 2, 'member', '2023-06-01'),
(5, '陈静', 'chenjing@company.com', 3, 'leader', '2023-02-01'),
(6, '赵敏', 'zhaomin@company.com', 4, 'leader', '2023-04-15'),
(7, '孙磊', 'sunlei@company.com', 1, 'member', '2023-08-01'),
(8, '周婷', 'zhouting@company.com', 2, 'member', '2023-09-01');

INSERT OR IGNORE INTO projects (id, name, description, start_date, end_date, status, priority) VALUES
(1, '电商APP重构', '全面重构移动端APP', '2024-01-01', '2024-06-30', 'active', 1),
(2, '数据分析平台', '内部数据分析系统', '2024-02-01', '2024-08-31', 'active', 2),
(3, '官网改版', '公司官网 redesign', '2024-03-01', '2024-04-30', 'completed', 3),
(4, 'API网关升级', '微服务架构改造', '2024-04-01', '2024-09-30', 'active', 1),
(5, '自动化测试', '搭建自动化测试框架', '2024-05-01', '2024-07-31', 'active', 2);

INSERT OR IGNORE INTO tasks (id, project_id, title, description, assignee_id, status, priority, estimated_hours, actual_hours, due_date) VALUES
(1, 1, '首页UI设计', '设计APP首页界面', 5, 'done', 'high', 40, 45, '2024-02-01'),
(2, 1, '商品列表页', '实现商品列表展示', 1, 'doing', 'high', 32, 20, '2024-02-15'),
(3, 1, '购物车功能', '实现购物车逻辑', 2, 'doing', 'high', 40, 15, '2024-02-20'),
(4, 1, '支付接口对接', '集成第三方支付', 3, 'todo', 'urgent', 24, 0, '2024-02-25'),
(5, 2, '数据采集模块', '设计数据采集方案', 3, 'done', 'medium', 32, 30, '2024-03-01'),
(6, 2, '数据可视化', '实现图表展示', 4, 'doing', 'medium', 48, 25, '2024-04-01'),
(7, 2, '报表导出', 'Excel和PDF导出', 8, 'todo', 'low', 16, 0, '2024-04-15'),
(8, 3, '设计稿评审', '评审UI设计稿', 5, 'done', 'medium', 8, 10, '2024-03-10'),
(9, 3, '前端页面开发', '实现响应式页面', 7, 'done', 'high', 40, 42, '2024-04-15'),
(10, 3, 'SEO优化', '搜索引擎优化', 1, 'done', 'low', 16, 12, '2024-04-20'),
(11, 4, '网关架构设计', '设计API网关架构', 3, 'done', 'high', 40, 38, '2024-05-01'),
(12, 4, '限流熔断实现', '实现限流熔断功能', 4, 'doing', 'high', 32, 18, '2024-06-01'),
(13, 4, '日志监控系统', '集成监控和告警', 8, 'review', 'medium', 24, 22, '2024-06-15'),
(14, 5, '测试框架搭建', '搭建自动化测试框架', 6, 'done', 'medium', 40, 35, '2024-06-01'),
(15, 5, 'UI自动化用例', '编写UI测试用例', 6, 'doing', 'low', 32, 15, '2024-07-01');

-- ============================================
-- 实用查询 1: 项目进度概览
-- ============================================

-- 各项目任务统计
SELECT 
    p.name as 项目名称,
    p.status as 项目状态,
    CASE p.priority 
        WHEN 1 THEN 'P1-最高'
        WHEN 2 THEN 'P2-高'
        WHEN 3 THEN 'P3-中'
        WHEN 4 THEN 'P4-低'
        ELSE 'P5-最低'
    END as 优先级,
    COUNT(t.id) as 总任务数,
    SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as 已完成,
    SUM(CASE WHEN t.status = 'doing' THEN 1 ELSE 0 END) as 进行中,
    SUM(CASE WHEN t.status = 'review' THEN 1 ELSE 0 END) as 审核中,
    SUM(CASE WHEN t.status = 'todo' THEN 1 ELSE 0 END) as 待处理,
    ROUND(
        100.0 * SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) / COUNT(t.id), 
        1
    ) || '%' as 完成率
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
GROUP BY p.id
ORDER BY p.priority ASC, 完成率 DESC;

-- ============================================
-- 实用查询 2: 成员工作量统计
-- ============================================

-- 各成员任务负载
SELECT 
    m.name as 成员,
    t2.name as 所属团队,
    m.role as 角色,
    COUNT(t.id) as 总任务数,
    SUM(CASE WHEN t.status != 'done' THEN 1 ELSE 0 END) as 未完成,
    SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as 已完成,
    ROUND(SUM(t.estimated_hours), 1) as 预估工时,
    ROUND(SUM(t.actual_hours), 1) as 实际工时,
    ROUND(
        SUM(t.actual_hours) - SUM(t.estimated_hours), 
        1
    ) as 工时偏差,
    CASE 
        WHEN SUM(t.estimated_hours) > 0 THEN
            ROUND(100.0 * SUM(t.actual_hours) / SUM(t.estimated_hours), 1) || '%'
        ELSE 'N/A'
    END as 工时完成率
FROM members m
JOIN teams t2 ON m.team_id = t2.id
LEFT JOIN tasks t ON m.id = t.assignee_id
GROUP BY m.id
ORDER BY 未完成 DESC;

-- ============================================
-- 实用查询 3: 即将到期任务预警
-- ============================================

-- 未来7天内到期的任务
SELECT 
    t.id as 任务ID,
    t.title as 任务标题,
    p.name as 所属项目,
    m.name as 负责人,
    t.priority as 优先级,
    t.status as 状态,
    t.due_date as 截止日期,
    JULIANDAY(t.due_date) - JULIANDAY('now') as 剩余天数,
    ROUND(t.estimated_hours - t.actual_hours, 1) as 剩余工时,
    CASE 
        WHEN JULIANDAY(t.due_date) - JULIANDAY('now') < 0 THEN '已逾期'
        WHEN JULIANDAY(t.due_date) - JULIANDAY('now') <= 3 THEN '紧急'
        ELSE '正常'
    END as 预警级别
FROM tasks t
JOIN projects p ON t.project_id = p.id
JOIN members m ON t.assignee_id = m.id
WHERE t.status NOT IN ('done', 'cancelled')
    AND t.due_date IS NOT NULL
    AND JULIANDAY(t.due_date) - JULIANDAY('now') <= 7
ORDER BY 剩余天数 ASC, 
    CASE t.priority 
        WHEN 'urgent' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END;

-- ============================================
-- 实用查询 4: 团队效率分析
-- ============================================

-- 各团队任务完成情况
SELECT 
    t.name as 团队,
    COUNT(DISTINCT m.id) as 团队人数,
    COUNT(task.id) as 分配任务数,
    SUM(CASE WHEN task.status = 'done' THEN 1 ELSE 0 END) as 已完成,
    ROUND(
        100.0 * SUM(CASE WHEN task.status = 'done' THEN 1 ELSE 0 END) / 
        NULLIF(COUNT(task.id), 0), 
        1
    ) || '%' as 完成率,
    ROUND(AVG(
        CASE 
            WHEN task.estimated_hours > 0 THEN 
                task.actual_hours / task.estimated_hours 
            ELSE NULL 
        END
    ), 2) as 平均工时比,
    ROUND(SUM(task.actual_hours), 1) as 实际总工时
FROM teams t
LEFT JOIN members m ON t.id = m.team_id
LEFT JOIN tasks task ON m.id = task.assignee_id
GROUP BY t.id
ORDER BY 实际总工时 DESC;

-- ============================================
-- 实用查询 5: 个人任务看板
-- ============================================

-- 指定成员的任务列表（可用于个人工作台）
WITH member_tasks AS (
    SELECT 
        t.id,
        t.title,
        p.name as project,
        t.priority,
        t.status,
        t.due_date,
        t.estimated_hours,
        t.actual_hours
    FROM tasks t
    JOIN projects p ON t.project_id = p.id
    WHERE t.assignee_id = 1  -- 修改成员ID查看不同人员
      AND t.status != 'done'
    ORDER BY 
        CASE t.priority 
            WHEN 'urgent' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'medium' THEN 3 
            ELSE 4 
        END,
        t.due_date ASC
    LIMIT 10
)
SELECT * FROM member_tasks;

-- ============================================
-- 实用查询 6: 延期任务分析
-- ============================================

-- 已延期任务统计
SELECT 
    t.id as 任务ID,
    t.title as 任务,
    p.name as 项目,
    m.name as 负责人,
    t.due_date as 原定截止日,
    t.status as 当前状态,
    ROUND(t.estimated_hours, 1) as 预估工时,
    ROUND(t.actual_hours, 1) as 已用工时,
    JULIANDAY('now') - JULIANDAY(t.due_date) as 延期天数,
    CASE 
        WHEN t.actual_hours > t.estimated_hours * 1.5 THEN '工时严重超标'
        WHEN t.actual_hours > t.estimated_hours THEN '工时略超'
        ELSE '工时正常'
    END as 工时评估
FROM tasks t
JOIN projects p ON t.project_id = p.id
JOIN members m ON t.assignee_id = m.id
WHERE t.due_date < DATE('now')
  AND t.status NOT IN ('done', 'cancelled')
ORDER BY 延期天数 DESC;

-- ============================================
-- 实用查询 7: 项目燃尽图数据
-- ============================================

-- 每日完成任务数（用于生成燃尽图）
SELECT 
    DATE(created_at) as 日期,
    COUNT(*) as 创建任务数
FROM tasks
WHERE project_id = 1  -- 指定项目
GROUP BY DATE(created_at)
ORDER BY 日期;

-- 按状态统计（每日快照）
SELECT 
    DATE(updated_at) as 日期,
    status as 状态,
    COUNT(*) as 任务数
FROM tasks
WHERE project_id = 1
GROUP BY DATE(updated_at), status
ORDER BY 日期, status;
