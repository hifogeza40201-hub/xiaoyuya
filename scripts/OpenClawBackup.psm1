#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw工作区备份模块 - 支持增量备份、错误处理和日志记录
.DESCRIPTION
    本模块提供工作区备份功能，支持：
    - 增量备份（基于时间戳或文件哈希）
    - 完整的错误处理和日志记录
    - 可配置的备份策略
    - 压缩和清理旧备份
.EXAMPLE
    Import-Module .\OpenClawBackup.psm1
    Start-WorkspaceBackup -ConfigPath .\backup-config.json
.NOTES
    作者: OpenClaw Automation
    版本: 1.0.0
    需要 PowerShell 5.1+
#>

# 模块级别变量
$script:ModuleConfig = @{
    LogPath = "$env:TEMP\OpenClawBackup.log"
    DefaultConfig = @{
        SourcePath = "$env:USERPROFILE\.openclaw\workspace"
        BackupRoot = "$env:USERPROFILE\Backups\OpenClaw"
        RetentionDays = 30
        CompressionLevel = 'Optimal'
        ExcludePatterns = @('*.tmp', '*.log', 'node_modules', '.git')
        IncrementalMode = 'Timestamp'  # 'Timestamp' 或 'Hash'
    }
}

# 日志记录函数
function Write-BackupLog {
    <#
    .SYNOPSIS
        写入备份日志
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        
        [ValidateSet('Info', 'Warning', 'Error', 'Success')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 控制台输出（带颜色）
    switch ($Level) {
        'Error'   { Write-Host $logEntry -ForegroundColor Red }
        'Warning' { Write-Host $logEntry -ForegroundColor Yellow }
        'Success' { Write-Host $logEntry -ForegroundColor Green }
        default   { Write-Host $logEntry }
    }
    
    # 写入日志文件
    try {
        Add-Content -Path $script:ModuleConfig.LogPath -Value $logEntry -ErrorAction Stop
    }
    catch {
        Write-Warning "无法写入日志文件: $_"
    }
}

# 加载配置文件
function Import-BackupConfig {
    <#
    .SYNOPSIS
        导入备份配置文件
    #>
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [Parameter()]
        [string]$ConfigPath
    )
    
    try {
        $config = $script:ModuleConfig.DefaultConfig.Clone()
        
        if ($ConfigPath -and (Test-Path $ConfigPath)) {
            Write-BackupLog "正在加载配置文件: $ConfigPath"
            $jsonConfig = Get-Content $ConfigPath -Raw | ConvertFrom-Json
            
            # 合并配置
            foreach ($key in $jsonConfig.PSObject.Properties.Name) {
                $config[$key] = $jsonConfig.$key
            }
        }
        else {
            Write-BackupLog "使用默认配置" -Level 'Warning'
        }
        
        # 验证配置
        if (-not (Test-Path $config.SourcePath)) {
            throw "源路径不存在: $($config.SourcePath)"
        }
        
        # 确保备份根目录存在
        if (-not (Test-Path $config.BackupRoot)) {
            New-Item -ItemType Directory -Path $config.BackupRoot -Force | Out-Null
            Write-BackupLog "创建备份目录: $($config.BackupRoot)" -Level 'Success'
        }
        
        return $config
    }
    catch {
        Write-BackupLog "配置加载失败: $_" -Level 'Error'
        throw
    }
}

# 获取文件哈希（用于增量备份）
function Get-FileHashQuick {
    <#
    .SYNOPSIS
        快速计算文件哈希
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [System.IO.FileInfo]$File
    )
    
    process {
        try {
            $stream = [System.IO.File]::OpenRead($File.FullName)
            $hash = [System.BitConverter]::ToString(
                [System.Security.Cryptography.MD5]::Create().ComputeHash($stream)
            ).Replace('-', '')
            $stream.Close()
            return $hash
        }
        catch {
            Write-BackupLog "无法计算文件哈希: $($File.FullName)" -Level 'Warning'
            return $null
        }
    }
}

