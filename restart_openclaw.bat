@echo off
chcp 65001 >nul
echo [小雨重启脚本] 2秒后执行重启...
timeout /t 2 /nobreak >nul

echo [小雨重启脚本] 正在关闭 OpenClaw...
taskkill /f /im node.exe 2>nul
taskkill /f /im openclaw.exe 2>nul

echo [小雨重启脚本] 等待进程退出...
timeout /t 3 /nobreak >nul

echo [小雨重启脚本] 正在启动 OpenClaw...
start "" openclaw gateway

echo [小雨重启脚本] 重启完成！
exit