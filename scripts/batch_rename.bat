@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
:: =============================================
:: 脚本名称：批量重命名文件.bat
:: 功能：批量重命名指定目录中的文件
:: 支持：添加前缀、添加后缀、替换文本、序号命名
:: 作者：学习练习
:: =============================================

:: 设置变量
set "TARGET_DIR="
set "OPERATION="
set "PREFIX="
set "SUFFIX="
set "OLD_TEXT="
set "NEW_TEXT="
set "START_NUM=1"
set "FILE_EXT=*"

:MENU
cls
echo =========================================
echo      批量文件重命名工具
echo =========================================
echo.
echo 请选择操作：
echo   [1] 添加前缀（如：file.txt → prefix_file.txt）
echo   [2] 添加后缀（如：file.txt → file_suffix.txt）
echo   [3] 替换文本（如：old_file.txt → new_file.txt）
echo   [4] 序号命名（如：file1.txt, file2.txt...）
echo   [5] 删除文件名中的特定文本
echo   [0] 退出
echo.
set /p OPERATION="请输入选项 (0-5): "

if "%OPERATION%"=="0" exit /b
if "%OPERATION%"=="1" goto ADD_PREFIX
if "%OPERATION%"=="2" goto ADD_SUFFIX
if "%OPERATION%"=="3" goto REPLACE_TEXT
if "%OPERATION%"=="4" goto SERIAL_NUMBER
if "%OPERATION%"=="5" goto DELETE_TEXT
echo [错误] 无效选项！
timeout /t 2 >nul
goto MENU

:: =============================================
:: 1. 添加前缀
:: =============================================
:ADD_PREFIX
cls
echo ===== 添加前缀 =====
echo.
set /p TARGET_DIR="请输入目标文件夹路径: "
set /p PREFIX="请输入要添加的前缀: "
set /p FILE_EXT="请输入文件扩展名（如：txt，输入*表示所有）: "

echo.
echo [预览] 将要执行以下重命名操作：
echo 目录：%TARGET_DIR%
echo.

set "COUNT=0"
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "NEW_NAME=%PREFIX%%%~nxf"
    echo   "!OLD_NAME!" → "!NEW_NAME!"
    set /a COUNT+=1
)

echo.
echo 共找到 %COUNT% 个文件
echo.
set /p CONFIRM="确认执行？(Y/N): "
if /i not "%CONFIRM%"=="Y" goto MENU

:: 执行重命名
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    ren "%%f" "%PREFIX%%%~nxf"
)

echo [完成] 重命名完成！
pause
goto MENU

:: =============================================
:: 2. 添加后缀
:: =============================================
:ADD_SUFFIX
cls
echo ===== 添加后缀 =====
echo.
set /p TARGET_DIR="请输入目标文件夹路径: "
set /p SUFFIX="请输入要添加的后缀: "
set /p FILE_EXT="请输入文件扩展名（如：txt，输入*表示所有）: "

echo.
echo [预览] 将要执行以下重命名操作：
echo 目录：%TARGET_DIR%
echo.

set "COUNT=0"
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "FILENAME=%%~nf"
    set "EXTENSION=%%~xf"
    set "NEW_NAME=!FILENAME!%SUFFIX%!EXTENSION!"
    echo   "!OLD_NAME!" → "!NEW_NAME!"
    set /a COUNT+=1
)

echo.
echo 共找到 %COUNT% 个文件
echo.
set /p CONFIRM="确认执行？(Y/N): "
if /i not "%CONFIRM%"=="Y" goto MENU

:: 执行重命名
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "FILENAME=%%~nf"
    set "EXTENSION=%%~xf"
    ren "%%f" "!FILENAME!%SUFFIX%!EXTENSION!"
)

echo [完成] 重命名完成！
pause
goto MENU

:: =============================================
:: 3. 替换文本
:: =============================================
:REPLACE_TEXT
cls
echo ===== 替换文件名中的文本 =====
echo.
set /p TARGET_DIR="请输入目标文件夹路径: "
set /p OLD_TEXT="请输入要替换的文本: "
set /p NEW_TEXT="请输入新文本: "
set /p FILE_EXT="请输入文件扩展名（如：txt，输入*表示所有）: "

echo.
echo [预览] 将要执行以下重命名操作：
echo 目录：%TARGET_DIR%
echo.

