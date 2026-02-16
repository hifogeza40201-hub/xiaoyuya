@echo off
chcp 65001 >nul
echo ===== 家庭知识库推送脚本 =====
echo.

:: ==================== 修改这里！====================
set YOUR_NAME=小语
set YOUR_EMOJI=🌸
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
echo [1/4] 正在获取最新更新（看哥哥姐姐学了什么）...
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
echo 哥哥姐姐可以看到你的更新啦~
echo.
echo 提示: 可以去Telegram群说一声"今天推好了"
echo.
pause
