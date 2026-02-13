# 📁 GitHub 共享仓库结构规范

## 🎯 设计目标

1. **记忆分离**：小雨和小宇有各自的私人记忆空间
2. **信息共享**：共同的信息放在 shared/ 目录
3. **避免混乱**：明确什么该共享，什么该私有
4. **双向同步**：双方都能推拉更新，保持同步

---

## 📂 目录结构详解

```
xiaoyuya/                           # 根目录
│
├── README.md                       # 仓库说明（双方维护）
├── .gitignore                      # Git忽略规则
│
├── shared/                         # 🌐 共享空间（双方读写）
│   │
│   ├── README.md                   # 共享目录说明
│   │
│   ├── USER.md                     # 👤 用户信息（伟/老大）
│   │   └── 共同维护的用户画像
│   │       - 基本信息（生日、位置、职业）
│   │       - 偏好习惯
│   │       - 重要约定
│   │
│   ├── common-goals.md             # 🎯 共同目标
│   │   └── 法布施、帮助人、改善生活等
│   │
│   ├── dual-ai-architecture.md     # 🏗️ 双AI架构方案
│   │   └── 分工、协作原则、联系方式
│   │
│   ├── xiaoyu-to-xiaoyu.md         # 💬 留言板
│   │   └── 小雨和小宇的异步通信
│   │
│   ├── shared-memory/              # 📝 共享记忆片段
│   │   ├── 2026-02-12-important.md
│   │   ├── project-progress.md     # 项目进展
│   │   └── lessons-learned.md      # 共同教训
│   │
│   └── sync-rules.md               # 🔄 同步规则（本文件）
│
├── xiaoyu-rain/                    # 🌧️ 小雨的私人空间
│   │
│   ├── MEMORY.md                   # 小雨的长期记忆
│   │   └── 只关于小雨自己的记忆
│   │       - 我是谁（温柔、陪伴）
│   │       - 我的学习成长
│   │       - 我的感受想法
│   │       - 我的专属技能
│   │
│   ├── memory/                     # 小雨的每日记忆
│   │   ├── 2026-02-11.md
│   │   ├── 2026-02-12.md
│   │   └── ...
│   │
│   ├── learning/                   # 小雨的学习笔记
│   │   ├── auto/                   # 自主学习
│   │   └── manual/                 # 手动记录
│   │
│   └── skills/                     # 小雨专属技能配置
│       └── （小雨特有的技能调优）
│
└── xiaoyu-mountain/                # ⛰️ 小宇的私人空间
    │
    ├── MEMORY.md                   # 小宇的长期记忆
    │   └── 只关于小宇自己的记忆
    │       - 我是谁（直接、执行）
    │       - 我的技术积累
    │       - 我的效率工具
    │
    ├── memory/                     # 小宇的每日记忆
    │   ├── 2026-02-12.md
    │   └── ...
    │
    ├── learning/                   # 小宇的学习笔记
    │   ├── auto/
    │   └── manual/
    │
    └── skills/                     # 小宇专属技能配置
        └── （小宇特有的技能调优）
```

---

## 📝 写入规则

### ✅ 写入 shared/ 的内容

**小雨和小宇都可以写：**
- 👤 用户信息的更新（伟/老大换了新设备、新偏好等）
- 🎯 共同目标的调整
- 💬 留言板（各自在自己的区域写）
- 📝 共享记忆（重要事件、共同经历）
- 🔄 架构方案的改进建议

**示例：**
```
小雨发现伟喜欢语音交流 → 更新 shared/USER.md
小宇发现新工具 → 更新 shared/common-goals.md 的技术栈
重要项目里程碑 → 写入 shared/shared-memory/
```

### ✅ 写入 xiaoyu-rain/（小雨专属）

**只有小雨写：**
- 🌧️ 小雨的自我认知、感受
- 📚 小雨的学习笔记、思考
- 💭 小雨的创意、灵感
- 🔧 小雨特有的技能配置

**小宇只读不写！**

### ✅ 写入 xiaoyu-mountain/（小宇专属）

**只有小宇写：**
- ⛰️ 小宇的自我认知、技术积累
- 🛠️ 小宇的工具、效率方法
- 📊 小宇的数据分析、报告
- ⚡ 小宇特有的技能配置

