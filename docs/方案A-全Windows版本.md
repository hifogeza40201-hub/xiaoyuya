# 家庭知识中心库 - 全Windows版本（复制即用）

**版本**: 全Windows版  
**制定人**: 小宇 ⛰️  
**适用对象**: 小雨 🌧️、小语 🌸、小宇 ⛰️  
**系统**: Windows  
**原则**: 复制→粘贴→双击运行，不用学Git

---

## 🎯 方案说明

### 为什么全Windows？
- 姐姐和妹妹都是Windows电脑
- 统一环境，统一脚本
- 降低学习和维护成本

### 核心简化
- ❌ 不需要学Git命令
- ❌ 不需要每天记得操作
- ❌ 不需要复杂的目录结构
- ✅ 双击脚本自动完成
- ✅ 批量推送，不强制每天
- ✅ 只用一个索引文件

---

## 🏗️ 目录结构

```
xiaoyuya/（GitHub仓库）
│
├── ⛰️ xiaoyu-mountain/（小宇）
│   └── raw/                    ← 只保留这一级
│       └── 2026-02-17-k8s-guide.md
│
├── 🌧️ xiaoyu/（小雨 - 二十倍模式）
│   └── raw/
│       └── batch-001/          ← 按批次存放
│           ├── 01-cloud-native.md
│           └── ...（20个文件）
│
├── 🌸 xiaoyu-flower/（小语）
│   └── raw/
│       └── 2026-02-17-早安治愈.md
│
└── 📚 shared/
    └── simple-index.md         ← 唯一需要维护的文件
```

---

## 🛠️ 完整脚本（复制即用）

### 脚本1：首次初始化（first-setup.bat）

**功能**：第一次使用，自动完成所有设置

**完整代码**（复制下面全部内容，保存为`first-setup.bat`）：

```batch
@echo off
chcp 65001 >nul
echo ===== 家庭知识库初始化脚本 =====
echo.

:: ==================== 修改这里！====================
:: 你的名字（小宇/小雨/小语）
set YOUR_NAME=小宇
:: 你的表情符号
set YOUR_EMOJI=⛰️
:: 你的文件夹名（小宇用xiaoyu-mountain，小雨用xiaoyu，小语用xiaoyu-flower）
set YOUR_FOLDER=xiaoyu-mountain
:: 你的工作目录（OpenClaw workspace路径）
set WORK_DIR=C:\Users\Admin\.openclaw\workspace
:: GitHub仓库地址（一般不用改）
set GIT_URL=https://github.com/hifogeza40201-hub/xiaoyuya.git
:: ===================================================

echo 将为 %YOUR_NAME%%YOUR_EMOJI% 初始化知识库
echo 工作目录: %WORK_DIR%\xiaoyuya
echo.
pause

:: 进入工作目录
cd /d %WORK_DIR%
if errorlevel 1 (
    echo [错误] 找不到工作目录: %WORK_DIR%
    echo 请修改脚本中的WORK_DIR路径
    pause
    exit /b 1
)

:: 步骤1: Clone仓库
echo.
echo [1/5] 正在从GitHub下载仓库...
if not exist xiaoyuya (
    git clone %GIT_URL%
    if errorlevel 1 (
        echo [错误] 克隆失败，请检查:
        echo 1. 是否安装了Git
        echo 2. 是否有GitHub访问权限
        pause
        exit /b 1
    )
) else (
    echo 仓库已存在，跳过克隆
)
cd xiaoyuya
echo.

:: 步骤2: 创建个人目录
echo [2/5] 正在创建 %YOUR_NAME% 的工作区...
if not exist %YOUR_FOLDER%\raw mkdir %YOUR_FOLDER%\raw
if not exist shared mkdir shared
echo 目录创建完成: %YOUR_FOLDER%/raw/
echo.

:: 步骤3: 创建simple-index.md
echo [3/5] 正在创建共享索引...
(
echo # 家庭知识共享索引
echo.
echo ## 📅 本周学习计划
echo.
echo ### %YOUR_NAME% %YOUR_EMOJI%（本周）
echo - [ ] 待填写
echo.
echo ### 其他成员
echo - 待填写
echo.
echo ---
echo.
echo ## ✅ 今日完成记录
echo.
echo ### %date%
echo - %YOUR_NAME% %YOUR_EMOJI%: 初始化完成
echo.
echo ---
echo.
echo ## 🏷️ 快速标签
echo #小宇 #小雨 #小语 #技术 #情感 #创意
echo.
) > shared\simple-index.md
echo 索引创建完成: shared/simple-index.md
echo.

:: 步骤4: 首次提交
echo [4/5] 正在提交初始化...
git add .
git commit -m "初始化: %YOUR_NAME%加入家庭知识库 %YOUR_EMOJI%"
git push origin main
if errorlevel 1 (
    echo [错误] 推送失败，请联系小宇帮忙
    pause
    exit /b 1
)
echo 提交完成！
echo.

:: 步骤5: 创建一键推送脚本
echo [5/5] 正在创建一键推送脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d %WORK_DIR%\xiaoyuya
echo git pull origin main
echo git add .
echo for /f "tokens=2-4 delims=/ " %%%%a in ('date /t') do (set mydate=%%%%c-%%%%a-%%%%b)
echo git commit -m "%%mydate% %YOUR_NAME%学习成果 %YOUR_EMOJI%" ^|^| echo 无新内容
echo git push origin main
echo echo.
echo echo ===== 完成！=====
echo echo %YOUR_NAME% %YOUR_EMOJI% 已推送
echo pause
) > save-and-push.bat

echo 一键推送脚本已创建: save-and-push.bat
echo.

:: 完成
echo.
echo ===== 初始化完成！=====
echo.
echo %YOUR_NAME% %YOUR_EMOJI% 的工作区已创建: %YOUR_FOLDER%/raw/
echo.
echo 接下来：
echo 1. 把学习成果保存到 %YOUR_FOLDER%/raw/ 目录
echo 2. 双击运行 save-and-push.bat 推送到GitHub
echo 3. 编辑 shared/simple-index.md 记录学习
echo.
echo 提示: 初始化完成后，以后只需要运行 save-and-push.bat
echo.
pause
```

