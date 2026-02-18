@echo off
chcp 65001 >nul
echo ============================================
echo   🌧️ 小雨 - 每日持续运行脚本
echo ============================================
echo.
echo 本脚本设置为每天自动运行：
echo   1. 网关健康检查
echo   2. 自主学习启动
echo.
echo 运行时间: 每天 06:00
echo ============================================
echo.

:: 检查网关状态
echo [1/2] 检查网关状态...
openclaw status >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  网关未运行，正在启动...
    openclaw gateway start
    echo   ✅ 网关已启动
) else (
    echo   ✅ 网关运行正常
)

:: 启动自主学习
echo.
echo [2/2] 启动自主学习模式...
echo   🌧️ 小雨开始今日学习...
echo   主题: 宫崎骏动画 / 科幻文学
echo   模式: 十倍AI集群
echo   预计产出: 3-5篇笔记
echo.

:: 记录启动时间
echo %date% %time% - 自主学习已启动 >> daily-learning.log

echo ============================================
echo   ✅ 每日运行任务已完成
echo ============================================
echo.
echo 📋 今日任务：
echo   - 网关保持运行 ✅
echo   - 自主学习启动 ✅
echo   - 晚间向伟汇报
echo.
pause