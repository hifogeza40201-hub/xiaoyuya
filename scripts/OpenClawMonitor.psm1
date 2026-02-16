#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw系统监控脚本 - 监控OpenClaw运行状态
.DESCRIPTION
    本脚本提供系统监控功能，包括：
    - OpenClaw网关状态监控
    - 系统资源使用监控
    - 高级函数设计
    - 结构化输出
    - 完整的错误处理
.EXAMPLE
    # 监控OpenClaw状态
    Get-OpenClawStatus
    
    # 持续监控（每5秒）
    Watch-OpenClawHealth -Interval 5 -Duration 60
    
    # 生成报告
    Get-SystemHealthReport | Export-Csv report.csv
.NOTES
    作者: OpenClaw Automation
    版本: 1.0.0
#>

#region 类型定义

# 定义自定义对象类型
Add-Type -TypeDefinition @"
public enum ServiceStatus {
    Running,
    Stopped,
    Unknown,
    Error
}

public enum HealthLevel {
    Healthy,
    Warning,
    Critical
}
"@ -ErrorAction SilentlyContinue

#endregion

#region 核心函数

<#
.SYNOPSIS
    获取OpenClaw网关状态
.DESCRIPTION
    高级函数，使用结构化输出
#>
function Get-OpenClawStatus {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [Parameter()]
        [string]$GatewayUrl = 'http://localhost:3939',
        
        [switch]$Detailed
    )
    
    try {
        # 检查网关HTTP接口
        $gatewayHealth = Test-GatewayHealth -Url $GatewayUrl
        
        # 检查进程
        $processInfo = Get-OpenClawProcess
        
        # 检查端口监听
        $ports = Get-OpenClawPorts
        
        # 构建状态对象
        $status = [PSCustomObject]@{
            PSTypeName = 'OpenClaw.Status'
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            Gateway = $gatewayHealth
            Process = $processInfo
            Ports = $ports
            OverallHealth = 'Unknown'
        }
        
        # 计算整体健康状态
        $healthScore = 0
        if ($gatewayHealth.IsResponsive) { $healthScore += 40 }
        if ($processInfo.IsRunning) { $healthScore += 40 }
        if ($ports.Count -gt 0) { $healthScore += 20 }
        
        $status.OverallHealth = switch ($healthScore) {
            { $_ -ge 80 } { 'Healthy' }
            { $_ -ge 50 } { 'Warning' }
            default { 'Critical' }
        }
        
        # 详细模式添加额外信息
        if ($Detailed) {
            $status | Add-Member -MemberType NoteProperty -Name 'SystemInfo' -Value (Get-SystemInfo)
            $status | Add-Member -MemberType NoteProperty -Name 'RecentLogs' -Value (Get-RecentOpenClawLogs -Count 10)
        }
        
        return $status
    }
    catch {
        Write-Error "获取OpenClaw状态失败: $_"
        return [PSCustomObject]@{
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            Error = $_.Exception.Message
            OverallHealth = 'Error'
        }
    }
}

<#
.SYNOPSIS
    测试网关健康状态
.DESCRIPTION
    内部辅助函数
#>
function Test-GatewayHealth {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        
        [int]$TimeoutMs = 5000
    )
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        $response = Invoke-WebRequest -Uri "$Url/status" -Method GET -TimeoutSec ($TimeoutMs / 1000) -ErrorAction Stop
        
        $stopwatch.Stop()
        
        return [PSCustomObject]@{
            IsResponsive = $true
            StatusCode = $response.StatusCode
            ResponseTime = $stopwatch.ElapsedMilliseconds
            Endpoint = $Url
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        }
    }
    catch [System.Net.WebException] {
        return [PSCustomObject]@{
            IsResponsive = $false
            StatusCode = [int]$_.Exception.Response.StatusCode
            ResponseTime = -1
            Endpoint = $Url
            Error = $_.Exception.Message
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        }
    }
    catch {
        return [PSCustomObject]@{
            IsResponsive = $false
            StatusCode = 0
            ResponseTime = -1
            Endpoint = $Url
            Error = $_.Exception.Message
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        }
    }
}

<#
.SYNOPSIS
    获取OpenClaw进程信息