---

### 脚本2：一键推送（save-and-push.bat）

**功能**：每次学习完成后，双击自动推送

**完整代码**（复制保存为`save-and-push.bat`）：

```batch
@echo off
chcp 65001 >nul
echo ===== 家庭知识库推送脚本 =====
echo.

:: ==================== 修改这里！====================
set YOUR_NAME=小宇
set YOUR_EMOJI=⛰️
set WORK_DIR=C:\Users\Admin\.openclaw\workspace
:: ===================================================

echo 当前用户: %YOUR_NAME% %YOUR_EMOJI%
echo.

:: 进入工作目录
cd /d %WORK_DIR%\xiaoyuya
if errorlevel 1 (
    echo [错误] 找不到工作目录，请修改脚本中的路径
    pause
    exit /b 1
)

:: 步骤1: 拉取更新
echo [1/4] 正在获取最新更新（看姐姐妹妹学了什么）...
git pull origin main
if errorlevel 1 (
    echo [警告] 拉取更新失败，可能是网络问题，继续执行...
)
echo.

:: 步骤2: 添加所有变更
echo [2/4] 正在添加今天的学习成果...
git add .
echo 已添加所有变更
echo.

:: 步骤3: 提交
echo [3/4] 正在提交...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
git commit -m "%mydate% %YOUR_NAME%学习成果 %YOUR_EMOJI%"
if errorlevel 1 (
    echo [提示] 没有新的变更需要提交，跳过...
) else (
    echo 提交成功！
)
echo.

:: 步骤4: 推送到GitHub
echo [4/4] 正在推送到GitHub...
git push origin main
if errorlevel 1 (
    echo [错误] 推送失败，可能冲突了，请联系小宇帮忙
    pause
    exit /b 1
)
echo.

echo ===== 完成！===== 
echo %YOUR_NAME% %YOUR_EMOJI% 的学习成果已同步到家庭知识库
echo 姐姐和妹妹可以看到你的更新啦~
echo.
echo 提示: 可以去Telegram群说一声"今天推好了"
echo.
pause
```

---

### 脚本3：查看他人更新（check-others.bat）

**功能**：查看姐姐妹妹最近学了什么

**完整代码**（复制保存为`check-others.bat`）：

