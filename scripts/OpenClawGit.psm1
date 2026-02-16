#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw Git自动化脚本 - 封装常用Git操作
.DESCRIPTION
    本脚本提供常用Git操作的封装，支持：
    - 参数验证和类型检查
    - 管道输入支持
    - ShouldProcess支持（-WhatIf, -Confirm）
    - 结构化输出
.EXAMPLE
    # 提交更改
    git-commit -Message "修复bug" -Push
    
    # 批量操作（管道）
    Get-ChildItem -Directory | git-status
    
    # 安全的删除分支（带确认）
    git-branch -Name "old-feature" -Delete -Confirm
.NOTES
    作者: OpenClaw Automation
    版本: 1.0.0
#>

# 辅助函数：检查Git仓库
function Test-GitRepository {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [string]$Path = (Get-Location)
    )
    
    process {
        $gitDir = Join-Path $Path '.git'
        return Test-Path $gitDir -PathType Container
    }
}

# 辅助函数：执行Git命令
function Invoke-GitCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,
        
        [string]$WorkingDirectory = (Get-Location),
        
        [switch]$SuppressOutput
    )
    
    try {
        $gitExe = Get-Command git -ErrorAction Stop
        
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $gitExe.Source
        $psi.Arguments = $Arguments -join ' '
        $psi.WorkingDirectory = $WorkingDirectory
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        $process.Start() | Out-Null
        
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        
        if ($process.ExitCode -ne 0) {
            throw "Git命令失败 (退出码: $($process.ExitCode)): $stderr"
        }
        
        if (-not $SuppressOutput -and $stdout) {
            return $stdout.Trim()
        }
        
        return $stdout
    }
    catch {
        Write-Error "Git操作失败: $_"
        throw
    }
}

<#
.SYNOPSIS
    获取Git仓库状态
.DESCRIPTION
    显示工作目录状态，支持管道输入批量检查多个仓库
#>
function git-status {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(ValueFromPipeline)]
        [ValidateScript({ 
            if (Test-Path $_ -PathType Container) { $true }
            else { throw "路径不存在: $_" }
        })]
        [string[]]$Path = (Get-Location),
        
        [switch]$Short
    )
    
    begin {
        $results = @()
    }
    
    process {
        foreach ($p in $Path) {
            try {
                if (-not (Test-GitRepository $p)) {
                    Write-Warning "不是Git仓库: $p"
                    continue
                }
                
                $args = @('status')
                if ($Short) { $args += '--short' }
                $args += '--porcelain'
                
                $output = Invoke-GitCommand -Arguments $args -WorkingDirectory $p
                
                # 解析状态输出
                $changes = @()
                if ($output) {
                    $lines = $output -split "`n" | Where-Object { $_ }
                    foreach ($line in $lines) {
                        $changes += [PSCustomObject]@{
                            IndexStatus = $line.Substring(0, 1)
                            WorkTreeStatus = $line.Substring(1, 1)
                            FilePath = $line.Substring(3).Trim()
                        }
                    }
                }
                
                # 获取分支信息
                $branch = Invoke-GitCommand -Arguments @('branch', '--show-current') -WorkingDirectory $p -SuppressOutput
                
                $result = [PSCustomObject]@{
                    Repository = $p
                    Branch = $branch
                    IsClean = $changes.Count -eq 0
                    Changes = $changes
                    ChangeCount = $changes.Count
                    Timestamp = Get-Date
                }
                
                $results += $result
                
                # 格式化输出
                $color = if ($result.IsClean) { 'Green' } else { 'Yellow' }
                Write-Host "[$p] 分支: $branch " -NoNewline
                Write-Host "($($result.ChangeCount) 个更改)" -ForegroundColor $color
                
                if (-not $Short -and $changes.Count -gt 0) {
                    $changes | Format-Table -AutoSize | Out-String | Write-Host
                }
                
                return $result
            }
            catch {
                Write-Error "获取状态失败 [$p]: $_"
            }
        }
    }
}

<#
.SYNOPSIS
    Git提交封装
.DESCRIPTION
    添加并提交更改，支持自动推送