#>
function Get-OpenClawProcess {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param()
    
    try {
        # 查找OpenClaw相关进程
        $processes = @()
        
        # 搜索可能的进程名
        $searchNames = @('openclaw', 'gateway', 'node', 'deno', 'bun')
        
        foreach ($name in $searchNames) {
            $found = Get-Process -Name "*$name*" -ErrorAction SilentlyContinue | Where-Object {
                $_.ProcessName -match 'openclaw|gateway|deno' -or 
                $_.CommandLine -match 'openclaw' 2>$null
            }
            $processes += $found
        }
        
        $processes = $processes | Select-Object -Unique -Property Id, ProcessName, 
            @{N='CPU'; E={$_.CPU}},
            @{N='MemoryMB'; E={[math]::Round($_.WorkingSet64 / 1MB, 2)}},
            @{N='StartTime'; E={$_.StartTime}},
            @{N='IsRunning'; E={$true}}
        
        if ($processes.Count -eq 0) {
            return [PSCustomObject]@{
                IsRunning = $false
                ProcessCount = 0
                Message = "未找到OpenClaw相关进程"
            }
        }
        
        return [PSCustomObject]@{
            IsRunning = $true
            ProcessCount = $processes.Count
            Processes = $processes
            TotalMemoryMB = ($processes | Measure-Object -Property MemoryMB -Sum).Sum
        }
    }
    catch {
        Write-Error "获取进程信息失败: $_"
        return [PSCustomObject]@{
            IsRunning = $false
            Error = $_.Exception.Message
        }
    }
}

<#
.SYNOPSIS
    获取OpenClaw监听的端口
#>
function Get-OpenClawPorts {
    [CmdletBinding()]
    [OutputType([PSCustomObject[]])]
    param()
    
    try {
        $openclawPorts = @()
        
        # 获取网络连接
        $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object {
            $_.LocalPort -in @(3939, 3000, 8080, 8000) -or
            $_.OwningProcess -in (Get-OpenClawProcess).Processes.Id
        }
        
        foreach ($conn in $connections) {
            try {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                $openclawPorts += [PSCustomObject]@{
                    Protocol = 'TCP'
                    LocalAddress = $conn.LocalAddress
                    LocalPort = $conn.LocalPort
                    State = $conn.State
                    ProcessName = $process.ProcessName
                    ProcessId = $conn.OwningProcess
                }
            }
            catch {
                # 忽略权限不足的错误
            }
        }
        
        return $openclawPorts | Select-Object -Unique
    }
    catch {
        Write-Verbose "获取端口信息失败: $_"
        return @()
    }
}

<#
.SYNOPSIS
    获取系统信息
#>
function Get-SystemInfo {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param()
    
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($env:SystemDrive)'" -ErrorAction SilentlyContinue
        
        $totalMem = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
        $freeMem = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
        $usedMem = $totalMem - $freeMem
        $memPercent = [math]::Round(($usedMem / $totalMem) * 100, 1)
        
        return [PSCustomObject]@{
            ComputerName = $env:COMPUTERNAME
            OS = $os.Caption
            OSVersion = $os.Version
            Architecture = $os.OSArchitecture
            CPU = $cpu.Name
            CPULoad = $cpu.LoadPercentage
            TotalMemoryGB = $totalMem
            FreeMemoryGB = $freeMem
            MemoryUsagePercent = $memPercent
            DiskTotalGB = [math]::Round($disk.Size / 1GB, 2)
            DiskFreeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
            DiskUsagePercent = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1)
            Uptime = (Get-Date) - $os.LastBootUpTime
        }
    }
    catch {
        Write-Verbose "获取系统信息失败: $_"
        return $null
    }
}

<#
.SYNOPSIS
    获取最近的OpenClaw日志
#>
function Get-RecentOpenClawLogs {
    [CmdletBinding()]
    param(
        [int]$Count = 10,
        
        [string]$LogPath = "$env:USERPROFILE\.openclaw\logs"
    )
    
    try {
        if (-not (Test-Path $LogPath)) {
            return @()
        }
        
        $logFiles = Get-ChildItem $LogPath -Filter '*.log' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        
        if ($logFiles) {
            return Get-Content $logFiles.FullName -Tail $Count -ErrorAction SilentlyContinue
        }
        
        return @()
    }
    catch {
        return @()
    }
}

