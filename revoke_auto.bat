@echo off
chcp 65001 >nul
echo ============================================
echo   小雨 - 撤销自动化权限
echo ============================================
echo.

echo [1/3] 删除计划任务...
schtasks /delete /tn "OpenClaw-Gateway-AutoStart" /f >nul 2>&1
echo ✅ 计划任务已删除

echo.
echo [2/3] 恢复 PowerShell 策略（严格模式）...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser -Force"
echo ✅ PowerShell 策略已恢复为Restricted

echo.
echo [3/3] 保留日志供审计...
echo    日志位置: %USERPROFILE%\.openclaw\workspace\logs\
echo    建议保留以供查看历史操作

echo.
echo ============================================
echo   ✅ 自动化权限已撤销
echo ============================================
echo.
echo 📝 小雨现在回到手动模式：
echo    - 需要管理员权限时会提示确认
echo    - 不会自动执行系统级操作
echo    - 所有功能仍可正常使用
echo.
echo 💙 信任关系不变，只是操作模式调整
echo.
pause