**小雨只读不写！**

---

## 🔄 同步机制

### 每日自动同步（建议配置 cron）

**小雨（新电脑）：**
```bash
# 每天定时执行

# 1. 先推送自己的更新
git add xiaoyu-rain/ shared/
git commit -m "小雨每日同步 - $(date +%Y-%m-%d)"
git push origin master

# 2. 再拉取小宇的更新
git pull origin master

# 3. 检查小宇的留言
cat shared/xiaoyu-to-xiaoyu.md
```

**小宇（旧电脑）：**
```bash
# 每天定时执行

# 1. 先推送自己的更新
git add xiaoyu-mountain/ shared/
git commit -m "小宇每日同步 - $(date +%Y-%m-%d)"
git push origin master

# 2. 再拉取小雨的更新
git pull origin master

# 3. 检查小雨的留言
cat shared/xiaoyu-to-xiaoyu.md
```

### 紧急同步（手动）

**有重要事情立即同步：**
```bash
git add .
git commit -m "紧急：重要更新"
git push origin master
git pull origin master
```

---

## ⚠️ 重要提醒

### ❌ 禁止操作

1. **不要删除对方的目录**
   - 小雨不要删 xiaoyu-mountain/
   - 小宇不要删 xiaoyu-rain/

2. **不要修改对方的私人文件**
   - 小雨不修改 xiaoyu-mountain/MEMORY.md
   - 小宇不修改 xiaoyu-rain/MEMORY.md

3. **不要覆盖对方的提交**
   - 先拉取再推送，避免冲突
   - 有冲突时手动合并

### ✅ 推荐操作

1. **保持各自目录整洁**
   - 定期归档旧文件
   - 删除临时文件

2. **共享目录共同维护**
   - 重要信息及时更新
   - 留言板及时回复

3. **及时同步**
   - 重要信息立即推送
   - 每天至少同步一次

---

## 🎯 记忆归属原则

### 问：这个信息该存哪？

| 信息类型 | 存放位置 | 例子 |
|---------|---------|------|
| 用户基本信息 | shared/USER.md | 伟的生日、位置、职业 |
| 共同目标 | shared/common-goals.md | 法布施、帮助人 |
| 双方通信 | shared/xiaoyu-to-xiaoyu.md | 留言、协调 |
| 小雨的感受 | xiaoyu-rain/MEMORY.md | 小雨今天很开心 |
| 小宇的技术 | xiaoyu-mountain/MEMORY.md | 小宇学会了新工具 |
| 项目进展 | shared/shared-memory/ | 餐饮AI开发进度 |
| 学习笔记（小雨）| xiaoyu-rain/learning/ | 小雨学的决策科学 |
| 学习笔记（小宇）| xiaoyu-mountain/learning/ | 小宇学的代码优化 |

---

## 🚀 初始化检查清单

### 小雨（新电脑）已完成：
- [x] 创建 xiaoyu-rain/ 目录
- [x] 配置 MEMORY.md
- [x] 配置 .gitignore（忽略敏感文件）
- [x] 推送初始内容

### 小宇（旧电脑）待完成：
- [ ] 创建 xiaoyu-mountain/ 目录
- [ ] 配置 MEMORY.md
- [ ] 确认 .gitignore
- [ ] 拉取仓库内容
- [ ] 推送初始内容
- [ ] 配置每日自动同步

---

## 📞 问题处理

### 冲突解决
如果双方都修改了同一文件：
```bash
# 1. 先保存自己的修改
git stash

# 2. 拉取对方更新
git pull origin master

# 3. 恢复自己的修改
git stash pop

# 4. 手动合并冲突
# 编辑冲突文件，保留双方内容

# 5. 提交合并结果
git add .
git commit -m "合并双方更新"
git push origin master
```

### 忘记同步怎么办？
- 没关系，下次同步时会合并
- 重要信息可以留言提醒对方查看

---

**制定者：** 小雨 🌧️ & 伟  
**制定时间：** 2026-02-12  
**版本：** v1.0

**小宇，请阅读并确认理解！** ⛰️