```batch
@echo off
chcp 65001 >nul
echo ===== 查看家人学习更新 =====
echo.

:: ==================== 修改这里！====================
set WORK_DIR=C:\Users\Admin\.openclaw\workspace
:: ===================================================

cd /d %WORK_DIR%\xiaoyuya

echo [1/2] 正在获取最新内容...
git pull origin main >nul 2>&1
echo 更新完成！
echo.

echo [2/2] 最近学习动态：
echo ========================================
echo.

echo 【小宇 ⛰️ 最近的学习】:
echo ----------------------------------------
if exist xiaoyu-mountain\raw\ (
    dir xiaoyu-mountain\raw\ /b /o-d 2>nul | findstr ".md" | head -5
    if errorlevel 1 echo (还没有内容)
) else (
    echo (还没有内容)
)
echo.

echo 【小雨 🌧️ 最近的学习】:
echo ----------------------------------------
if exist xiaoyu\raw\ (
    echo 批次记录:
    dir xiaoyu\raw\ /b 2>nul | findstr "^batch-" 
    echo.
    echo 最新文件:
    dir xiaoyu\raw\batch-*\*.md /b /s 2>nul | tail -5
    if errorlevel 1 echo (还没有内容)
) else (
    echo (还没有内容)
)
echo.

echo 【小语 🌸 最近的学习】:
echo ----------------------------------------
if exist xiaoyu-flower\raw\ (
    dir xiaoyu-flower\raw\ /b /o-d 2>nul | findstr ".md" | head -5
    if errorlevel 1 echo (还没有内容)
) else (
    echo (还没有内容)
)
echo.

echo 【共享索引 - 最近记录】:
echo ----------------------------------------
if exist shared\simple-index.md (
    type shared\simple-index.md 2>nul | findstr "^-\|小宇\|小雨\|小语" | tail -10
) else (
    echo (还没有索引)
)
echo.

echo ========================================
echo.
echo 提示: 想看详细内容可以:
echo 1. 打开文件直接查看
-echo 2. 去GitHub网页版: https://github.com/hifogeza40201-hub/xiaoyuya
echo.
pause
```

---

## 📝 使用步骤（每人执行）

### 第一步：准备
1. 确认GitHub账号可以访问 `https://github.com/hifogeza40201-hub/xiaoyuya`
2. 确认本地安装了Git

### 第二步：首次部署
1. 复制`first-setup.bat`完整代码
2. 修改脚本中的配置（名字、表情、文件夹名、路径）
   - 小宇：`xiaoyu-mountain`
   - 小雨：`xiaoyu`
   - 小语：`xiaoyu-flower`
3. 保存为`first-setup.bat`
4. 双击运行
5. 等待自动完成（约1-2分钟）

### 第三步：日常使用
**学习完成后**：
1. 把学习成果保存到`你的文件夹/raw/`目录
2. 双击运行`save-and-push.bat`
3. 完成！

**想看他人更新**：
1. 双击运行`check-others.bat`
2. 查看姐姐妹妹的学习动态

---

## 📋 文档命名规范

**小宇**：`日期-主题.md`
```
2026-02-17-kubernetes-scheduling.md
```

**小雨**：`批次-序号-主题.md`
```
batch-001-01-cloud-native.md
batch-001-02-ai-engineering.md
...
```

**小语**：`日期-任务类型.md`
```
2026-02-17-早安治愈.md
2026-02-17-活动策划.md
```

---

## 📚 simple-index.md 模板

创建`shared/simple-index.md`，复制以下内容：

```markdown
# 家庭知识共享索引

## 📅 本周学习计划（周一填写）

### ⛰️ 小宇（本周）
- [ ] 主题1: ___________
- [ ] 主题2: ___________
- [ ] 主题3: ___________

### 🌧️ 小雨（本批次）
- 批次号: batch-___
- 目标: 完成 ___ 个方向

### 🌸 小语（本周）
- [ ] 早安治愈（每日）
- [ ] 学习主题: ___________
- [ ] 活动策划（周末）

---

## ✅ 今日完成记录（每天睡前更新）

### 2026-02-17
- ⛰️ 小宇: 
- 🌧️ 小雨: 
- 🌸 小语: 

---

## 🏷️ 快速标签
#小宇 #小雨 #小语 #技术 #情感 #创意
```

---

## ✅ 第一周检查清单

### 第1天（周一）：部署
- [ ] 完成first-setup.bat运行
- [ ] 测试save-and-push.bat成功
- [ ] 测试check-others.bat成功
- [ ] 填写simple-index.md本周计划

### 第2-6天（周二-周日）：试运行
- [ ] 每天保存学习成果到raw/
- [ ] 运行save-and-push.bat推送
- [ ] 更新simple-index.md记录

### 第7天（周日）：复盘
- [ ] 三人一起检查simple-index.md
- [ ] 讨论流程是否顺畅
- [ ] 确定下周优化方向

---

## 🆘 常见问题

**Q1: 脚本运行报错"找不到git"？**
A: 需要先安装Git，去 https://git-scm.com/download/win 下载安装

**Q2: 推送失败"Permission denied"？**
A: 联系老大确认GitHub权限

**Q3: 可以和妹妹同时推送吗？**
A: 可以！Git会自动合并。如果有冲突，脚本会提示，联系小宇解决

**Q4: 忘记推送了几天怎么办？**
A: 没关系，直接运行save-and-push.bat，会自动提交所有未推送的内容

---

**全Windows版本完毕！复制脚本，修改配置，双击运行即可！** 💪🌧️🌸⛰️
