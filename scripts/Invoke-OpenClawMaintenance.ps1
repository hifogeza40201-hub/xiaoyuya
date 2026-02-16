#requires -Version 5.1
#requires -Modules OpenClaw-Monitor, Git-OpenClawHelper

<#
.SYNOPSIS
    OpenClaw每日维护自动化脚本
.DESCRIPTION
    综合今日学习的PowerShell进阶知识，创建一站式维护工具
    整合：模块系统 + 错误处理 + 高级函数 + 日志记录
.PARAMETER Task
    维护任务：All | Backup | GitSync | Cleanup | HealthCheck | Report
.PARAMETER ConfigPath
    配置文件路径
.PARAMETER Silent
    静默模式（仅记录日志，不输出到控制台）
.EXAMPLE
    .\Invoke-OpenClawMaintenance.ps1 -Task All
    执行所有维护任务
.EXAMPLE
    .\Invoke-OpenClawMaintenance.ps1 -Task Backup -Silent
    静默执行备份任务
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Position = 0)]
    [ValidateSet('All', 'Backup', 'GitSync', 'Cleanup', 'HealthCheck', 'Report')]
    [string]$Task = 'All',

    [Parameter()]
    [ValidateScript({
        if ($_ -and !(Test-Path $_)) {
            throw "配置文件不存在: $_"
        }
        $true
    })]
    [string]$ConfigPath = "$PSScriptRoot\..\config\maintenance-config.json",

    [Parameter()]
    [switch]$Silent,

    [Parameter()]
    [switch]$Force
)

#region 配置和初始化
$Script:Config = @{
    WorkspacePath = "$env:USERPROFILE\.openclaw\workspace"
    BackupPath = "D:\OpenClaw-Backups"
    GitRemote = "origin"
    GitBranch = "main"
    KeepBackupVersions = 7
    CleanupDays = 30
    LogPath = "$env:TEMP\openclaw-maintenance.log"
    ReportPath = "$env:TEMP\openclaw-maintenance-report.json"
}

# 加载外部配置
if (Test-Path $ConfigPath) {
    try {
        $externalConfig = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        $externalConfig.PSObject.Properties | ForEach-Object {
            $Script:Config[$_.Name] = $_.Value
        }
    } catch {
        Write-Warning "无法加载配置文件，使用默认配置"
    }
}
#endregion

#region 日志系统
function Write-MaintenanceLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [Parameter()]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS', 'DEBUG', 'TASK')]
        [string]$Level = 'INFO',

        [Parameter()]
        [string]$TaskName = ''
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $taskPrefix = if ($TaskName) { "[$TaskName] " } else { "" }
    $logEntry = "[$timestamp] [$Level] $taskPrefix$Message"
    
    # 确保日志目录存在
    $logDir = Split-Path $Script:Config.LogPath -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # 写入日志文件
    Add-Content -Path $Script:Config.LogPath -Value $logEntry
    
    # 控制台输出（非静默模式）
    if (!$Silent) {
        switch ($Level) {
            'ERROR'   { Write-Host $logEntry -ForegroundColor Red }
            'WARN'    { Write-Host $logEntry -ForegroundColor Yellow }
            'SUCCESS' { Write-Host $logEntry -ForegroundColor Green }
            'TASK'    { Write-Host $logEntry -ForegroundColor Cyan }
            'DEBUG'   { Write-Host $logEntry -ForegroundColor Gray }
            default   { Write-Host $logEntry }
        }
    }
}
#endregion

