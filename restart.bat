@echo off
echo [Restart] Closing OpenClaw...
taskkill /f /im node.exe 2>nul
timeout /t 3 /nobreak >nul
echo [Restart] Starting OpenClaw...
openclaw gateway
exit