#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw工作区备份脚本
.DESCRIPTION
    使用PowerShell模块方式组织的备份脚本，支持增量备份、错误处理和日志记录
.PARAMETER SourcePath
    要备份的源目录
.PARAMETER BackupPath
    备份目标目录
.PARAMETER Mode
    备份模式：Full(完整) | Incremental(增量) | Mirror(镜像)
.PARAMETER KeepVersions
    保留的备份版本数量
.PARAMETER LogPath
    日志文件路径
.EXAMPLE
    .\Backup-OpenClawWorkspace.ps1 -Mode Incremental
    执行增量备份
.EXAMPLE
    .\Backup-OpenClawWorkspace.ps1 -SourcePath "C:\Custom\Path" -Mode Full -KeepVersions 10
    自定义源路径，执行完整备份，保留10个版本
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter()]
    [ValidateScript({
        if (!(Test-Path $_)) {
            throw "源路径不存在: $_"
        }
        $true
    })]
    [string]$SourcePath = "$env:USERPROFILE\.openclaw\workspace",

    [Parameter()]
    [string]$BackupPath = "D:\OpenClaw-Backups",

    [Parameter()]
    [ValidateSet('Full', 'Incremental', 'Mirror')]
    [string]$Mode = 'Incremental',

    [Parameter()]
    [ValidateRange(1, 100)]
    [int]$KeepVersions = 7,

    [Parameter()]
    [string]$LogPath = "$env:TEMP\openclaw-backup.log",

    [switch]$Force
)

#region 日志函数
function Write-BackupLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [Parameter()]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS', 'DEBUG')]
        [string]$Level = 'INFO'
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 确保日志目录存在
    $logDir = Split-Path $LogPath -Parent
    if (!(Test-Path $logDir)) {
        try {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        } catch {
            Write-Warning "无法创建日志目录: $_"
        }
    }
    
    # 写入日志文件
    try {
        Add-Content -Path $LogPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {
        # 如果无法写入文件，至少输出到控制台
    }
    
    # 控制台输出（带颜色）
    switch ($Level) {
        'ERROR'   { Write-Host $logEntry -ForegroundColor Red }
        'WARN'    { Write-Host $logEntry -ForegroundColor Yellow }
        'SUCCESS' { Write-Host $logEntry -ForegroundColor Green }
        'DEBUG'   { Write-Host $logEntry -ForegroundColor Gray }
        default   { Write-Host $logEntry }
    }
}
#endregion

#region 备份核心函数
function Invoke-FullBackup {
    [CmdletBinding()]
    param(
        [string]$Source,
        [string]$Destination,
        [string]$BackupName
    )

    $backupFullPath = Join-Path $Destination $BackupName
    
    try {
        Write-BackupLog "开始完整备份到: $backupFullPath" -Level 'INFO'
        
        # 使用Compress-Archive进行压缩备份
        Compress-Archive -Path "$Source\*" -DestinationPath $backupFullPath -Force -ErrorAction Stop
        
        $backupSize = (Get-Item $backupFullPath).Length / 1MB
        Write-BackupLog "完整备份完成，大小: $([math]::Round($backupSize, 2)) MB" -Level 'SUCCESS'
        
        return $true
    } catch {
        Write-BackupLog "完整备份失败: $_" -Level 'ERROR'
        return $false
    }
}

