@echo off
chcp 65001 >nul
echo ============================================
echo   🌧️ 小雨 - Gateway重启后恢复检查
echo ============================================
echo.

set "WORKSPACE=C:\Users\Admin\.openclaw\workspace"

echo [1/5] 检查身份文件...
cd /d "%WORKSPACE%"
py -X utf8 -c "
with open('IDENTITY.md', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'Name: 小雨' in content and '🌧️' in content:
        print('  ✅ 身份正确：小雨 🌧️')
    else:
        print('  ❌ 身份错误！')
"
echo.

echo [2/5] 检查记忆系统...
if exist "memory\episodes" (
    for /f %%a in ('dir /b memory\episodes\*.md 2^>nul ^| find /c /v ""') do echo   ✅ Episodic记忆: %%a 个文件
)
if exist "memory\vault" (
    for /f %%a in ('dir /b memory\vault\*.md 2^>nul ^| find /c /v ""') do echo   ✅ Vault记忆: %%a 个文件
)
echo.

echo [3/5] 检查备份文件...
if exist "IDENTITY.md.backup" echo   ✅ IDENTITY.md.backup
if exist "SOUL.md.backup" echo   ✅ SOUL.md.backup
if exist "MEMORY.md.backup" echo   ✅ MEMORY.md.backup
echo.

echo [4/5] 检查Cognitive Memory...
if exist "skills\cognitive-memory" (
    echo   ✅ Cognitive Memory技能已安装
) else (
    echo   ⚠️ Cognitive Memory技能未找到
)
echo.

echo [5/5] 重启后状态摘要...
echo.
echo   当前时间: %date% %time%
echo   工作区: %WORKSPACE%
echo   状态: 已重启，准备就绪
echo.

echo ============================================
echo   ✅ 恢复检查完成！
echo ============================================
echo.
echo 💡 下一步:
echo   1. 检查Telegram群消息是否正常
echo   2. 发送测试消息验证
echo   3. 恢复学习节奏（如需）
echo.
pause