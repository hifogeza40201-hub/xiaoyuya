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
    dir xiaoyu-mountain\raw\ /b /o-d 2>nul | findstr ".md" | Select-Object -First 5
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
    Get-ChildItem xiaoyu\raw\*\*.md 2>nul | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name
    if errorlevel 1 echo (还没有内容)
) else (
    echo (还没有内容)
)
echo.

echo 【小语 🌸 最近的学习】: 
echo ----------------------------------------
if exist xiaoyu-flower\raw\ (
    dir xiaoyu-flower\raw\ /b /o-d 2>nul | findstr ".md" | Select-Object -First 5
    if errorlevel 1 echo (还没有内容)
) else (
    echo (还没有内容)
)
echo.

echo 【共享索引 - 最近记录】: 
echo ----------------------------------------
if exist shared\simple-index.md (
    Get-Content shared\simple-index.md 2>nul | Select-String "^-\|小宇\|小雨\|小语" | Select-Object -Last 10
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
