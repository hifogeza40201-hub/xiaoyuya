@echo off
REM Daily Memory Backup Script
REM Runs automatically via cron job

echo [%date% %time%] Starting memory backup...

cd /d C:\Users\Admin\.openclaw\workspace

REM Add all changes
git add .

REM Commit with timestamp
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set dt=%%a
set dateStamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%
git commit -m "Memory backup - %dateStamp%"

REM Push to GitHub
git push origin master

echo [%date% %time%] Backup completed!

REM Send completion signal
echo "backup_complete"