# 核心备份函数
function Start-WorkspaceBackup {
    <#
    .SYNOPSIS
        执行工作区备份
    .DESCRIPTION
        执行增量备份，支持时间戳或哈希模式
    .EXAMPLE
        Start-WorkspaceBackup -ConfigPath .\config.json -Verbose
    .EXAMPLE
        Start-WorkspaceBackup -SourcePath "C:\Work" -BackupRoot "D:\Backups"
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter()]
        [string]$ConfigPath,
        
        [Parameter()]
        [string]$SourcePath,
        
        [Parameter()]
        [string]$BackupRoot,
        
        [ValidateSet('Timestamp', 'Hash')]
        [string]$IncrementalMode = 'Timestamp'
    )
    
    begin {
        Write-BackupLog "=== 备份任务开始 ==="
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    }
    
    process {
        try {
            # 加载配置
            $config = Import-BackupConfig -ConfigPath $ConfigPath
            
            # 参数覆盖配置
            if ($SourcePath) { $config.SourcePath = $SourcePath }
            if ($BackupRoot) { $config.BackupRoot = $BackupRoot }
            $config.IncrementalMode = $IncrementalMode
            
            Write-BackupLog "源路径: $($config.SourcePath)"
            Write-BackupLog "备份模式: $($config.IncrementalMode)"
            
            # 生成备份名称
            $backupName = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            $backupPath = Join-Path $config.BackupRoot $backupName
            
            # 检查是否需要执行
            if (-not $PSCmdlet.ShouldProcess($config.SourcePath, "备份到 $backupPath")) {
                return
            }
            
            # 查找上次备份（用于增量）
            $lastBackup = Get-ChildItem $config.BackupRoot -Directory -Filter 'backup_*' |
                Sort-Object CreationTime -Descending | Select-Object -First 1
            
            # 收集需要备份的文件
            $files = Get-ChildItem $config.SourcePath -Recurse -File | Where-Object {
                $file = $_
                $exclude = $false
                foreach ($pattern in $config.ExcludePatterns) {
                    if ($file.Name -like $pattern) {
                        $exclude = $true
                        break
                    }
                }
                -not $exclude
            }
            
            $stats = @{
                TotalFiles = $files.Count
                NewFiles = 0
                ModifiedFiles = 0
                UnchangedFiles = 0
                Errors = 0
            }
            
            # 创建备份目录
            New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
            
            # 处理每个文件
            foreach ($file in $files) {
                try {
                    $relativePath = $file.FullName.Substring($config.SourcePath.Length + 1)
                    $targetPath = Join-Path $backupPath $relativePath
                    $targetDir = Split-Path $targetPath -Parent
                    
                    # 检查增量条件
                    $needBackup = $true
                    
                    if ($lastBackup -and $config.IncrementalMode -eq 'Timestamp') {
                        $lastFile = Join-Path $lastBackup.FullName $relativePath
                        if (Test-Path $lastFile) {
                            $lastWriteTime = (Get-Item $lastFile).LastWriteTime
                            if ($file.LastWriteTime -le $lastWriteTime) {
                                $needBackup = $false
                                $stats.UnchangedFiles++
                            }
                        }
                    }
                    elseif ($lastBackup -and $config.IncrementalMode -eq 'Hash') {
                        # 哈希模式（较慢但更精确）
                        $lastFile = Join-Path $lastBackup.FullName $relativePath
                        if (Test-Path $lastFile) {
                            $currentHash = $file | Get-FileHashQuick
                            $lastHash = Get-Item $lastFile | Get-FileHashQuick
                            if ($currentHash -eq $lastHash) {
                                $needBackup = $false
                                $stats.UnchangedFiles++
                            }
                        }
                    }
                    
                    if ($needBackup) {
                        # 确保目标目录存在
                        if (-not (Test-Path $targetDir)) {
                            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                        }
                        
                        Copy-Item $file.FullName $targetPath -Force
                        
                        if ($lastBackup) {
                            $stats.ModifiedFiles++
                        }
                        else {
                            $stats.NewFiles++
                        }
                    }
                    
                    Write-Verbose "处理: $relativePath"
                }
                catch {
                    $stats.Errors++
                    Write-BackupLog "备份失败 [$($file.FullName)]: $_" -Level 'Error'
                }
            }
            
            # 创建备份清单
            $manifest = @{
                BackupDate = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
                SourcePath = $config.SourcePath
                BackupPath = $backupPath
                Mode = $config.IncrementalMode
                Statistics = $stats
                ComputerName = $env:COMPUTERNAME
                UserName = $env:USERNAME
            }
            
            $manifestPath = Join-Path $backupPath 'manifest.json'
            $manifest | ConvertTo-Json -Depth 3 | Out-File $manifestPath
            
            Write-BackupLog "备份完成: $backupName" -Level 'Success'
            Write-BackupLog "统计 - 新文件: $($stats.NewFiles), 修改: $($stats.ModifiedFiles), 未变: $($stats.UnchangedFiles), 错误: $($stats.Errors)"
            
            # 清理旧备份
            Invoke-BackupCleanup -Config $config
            
            return [PSCustomObject]$manifest
        }
        catch {
            Write-BackupLog "备份任务失败: $_" -Level 'Error'
            throw
        }
    }
    
    end {
        $stopwatch.Stop()
        Write-BackupLog "=== 备份任务结束 (耗时: $($stopwatch.Elapsed.ToString('hh\:mm\:ss'))) ==="
    }
}

