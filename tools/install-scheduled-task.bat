@echo off
REM Create OpenClaw Auto Backup Scheduled Task
REM Run as Administrator

echo Creating OpenClaw Auto Backup task...

schtasks /create /tn "OpenClawBackup" /tr "C:\Users\Admin\.openclaw\workspace\tools\backup.bat" /sc HOURLY /mo 3 /ru SYSTEM /f

if %errorlevel% equ 0 (
  echo.
  echo ✅ Scheduled task created successfully!
  echo.
  echo Task Details:
  echo   Name: OpenClawBackup
  echo   Runs every: 3 hours
  echo   Command: backup.bat
  echo.
  echo To verify: schtasks /query /tn "OpenClawBackup"
  echo To run now: schtasks /run /tn "OpenClawBackup"
) else (
  echo ❌ Failed to create task
  echo Please run this script as Administrator
)

pause
