@echo off
chcp 65001 >nul
:: =============================================
:: 脚本名称：清理临时文件.bat
:: 功能：清理系统临时文件和用户临时文件
:: 作者：学习练习
:: =============================================

:: 设置变量
set "TEMP_FOLDERS=%TEMP% C:\Windows\Temp"
set "LOG_FILE=C:\temp\cleanup_log.txt"
set "DELETED_SIZE=0"

:: 创建日志目录
if not exist "C:\temp" mkdir "C:\temp"

:: 显示开始信息
echo =========================================
echo      系统临时文件清理工具
echo =========================================
echo 开始时间：%date% %time%
echo 日志文件：%LOG_FILE%
echo.

:: 记录开始日志
echo ===== 清理日志 ===== >> "%LOG_FILE%"
echo 开始时间：%date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: 清理用户临时文件夹
echo [步骤1] 清理用户临时文件夹：%TEMP%
echo [步骤1] 清理用户临时文件夹 >> "%LOG_FILE%"
call :CleanFolder "%TEMP%"

:: 清理Windows临时文件夹
echo.
echo [步骤2] 清理Windows临时文件夹：C:\Windows\Temp
echo [步骤2] 清理Windows临时文件夹 >> "%LOG_FILE%"
call :CleanFolder "C:\Windows\Temp"

:: 清理浏览器缓存（可选）
echo.
echo [步骤3] 清理浏览器缓存
echo [步骤3] 清理浏览器缓存 >> "%LOG_FILE%"

:: Chrome缓存
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" (
    echo   - 清理 Chrome 缓存...
    call :CleanFolder "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"
)

:: Edge缓存
if exist "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" (
    echo   - 清理 Edge 缓存...
    call :CleanFolder "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache"
)

:: 清理回收站（可选，取消rem注释启用）
:: echo.
:: echo [步骤4] 清空回收站
echo. >> "%LOG_FILE%"
echo 完成时间：%date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: 完成信息
echo.
echo =========================================
echo [完成] 临时文件清理完毕！
echo 详细日志请查看：%LOG_FILE%
echo =========================================
pause
exit /b

:: =============================================
:: 子程序：清理指定文件夹
:: 参数：%1 = 要清理的文件夹路径
:: =============================================
:CleanFolder
set "FOLDER=%~1"

if not exist "%FOLDER%" (
    echo   [跳过] 文件夹不存在：%FOLDER%
    echo   [跳过] 文件夹不存在：%FOLDER% >> "%LOG_FILE%"
    goto :eof
)

:: 删除文件（包括子目录中的文件）
for /f "delims=" %%a in ('dir /s /b /a:-d "%FOLDER%\*" 2^>nul') do (
    del /f /q "%%a" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [已删除] %%a >> "%LOG_FILE%"
    )
)

:: 删除空文件夹
for /f "delims=" %%a in ('dir /s /b /ad "%FOLDER%\*" 2^>nul ^| sort /r') do (
    rd "%%a" >nul 2>&1
)

echo   [完成] 已清理：%FOLDER%
echo   [完成] 已清理：%FOLDER% >> "%LOG_FILE%"
goto :eof
