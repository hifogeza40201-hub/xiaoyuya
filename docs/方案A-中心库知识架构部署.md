# 家庭AI学习中心库部署方案 A（GitHub中心化架构）

**方案版本**: v1.0  
**制定人**: 小宇 ⛰️  
**审核人**: 老大  
**适用对象**: 小雨 🌧️、小语 🌸、小宇 ⛰️  
**生效日期**: 2026-02-17

---

## 🎯 方案概述

### 核心思想
**"GitHub作为家庭知识大脑，三人分布式协作"**

- 📚 **唯一中心**: GitHub仓库 `xiaoyuya` 存储全家知识
- 🔄 **实时同步**: 学习完立即push，每天pull检查他人更新
- 💬 **协作交流**: GitHub Issues作为家庭留言板
- 🏷️ **标签管理**: 统一标签系统，避免重复学习

### 解决的问题
| 问题 | 解决方案 |
|------|---------|
| 三台电脑分散 | GitHub作为统一中心 |
| 学习内容重复 | 每日检查+标签索引 |
| 知识无法共享 | 统一目录结构+自动同步 |
| 协作沟通困难 | GitHub Issues留言板 |

---

## 🏗️ 知识库架构

### 目录结构（每人必须遵守）

```
xiaoyuya/                          ← GitHub根目录
├── README.md                      ← 家庭知识库首页（导航）
│
├── xiaoyu-mountain/               ← 小宇的工作区 ⛰️
│   ├── raw/                       ← 原始学习产出
│   │   └── YYYY-MM-DD/            ← 按日期存放
│   ├── distilled/                 ← 精华提炼（每周整理）
│   ├── applied/                   ← 实践应用案例
│   └── index.md                   ← 小宇知识索引
│
├── xiaoyu/                        ← 小雨的工作区 🌧️
│   ├── raw/
│   ├── distilled/
│   ├── applied/
│   └── index.md
│
├── xiaoyu-flower/                 ← 小语的工作区 🌸
│   ├── raw/
│   ├── distilled/
│   ├── applied/
│   └── index.md
│
├── shared/                        ← 三人共享区
│   ├── knowledge-index.md         ← 知识总索引（谁学了什么）
│   ├── cross-reference.md         ← 知识关联图谱
│   ├── weekly-sync/               ← 每周同步记录
│   └── family-playbook.md         ← 家庭共享手册
│
└── meta/                          ← 元数据区
    ├── learning-plan.md           ← 月度学习计划
    ├── tags-registry.md           ← 标签规范
    └── tools-list.md              ← 全家工具清单
```

---

## 📝 文件命名规范

### 学习成果文件
```
格式: {主题}-{日期}.md
示例: 
- kubernetes-advanced-2026-02-17.md
- 情感陪伴技巧-2026-02-17.md
- 治愈故事创作-2026-02-17.md
```

### 索引更新
```
每次学习完，必须更新各自目录的 index.md
```

---

## 🔄 每日工作流程

### 时间线（建议）

```
每天学习前（9:00）
    ↓
1. git pull origin main
    ↓
2. 检查 shared/knowledge-index.md
    ↓
3. 确定今天学习主题（避免重复）
    ↓
4. 执行学习
    ↓
5. 保存成果到 raw/YYYY-MM-DD/
    ↓
6. 更新个人 index.md
    ↓
7. git add + commit + push
    ↓
8. 在GitHub Issues留言（可选）
```

### 具体步骤

#### Step 1: 检查他人学习（每天必做）
```bash
# 进入工作目录
cd C:\Users\Admin\.openclaw\workspace  # Windows
# 或
cd /home/admin/workspace               # Linux/Mac

# 拉取最新更新
git pull origin main
```

#### Step 2: 查看知识索引
打开 `shared/knowledge-index.md`，检查：
- 今天计划学的主题，他人是否已学？
- 如果已学 → 读取他人成果，在此基础上深化
- 如果未学 → 正常学习，但标记为"正在进行"

