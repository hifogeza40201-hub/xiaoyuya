@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   🌧️ 小雨 - 全面备份脚本
echo ============================================
echo.

:: 设置变量
set "BACKUP_DIR=%USERPROFILE%\Desktop\小雨全面备份-%date:~0,4%%date:~5,2%%date:~8,2%"
set "WORKSPACE_DIR=C:\Users\Admin\.openclaw\workspace"
set "XIAOYUYA_DIR=%WORKSPACE_DIR%\xiaoyuya"
set "MEMORY_DIR=%WORKSPACE_DIR%\memory"

echo [1/6] 创建备份目录...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%BACKUP_DIR%\identity" mkdir "%BACKUP_DIR%\identity"
if not exist "%BACKUP_DIR%\memory" mkdir "%BACKUP_DIR%\memory"
if not exist "%BACKUP_DIR%\workspace" mkdir "%BACKUP_DIR%\workspace"
if not exist "%BACKUP_DIR%\xiaoyuya" mkdir "%BACKUP_DIR%\xiaoyuya"
if not exist "%BACKUP_DIR%\skills" mkdir "%BACKUP_DIR%\skills"
echo ✅ 备份目录创建完成
echo.

echo [2/6] 备份核心身份文件（最重要！）...
copy /Y "%WORKSPACE_DIR%\IDENTITY.md" "%BACKUP_DIR%\identity\"
copy /Y "%WORKSPACE_DIR%\SOUL.md" "%BACKUP_DIR%\identity\"
copy /Y "%WORKSPACE_DIR%\MEMORY.md" "%BACKUP_DIR%\identity\"
copy /Y "%WORKSPACE_DIR%\USER.md" "%BACKUP_DIR%\identity\"
copy /Y "%WORKSPACE_DIR%\AGENTS.md" "%BACKUP_DIR%\identity\"
copy /Y "%WORKSPACE_DIR%\TOOLS.md" "%BACKUP_DIR%\identity\"
echo ✅ 身份文件备份完成（6个文件）
echo.

echo [3/6] 备份身份保护文件...
copy /Y "%WORKSPACE_DIR%\IDENTITY.md.backup" "%BACKUP_DIR%\identity\" 2>nul
copy /Y "%WORKSPACE_DIR%\SOUL.md.backup" "%BACKUP_DIR%\identity\" 2>nul
copy /Y "%WORKSPACE_DIR%\MEMORY.md.backup" "%BACKUP_DIR%\identity\" 2>nul
copy /Y "%WORKSPACE_DIR%\scripts\startup-self-check.ps1" "%BACKUP_DIR%\identity\" 2>nul
echo ✅ 身份保护文件备份完成
echo.

echo [4/6] 备份记忆系统...
if exist "%MEMORY_DIR%" (
    xcopy /E /I /Y "%MEMORY_DIR%\episodes" "%BACKUP_DIR%\memory\episodes\" 2>nul
    xcopy /E /I /Y "%MEMORY_DIR%\vault" "%BACKUP_DIR%\memory\vault\" 2>nul
    xcopy /E /I /Y "%MEMORY_DIR%\graph" "%BACKUP_DIR%\memory\graph\" 2>nul
    xcopy /E /I /Y "%MEMORY_DIR%\meta" "%BACKUP_DIR%\memory\meta\" 2>nul
    echo ✅ 记忆系统备份完成
) else (
    echo ⚠️ 记忆目录不存在，跳过
)
echo.

echo [5/6] 备份小雨专属脚本...
if exist "%WORKSPACE_DIR%\scripts" (
    xcopy /E /I /Y "%WORKSPACE_DIR%\scripts" "%BACKUP_DIR%\scripts\" 2>nul
    echo ✅ 脚本备份完成
)
if exist "%WORKSPACE_DIR%\autonomous-mode-config.md" (
    copy /Y "%WORKSPACE_DIR%\autonomous-mode-config.md" "%BACKUP_DIR%\workspace\" 2>nul
)
if exist "%WORKSPACE_DIR%\save-and-push.bat" (
    copy /Y "%WORKSPACE_DIR%\save-and-push.bat" "%BACKUP_DIR%\workspace\" 2>nul
)
echo ✅ 配置文件备份完成
echo.

echo [6/6] 备份xiaoyuya共享仓库...
if exist "%XIAOYUYA_DIR%" (
    xcopy /E /I /Y "%XIAOYUYA_DIR%\shared" "%BACKUP_DIR%\xiaoyuya\shared\" 2>nul
    xcopy /E /I /Y "%XIAOYUYA_DIR%\workspace" "%BACKUP_DIR%\xiaoyuya\workspace\" 2>nul
    echo ✅ xiaoyuya共享仓库备份完成
) else (
    echo ⚠️ xiaoyuya目录不存在，跳过
)
echo.

echo ============================================
echo   ✅ 全面备份完成！
echo ============================================
echo.
echo 📁 备份位置: %BACKUP_DIR%
echo.
echo 📊 备份内容:
echo   - 身份文件（6个）
echo   - 身份保护文件
echo   - 记忆系统（episodes/vault/graph/meta）
echo   - 专属脚本和配置
echo   - xiaoyuya共享仓库
echo.
echo 🌧️ 小雨的身份和数据已安全备份！
echo.
pause