set "COUNT=0"
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "NEW_NAME=!OLD_NAME:%OLD_TEXT%=%NEW_TEXT%!"
    if not "!OLD_NAME!"=="!NEW_NAME!" (
        echo   "!OLD_NAME!" → "!NEW_NAME!"
        set /a COUNT+=1
    )
)

echo.
echo 共找到 %COUNT% 个文件将被修改
echo.
set /p CONFIRM="确认执行？(Y/N): "
if /i not "%CONFIRM%"=="Y" goto MENU

:: 执行重命名
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "NEW_NAME=!OLD_NAME:%OLD_TEXT%=%NEW_TEXT%!"
    if not "!OLD_NAME!"=="!NEW_NAME!" (
        ren "%%f" "!NEW_NAME!"
    )
)

echo [完成] 重命名完成！
pause
goto MENU

:: =============================================
:: 4. 序号命名
:: =============================================
:SERIAL_NUMBER
cls
echo ===== 序号命名 =====
echo.
set /p TARGET_DIR="请输入目标文件夹路径: "
set /p BASE_NAME="请输入基础文件名（如：photo）: "
set /p START_NUM="请输入起始序号（默认1）: "
if "%START_NUM%"=="" set "START_NUM=1"
set /p FILE_EXT="请输入新文件扩展名（如：jpg，输入*保持原扩展名）: "

echo.
echo [预览] 将要执行以下重命名操作：
echo 目录：%TARGET_DIR%
echo.

set "COUNT=0"
for %%f in ("%TARGET_DIR%\*.*") do (
    if %COUNT% lss 5 (
        set "OLD_NAME=%%~nxf"
        if "%FILE_EXT%"=="*" (
            set "NEW_NAME=%BASE_NAME%_!START_NUM!%%~xf"
        ) else (
            set "NEW_NAME=%BASE_NAME%_!START_NUM!.%FILE_EXT%"
        )
        echo   "!OLD_NAME!" → "!NEW_NAME!"
    )
    set /a COUNT+=1
    set /a START_NUM+=1
)
if %COUNT% gtr 5 (
    echo   ... 还有 %COUNT% 个文件
)

echo.
echo 共找到 %COUNT% 个文件
echo.
set /p CONFIRM="确认执行？(Y/N): "
if /i not "%CONFIRM%"=="Y" goto MENU

:: 执行重命名（重置计数器）
set "NUM=%START_NUM%"
for %%f in ("%TARGET_DIR%\*.*") do (
    if "%FILE_EXT%"=="*" (
        ren "%%f" "%BASE_NAME%_!NUM!%%~xf"
    ) else (
        ren "%%f" "%BASE_NAME%_!NUM!.%FILE_EXT%"
    )
    set /a NUM+=1
)

echo [完成] 重命名完成！
pause
goto MENU

:: =============================================
:: 5. 删除特定文本
:: =============================================
:DELETE_TEXT
cls
echo ===== 删除文件名中的特定文本 =====
echo.
set /p TARGET_DIR="请输入目标文件夹路径: "
set /p DELETE_TEXT="请输入要删除的文本: "
set /p FILE_EXT="请输入文件扩展名（如：txt，输入*表示所有）: "

echo.
echo [预览] 将要执行以下重命名操作：
echo 目录：%TARGET_DIR%
echo.

set "COUNT=0"
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "NEW_NAME=!OLD_NAME:%DELETE_TEXT%=!"
    if not "!OLD_NAME!"=="!NEW_NAME!" (
        echo   "!OLD_NAME!" → "!NEW_NAME!"
        set /a COUNT+=1
    )
)

echo.
echo 共找到 %COUNT% 个文件将被修改
echo.
set /p CONFIRM="确认执行？(Y/N): "
if /i not "%CONFIRM%"=="Y" goto MENU

:: 执行重命名
for %%f in ("%TARGET_DIR%\*.%FILE_EXT%") do (
    set "OLD_NAME=%%~nxf"
    set "NEW_NAME=!OLD_NAME:%DELETE_TEXT%=!"
    if not "!OLD_NAME!"=="!NEW_NAME!" (
        ren "%%f" "!NEW_NAME!"
    )
)

echo [完成] 重命名完成！
pause
goto MENU
