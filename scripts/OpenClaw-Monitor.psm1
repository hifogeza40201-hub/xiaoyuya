#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw系统监控脚本
.DESCRIPTION
    监控OpenClaw运行状态的PowerShell高级函数，支持结构化输出
.PARAMETER CheckType
    检查类型：All | Gateway | Disk | Memory | Services
.PARAMETER OutputFormat
    输出格式：Table | Json | Object
.PARAMETER AlertThreshold
    警报阈值（磁盘使用率百分比）
.EXAMPLE
    Get-OpenClawStatus
    获取完整状态报告
.EXAMPLE
    Get-OpenClawStatus -CheckType Disk -AlertThreshold 80
    检查磁盘空间，超过80%时发出警告
.EXAMPLE
    Get-OpenClawStatus | Where-Object { $_.Status -eq 'Error' }
    只显示有问题的项目
#>
function Get-OpenClawStatus {
    [CmdletBinding()]
    [OutputType([PSCustomObject[]])]
    param(
        [Parameter()]
        [ValidateSet('All', 'Gateway', 'Disk', 'Memory', 'Services', 'Git')]
        [string]$CheckType = 'All',

        [Parameter()]
        [ValidateSet('Table', 'Json', 'Object')]
        [string]$OutputFormat = 'Table',

        [Parameter()]
        [ValidateRange(1, 99)]
        [int]$AlertThreshold = 80
    )

    $results = [System.Collections.ArrayList]::new()

    # 检查Gateway状态
    if ($CheckType -in @('All', 'Gateway')) {
        try {
            $gatewayPort = 18789
            $connection = Test-NetConnection -ComputerName localhost -Port $gatewayPort -WarningAction SilentlyContinue
            
            $gatewayStatus = [PSCustomObject]@{
                Component = 'OpenClaw Gateway'
                Status = if ($connection.TcpTestSucceeded) { 'OK' } else { 'Error' }
                Port = $gatewayPort
                Details = if ($connection.TcpTestSucceeded) { '运行中' } else { '无法连接' }
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
            [void]$results.Add($gatewayStatus)
        } catch {
            [void]$results.Add([PSCustomObject]@{
                Component = 'OpenClaw Gateway'
                Status = 'Error'
                Details = $_.Exception.Message
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            })
        }
    }

    # 检查磁盘空间
    if ($CheckType -in @('All', 'Disk')) {
        Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } | ForEach-Object {
            $freePercent = [math]::Round(($_.FreeSpace / $_.Size) * 100, 2)
            $usedPercent = 100 - $freePercent
            
            $diskStatus = [PSCustomObject]@{
                Component = "Disk $($_.DeviceID)"
                Status = if ($usedPercent -gt $AlertThreshold) { 'Warning' } else { 'OK' }
                TotalGB = [math]::Round($_.Size / 1GB, 2)
                FreeGB = [math]::Round($_.FreeSpace / 1GB, 2)
                UsedPercent = $usedPercent
                Details = if ($usedPercent -gt $AlertThreshold) { "使用率超过 ${AlertThreshold}%" } else { "正常" }
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
            [void]$results.Add($diskStatus)
        }
    }

    # 检查内存
    if ($CheckType -in @('All', 'Memory')) {
        try {
            $memory = Get-CimInstance -ClassName Win32_OperatingSystem
            $totalMemory = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
            $freeMemory = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
            $usedPercent = [math]::Round((($totalMemory - $freeMemory) / $totalMemory) * 100, 2)
            
            $memoryStatus = [PSCustomObject]@{
                Component = 'Memory'
                Status = if ($usedPercent -gt 90) { 'Warning' } elseif ($usedPercent -gt 75) { 'Caution' } else { 'OK' }
                TotalGB = $totalMemory
                FreeGB = $freeMemory
                UsedPercent = $usedPercent
                Details = "已用 ${usedPercent}%"
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
            [void]$results.Add($memoryStatus)
        } catch {
            [void]$results.Add([PSCustomObject]@{
                Component = 'Memory'
                Status = 'Error'
                Details = $_.Exception.Message
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            })
        }
    }

    # 检查关键服务
    if ($CheckType -in @('All', 'Services')) {
        $services = @(
            @{ Name = 'OpenClaw Gateway'; Check = 'Scheduled Task' }
        )
        
        foreach ($svc in $services) {
            try {
                $task = Get-ScheduledTask -TaskName $svc.Name -ErrorAction SilentlyContinue
                $svcStatus = if ($task) { $task.State } else { 'Not Found' }
                
                [void]$results.Add([PSCustomObject]@{
                    Component = $svc.Name
                    Status = if ($svcStatus -eq 'Running' -or $svcStatus -eq 'Ready') { 'OK' } else { 'Warning' }
                    Details = $svcStatus
                    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                })
            } catch {
                [void]$results.Add([PSCustomObject]@{
                    Component = $svc.Name
                    Status = 'Error'
                    Details = $_.Exception.Message
                    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                })
            }
        }
    }

    # 检查Git仓库状态
    if ($CheckType -in @('All', 'Git')) {
        $workspacePath = "$env:USERPROFILE\.openclaw\workspace"
        if (Test-Path (Join-Path $workspacePath '.git')) {
            try {
                Push-Location $workspacePath
                $gitStatus = git status --short 2>$null
                $hasChanges = ![string]::IsNullOrWhiteSpace($gitStatus)
                
                [void]$results.Add([PSCustomObject]@{
                    Component = 'Git Repository'
                    Status = if ($hasChanges) { 'Warning' } else { 'OK' }
                    Details = if ($hasChanges) { "有未提交的更改" } else { "已同步" }
                    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                })
                Pop-Location
            } catch {
                [void]$results.Add([PSCustomObject]@{
                    Component = 'Git Repository'
                    Status = 'Error'
                    Details = $_.Exception.Message
                    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                })
            }
        }
    }

    # 输出结果
    switch ($OutputFormat) {
        'Table' {
            $results | Format-Table -AutoSize
        }
        'Json' {
            $results | ConvertTo-Json -Depth 3
        }
        'Object' {
            return $results
        }
    }
}

<#
.SYNOPSIS
    测试OpenClaw连通性
#>
function Test-OpenClawConnection {
    [CmdletBinding()]
    param(
        [Parameter()]
        [int]$TimeoutSeconds = 10
    )

    $tests = @(
        @{ Name = 'Gateway'; Target = 'localhost'; Port = 18789 }
        @{ Name = 'NodeService'; Target = 'localhost'; Port = 18792 }
    )

    foreach ($test in $tests) {
        Write-Host "测试 $($test.Name) ... " -NoNewline
        try {
            $result = Test-NetConnection -ComputerName $test.Target -Port $test.Port -WarningAction SilentlyContinue
            if ($result.TcpTestSucceeded) {
                Write-Host "✓ 成功" -ForegroundColor Green
            } else {
                Write-Host "✗ 失败" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ 错误: $_" -ForegroundColor Red
        }
    }
}

# 导出函数
Export-ModuleMember -Function Get-OpenClawStatus, Test-OpenClawConnection