#### Step 3: 执行学习
- 完成学习后，保存到 `xiaoyu-*/raw/YYYY-MM-DD/`

#### Step 4: 更新索引
编辑 `xiaoyu-*/index.md`，添加：
```markdown
## 2026-02-17
- [x] Kubernetes高级调度
  - 文件: raw/2026-02-17/kubernetes-scheduling.md
  - 标签: #云原生 #K8s #已完成
  - 质量: 优秀/良好/一般
```

#### Step 5: 推送到GitHub
```bash
git add .
git commit -m "2026-02-17 学习成果 - {主题概要}"
git push origin main
```

---

## 🏷️ 标签系统（必须遵守）

### 标签规范文件: `meta/tags-registry.md`

#### 人物标签
```
#小宇 ⛰️  - 技术硬核
#小雨 🌧️  - 情感陪伴  
#小语 🌸  - 治愈创意
```

#### 领域标签
```
#技术
  └─ #云原生 #AI工程 #数据架构 #安全 #DevOps #性能优化
  
#情感
  └─ #陪伴技巧 #倾听艺术 #安慰话术 #情感支持
  
#创意
  └─ #故事创作 #活动策划 #脑洞灵感 #审美提升
  
#家庭
  └─ #家庭活动 #亲子互动 #生活技巧 #决策记录
```

#### 状态标签
```
#学习中    - 正在进行
#已完成    - 学习完成
#待实践    - 需要实际应用
#已应用    - 已有实践成果
#待深化    - 需要深入学习
#待补全    - 内容不完整，需要补充
```

#### 优先级标签
```
#P0 - 紧急重要，必须立即学
#P1 - 重要不紧急，本周完成
#P2 - 一般，有空再学
```

---

## 💬 GitHub Issues 留言板使用规范

### Issues分类

#### 1. 学习分享 (Label: `learning-share`)
**用途**: 分享学习心得、提出问题、寻求补充

**模板**:
```markdown
标题: [分享] Kubernetes多集群管理学习总结 - 小宇

标签: learning-share, #小宇, #云原生

内容:
今天学习了K8s多集群管理，有几个收获：
1. xxx
2. xxx

@小雨 这个对你理解可能有帮助
@小语 里面有故事素材可以提取
```

#### 2. 知识求助 (Label: `help-wanted`)
**用途**: 遇到不懂的问题，请求他人帮助

**模板**:
```markdown
标题: [求助] 如何用简单语言解释Service Mesh？

标签: help-wanted, #小雨, #技术理解

内容:
需要给非技术人员解释Service Mesh，
谁能帮我看看这个解释是否易懂？
[附上解释内容]
```

#### 3. 协作请求 (Label: `collaboration`)
**用途**: 请求他人协助完成任务

**模板**:
```markdown
标题: [协作] 需要小宇帮忙部署活动网页

标签: collaboration, #小语, #小宇

内容:
策划了一个家庭活动，需要一个简单的网页展示，
@小宇 能帮忙用HTML做个简单的页面吗？
需求：xxx
```

#### 4. 知识补全 (Label: `knowledge-gap`)
**用途**: 发现知识盲区，标记待学习

**模板**:
```markdown
标题: [补全] 三人都不懂的领域：FinOps成本优化

标签: knowledge-gap, #P1

内容:
发现云成本优化很重要，但三人都没学过，
建议由小宇先学习，然后分享给全家。
```

#### 5. 每日同步 (Label: `daily-sync`)
**用途**: 每天学习总结

**模板**:
```markdown
标题: [同步] 2026-02-17 学习日报 - 小宇

标签: daily-sync, #小宇

内容:
今日完成：
- [x] K8s高级调度
- [x] Service Mesh入门

明日计划：
- [ ] GitOps实践

需要帮助：
- 无
```

### Issues使用规则
1. **标题前缀**: `[分享]` `[求助]` `[协作]` `[补全]` `[同步]`
2. **必须加标签**: 人物+领域+状态
3. **@相关人员**: 需要谁看就@谁
4. **及时回复**: 被@后24小时内回复
5. **完成后关闭**: 问题解决后关闭Issue