function Invoke-IncrementalBackup {
    [CmdletBinding()]
    param(
        [string]$Source,
        [string]$Destination,
        [string]$BackupName
    )

    $backupFullPath = Join-Path $Destination $BackupName
    $manifestPath = Join-Path $Destination ".backup-manifest.json"
    
    try {
        Write-BackupLog "开始增量备份..." -Level 'INFO'
        
        # 读取上次备份的清单
        $lastBackupTime = $null
        if (Test-Path $manifestPath) {
            try {
                $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
                $lastBackupTime = [datetime]$manifest.LastBackupTime
                Write-BackupLog "上次备份时间: $lastBackupTime" -Level 'DEBUG'
            } catch {
                Write-BackupLog "无法读取备份清单，将执行完整备份" -Level 'WARN'
            }
        }
        
        # 收集需要备份的文件
        $filesToBackup = Get-ChildItem -Path $Source -Recurse -File | Where-Object {
            !$lastBackupTime -or $_.LastWriteTime -gt $lastBackupTime
        }
        
        if ($filesToBackup.Count -eq 0) {
            Write-BackupLog "没有需要备份的新文件或修改过的文件" -Level 'INFO'
            return $true
        }
        
        Write-BackupLog "找到 $($filesToBackup.Count) 个需要备份的文件" -Level 'INFO'
        
        # 创建临时目录存放增量文件
        $tempDir = Join-Path $env:TEMP "OpenClaw-Incremental-$(Get-Date -Format 'yyyyMMddHHmmss')"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        try {
            # 复制文件到临时目录
            foreach ($file in $filesToBackup) {
                $relativePath = $file.FullName.Substring($Source.Length + 1)
                $destPath = Join-Path $tempDir $relativePath
                $destDir = Split-Path $destPath -Parent
                
                if (!(Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                
                Copy-Item $file.FullName $destPath -Force
            }
            
            # 压缩备份
            Compress-Archive -Path "$tempDir\*" -DestinationPath $backupFullPath -Force
            
            $backupSize = (Get-Item $backupFullPath).Length / 1MB
            Write-BackupLog "增量备份完成，大小: $([math]::Round($backupSize, 2)) MB" -Level 'SUCCESS'
            
        } finally {
            # 清理临时目录
            Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        return $true
        
    } catch {
        Write-BackupLog "增量备份失败: $_" -Level 'ERROR'
        return $false
    }
}

function Invoke-MirrorBackup {
    [CmdletBinding()]
    param(
        [string]$Source,
        [string]$Destination
    )

    $mirrorPath = Join-Path $Destination "mirror-$(Get-Date -Format 'yyyyMMdd')"
    
    try {
        Write-BackupLog "开始镜像备份到: $mirrorPath" -Level 'INFO'
        
        # 使用robocopy进行镜像同步
        $robocopyArgs = @(
            '"$Source"',
            '"$mirrorPath"',
            '/MIR',           # 镜像模式
            '/R:3',           # 重试3次
            '/W:5',           # 等待5秒
            '/NP',            # 不显示进度
            '/NDL',           # 不显示目录列表
            '/NFL'            # 不显示文件列表
        )
        
        $process = Start-Process -FilePath "robocopy" -ArgumentList $robocopyArgs -Wait -PassThru -WindowStyle Hidden
        
        if ($process.ExitCode -le 7) {  # robocopy 0-7表示成功
            Write-BackupLog "镜像备份完成" -Level 'SUCCESS'
            return $true
        } else {
            Write-BackupLog "镜像备份可能存在问题，退出码: $($process.ExitCode)" -Level 'WARN'
            return $false
        }
        
    } catch {
        Write-BackupLog "镜像备份失败: $_" -Level 'ERROR'
        return $false
    }
}

function Clear-OldBackups {
    [CmdletBinding()]
    param(
        [string]$BackupDirectory,
        [int]$KeepCount
    )

    try {
        $backups = Get-ChildItem -Path $BackupDirectory -Filter "workspace_*.zip" | 
            Sort-Object CreationTime -Descending
        
        if ($backups.Count -gt $KeepCount) {
            $backupsToDelete = $backups | Select-Object -Skip $KeepCount
            
            Write-BackupLog "清理 $($backupsToDelete.Count) 个旧备份版本" -Level 'INFO'
            
            foreach ($backup in $backupsToDelete) {
                Remove-Item $backup.FullName -Force
                Write-BackupLog "已删除: $($backup.Name)" -Level 'DEBUG'
            }
        }
    } catch {
        Write-BackupLog "清理旧备份时出错: $_" -Level 'WARN'
    }
}
#endregion

#region 主程序
Write-BackupLog "=== OpenClaw工作区备份开始 ===" -Level 'INFO'
Write-BackupLog "备份模式: $Mode" -Level 'INFO'
Write-BackupLog "源路径: $SourcePath" -Level 'INFO'
Write-BackupLog "备份路径: $BackupPath" -Level 'INFO'

try {
    # 验证源路径
    if (!(Test-Path $SourcePath)) {
        throw "源路径不存在: $SourcePath"
    }
    
    # 确保备份目录存在
    if (!(Test-Path $BackupPath)) {
        if ($PSCmdlet.ShouldProcess($BackupPath, "创建备份目录")) {
            New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
        }
    }
    
    # 生成备份文件名
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = switch ($Mode) {
        'Full'        { "workspace_full_$timestamp.zip" }
        'Incremental' { "workspace_incr_$timestamp.zip" }
        default       { "workspace_$timestamp.zip" }
    }
    
    # 执行备份
    $success = $false
    switch ($Mode) {
        'Full'        { $success = Invoke-FullBackup -Source $SourcePath -Destination $BackupPath -BackupName $backupName }
        'Incremental' { $success = Invoke-IncrementalBackup -Source $SourcePath -Destination $BackupPath -BackupName $backupName }
        'Mirror'      { $success = Invoke-MirrorBackup -Source $SourcePath -Destination $BackupPath }
    }
    
    # 更新清单
    if ($success -and ($Mode -ne 'Mirror')) {
        $manifest = @{
            LastBackupTime = (Get-Date -Format "o")
            Mode = $Mode
            LastBackupName = $backupName
            SourcePath = $SourcePath
        }
        $manifestPath = Join-Path $BackupPath ".backup-manifest.json"
        $manifest | ConvertTo-Json | Set-Content $manifestPath
    }
    
    # 清理旧备份
    if ($success -and ($Mode -ne 'Mirror')) {
        Clear-OldBackups -BackupDirectory $BackupPath -KeepCount $KeepVersions
    }
    
    if ($success) {
        Write-BackupLog "=== 备份成功完成 ===" -Level 'SUCCESS'
        exit 0
    } else {
        Write-BackupLog "=== 备份失败 ===" -Level 'ERROR'
        exit 1
    }
    
} catch {
    Write-BackupLog "备份过程中发生错误: $_" -Level 'ERROR'
    Write-BackupLog "错误详情: $($_.Exception.StackTrace)" -Level 'DEBUG'
    exit 1
}
#endregion
