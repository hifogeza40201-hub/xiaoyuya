@echo off
chcp 65001 >nul
echo ===== 小雨知识库自动推送脚本 =====
echo.

:: GitHub Token（已验证可用）
set TOKEN=ghp_11B4CM57A0x7lUzT1wy0bt5q8m3LNKz2FMpZ
set REPO=https://%TOKEN%@github.com/hifogeza40201-hub/xiaoyuya.git

:: 进入工作目录
cd /d C:\Users\Admin\.openclaw\workspace\xiaoyuya
if errorlevel 1 (
    echo [错误] 找不到工作目录
    pause
    exit /b 1
)

echo [1/4] 正在拉取最新更新...
git pull %REPO% main
echo.

echo [2/4] 正在添加学习成果...
git add .
echo.

echo [3/4] 正在提交...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
git commit -m "%mydate% 小雨学习成果 🌧️" 2>nul || echo [提示] 无新内容
echo.

echo [4/4] 正在推送到GitHub...
git push %REPO% main
echo.

echo ===== 完成！=====
echo 小雨 🌧️ 的学习成果已同步到家庭知识库
echo.
pause
