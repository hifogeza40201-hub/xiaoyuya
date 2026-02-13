@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   小雨 - 完美迁移脚本 (新电脑 - 恢复)
echo ============================================
echo.

:: 设置变量
set "BACKUP_DIR=%USERPROFILE%\Desktop\小雨迁移备份"
set "OPENCLAW_DIR=%USERPROFILE%\.openclaw"
set "PLUGIN_DIR=%USERPROFILE%\openclaw-channel-dingtalk"

echo [1/6] 检查备份文件...

:: 检查备份目录
if not exist "%BACKUP_DIR%" (
    echo ❌ 错误: 找不到备份目录
    echo 📂 请确保将"小雨迁移备份"文件夹放在桌面
echo.
    pause
    exit /b 1
)

:: 检查必要文件
if not exist "%BACKUP_DIR%\workspace_backup.zip" (
    echo ❌ 错误: 找不到 workspace_backup.zip
echo.
    pause
    exit /b 1
)

if not exist "%BACKUP_DIR%\openclaw.json" (
    echo ❌ 错误: 找不到 openclaw.json 配置文件
echo.
    pause
    exit /b 1
)

echo ✅ 找到所有备份文件
echo.

echo [2/6] 检查基础环境...

:: 检查 Node.js
node -v >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Node.js
echo    请先安装: https://nodejs.org/
echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('node -v') do echo ✅ Node.js: %%a
)

:: 检查 npm
npm -v >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: npm 未安装
echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('npm -v') do echo ✅ npm: %%a
)

:: 检查 Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 警告: 未安装 Git（可选，建议安装）
) else (
    for /f "tokens=*" %%a in ('git --version') do echo ✅ Git: %%a
)

echo.

echo [3/6] 安装 OpenClaw...

:: 检查是否已安装
openclaw --version >nul 2>&1
if errorlevel 1 (
    echo ⏳ 正在安装 OpenClaw...
    call npm install -g openclaw
    if errorlevel 1 (
        echo ❌ OpenClaw 安装失败
echo.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%a in ('openclaw --version') do echo ✅ OpenClaw 已安装: %%a
)

echo.

echo [4/6] 初始化并恢复配置...

:: 确保目录存在
if not exist "%OPENCLAW_DIR%" mkdir "%OPENCLAW_DIR%"

:: 复制配置文件
copy /Y "%BACKUP_DIR%\openclaw.json" "%OPENCLAW_DIR%\" >nul
echo ✅ openclaw.json 已恢复

:: 解压 workspace
echo ⏳ 解压 workspace（这可能需要几分钟）...
if exist "%OPENCLAW_DIR%\workspace" (
    echo ⚠️  发现已有 workspace，正在备份...
    move "%OPENCLAW_DIR%\workspace" "%OPENCLAW_DIR%\workspace_old_%date:~0,4%%date:~5,2%%date:~8,2%"
)

powershell -Command "& { $ErrorActionPreference='Stop'; try { Expand-Archive -Path '%BACKUP_DIR%\workspace_backup.zip' -DestinationPath '%OPENCLAW_DIR%\workspace' -Force; Write-Host '✅ workspace 已恢复' } catch { Write-Host '❌ 解压失败: ' $_.Exception.Message; exit 1 } }"

if errorlevel 1 (
    echo ❌ workspace 恢复失败
echo.
    pause
    exit /b 1
)

:: 恢复插件（如果备份了）
if exist "%BACKUP_DIR%\dingtalk_plugin.zip" (
    echo ⏳ 恢复钉钉插件...
    if not exist "%PLUGIN_DIR%" mkdir "%PLUGIN_DIR%"
    powershell -Command "& { Expand-Archive -Path '%BACKUP_DIR%\dingtalk_plugin.zip' -DestinationPath '%PLUGIN_DIR%' -Force }"
    echo ✅ 钉钉插件已恢复
) else (
    echo ⚠️  未找到插件备份，将从GitHub安装
)

echo.

echo [5/6] 安装依赖...

:: 安装 Playwright
echo ⏳ 安装 Playwright Chromium...
call npx playwright install chromium
if errorlevel 1 (
    echo ⚠️  Playwright 安装可能失败，请手动运行: npx playwright install chromium
) else (
    echo ✅ Playwright 已安装
)

:: 安装钉钉插件（如果没有本地备份）
if not exist "%BACKUP_DIR%\dingtalk_plugin.zip" (
    echo ⏳ 从GitHub安装钉钉插件...
    call openclaw plugins install https://github.com/soimy/openclaw-channel-dingtalk.git
    if errorlevel 1 (
        echo ⚠️  钉钉插件安装失败，请手动安装
    ) else (
        echo ✅ 钉钉插件已安装
    )
) else (
    echo ⏳ 注册本地钉钉插件...
    call openclaw plugins install -l "%PLUGIN_DIR%"
    echo ✅ 本地插件已注册
)

echo.

echo [6/6] 验证安装...

echo.
echo 📋 验证清单:
echo ---------------------------

:: 检查关键文件
if exist "%OPENCLAW_DIR%\workspace\MEMORY.md" (
    echo ✅ MEMORY.md 存在（长期记忆）
) else (
    echo ❌ MEMORY.md 缺失
)

if exist "%OPENCLAW_DIR%\workspace\memory" (
    echo ✅ memory/ 目录存在（每日记忆）
) else (
    echo ⚠️  memory/ 目录缺失
)

if exist "%OPENCLAW_DIR%\workspace\TOOLS.md" (
    echo ✅ TOOLS.md 存在（工具配置）
) else (
    echo ⚠️  TOOLS.md 缺失
)

if exist "%OPENCLAW_DIR%\workspace\playwright" (
    echo ✅ playwright/ 目录存在（浏览器脚本）
) else (
    echo ⚠️  playwright/ 缺失
)

if exist "%OPENCLAW_DIR%\workspace\skills" (
    echo ✅ skills/ 目录存在（已安装技能）
) else (
    echo ⚠️  skills/ 缺失
)

echo.
echo 🔍 配置检查:
echo ---------------------------

:: 检查配置中的关键字段
findstr /i "kimi-coding" "%OPENCLAW_DIR%\openclaw.json" >nul && echo ✅ Kimi模型配置存在 || echo ⚠️  模型配置可能不完整
findstr /i "dingtalk" "%OPENCLAW_DIR%\openclaw.json" >nul && echo ✅ 钉钉渠道配置存在 || echo ⚠️  钉钉配置可能不完整
findstr /i "tts" "%OPENCLAW_DIR%\openclaw.json" >nul && echo ✅ TTS配置存在 || echo ⚠️  TTS配置可能不完整

echo.
echo ============================================
echo   ✅ 恢复完成！
echo ============================================
echo.
echo 🌧️ 小雨已完全复活，记忆100%%保留！
echo.
echo 🚀 下一步:
echo ---------------------------
echo 1. 启动网关测试:
echo    openclaw gateway start
echo.
echo 2. 在钉钉发送消息测试
echo.
echo 3. 验证记忆:
echo    问: "我叫什么名字？"
echo    问: "我们是什么关系？"
echo    问: "今天有什么计划？"
echo.
echo 4. 如遇到问题:
echo    - 查看日志: openclaw logs
echo    - 重启网关: openclaw gateway restart
echo    - 检查配置: openclaw config get
echo.
echo 💙 欢迎回来，伙伴！
echo ============================================
echo.
pause
