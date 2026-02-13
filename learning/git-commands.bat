@echo off
REM ###############################################################################
REM Git 常用命令脚本合集 - Windows版本
REM 文件名: git-commands.bat
REM 说明: Windows批处理版本的Git快捷命令
REM 使用方法: 直接运行或添加到PATH
REM ###############################################################################

if "%1"=="" goto :help
if "%1"=="help" goto :help
if "%1"=="init" goto :init
if "%1"=="quick" goto :quick
if "%1"=="feature" goto :feature
if "%1"=="hotfix" goto :hotfix
if "%1"=="home" goto :home
if "%1"=="status" goto :status
if "%1"=="log" goto :log
if "%1"=="cleanup" goto :cleanup
if "%1"=="undo" goto :undo
if "%1"=="backup" goto :backup
goto :help

REM ==================== 基础操作 ====================

:init
if "%2"=="" (
    echo ❌ 用法: git-cmd init ^<仓库名^>
    exit /b 1
)
mkdir %2
cd %2
git init
echo # %2 > README.md
git add README.md
git commit -m "feat: 初始化仓库"
echo ✅ 仓库 '%2' 初始化完成
exit /b

:quick
if "%2"=="" (
    echo ❌ 用法: git-cmd quick ^<提交信息^>
    exit /b 1
)
git add .
git commit -m %2
echo ✅ 提交完成: %2
exit /b

REM ==================== 分支操作 ====================

:feature
if "%2"=="" (
    echo ❌ 用法: git-cmd feature ^<功能名^>
    exit /b 1
)
git checkout -b feature/%2
echo ✅ 已创建并切换到分支: feature/%2
exit /b

:hotfix
if "%2"=="" (
    echo ❌ 用法: git-cmd hotfix ^<修复名^>
    exit /b 1
)
git checkout main 2>nul || git checkout master
git pull
git checkout -b hotfix/%2
echo ✅ 已创建并切换到分支: hotfix/%2
exit /b

:home
git checkout main 2>nul || git checkout master
git pull
echo ✅ 已回到主分支并更新
exit /b

REM ==================== 信息查看 ====================

:status
echo 📊 Git 状态:
git status -s
echo.
echo 📋 最近提交:
git log --oneline -5
exit /b

:log
git log --graph --oneline --all --decorate -20
exit /b

REM ==================== 维护操作 ====================

:cleanup
git remote prune origin
echo ✅ 已清理远程分支引用
echo.
echo 🧹 已合并的本地分支:
git branch --merged | findstr /v "\*" | findstr /v "main master"
exit /b

:undo
echo ⚠️ 确定要放弃所有未提交的修改吗？
set /p confirm="输入 Y 确认: "
if /i "%confirm%"=="Y" (
    git checkout -- .
    git clean -fd
    echo ✅ 所有修改已放弃
) else (
    echo ❌ 操作已取消
)
exit /b

:backup
git add .
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set datetime=%%I
set datetime=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%
git commit -m "WIP: %datetime% 备份"
echo ✅ 工作区已备份
exit /b

REM ==================== 帮助信息 ====================

:help
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                     🚀 Git 快捷命令脚本帮助                               ║
echo ╠══════════════════════════════════════════════════════════════════════════╣
echo ║ 基础操作                                                                  ║
echo ║   git-cmd init ^<名^>       快速初始化新仓库                              ║
echo ║   git-cmd quick ^<消息^>    快速add+commit                                ║
echo ╠══════════════════════════════════════════════════════════════════════════╣
echo ║ 分支操作                                                                  ║
echo ║   git-cmd feature ^<名^>    创建功能分支                                  ║
echo ║   git-cmd hotfix ^<名^>     创建修复分支                                  ║
echo ║   git-cmd home              回到主分支并更新                              ║
echo ╠══════════════════════════════════════════════════════════════════════════╣
echo ║ 信息查看                                                                  ║
echo ║   git-cmd status            简洁状态                                      ║
echo ║   git-cmd log               图形化历史                                    ║
echo ╠══════════════════════════════════════════════════════════════════════════╣
echo ║ 维护操作                                                                  ║
echo ║   git-cmd cleanup           清理已合并分支                                ║
echo ║   git-cmd undo              放弃所有未提交修改                            ║
echo ║   git-cmd backup            备份工作区                                    ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
