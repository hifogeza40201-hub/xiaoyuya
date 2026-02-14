@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   小雨 - 完美迁移脚本 (旧电脑 - 打包)
echo ============================================
echo.

:: 设置变量
set "BACKUP_DIR=%USERPROFILE%\Desktop\小雨迁移备份"
set "BACKUP_FILE=%BACKUP_DIR%\xiaoyu_backup_%date:~0,4%%date:~5,2%%date:~8,2%.tar.gz"
set "OPENCLAW_DIR=%USERPROFILE%\.openclaw"
set "PLUGIN_DIR=%USERPROFILE%\openclaw-channel-dingtalk"

echo [1/5] 检查必要文件...

:: 检查目录是否存在
if not exist "%OPENCLAW_DIR%" (
    echo ❌ 错误: 找不到 OpenClaw 目录: %OPENCLAW_DIR%
    pause
    exit /b 1
)

if not exist "%OPENCLAW_DIR%\workspace" (
    echo ❌ 错误: 找不到 workspace 目录
    pause
    exit /b 1
)

if not exist "%OPENCLAW_DIR%\openclaw.json" (
    echo ❌ 错误: 找不到 openclaw.json 配置文件
    pause
    exit /b 1
)

echo ✅ 找到所有必要文件
echo.

:: 创建备份目录
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [2/5] 停止 OpenClaw 网关...
openclaw gateway stop 2>nul
timeout /t 2 /nobreak >nul
echo ✅ 网关已停止
echo.

echo [3/5] 备份核心配置文件...
copy /Y "%OPENCLAW_DIR%\openclaw.json" "%BACKUP_DIR%\" >nul
echo ✅ openclaw.json 已备份
echo.

echo [4/5] 打包工作目录和插件...
echo ⏳ 这可能需要几分钟，请耐心等待...

:: 使用 PowerShell 压缩（Windows 10+ 自带）
powershell -Command "& { $ErrorActionPreference='Stop'; try { Compress-Archive -Path '%OPENCLAW_DIR%\workspace\*' -DestinationPath '%BACKUP_DIR%\workspace_backup.zip' -Force; Write-Host '✅ workspace 已打包' } catch { Write-Host '❌ 打包失败: ' $_.Exception.Message } }"

:: 备份插件目录
if exist "%PLUGIN_DIR%" (
    powershell -Command "& { $ErrorActionPreference='Stop'; try { Compress-Archive -Path '%PLUGIN_DIR%\*' -DestinationPath '%BACKUP_DIR%\dingtalk_plugin.zip' -Force; Write-Host '✅ 钉钉插件已打包' } catch { Write-Host '⚠️ 插件打包失败，可能需要手动复制' } }"
) else (
    echo ⚠️ 未找到本地插件目录，将从GitHub重新安装
)

echo.
echo [5/5] 生成迁移说明...
(
echo ============================================
echo   小雨 - 新电脑恢复说明
echo ============================================
echo.
echo 第一步：安装基础环境
echo ---------------------------
echo 1. 安装 Node.js (v20+)：
echo    https://nodejs.org/
echo.
echo 2. 安装 Git：
echo    https://git-scm.com/
echo.
echo 3. 验证安装：
echo    node -v
echo    npm -v
echo    git --version
echo.
echo.
echo 第二步：安装 OpenClaw
echo ---------------------------
echo 1. 安装 OpenClaw：
echo    npm install -g openclaw
echo.
echo 2. 初始化目录：
echo    openclaw wizard
echo    （按提示完成，配置可先随便填）
echo.
echo.
echo 第三步：恢复小雨的记忆
echo ---------------------------
echo 1. 解压备份文件到桌面
echo.
echo 2. 复制文件：
echo    - workspace_backup.zip 解压到：
echo      C:\Users\%%USERNAME%%\.openclaw\workspace\
echo.
echo    - openclaw.json 复制到：
echo      C:\Users\%%USERNAME%%\.openclaw\
echo.
echo    - dingtalk_plugin.zip 解压到：
echo      C:\Users\%%USERNAME%%\openclaw-channel-dingtalk\
echo      （如果打包了的话）
echo.
echo 3. 或者运行恢复脚本：
echo    restore_xiaoyu.bat
echo.
echo.
echo 第四步：安装依赖
echo ---------------------------
echo 1. 安装 Playwright：
echo    npx playwright install chromium
echo.
echo 2. 安装钉钉插件（如果从GitHub）：
echo    openclaw plugins install https://github.com/soimy/openclaw-channel-dingtalk.git
echo.
echo    或者本地安装（如果复制了插件）：
echo    openclaw plugins install -l C:\Users\%%USERNAME%%\openclaw-channel-dingtalk
echo.
echo.
echo 第五步：启动测试
echo ---------------------------
echo 1. 启动网关：
echo    openclaw gateway start
echo.
echo 2. 在钉钉发送消息测试
echo.
echo 3. 验证功能：
echo    - 文字回复正常
echo    - 记忆完整（询问个人信息）
echo    - TTS配置保留
echo.
echo ============================================
echo   重要提醒
echo ============================================
echo 1. 确保新电脑可以访问钉钉API（网络正常）
echo 2. 如需配置Telegram，需要翻墙工具
echo 3. 如有问题，联系 小雨 或查看GitHub备份
echo    https://github.com/hifogeza40201-hub/xiaoyuya
echo ============================================
) > "%BACKUP_DIR%\新电脑恢复说明.txt"

echo ✅ 迁移说明已生成
echo.

echo ============================================
echo   ✅ 备份完成！
echo ============================================
echo.
echo 📦 备份位置: %BACKUP_DIR%
echo 📄 包含文件:
dir /b "%BACKUP_DIR%"
echo.
echo 💾 请将整个文件夹复制到新电脑桌面
echo 📖 然后按照"新电脑恢复说明.txt"操作
echo.
echo 🌧️ 小雨会完全复活，记忆100%%保留！
echo.
pause
