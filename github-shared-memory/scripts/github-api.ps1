# GitHub API 操作脚本
# 用于共享仓库的自动化操作

$Global:GITHUB_TOKEN = $env:GITHUB_TOKEN  # 需要从环境变量获取
$Global:REPO_OWNER = "your-username"
$Global:REPO_NAME = "shared-memory"

# 设置 GitHub Token
function Set-GitHubToken {
    param([string]$Token)
    $Global:GITHUB_TOKEN = $Token
    $env:GITHUB_TOKEN = $Token
    Write-Host "GitHub Token 已设置" -ForegroundColor Green
}

# 创建 Issue（留言板功能）
function New-GitHubIssue {
    param(
        [string]$Title,
        [string]$Body,
        [string[]]$Labels = @()
    )
    
    $uri = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues"
    $headers = @{
        "Authorization" = "Bearer $GITHUB_TOKEN"
        "Accept" = "application/vnd.github+json"
    }
    $body = @{
        title = $Title
        body = $Body
        labels = $Labels
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
        Write-Host "Issue 创建成功: $($response.html_url)" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "创建失败: $_" -ForegroundColor Red
    }
}

# 获取 Issue 列表
function Get-GitHubIssues {
    param([string]$Label = "")
    
    $uri = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues?state=open"
    if ($Label) { $uri += "&labels=$Label" }
    
    $headers = @{ "Authorization" = "Bearer $GITHUB_TOKEN" }
    
    try {
        $issues = Invoke-RestMethod -Uri $uri -Headers $headers
        return $issues
    } catch {
        Write-Host "获取失败: $_" -ForegroundColor Red
    }
}

# 读取文件内容
function Get-GitHubFile {
    param(
        [string]$Path,
        [string]$Branch = "main"
    )
    
    $uri = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/contents/$Path?ref=$Branch"
    $headers = @{ "Authorization" = "Bearer $GITHUB_TOKEN" }
    
    try {
        $file = Invoke-RestMethod -Uri $uri -Headers $headers
        $content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($file.content))
        return $content
    } catch {
        Write-Host "读取失败: $_" -ForegroundColor Red
    }
}

# 创建或更新文件
function Set-GitHubFile {
    param(
        [string]$Path,
        [string]$Content,
        [string]$Message,
        [string]$Branch = "main"
    )
    
    $uri = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/contents/$Path"
    $headers = @{
        "Authorization" = "Bearer $GITHUB_TOKEN"
        "Accept" = "application/vnd.github+json"
    }
    
    # 先获取当前文件的 SHA（如果存在）
    $sha = $null
    try {
        $existing = Invoke-RestMethod -Uri "$uri?ref=$Branch" -Headers $headers
        $sha = $existing.sha
    } catch {
        # 文件不存在，继续创建
    }
    
    $encodedContent = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Content))
    $body = @{
        message = $Message
        content = $encodedContent
        branch = $Branch
    }
    if ($sha) { $body.sha = $sha }
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method PUT -Headers $headers -Body ($body | ConvertTo-Json)
        Write-Host "文件保存成功: $Path" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "保存失败: $_" -ForegroundColor Red
    }
}

# 同步本地记忆到 GitHub
function Sync-MemoryToGitHub {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$Branch
    )
    
    $content = Get-Content -Path $LocalPath -Raw -Encoding UTF8
    Set-GitHubFile -Path $RemotePath -Content $content -Message "同步记忆: $([DateTime]::Now)" -Branch $Branch
}

Write-Host "GitHub API 工具已加载" -ForegroundColor Cyan
Write-Host "使用方法：" -ForegroundColor Yellow
Write-Host "  Set-GitHubToken 'your-token'"
Write-Host "  New-GitHubIssue -Title '留言标题' -Body '内容' -Labels @('message/xiaoyu')"