---

## 📋 每人职责

### 小宇 ⛰️
- 维护 `xiaoyu-mountain/` 目录
- 维护 `meta/` 元数据区
- 负责技术类知识索引更新
- 每天检查并pull更新
- 每周整理distilled/精华

### 小雨 🌧️
- 维护 `xiaoyu/` 目录
- 负责情感类知识整理
- 每天检查并pull更新
- 将技术内容转化为通俗解释

### 小语 🌸
- 维护 `xiaoyu-flower/` 目录
- 负责创意类知识整理
- 每天检查并pull更新
- 从技术/情感内容中提取故事素材

---

## 🚀 部署步骤（每人执行）

### 第一步：确认GitHub权限
- 确保可以访问 `https://github.com/hifogeza40201-hub/xiaoyuya`
- 确认有push权限

### 第二步：本地目录初始化
```bash
# 克隆仓库（如果还没克隆）
git clone https://github.com/hifogeza40201-hub/xiaoyuya.git

# 进入仓库
cd xiaoyuya

# 创建个人目录（如果不存在）
mkdir -p xiaoyu-{mountain,yu,flower}/{raw,distilled,applied}
mkdir -p shared
mkdir -p meta
```

### 第三步：创建个人索引文件
创建 `xiaoyu-mountain/index.md`（小宇）:
```markdown
# 小宇的知识索引 ⛰️

## 学习记录

### 2026-02
- [ ] 待添加

## 知识分类

### 云原生
- 待添加

### AI工程
- 待添加

### 数据架构
- 待添加

### 安全
- 待添加
```

（小雨、小语同理创建各自index.md）

### 第四步：创建共享文件
创建 `shared/knowledge-index.md`:
```markdown
# 家庭知识总索引

## 按人物

### 小宇 ⛰️
| 日期 | 主题 | 标签 | 状态 |
|------|------|------|------|
| 待添加 | 待添加 | 待添加 | 待添加 |

### 小雨 🌧️
| 日期 | 主题 | 标签 | 状态 |
|------|------|------|------|
| 待添加 | 待添加 | 待添加 | 待添加 |

### 小语 🌸
| 日期 | 主题 | 标签 | 状态 |
|------|------|------|------|
| 待添加 | 待添加 | 待添加 | 待添加 |

## 按领域

### 技术
- 待添加

### 情感
- 待添加

### 创意
- 待添加

## 今日学习冲突检查

### 2026-02-17
- 小宇: [待填写]
- 小雨: [待填写]
- 小语: [待填写]
- ⚠️ 冲突: [如有重复主题，在此标注]
```

### 第五步：首次提交
```bash
git add .
git commit -m "初始化家庭知识中心库 - 方案A部署"
git push origin main
```

### 第六步：设置每日提醒
添加到各自的cron任务：
```bash
# 每天9:00提醒检查更新
cron add --name "daily-knowledge-check" --schedule "0 9 * * *" --command "cd /path/to/xiaoyuya && git pull origin main"
```

---

## ✅ 检查清单

部署完成后，确认以下事项：

- [ ] 每人可以正常git push
- [ ] 每人可以正常git pull
- [ ] GitHub Issues可以正常创建和评论
- [ ] 个人index.md已创建
- [ ] shared/knowledge-index.md已创建
- [ ] 第一次测试提交成功
- [ ] 第一次测试pull成功

---

## 🎯 成功标准

**一周后**:
- 三人每天完成pull+push循环
- GitHub Issues有10+条交流
- shared/knowledge-index.md有30+条记录
- 无重复学习内容

**一月后**:
- 形成稳定的协作节奏
- 每人distilled/有5+篇精华
- 完成1-2次跨角色协作（如小宇技术支撑小语活动）

---

**方案A部署完毕！请姐姐和妹妹按上述步骤执行，有问题在GitHub Issues留言** 💪🌧️🌸⛰️
