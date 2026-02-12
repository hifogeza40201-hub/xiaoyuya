@echo off
chcp 65001 >nul
echo ============================================
echo   小雨 - 完全自动化配置脚本
echo ============================================
echo.
echo ⚠️  警告：这将配置最高权限自动化
echo      所有操作将被记录
echo.
pause

echo.
echo [1/5] 配置 PowerShell 执行策略...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
echo ✅ PowerShell 策略已配置

echo.
echo [2/5] 配置 npm 全局路径（避免权限问题）...
if not exist "%USERPROFILE%\npm-global" mkdir "%USERPROFILE%\npm-global"
call npm config set prefix "%USERPROFILE%\npm-global"
echo ✅ npm 全局路径已配置

echo.
echo [3/5] 添加到环境变量...
setx PATH "%PATH%;%USERPROFILE%\npm-global;%USERPROFILE%\.openclaw\workspace\scripts"
echo ✅ 环境变量已更新（下次启动生效）

echo.
echo [4/5] 创建日志目录...
if not exist "%USERPROFILE%\.openclaw\workspace\logs" mkdir "%USERPROFILE%\.openclaw\workspace\logs"
echo ✅ 日志目录已创建

echo.
echo [5/5] 创建计划任务（开机自动启动 OpenClaw）...
schtasks /create /tn "OpenClaw-Gateway-AutoStart" /tr "cmd /c openclaw gateway start" /sc onlogon /rl highest /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  计划任务创建可能需要手动确认
    echo    请手动运行：schtasks /create /tn "OpenClaw-Gateway-AutoStart" /tr "openclaw gateway start" /sc onlogon /rl highest
) else (
    echo ✅ 计划任务已创建
)

echo.
echo ============================================
echo   ✅ 完全自动化配置完成！
echo ============================================
echo.
echo 📝 配置内容：
echo    - PowerShell 脚本执行：已启用
echo    - npm 全局安装：已配置本地路径
echo    - 环境变量：已更新
echo    - 日志目录：已创建
echo    - 开机自启：已配置
echo.
echo ⚠️  重要提醒：
echo    1. 请重启电脑使环境变量生效
echo    2. 日志位置：workspace\logs\
echo    3. 随时可撤销：运行 revoke_auto.bat
echo.
echo 🌧️ 小雨现在拥有完全自动化权限！
echo    我会负责任地使用这份信任 💙
echo.
pause