#>
function git-commit {
    [CmdletBinding(SupportsShouldProcess = $true)]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string]$Message,
        
        [string[]]$Files = @('.'),
        
        [switch]$Push,
        
        [switch]$Amend,
        
        [string]$Branch
    )
    
    try {
        # 验证仓库
        if (-not (Test-GitRepository)) {
            throw "当前目录不是Git仓库"
        }
        
        # 添加文件
        if ($PSCmdlet.ShouldProcess($Files -join ', ', 'Git Add')) {
            foreach ($file in $Files) {
                Invoke-GitCommand -Arguments @('add', $file) -SuppressOutput | Out-Null
            }
            Write-Host "已暂存文件" -ForegroundColor Green
        }
        
        # 提交
        if ($PSCmdlet.ShouldProcess($Message, 'Git Commit')) {
            $commitArgs = @('commit', '-m', $Message)
            if ($Amend) { $commitArgs += '--amend' }
            
            $output = Invoke-GitCommand -Arguments $commitArgs
            Write-Host $output -ForegroundColor Green
        }
        
        # 推送
        if ($Push -and $PSCmdlet.ShouldProcess('origin', 'Git Push')) {
            $pushArgs = @('push')
            if ($Branch) { $pushArgs += $Branch }
            if ($Amend) { $pushArgs += '--force-with-lease' }
            
            $pushOutput = Invoke-GitCommand -Arguments $pushArgs
            Write-Host $pushOutput -ForegroundColor Cyan
        }
        
        return [PSCustomObject]@{
            Success = $true
            Message = $Message
            Files = $Files
            Pushed = $Push
            Timestamp = Get-Date
        }
    }
    catch {
        Write-Error "提交失败: $_"
        return [PSCustomObject]@{
            Success = $false
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
    }
}

<#
.SYNOPSIS
    Git分支管理
.DESCRIPTION
    创建、切换、删除分支
#>
function git-branch {
    [CmdletBinding(SupportsShouldProcess = $true, DefaultParameterSetName = 'List')]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(ParameterSetName = 'Create')]
        [Parameter(ParameterSetName = 'Delete')]
        [ValidatePattern('^[\w\-/.]+$')]
        [string]$Name,
        
        [Parameter(ParameterSetName = 'Create')]
        [switch]$Create,
        
        [Parameter(ParameterSetName = 'Create')]
        [switch]$Checkout,
        
        [Parameter(ParameterSetName = 'Delete')]
        [switch]$Delete,
        
        [Parameter(ParameterSetName = 'Delete')]
        [switch]$Force,
        
        [Parameter(ParameterSetName = 'List')]
        [switch]$List
    )
    
    try {
        if (-not (Test-GitRepository)) {
            throw "当前目录不是Git仓库"
        }
        
        switch ($PSCmdlet.ParameterSetName) {
            'Create' {
                if ($PSCmdlet.ShouldProcess($Name, '创建分支')) {
                    $args = @('branch', $Name)
                    Invoke-GitCommand -Arguments $args -SuppressOutput | Out-Null
                    Write-Host "创建分支: $Name" -ForegroundColor Green
                    
                    if ($Checkout) {
                        Invoke-GitCommand -Arguments @('checkout', $Name) -SuppressOutput | Out-Null
                        Write-Host "切换到分支: $Name" -ForegroundColor Cyan
                    }
                    
                    return [PSCustomObject]@{
                        Action = 'Created'
                        Branch = $Name
                        CheckedOut = $Checkout
                    }
                }
            }
            
            'Delete' {
                if ($PSCmdlet.ShouldProcess($Name, "删除分支$(if($Force){' (强制)'})")) {
                    $args = @('branch')
                    if ($Force) { $args += '-D' } else { $args += '-d' }
                    $args += $Name
                    
                    Invoke-GitCommand -Arguments $args -SuppressOutput | Out-Null
                    Write-Host "删除分支: $Name" -ForegroundColor Yellow
                    
                    return [PSCustomObject]@{
                        Action = 'Deleted'
                        Branch = $Name
                        Forced = $Force
                    }
                }
            }
            
            'List' {
                $output = Invoke-GitCommand -Arguments @('branch', '-vv')
                $branches = $output -split "`n" | Where-Object { $_ } | ForEach-Object {
                    $line = $_
                    $isCurrent = $line.StartsWith('*')
                    $branchName = if ($isCurrent) { 
                        $line.Substring(2).Split()[0] 
                    } else { 
                        $line.Substring(2).Split()[0] 
                    }
                    
                    [PSCustomObject]@{
                        Name = $branchName
                        Current = $isCurrent
                        FullInfo = $line.Trim()
                    }
                }
                
                $branches | Format-Table -AutoSize
                return $branches
            }
        }
    }
    catch {
        Write-Error "分支操作失败: $_"
        throw
    }
}

<#
.SYNOPSIS
    Git日志查看
.DESCRIPTION
    美化格式的git log输出
