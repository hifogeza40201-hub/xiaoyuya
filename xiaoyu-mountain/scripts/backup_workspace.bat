@echo off
chcp 65001 >nul
:: =============================================
:: 脚本名称：自动备份工作目录.bat
:: 功能：自动备份指定工作目录到备份文件夹
:: 作者：学习练习
:: =============================================

:: 设置变量
set "SOURCE_DIR=C:\Users\Admin\.openclaw\workspace"  :: 要备份的源目录
set "BACKUP_DIR=C:\Backup\Workspace"                :: 备份目标目录
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
:: TIMESTAMP格式：年月日_时分秒，如 20260213_095000

:: 将时间中的空格替换为0（防止上午时间有空格）
set "TIMESTAMP=%TIMESTAMP: =0%"

set "BACKUP_FOLDER=%BACKUP_DIR%\backup_%TIMESTAMP%"

:: 显示开始信息
echo =========================================
echo      自动备份工作目录工具
echo =========================================
echo 源目录：%SOURCE_DIR%
echo 备份目标：%BACKUP_FOLDER%
echo 开始时间：%date% %time%
echo.

:: 检查源目录是否存在
if not exist "%SOURCE_DIR%" (
    echo [错误] 源目录不存在：%SOURCE_DIR%
    pause
    exit /b 1
)

:: 创建备份目录（如果不存在）
if not exist "%BACKUP_DIR%" (
    echo [信息] 创建备份主目录...
    mkdir "%BACKUP_DIR%"
)

:: 创建本次备份文件夹
echo [信息] 创建备份文件夹：%BACKUP_FOLDER%
mkdir "%BACKUP_FOLDER%"

:: 执行备份（使用xcopy，/E包含子目录，/I假设目标是目录，/Y覆盖不提示）
echo [信息] 正在备份文件...
xcopy "%SOURCE_DIR%\*" "%BACKUP_FOLDER%\" /E /I /Y /H /R

:: 检查备份是否成功
if %errorlevel% equ 0 (
    echo.
    echo [成功] 备份完成！
    echo 备份位置：%BACKUP_FOLDER%
) else (
    echo.
    echo [警告] 备份过程中可能出现问题，错误码：%errorlevel%
)

echo.
echo 完成时间：%date% %time%
echo =========================================
pause
