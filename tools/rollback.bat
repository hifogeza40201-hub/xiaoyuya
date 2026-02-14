@echo off
REM OpenClaw Config Rollback Script for Windows
REM Restores openclaw.json from latest or specified backup

set BACKUP_DIR=%USERPROFILE%\.openclaw
set CONFIG_FILE=%BACKUP_DIR%\openclaw.json

echo ========================================
echo OpenClaw Configuration Rollback
echo ========================================
echo.
echo Available backups (most recent first):
dir /b /o-d %BACKUP_DIR%\openclaw.json.bak.* 2>nul
echo.
echo Usage:
echo   rollback.bat               - Interactive mode
echo   rollback.bat latest        - Restore latest backup
echo   rollback.bat 1             - Restore backup #1 (most recent)
echo   rollback.bat 2             - Restore backup #2
echo.
echo After rollback, run:
echo   openclaw gateway restart
echo ========================================

if "%1"=="latest" goto restore_latest
if "%1"=="1" goto restore_1
if "%1"=="2" goto restore_2
goto interactive

:restore_latest
for /f "tokens=*" %%a in ('dir /b /o-d %BACKUP_DIR%\openclaw.json.bak.* 2^>nul ^| head -1') do set BACKUP_FILE=%%a
goto do_restore

:restore_1
for /f "tokens=*" %%a in ('dir /b /o-d %BACKUP_DIR%\openclaw.json.bak.* 2^>nul ^| head -1') do set BACKUP_FILE=%%a
goto do_restore

:restore_2
for /f "tokens=*" %%a in ('dir /b /o-d %BACKUP_DIR%\openclaw.json.bak.* 2^>nul ^| head -2 ^| tail -1') do set BACKUP_FILE=%%a
goto do_restore

:interactive
echo Enter the backup filename to restore (or press Enter for latest):
set /p BACKUP_FILE="Backup file: "
if "%BACKUP_FILE%"=="" (
  for /f "tokens=*" %%a in ('dir /b /o-d %BACKUP_DIR%\openclaw.json.bak.* 2^>nul ^| head -1') do set BACKUP_FILE=%%a
)

:do_restore
if exist "%BACKUP_DIR%\%BACKUP_FILE%" (
  echo Restoring %BACKUP_FILE%...
  copy "%BACKUP_DIR%\%BACKUP_FILE%" %CONFIG_FILE% >nul
  echo Restore complete!
  echo.
  echo Run: openclaw gateway restart
) else (
  echo Error: Backup file not found!
)