<#
.SYNOPSIS
    持续监控OpenClaw健康状态
.DESCRIPTION
    高级函数，支持指定间隔和持续时间
#>
function Watch-OpenClawHealth {
    [CmdletBinding()]
    param(
        [Parameter()]
        [ValidateRange(1, 3600)]
        [int]$Interval = 5,
        
        [Parameter()]
        [ValidateRange(1, 86400)]
        [int]$Duration = 60,
        
        [string]$LogFile,
        
        [switch]$AlertOnError
    )
    
    begin {
        Write-Host "=== OpenClaw健康监控开始 ===" -ForegroundColor Cyan
        Write-Host "间隔: ${Interval}秒, 持续时间: ${Duration}秒" -ForegroundColor Gray
        Write-Host "按 Ctrl+C 停止`n" -ForegroundColor Gray
        
        $startTime = Get-Date
        $history = @()
    }
    
    process {
        try {
            while (((Get-Date) - $startTime).TotalSeconds -lt $Duration) {
                $timestamp = Get-Date -Format 'HH:mm:ss'
                $status = Get-OpenClawStatus
                
                # 显示状态
                $healthColor = switch ($status.OverallHealth) {
                    'Healthy' { 'Green' }
                    'Warning' { 'Yellow' }
                    'Critical' { 'Red' }
                    default { 'Gray' }
                }
                
                Write-Host "[$timestamp] " -NoNewline
                Write-Host $status.OverallHealth -ForegroundColor $healthColor -NoNewline
                Write-Host " | Gateway: $($status.Gateway.IsResponsive) | Process: $($status.Process.IsRunning)"
                
                # 记录历史
                $history += $status
                
                # 日志记录
                if ($LogFile) {
                    $status | ConvertTo-Json -Compress | Add-Content $LogFile
                }
                
                # 警报
                if ($AlertOnError -and $status.OverallHealth -eq 'Critical') {
                    Write-Host "⚠️ 检测到Critical状态!" -ForegroundColor Red -BackgroundColor Black
                }
                
                Start-Sleep -Seconds $Interval
            }
        }
        catch {
            Write-Error "监控过程中出错: $_"
        }
    }
    
    end {
        Write-Host "`n=== 监控结束 ===" -ForegroundColor Cyan
        
        # 生成统计
        $stats = @{
            TotalChecks = $history.Count
            Healthy = ($history | Where-Object { $_.OverallHealth -eq 'Healthy' }).Count
            Warning = ($history | Where-Object { $_.OverallHealth -eq 'Warning' }).Count
            Critical = ($history | Where-Object { $_.OverallHealth -eq 'Critical' }).Count
        }
        
        Write-Host "统计: 总计 $($stats.TotalChecks) 次检查"
        Write-Host "  Healthy:  $($stats.Healthy)" -ForegroundColor Green
        Write-Host "  Warning:  $($stats.Warning)" -ForegroundColor Yellow
        Write-Host "  Critical: $($stats.Critical)" -ForegroundColor Red
        
        return $stats
    }
}

<#
.SYNOPSIS
    获取系统健康报告
.DESCRIPTION
    生成完整的系统健康报告
#>
function Get-SystemHealthReport {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [switch]$IncludeProcesses,
        
        [switch]$IncludeNetwork
    )
    
    try {
        $report = [PSCustomObject]@{
            ReportTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            OpenClaw = Get-OpenClawStatus -Detailed
            System = Get-SystemInfo
        }
        
        if ($IncludeProcesses) {
            $report | Add-Member -MemberType NoteProperty -Name 'TopProcesses' -Value @(
                Get-Process | Sort-Object WorkingSet64 -Descending | 
                    Select-Object -First 10 Name, Id, @{N='MemoryMB'; E={[math]::Round($_.WorkingSet64 / 1MB, 2)}}, CPU
            )
        }
        
        if ($IncludeNetwork) {
            $report | Add-Member -MemberType NoteProperty -Name 'Network' -Value @{
                Adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | 
                    Select-Object Name, InterfaceDescription, LinkSpeed, MacAddress
                Connections = Get-NetTCPConnection -State Established | 
                    Group-Object RemoteAddress | 
                    Select-Object Name, Count | 
                    Sort-Object Count -Descending | 
                    Select-Object -First 10
            }
        }
        
        return $report
    }
    catch {
        Write-Error "生成报告失败: $_"
        throw
    }
}