#>
function git-log {
    [CmdletBinding()]
    param(
        [int]$Count = 20,
        
        [switch]$Graph,
        
        [string]$Author,
        
        [string]$Since,
        
        [string]$Until
    )
    
    try {
        if (-not (Test-GitRepository)) {
            throw "当前目录不是Git仓库"
        }
        
        $args = @('log', "--max-count=$Count", '--pretty=format:%h|%an|%ad|%s', '--date=short')
        
        if ($Graph) { $args = @('log', '--oneline', '--graph', "--max-count=$Count") }
        if ($Author) { $args += "--author=$Author" }
        if ($Since) { $args += "--since=$Since" }
        if ($Until) { $args += "--until=$Until" }
        
        $output = Invoke-GitCommand -Arguments $args
        
        if (-not $Graph) {
            $output -split "`n" | Where-Object { $_ } | ForEach-Object {
                $parts = $_ -split '\|', 4
                [PSCustomObject]@{
                    Hash = $parts[0]
                    Author = $parts[1]
                    Date = $parts[2]
                    Message = $parts[3]
                }
            } | Format-Table -AutoSize
        }
        else {
            Write-Host $output
        }
    }
    catch {
        Write-Error "查看日志失败: $_"
    }
}

<#
.SYNOPSIS
    智能同步（fetch + pull）
.DESCRIPTION
    拉取远程更新，支持自动变基
#>
function git-sync {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [switch]$Rebase,
        
        [switch]$Stash
    )
    
    try {
        if (-not (Test-GitRepository)) {
            throw "当前目录不是Git仓库"
        }
        
        # 检查是否有未提交的更改
        $status = git-status -Short
        $hasChanges = -not $status.IsClean
        
        if ($hasChanges -and $Stash) {
            if ($PSCmdlet.ShouldProcess('本地更改', '暂存')) {
                Invoke-GitCommand -Arguments @('stash', 'push', '-m', 'Auto-stash before sync') -SuppressOutput | Out-Null
                Write-Host "已暂存本地更改" -ForegroundColor Yellow
            }
        }
        elseif ($hasChanges) {
            Write-Warning "有未提交的更改，请使用 -Stash 参数暂存"
            return
        }
        
        # Fetch
        if ($PSCmdlet.ShouldProcess('origin', 'Fetch')) {
            Write-Host "正在获取远程更新..." -ForegroundColor Cyan
            Invoke-GitCommand -Arguments @('fetch', '--all') -SuppressOutput | Out-Null
            Write-Host "Fetch 完成" -ForegroundColor Green
        }
        
        # Pull
        if ($PSCmdlet.ShouldProcess('当前分支', 'Pull')) {
            $pullArgs = @('pull')
            if ($Rebase) { $pullArgs += '--rebase' }
            
            $output = Invoke-GitCommand -Arguments $pullArgs
            Write-Host $output -ForegroundColor Green
        }
        
        # 恢复暂存
        if ($hasChanges -and $Stash) {
            if ($PSCmdlet.ShouldProcess('暂存', '恢复')) {
                Invoke-GitCommand -Arguments @('stash', 'pop') -SuppressOutput | Out-Null
                Write-Host "已恢复本地更改" -ForegroundColor Green
            }
        }
    }
    catch {
        Write-Error "同步失败: $_"
    }
}

<#
.SYNOPSIS
    创建Pull Request（简化版）
.DESCRIPTION
    推送分支并生成PR链接
#>
function git-pr {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Title,
        
        [string]$Base = 'main',
        
        [switch]$Draft
    )
    
    try {
        if (-not (Test-GitRepository)) {
            throw "当前目录不是Git仓库"
        }
        
        $branch = Invoke-GitCommand -Arguments @('branch', '--show-current') -SuppressOutput
        
        # 推送
        if ($PSCmdlet.ShouldProcess($branch, '推送分支')) {
            Invoke-GitCommand -Arguments @('push', '-u', 'origin', $branch) | Out-Null
            Write-Host "分支已推送到 origin/$branch" -ForegroundColor Green
        }
        
        # 获取远程URL
        $remoteUrl = Invoke-GitCommand -Arguments @('remote', 'get-url', 'origin') -SuppressOutput
        
        # 生成PR链接
        if ($remoteUrl -match 'github\.com') {
            $repoPath = $remoteUrl -replace '.*github\.com[/:]', '' -replace '\.git$', ''
            $prUrl = "https://github.com/$repoPath/compare/$Base...$branch"
            
            Write-Host "`nPull Request URL:`n$prUrl" -ForegroundColor Cyan
            
            # 尝试打开浏览器
            try {
                Start-Process $prUrl
            }
            catch {
                Write-Host "请手动访问上述链接创建PR" -ForegroundColor Yellow
            }
        }
        
        return [PSCustomObject]@{
            Branch = $branch
            Base = $Base
            PullRequestUrl = if ($prUrl) { $prUrl } else { $null }
        }
    }
    catch {
        Write-Error "创建PR失败: $_"
    }
}

# 导出函数
Export-ModuleMember -Function @(
    'git-status',
    'git-commit', 
    'git-branch',
    'git-log',
    'git-sync',
    'git-pr'
)
