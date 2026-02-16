#requires -Version 5.1
<#
.SYNOPSIS
    OpenClaw Git自动化助手
.DESCRIPTION
    封装常用Git操作的PowerShell模块，支持参数验证、管道输入和ShouldProcess
.PARAMETER Action
    Git操作：status | add | commit | push | pull | log | branch
.PARAMETER Message
    提交信息（用于commit操作）
.PARAMETER Path
    要操作的文件或目录路径
.PARAMETER Branch
    分支名称
.EXAMPLE
    Invoke-OpenClawGit -Action status
    查看当前仓库状态
.EXAMPLE
    Get-ChildItem *.ps1 | Invoke-OpenClawGit -Action add
    通过管道添加所有ps1文件
.EXAMPLE
    Invoke-OpenClawGit -Action commit -Message "修复bug"
    提交更改
#>
function Invoke-OpenClawGit {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory, Position = 0)]
        [ValidateSet('status', 'add', 'commit', 'push', 'pull', 'log', 'branch', 'checkout', 'merge', 'stash')]
        [string]$Action,

        [Parameter(ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias('FullName')]
        [string[]]$Path,

        [Parameter()]
        [string]$Message,

        [Parameter()]
        [string]$Branch,

        [Parameter()]
        [switch]$All
    )

    begin {
        # 查找OpenClaw工作区
        $workspacePath = "$env:USERPROFILE\.openclaw\workspace"
        if (!(Test-Path (Join-Path $workspacePath '.git'))) {
            Write-Error "未找到Git仓库。请确保在OpenClaw工作区目录运行。"
            return
        }
        
        Set-Location $workspacePath
        $collectedPaths = @()
    }

    process {
        if ($Path) {
            $collectedPaths += $Path
        }
    }

    end {
        try {
            switch ($Action) {
                'status' {
                    if ($PSCmdlet.ShouldProcess("Git仓库", "查看状态")) {
                        git status --short
                    }
                }
                
                'add' {
                    $targets = if ($All) { "." } elseif ($collectedPaths) { $collectedPaths } else { "." }
                    
                    foreach ($target in $targets) {
                        if ($PSCmdlet.ShouldProcess($target, "添加到暂存区")) {
                            git add $target
                            Write-Host "已添加: $target" -ForegroundColor Green
                        }
                    }
                }
                
                'commit' {
                    if ([string]::IsNullOrWhiteSpace($Message)) {
                        $Message = Read-Host "请输入提交信息"
                    }
                    
                    if ([string]::IsNullOrWhiteSpace($Message)) {
                        Write-Error "提交信息不能为空"
                        return
                    }
                    
                    if ($PSCmdlet.ShouldProcess($Message, "提交更改")) {
                        git commit -m $Message
                    }
                }
                
                'push' {
                    if ($PSCmdlet.ShouldProcess("当前分支", "推送到远程")) {
                        git push
                    }
                }
                
                'pull' {
                    if ($PSCmdlet.ShouldProcess("当前分支", "拉取远程更新")) {
                        git pull
                    }
                }
                
                'log' {
                    $logFormat = "%h - %an, %ar : %s"
                    git log --oneline --graph --decorate -20
                }
                
                'branch' {
                    if ($Branch) {
                        if ($PSCmdlet.ShouldProcess($Branch, "创建新分支")) {
                            git checkout -b $Branch
                        }
                    } else {
                        git branch -vv
                    }
                }
                
                'checkout' {
                    if ([string]::IsNullOrWhiteSpace($Branch)) {
                        Write-Error "请指定分支名称: -Branch <name>"
                        return
                    }
                    if ($PSCmdlet.ShouldProcess($Branch, "切换分支")) {
                        git checkout $Branch
                    }
                }
                
                'merge' {
                    if ([string]::IsNullOrWhiteSpace($Branch)) {
                        Write-Error "请指定要合并的分支: -Branch <name>"
                        return
                    }
                    if ($PSCmdlet.ShouldProcess($Branch, "合并分支")) {
                        git merge $Branch
                    }
                }
                
                'stash' {
                    if ($PSCmdlet.ShouldProcess("当前更改", "暂存")) {
                        git stash push -m "自动暂存 $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
                        Write-Host "更改已暂存" -ForegroundColor Green
                    }
                }
            }
        } catch {
            Write-Error "Git操作失败: $_"
        }
    }
}

# 设置别名
Set-Alias -Name ocg -Value Invoke-OpenClawGit

# 导出函数
Export-ModuleMember -Function Invoke-OpenClawGit
Export-ModuleMember -Alias ocg
