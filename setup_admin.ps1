# OpenClaw 管理员权限配置脚本
# 以管理员运行此脚本

$ErrorActionPreference = "Stop"

Write-Host "=== OpenClaw 管理员权限配置 ===" -ForegroundColor Cyan

# 1. 检查是否以管理员运行
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ 错误：请以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host "右键点击 PowerShell → 以管理员身份运行，然后执行此脚本" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 已确认管理员权限" -ForegroundColor Green

# 2. 查找 openclaw 路径
try {
    $openclawPath = (Get-Command openclaw).Source
    Write-Host "✅ 找到 OpenClaw: $openclawPath" -ForegroundColor Green
} catch {
    # 尝试常见路径
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\openclaw\openclaw.exe",
        "$env:PROGRAMFILES\openclaw\openclaw.exe",
        "$env:PROGRAMFILES(x86)\openclaw\openclaw.exe",
        "$env:APPDATA\npm\openclaw.exe",
        "C:\Program Files\openclaw\openclaw.exe"
    )
    
    $openclawPath = $null
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $openclawPath = $path
            break
        }
    }
    
    if (-not $openclawPath) {
        Write-Host "❌ 未找到 openclaw.exe，请手动指定路径" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 找到 OpenClaw: $openclawPath" -ForegroundColor Green
}

# 3. 删除旧任务（如果存在）
$taskName = "OpenClaw-Admin"
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 已清理旧任务" -ForegroundColor Green
} catch {}

# 4. 创建新任务
Write-Host "正在创建计划任务..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction -Execute $openclawPath -Argument "gateway"

# 触发器：用户登录时启动
$trigger = New-ScheduledTaskTrigger -AtLogOn

# 设置：最高权限、不停止、网络可用时运行
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -DontStopOnIdleEnd

# 主体：当前用户，最高权限
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# 注册任务
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force
    
    Write-Host "✅ 计划任务创建成功！" -ForegroundColor Green
} catch {
    Write-Host "❌ 创建任务失败: $_" -ForegroundColor Red
    exit 1
}

# 5. 验证任务
$task = Get-ScheduledTask -TaskName $taskName
if ($task) {
    Write-Host "✅ 任务状态: $($task.State)" -ForegroundColor Green
    Write-Host "✅ 运行级别: $($task.Principal.RunLevel)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 配置完成 ===" -ForegroundColor Cyan
Write-Host "📋 任务名称: $taskName" -ForegroundColor White
Write-Host "🚀 启动方式: 用户登录时自动启动" -ForegroundColor White
Write-Host "👑 权限级别: 管理员 (Highest)" -ForegroundColor White
Write-Host ""
Write-Host "💡 现在你可以：" -ForegroundColor Yellow
Write-Host "   1. 重启电脑，OpenClaw 会自动以管理员运行" -ForegroundColor White
Write-Host "   2. 或在任务计划程序中手动运行此任务" -ForegroundColor White
Write-Host "   3. 或执行: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