# 清理旧备份
function Invoke-BackupCleanup {
    <#
    .SYNOPSIS
        清理超过保留期限的旧备份
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [hashtable]$Config
    )
    
    try {
        $cutoffDate = (Get-Date).AddDays(-$Config.RetentionDays)
        $oldBackups = Get-ChildItem $Config.BackupRoot -Directory -Filter 'backup_*' |
            Where-Object { $_.CreationTime -lt $cutoffDate }
        
        foreach ($backup in $oldBackups) {
            try {
                Remove-Item $backup.FullName -Recurse -Force
                Write-BackupLog "删除旧备份: $($backup.Name)" -Level 'Warning'
            }
            catch {
                Write-BackupLog "无法删除旧备份 [$($backup.Name)]: $_" -Level 'Error'
            }
        }
        
        Write-BackupLog "清理完成，删除 $($oldBackups.Count) 个旧备份"
    }
    catch {
        Write-BackupLog "清理失败: $_" -Level 'Error'
    }
}

# 获取备份历史
function Get-BackupHistory {
    <#
    .SYNOPSIS
        获取备份历史记录
    #>
    [CmdletBinding()]
    [OutputType([PSCustomObject[]])]
    param(
        [Parameter()]
        [string]$BackupRoot = $script:ModuleConfig.DefaultConfig.BackupRoot
    )
    
    try {
        $backups = Get-ChildItem $BackupRoot -Directory -Filter 'backup_*' |
            Sort-Object CreationTime -Descending
        
        foreach ($backup in $backups) {
            $manifestPath = Join-Path $backup.FullName 'manifest.json'
            if (Test-Path $manifestPath) {
                Get-Content $manifestPath -Raw | ConvertFrom-Json
            }
            else {
                [PSCustomObject]@{
                    BackupDate = $backup.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
                    BackupPath = $backup.FullName
                    Mode = 'Unknown'
                }
            }
        }
    }
    catch {
        Write-BackupLog "获取备份历史失败: $_" -Level 'Error'
    }
}

# 导出模块成员
Export-ModuleMember -Function @(
    'Start-WorkspaceBackup',
    'Get-BackupHistory',
    'Import-BackupConfig'
) -Variable 'ModuleConfig'