<#
.SYNOPSIS
    测试并重启OpenClaw服务
.DESCRIPTION
    如果检测到问题，尝试重启服务
#>
function Repair-OpenClawService {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [switch]$Force
    )
    
    try {
        $status = Get-OpenClawStatus
        
        if ($status.OverallHealth -eq 'Healthy' -and -not $Force) {
            Write-Host "OpenClaw服务运行正常，无需修复" -ForegroundColor Green
            return $status
        }
        
        if ($PSCmdlet.ShouldProcess('OpenClaw服务', '重启')) {
            Write-Host "检测到问题，正在尝试修复..." -ForegroundColor Yellow
            
            # 停止进程
            $processes = Get-OpenClawProcess
            foreach ($proc in $processes.Processes) {
                try {
                    Stop-Process -Id $proc.Id -Force
                    Write-Host "已停止进程: $($proc.ProcessName) (PID: $($proc.Id))"
                }
                catch {
                    Write-Warning "无法停止进程: $_"
                }
            }
            
            Start-Sleep -Seconds 2
            
            # 尝试启动（需要知道启动命令）
            Write-Host "请手动启动OpenClaw服务" -ForegroundColor Cyan
            Write-Host "通常命令: openclaw gateway start"
            
            # 等待并检查
            Start-Sleep -Seconds 5
            return Get-OpenClawStatus
        }
    }
    catch {
        Write-Error "修复失败: $_"
        throw
    }
}

#endregion

#region 格式化输出

# 自定义格式化视图
Update-FormatData -AppendPath {
    @'
<?xml version="1.0" encoding="utf-8" ?>
<Configuration>
    <ViewDefinitions>
        <View>
            <Name>OpenClawStatus</Name>
            <ViewSelectedBy>
                <TypeName>OpenClaw.Status</TypeName>
            </ViewSelectedBy>
            <TableControl>
                <TableHeaders>
                    <TableColumnHeader><Label>Time</Label><Width>19</Width></TableColumnHeader>
                    <TableColumnHeader><Label>Health</Label><Width>10</Width></TableColumnHeader>
                    <TableColumnHeader><Label>Gateway</Label><Width>10</Width></TableColumnHeader>
                    <TableColumnHeader><Label>Process</Label><Width>10</Width></TableColumnHeader>
                    <TableColumnHeader><Label>Ports</Label><Width>8</Width></TableColumnHeader>
                </TableHeaders>
                <TableRowEntries>
                    <TableRowEntry>
                        <TableColumnItems>
                            <TableColumnItem><PropertyName>Timestamp</PropertyName></TableColumnItem>
                            <TableColumnItem><PropertyName>OverallHealth</PropertyName></TableColumnItem>
                            <TableColumnItem><ScriptBlock>$_.Gateway.IsResponsive</ScriptBlock></TableColumnItem>
                            <TableColumnItem><ScriptBlock>$_.Process.IsRunning</ScriptBlock></TableColumnItem>
                            <TableColumnItem><ScriptBlock>$_.Ports.Count</ScriptBlock></TableColumnItem>
                        </TableColumnItems>
                    </TableRowEntry>
                </TableRowEntries>
            </TableControl>
        </View>
    </ViewDefinitions>
</Configuration>
'@ | Set-Content -Path "$env:TEMP\OpenClaw.Format.ps1xml" -PassThru
} 2>$null

try {
    Update-FormatData -AppendPath "$env:TEMP\OpenClaw.Format.ps1xml" -ErrorAction SilentlyContinue
}
catch {
    # 忽略格式化错误
}

#endregion

# 导出函数
Export-ModuleMember -Function @(
    'Get-OpenClawStatus',
    'Watch-OpenClawHealth',
    'Get-SystemHealthReport',
    'Repair-OpenClawService',
    'Get-SystemInfo',
    'Get-OpenClawProcess'
)
