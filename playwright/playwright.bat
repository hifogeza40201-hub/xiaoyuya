@echo off
chcp 65001 > nul
echo.
echo 🎭 Playwright 浏览器自动化工具
echo =================================
echo.
echo 可用命令:
echo.
echo   screenshot ^<url^> [输出文件]  - 截图网页
echo   codegen ^<url^^>                - 录制操作生成代码
echo   open ^<url^>                   - 打开浏览器访问网页
echo   test                          - 测试 Playwright 是否工作
echo.
echo 示例:
echo   playwright screenshot https://manus.im/app manus.png
echo   playwright codegen https://manus.im/app
echo.

set CMD=%1
set URL=%2
set OUTPUT=%3

if "%CMD%"=="screenshot" (
  if "%URL%"=="" (
    echo ❌ 需要提供 URL
    exit /b 1
  )
  if "%OUTPUT%"=="" set OUTPUT=screenshot.png
  node "%~dp0screenshot.js" %URL% %OUTPUT%
  exit /b
)

if "%CMD%"=="codegen" (
  if "%URL%"=="" (
    echo ❌ 需要提供 URL
    exit /b 1
  )
  npx playwright codegen %URL%
  exit /b
)

if "%CMD%"=="open" (
  if "%URL%"=="" (
    echo ❌ 需要提供 URL
    exit /b 1
  )
  node -e "const { chromium } = require('playwright'); (async () => { const b = await chromium.launch({ headless: false }); const p = await b.newPage(); await p.goto('%URL%'); })();"
  exit /b
)

if "%CMD%"=="test" (
  node -e "const { chromium } = require('playwright'); console.log('✅ Playwright 已安装，版本:', require('playwright/package.json').version); console.log('📁 Chromium 路径:', chromium.executablePath());"
  exit /b
)

echo ❌ 未知命令: %CMD%
echo 请使用: screenshot, codegen, open, test
exit /b 1
