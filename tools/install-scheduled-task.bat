@echo off
REM Create OpenClaw Auto Backup Scheduled Task
REM Run as Administrator

echo Creating OpenClaw Auto Backup tasks...

REM 任务1: 中午12点备份
schtasks /create /tn "OpenClawBackup-Noon" /tr "C:\Users\Admin\.openclaw\workspace\tools\backup.bat" /sc DAILY /st 12:00:00 /ru SYSTEM /f

REM 任务2: 晚上12点备份
schtasks /create /tn "OpenClawBackup-Midnight" /tr "C:\Users\Admin\.openclaw\workspace\tools\backup.bat" /sc DAILY /st 00:00:00 /ru SYSTEM /f

if %errorlevel% equ 0 (
  echo.
  echo ✅ 定时任务创建成功!
  echo.
  echo 任务详情:
  echo   OpenClawBackup-Noon    - 每天中午 12:00
  echo   OpenClawBackup-Midnight - 每天晚上 12:00
  echo.
  echo 备份命令: backup.bat
  echo 保留数量: 10个备份(最近5天)
  echo.
  echo 立即运行: schtasks /run /tn "OpenClawBackup-Noon"
) else (
  echo ❌ 创建失败，请以管理员身份运行
)

pause
