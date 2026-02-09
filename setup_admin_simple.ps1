# OpenClaw 管理员权限配置 - 简化版
# 请以管理员身份运行 PowerShell，然后粘贴执行

Write-Host "=== OpenClaw 管理员权限配置 ===" -ForegroundColor Cyan

# 检查管理员权限
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ 请以管理员身份运行 PowerShell！" -ForegroundColor Red
    exit
}

# 查找 openclaw
$openclaw = Get-Command openclaw -ErrorAction SilentlyContinue
if ($openclaw) {
    $exe = $openclaw.Source
} else {
    $exe = "$env:LOCALAPPDATA\Programs\openclaw\openclaw.exe"
    if (-not (Test-Path $exe)) {
        $exe = "$env:APPDATA\npm\openclaw.exe"
    }
}

Write-Host "OpenClaw 路径: $exe" -ForegroundColor Green

# 删除旧任务
Unregister-ScheduledTask -TaskName "OpenClaw-Admin" -Confirm:$false -ErrorAction SilentlyContinue

# 创建新任务
$action = New-ScheduledTaskAction -Execute $exe -Argument "gateway"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName "OpenClaw-Admin" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "✅ 配置完成！重启后生效" -ForegroundColor Green
Write-Host "立即运行: Start-ScheduledTask -TaskName 'OpenClaw-Admin'" -ForegroundColor Yellow