#region 任务函数
function Invoke-MaintenanceBackup {
    [CmdletBinding()]
    param()

    $taskName = 'Backup'
    Write-MaintenanceLog "开始备份任务..." -Level 'TASK' -TaskName $taskName

    try {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupName = "workspace_$timestamp.zip"
        $backupPath = Join-Path $Script:Config.BackupPath $backupName

        # 检查源路径
        if (!(Test-Path $Script:Config.WorkspacePath)) {
            throw "工作区路径不存在: $($Script:Config.WorkspacePath)"
        }

        # 确保备份目录存在
        if (!(Test-Path $Script:Config.BackupPath)) {
            New-Item -ItemType Directory -Path $Script:Config.BackupPath -Force | Out-Null
        }

        # 执行备份
        Write-MaintenanceLog "正在压缩工作区..." -Level 'INFO' -TaskName $taskName
        Compress-Archive -Path "$($Script:Config.WorkspacePath)\*" -DestinationPath $backupPath -Force

        $backupSize = (Get-Item $backupPath).Length / 1MB
        Write-MaintenanceLog "备份完成: $backupName ($([math]::Round($backupSize, 2)) MB)" -Level 'SUCCESS' -TaskName $taskName

        # 清理旧备份
        $backups = Get-ChildItem -Path $Script:Config.BackupPath -Filter "workspace_*.zip" | Sort-Object CreationTime -Descending
        if ($backups.Count -gt $Script:Config.KeepBackupVersions) {
            $backups | Select-Object -Skip $Script:Config.KeepBackupVersions | Remove-Item -Force
            Write-MaintenanceLog "已清理旧备份版本" -Level 'INFO' -TaskName $taskName
        }

        return @{ Success = $true; BackupPath = $backupPath; SizeMB = [math]::Round($backupSize, 2) }

    } catch {
        Write-MaintenanceLog "备份失败: $_" -Level 'ERROR' -TaskName $taskName
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Invoke-MaintenanceGitSync {
    [CmdletBinding()]
    param()

    $taskName = 'GitSync'
    Write-MaintenanceLog "开始Git同步任务..." -Level 'TASK' -TaskName $taskName

    try {
        Push-Location $Script:Config.WorkspacePath

        # 检查Git仓库
        if (!(Test-Path '.git')) {
            Write-MaintenanceLog "当前目录不是Git仓库，跳过同步" -Level 'WARN' -TaskName $taskName
            return @{ Success = $true; Skipped = $true }
        }

        # 检查状态
        $status = git status --short 2>$null
        if ($status) {
            Write-MaintenanceLog "检测到未提交的更改，准备提交..." -Level 'INFO' -TaskName $taskName
            
            git add .
            $commitMsg = "自动维护提交 $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
            git commit -m $commitMsg
            
            Write-MaintenanceLog "已提交更改: $commitMsg" -Level 'INFO' -TaskName $taskName
        } else {
            Write-MaintenanceLog "没有需要提交的更改" -Level 'INFO' -TaskName $taskName
        }

        # 拉取更新
        Write-MaintenanceLog "正在拉取远程更新..." -Level 'INFO' -TaskName $taskName
        $pullResult = git pull $Script:Config.GitRemote $Script:Config.GitBranch 2>&1
        Write-MaintenanceLog "拉取完成" -Level 'SUCCESS' -TaskName $taskName

        # 推送更改
        if ($status) {
            Write-MaintenanceLog "正在推送更改..." -Level 'INFO' -TaskName $taskName
            git push $Script:Config.GitRemote $Script:Config.GitBranch
            Write-MaintenanceLog "推送完成" -Level 'SUCCESS' -TaskName $taskName
        }

        Pop-Location
        return @{ Success = $true }

    } catch {
        Write-MaintenanceLog "Git同步失败: $_" -Level 'ERROR' -TaskName $taskName
        Pop-Location
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Invoke-MaintenanceCleanup {
    [CmdletBinding()]
    param()

    $taskName = 'Cleanup'
    Write-MaintenanceLog "开始清理任务..." -Level 'TASK' -TaskName $taskName

    $cleanupResults = @{
        TempFiles = 0
        OldLogs = 0
        EmptyDirs = 0
    }

    try {
        # 清理临时文件
        $tempFiles = Get-ChildItem -Path $env:TEMP -Filter "openclaw-*" -File | 
            Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$Script:Config.CleanupDays) }
        
        foreach ($file in $tempFiles) {
            Remove-Item $file.FullName -Force
            $cleanupResults.TempFiles++
        }
        Write-MaintenanceLog "清理了 $($cleanupResults.TempFiles) 个临时文件" -Level 'INFO' -TaskName $taskName

        # 清理旧日志
        $logDir = Split-Path $Script:Config.LogPath -Parent
        if (Test-Path $logDir) {
            $oldLogs = Get-ChildItem -Path $logDir -Filter "*.log" | 
                Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$Script:Config.CleanupDays) }
            
            foreach ($log in $oldLogs) {
                Remove-Item $log.FullName -Force
                $cleanupResults.OldLogs++
            }
            Write-MaintenanceLog "清理了 $($cleanupResults.OldLogs) 个旧日志文件" -Level 'INFO' -TaskName $taskName
        }

        return @{ Success = $true; Results = $cleanupResults }

    } catch {
        Write-MaintenanceLog "清理失败: $_" -Level 'ERROR' -TaskName $taskName
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Invoke-MaintenanceHealthCheck {
    [CmdletBinding()]
    param()

    $taskName = 'HealthCheck'
    Write-MaintenanceLog "开始健康检查..." -Level 'TASK' -TaskName $taskName

    $healthResults = @{
        DiskSpace = @{}
        Memory = @{}
        Gateway = @{}
        GitStatus = @{}
    }

    try {
        # 磁盘空间检查
        Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } | ForEach-Object {
            $freePercent = [math]::Round(($_.FreeSpace / $_.Size) * 100, 2)
            $healthResults.DiskSpace[$_.DeviceID] = @{
                FreePercent = $freePercent
                Status = if ($freePercent -lt 10) { 'Warning' } else { 'OK' }
            }
        }

        # 内存检查
        $memory = Get-CimInstance -ClassName Win32_OperatingSystem
        $freePercent = [math]::Round(($memory.FreePhysicalMemory / $memory.TotalVisibleMemorySize) * 100, 2)
        $healthResults.Memory = @{
            FreePercent = $freePercent
            Status = if ($freePercent -lt 10) { 'Warning' } else { 'OK' }
        }

        # Gateway检查
        $gatewayTest = Test-NetConnection -ComputerName localhost -Port 18789 -WarningAction SilentlyContinue
        $healthResults.Gateway = @{
            Status = if ($gatewayTest.TcpTestSucceeded) { 'OK' } else { 'Error' }
        }

        # Git状态检查
        Push-Location $Script:Config.WorkspacePath
        $gitStatus = git status --short 2>$null
        $healthResults.GitStatus = @{
            HasChanges = ![string]::IsNullOrWhiteSpace($gitStatus)
            Status = if ($gitStatus) { 'Warning' } else { 'OK' }
        }
        Pop-Location

        Write-MaintenanceLog "健康检查完成" -Level 'SUCCESS' -TaskName $taskName
        return @{ Success = $true; Results = $healthResults }

    } catch {
        Write-MaintenanceLog "健康检查失败: $_" -Level 'ERROR' -TaskName $taskName
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}
#endregion

#region 主程序
Write-MaintenanceLog "=== OpenClaw维护任务开始 ===" -Level 'TASK'
Write-MaintenanceLog "执行任务: $Task" -Level 'INFO'

$executionResults = @{
    StartTime = Get-Date -Format "o"
    Task = $Task
    Results = @{}
    Success = $true
}

# 执行选定的任务
if ($Task -in @('All', 'Backup')) {
    $executionResults.Results.Backup = Invoke-MaintenanceBackup
    if (!$executionResults.Results.Backup.Success) { $executionResults.Success = $false }
}

if ($Task -in @('All', 'GitSync')) {
    $executionResults.Results.GitSync = Invoke-MaintenanceGitSync
    if (!$executionResults.Results.GitSync.Success) { $executionResults.Success = $false }
}

if ($Task -in @('All', 'Cleanup')) {
    $executionResults.Results.Cleanup = Invoke-MaintenanceCleanup
    if (!$executionResults.Results.Cleanup.Success) { $executionResults.Success = $false }
}

if ($Task -in @('All', 'HealthCheck')) {
    $executionResults.Results.HealthCheck = Invoke-MaintenanceHealthCheck
    if (!$executionResults.Results.HealthCheck.Success) { $executionResults.Success = $false }
}

# 生成报告
$executionResults.EndTime = Get-Date -Format "o"
$executionResults | ConvertTo-Json -Depth 5 | Set-Content $Script:Config.ReportPath

# 输出总结
Write-MaintenanceLog "=== 维护任务完成 ===" -Level 'TASK'
Write-MaintenanceLog "总体状态: $(if ($executionResults.Success) { '成功' } else { '有失败' })" -Level $(if ($executionResults.Success) { 'SUCCESS' } else { 'WARN' })
Write-MaintenanceLog "报告已保存: $($Script:Config.ReportPath)" -Level 'INFO'

# 返回结果（管道支持）
return [PSCustomObject]$executionResults
#endregion
