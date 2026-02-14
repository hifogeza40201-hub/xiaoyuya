@echo off
REM OpenClaw Config Backup Script for Windows
REM Creates timestamped backups of openclaw.json

set BACKUP_DIR=%USERPROFILE%\.openclaw
set CONFIG_FILE=%BACKUP_DIR%\openclaw.json
set BACKUP_PREFIX=%BACKUP_DIR%\openclaw.json.bak

REM Get timestamp (YYYYMMDDHHMM)
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set dt=%%a
set TIMESTAMP=%dt:~0,12%

REM Create backup
copy %CONFIG_FILE% %BACKUP_PREFIX%.%TIMESTAMP% >nul

echo Backup created: %BACKUP_PREFIX%.%TIMESTAMP%

REM Count backups
dir /b %BACKUP_PREFIX%.* 2>nul | find /c /v "" > %TEMP%\count.tmp
set /p backup_count=<%TEMP%\count.tmp
echo Total backups: %backup_count%

REM Keep only last 10 backups
for /f "skip=10 delims=" %%i in ('dir /b /o-d %BACKUP_PREFIX%.* 2^>nul') do del %%i 2>nul

echo Backup complete!
