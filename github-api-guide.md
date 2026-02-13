# GitHub API 操作指南

> 涵盖文件读写、Issue 管理、分支操作，附 PowerShell 与 Python 完整示例

---

## 📋 目录

1. [前置准备](#前置准备)
2. [认证方式](#认证方式)
3. [文件操作](#文件操作)
4. [Issue 管理](#issue-管理)
5. [分支管理](#分支管理)
6. [完整示例脚本](#完整示例脚本)
7. [常见问题](#常见问题)

---

## 前置准备

### 1. 获取 Personal Access Token (PAT)

访问: https://github.com/settings/tokens

**推荐权限范围:**
- `repo` - 完全仓库访问
- `workflow` - 工作流管理
- `write:packages` - 包管理 (可选)

**经典 Token vs Fine-grained Token:**
- **Classic**: 权限较宽泛，兼容性好
- **Fine-grained**: 精确到仓库和权限，更安全

### 2. 设置环境变量

```powershell
# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
$env:GITHUB_OWNER = "your-username"
$env:GITHUB_REPO = "your-repo"
```

```bash
# Linux/macOS
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_OWNER="your-username"
export GITHUB_REPO="your-repo"
```

---

## 认证方式

### 方式一: Header 认证 (推荐)

```http
Authorization: Bearer YOUR_TOKEN
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### 方式二: Query 参数 (不推荐用于生产)

```
https://api.github.com/repos/owner/repo?access_token=YOUR_TOKEN
```

---

## 文件操作

### 🔍 读取文件内容

**API 端点:**
```
GET /repos/{owner}/{repo}/contents/{path}
```

#### PowerShell 示例

```powershell
$Owner = $env:GITHUB_OWNER
$Repo = $env:GITHUB_REPO
$Path = "README.md"
$Token = $env:GITHUB_TOKEN

$headers = @{
    "Authorization" = "Bearer $Token"
    "Accept" = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/contents/$Path" `
        -Headers $headers -Method GET
    
    # 内容以 Base64 编码
    $content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content))
    
    Write-Host "文件名: $($response.name)"
    Write-Host "路径: $($response.path)"
    Write-Host "SHA: $($response.sha)"  # 更新时需要用到
    Write-Host "内容长度: $($response.size) 字节"
    Write-Host "---内容---"
    Write-Host $content
}
catch {
    Write-Error "读取失败: $_"
}
```

#### Python 示例

```python
import base64
import os
import requests

OWNER = os.environ.get('GITHUB_OWNER')
REPO = os.environ.get('GITHUB_REPO')
TOKEN = os.environ.get('GITHUB_TOKEN')
PATH = "README.md"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def read_file(owner, repo, path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Base64 解码
        content = base64.b64decode(data['content']).decode('utf-8')
        return {
            'content': content,
            'sha': data['sha'],  # 更新时需要
            'path': data['path'],
            'size': data['size']
        }
    elif response.status_code == 404:
        return None  # 文件不存在
    else:
        raise Exception(f"读取失败: {response.status_code} - {response.text}")

# 使用示例
file_info = read_file(OWNER, REPO, PATH)
if file_info:
    print(f"文件名: {file_info['path']}")
    print(f"SHA: {file_info['sha']}")
    print(f"内容:\n{file_info['content']}")
else:
    print("文件不存在")
```

---

### ✏️ 创建/更新文件

**API 端点:**
```
PUT /repos/{owner}/{repo}/contents/{path}
```

#### PowerShell 示例

```powershell
function Update-GitHubFile {
    param(
        [string]$Path,
        [string]$Message,
        [string]$Content,
        [string]$Branch = "main",
        [string]$SHA = $null  # 更新时必需，创建时可省略
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    # Base64 编码内容
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $encodedContent = [System.Convert]::ToBase64String($bytes)
    
    $body = @{
        message = $Message
        content = $encodedContent
        branch = $Branch
    }
    
    # 如果是更新，需要添加 SHA
    if ($SHA) {
        $body['sha'] = $SHA
    }
    
    $jsonBody = $body | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/contents/$Path" `
            -Headers $headers -Method PUT -Body $jsonBody -ContentType "application/json"
        
        Write-Host "✅ 文件操作成功!"
        Write-Host "提交 SHA: $($response.commit.sha)"
        Write-Host "文件 SHA: $($response.content.sha)"
        return $response.content.sha
    }
    catch {
        Write-Error "操作失败: $_"
        return $null
    }
}

# 创建新文件
$sha = Update-GitHubFile `
    -Path "docs/new-file.md" `
    -Message "创建新文档" `
    -Content "# 新文档`n`n这是通过 API 创建的内容。"

# 更新现有文件 (需要先读取获取 SHA)
$fileInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/contents/docs/new-file.md" `
    -Headers $headers -Method GET

Update-GitHubFile `
    -Path "docs/new-file.md" `
    -Message "更新文档" `
    -Content "# 更新的内容`n`n添加了新内容。" `
    -SHA $fileInfo.sha
```

#### Python 示例

```python
import base64
import json
import os
import requests

OWNER = os.environ.get('GITHUB_OWNER')
REPO = os.environ.get('GITHUB_REPO')
TOKEN = os.environ.get('GITHUB_TOKEN')

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def create_or_update_file(owner, repo, path, message, content, branch="main", sha=None):
    """
    创建或更新文件
    sha: 如果提供则为更新，否则为创建
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    # Base64 编码
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    data = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }
    
    if sha:
        data["sha"] = sha  # 更新时需要
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        return {
            'success': True,
            'commit_sha': result['commit']['sha'],
            'content_sha': result['content']['sha'],
            'html_url': result['content']['html_url']
        }
    else:
        raise Exception(f"操作失败: {response.status_code} - {response.text}")

def upload_file_from_local(owner, repo, github_path, local_path, message, branch="main"):
    """从本地文件上传"""
    with open(local_path, 'rb') as f:
        content = f.read()
    
    # 获取现有文件的 SHA (如果存在)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{github_path}"
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None
    
    # 上传
    result = create_or_update_file(
        owner, repo, github_path, message, 
        content.decode('utf-8'), branch, sha
    )
    return result

# 使用示例
# 1. 创建新文件
result = create_or_update_file(
    OWNER, REPO,
    path="automation/report.md",
    message="添加自动化报告",
    content="# 每日报告\n\n生成时间: 2025-01-01\n",
    branch="main"
)
print(f"创建成功: {result['html_url']}")

# 2. 更新文件
file_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/automation/report.md"
response = requests.get(file_url, headers=headers)
if response.status_code == 200:
    file_sha = response.json()['sha']
    
    result = create_or_update_file(
        OWNER, REPO,
        path="automation/report.md",
        message="更新报告内容",
        content="# 每日报告\n\n生成时间: 2025-01-02\n\n已更新！",
        branch="main",
        sha=file_sha
    )
    print(f"更新成功: {result['html_url']}")
```

---

### 🗑️ 删除文件

**API 端点:**
```
DELETE /repos/{owner}/{repo}/contents/{path}
```

#### PowerShell 示例

```powershell
function Remove-GitHubFile {
    param(
        [string]$Path,
        [string]$Message,
        [string]$SHA,
        [string]$Branch = "main"
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $body = @{
        message = $Message
        sha = $SHA
        branch = $Branch
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/contents/$Path" `
            -Headers $headers -Method DELETE -Body $body -ContentType "application/json"
        
        Write-Host "✅ 文件删除成功!"
        Write-Host "提交 SHA: $($response.commit.sha)"
    }
    catch {
        Write-Error "删除失败: $_"
    }
}

# 使用 (需要先获取 SHA)
$fileInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/contents/docs/temp.md" `
    -Headers @{ "Authorization" = "Bearer $Token" } -Method GET

Remove-GitHubFile -Path "docs/temp.md" -Message "删除临时文件" -SHA $fileInfo.sha
```

#### Python 示例

```python
import os
import requests

OWNER = os.environ.get('GITHUB_OWNER')
REPO = os.environ.get('GITHUB_REPO')
TOKEN = os.environ.get('GITHUB_TOKEN')

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def delete_file(owner, repo, path, message, sha, branch="main"):
    """删除文件"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    data = {
        "message": message,
        "sha": sha,
        "branch": branch
    }
    
    response = requests.delete(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"删除失败: {response.status_code} - {response.text}")

# 使用示例
# 先获取 SHA
file_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/docs/temp.md"
response = requests.get(file_url, headers=headers)

if response.status_code == 200:
    sha = response.json()['sha']
    result = delete_file(OWNER, REPO, "docs/temp.md", "删除临时文件", sha)
    print("删除成功")
```

---

## Issue 管理

### 📬 创建 Issue (作为留言板)

**API 端点:**
```
POST /repos/{owner}/{repo}/issues
```

#### PowerShell 示例

```powershell
function New-GitHubIssue {
    param(
        [string]$Title,
        [string]$Body = "",
        [string[]]$Labels = @(),
        [string[]]$Assignees = @()
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $issueBody = @{
        title = $Title
        body = $Body
    }
    
    if ($Labels.Count -gt 0) { $issueBody['labels'] = $Labels }
    if ($Assignees.Count -gt 0) { $issueBody['assignees'] = $Assignees }
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/issues" `
            -Headers $headers -Method POST -Body ($issueBody | ConvertTo-Json) -ContentType "application/json"
        
        Write-Host "✅ Issue 创建成功!"
        Write-Host "编号: #$($response.number)"
        Write-Host "URL: $($response.html_url)"
        return $response
    }
    catch {
        Write-Error "创建失败: $_"
        return $null
    }
}

# 使用示例 - 作为留言板
New-GitHubIssue `
    -Title "💬 用户反馈 - 2025-01-01" `
    -Body @"
## 反馈详情

**用户**: @someuser
**时间**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**类型**: 功能建议

### 内容
建议在首页添加搜索功能。

### 联系方式
email@example.com
"@ `
    -Labels @("feedback", "enhancement")
```

#### Python 示例

```python
import os
import requests
from datetime import datetime

OWNER = os.environ.get('GITHUB_OWNER')
REPO = os.environ.get('GITHUB_REPO')
TOKEN = os.environ.get('GITHUB_TOKEN')

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def create_issue(owner, repo, title, body="", labels=None, assignees=None):
    """创建 Issue"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    data = {
        "title": title,
        "body": body
    }
    
    if labels:
        data["labels"] = labels
    if assignees:
        data["assignees"] = assignees
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"创建失败: {response.status_code} - {response.text}")

def create_guestbook_entry(owner, repo, username, message, contact=""):
    """创建留言板条目"""
    title = f"💬 留言 - {username} - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = f"""## 留言详情

| 项目 | 内容 |
|------|------|
| **留言者** | @{username} |
| **时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

### 留言内容

{message}

---
"""
    if contact:
        body += f"\n### 联系方式\n{contact}"
    
    return create_issue(owner, repo, title, body, labels=["guestbook", "feedback"])

# 使用示例
# 1. 普通 Issue
issue = create_issue(
    OWNER, REPO,
    title="🐛 Bug: 登录页面无法访问",
    body="描述: 点击登录按钮无反应\n浏览器: Chrome 120",
    labels=["bug", "high-priority"],
    assignees=["developer-name"]
)
print(f"Issue 创建成功: {issue['html_url']}")

# 2. 留言板模式
guestbook = create_guestbook_entry(
    OWNER, REPO,
    username="张三",
    message="这个工具太好用了，感谢开发者！",
    contact="zhangsan@example.com"
)
print(f"留言已记录: {guestbook['html_url']}")
```

---

### 📋 列出 Issues

**API 端点:**
```
GET /repos/{owner}/{repo}/issues
```

#### PowerShell 示例

```powershell
function Get-GitHubIssues {
    param(
        [string]$State = "open",  # open, closed, all
        [string[]]$Labels = @(),
        [int]$PerPage = 30,
        [int]$Page = 1
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $params = @{
        state = $State
        per_page = $PerPage
        page = $Page
    }
    
    if ($Labels.Count -gt 0) {
        $params['labels'] = $Labels -join ","
    }
    
    $queryString = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/issues?$queryString" `
            -Headers $headers -Method GET
        
        return $response | Select-Object number, title, state, @{N="user";E={$_.user.login}}, 
            created_at, labels, html_url
    }
    catch {
        Write-Error "获取失败: $_"
        return $null
    }
}

# 使用示例
Get-GitHubIssues -State "open" -Labels @("bug") -PerPage 10 | Format-Table

# 获取所有留言板条目
Get-GitHubIssues -Labels @("guestbook") -State "all" | ForEach-Object {
    Write-Host "[#$($_.number)] $($_.title) - @($($_.user))"
}
```

#### Python 示例

```python
import os
import requests

OWNER = os.environ.get('GITHUB_OWNER')
REPO = os.environ.get('GITHUB_REPO')
TOKEN = os.environ.get('GITHUB_TOKEN')

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def list_issues(owner, repo, state="open", labels=None, per_page=30, page=1):
    """列出 Issues"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    params = {
        "state": state,
        "per_page": per_page,
        "page": page
    }
    
    if labels:
        params["labels"] = ",".join(labels)
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        issues = response.json()
        # 过滤掉 Pull Request (GitHub 将 PR 也作为 issue 返回)
        return [i for i in issues if 'pull_request' not in i]
    else:
        raise Exception(f"获取失败: {response.status_code}")

def search_guestbook(owner, repo, keyword=""):
    """搜索留言板"""
    issues = list_issues(owner, repo, state="all", labels=["guestbook"], per_page=100)
    
    if keyword:
        issues = [i for i in issues if keyword.lower() in i['title'].lower() 
                  or keyword.lower() in i['body'].lower()]
    
    return issues

# 使用示例
issues = list_issues(OWNER, REPO, state="open", labels=["bug"])
for issue in issues:
    print(f"[#{issue['number']}] {issue['title']} by @{issue['user']['login']}")

# 搜索留言
guestbooks = search_guestbook(OWNER, REPO, keyword="感谢")
print(f"\n找到 {len(guestbooks)} 条相关留言")
```

---

### 📝 添加评论

**API 端点:**
```
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
```

#### PowerShell 示例

```powershell
function Add-GitHubComment {
    param(
        [int]$IssueNumber,
        [string]$Body
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $bodyJson = @{ body = $Body } | ConvertTo-Json
    
    $response = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Owner/$Repo/issues/$IssueNumber/comments" `
        -Headers $headers -Method POST -Body $bodyJson -ContentType "application/json"
    
    return $response
}

# 回复留言
Add-GitHubComment -IssueNumber 42 -Body "感谢您的反馈！我们会尽快处理。"
```

#### Python 示例

```python
def add_comment(owner, repo, issue_number, body):
    """添加评论"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    
    response = requests.post(url, headers=headers, json={"body": body})
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"评论失败: {response.status_code}")

# 使用
comment = add_comment(OWNER, REPO, 42, "感谢您的留言！❤️")
```

---

## 分支管理

### 🌿 列出分支

**API 端点:**
```
GET /repos/{owner}/{repo}/branches
```

#### PowerShell 示例

```powershell
function Get-GitHubBranches {
    param(
        [int]$PerPage = 100
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
    }
    
    $response = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Owner/$Repo/branches?per_page=$PerPage" `
        -Headers $headers -Method GET
    
    return $response | Select-Object name, @{N="sha";E={$_.commit.sha}}
}

# 使用
Get-GitHubBranches | Format-Table name, sha
```

#### Python 示例

```python
def list_branches(owner, repo, per_page=100):
    """列出所有分支"""
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    params = {"per_page": per_page}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取失败: {response.status_code}")

# 使用
branches = list_branches(OWNER, REPO)
for branch in branches:
    print(f"{branch['name']}: {branch['commit']['sha'][:7]}")
```

---

### ➕ 创建分支

**API 端点:**
```
POST /repos/{owner}/{repo}/git/refs
```

#### PowerShell 示例

```powershell
function New-GitHubBranch {
    param(
        [string]$BranchName,
        [string]$FromBranch = "main"  # 基于哪个分支创建
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    # 1. 获取源分支的 SHA
    $refResponse = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Owner/$Repo/git/refs/heads/$FromBranch" `
        -Headers $headers -Method GET
    
    $sha = $refResponse.object.sha
    
    # 2. 创建新分支
    $body = @{
        ref = "refs/heads/$BranchName"
        sha = $sha
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Owner/$Repo/git/refs" `
        -Headers $headers -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "✅ 分支 '$BranchName' 创建成功!"
    Write-Host "基于: $FromBranch ($($sha.Substring(0,7)))"
    return $response
}

# 使用
New-GitHubBranch -BranchName "feature/new-feature" -FromBranch "main"
```

#### Python 示例

```python
def create_branch(owner, repo, new_branch, from_branch="main"):
    """创建新分支"""
    # 1. 获取源分支的 SHA
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"无法获取源分支: {response.text}")
    
    sha = response.json()['object']['sha']
    
    # 2. 创建新分支
    create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    data = {
        "ref": f"refs/heads/{new_branch}",
        "sha": sha
    }
    
    response = requests.post(create_url, headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 422:
        raise Exception("分支已存在")
    else:
        raise Exception(f"创建失败: {response.text}")

# 使用
try:
    result = create_branch(OWNER, REPO, "feature/automation", "main")
    print(f"分支创建成功: {result['ref']}")
except Exception as e:
    print(f"错误: {e}")
```

---

### 🔀 合并分支

**API 端点:**
```
POST /repos/{owner}/{repo}/merges
```

#### PowerShell 示例

```powershell
function Merge-GitHubBranch {
    param(
        [string]$Base,      # 合并到哪个分支 (如 main)
        [string]$Head,      # 要合并的分支 (如 feature-branch)
        [string]$CommitMessage = "Merge $Head into $Base"
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    
    $body = @{
        base = $Base
        head = $Head
        commit_message = $CommitMessage
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod `
            -Uri "https://api.github.com/repos/$Owner/$Repo/merges" `
            -Headers $headers -Method POST -Body $body -ContentType "application/json"
        
        Write-Host "✅ 合并成功!"
        Write-Host "提交: $($response.sha)"
        return $response
    }
    catch {
        $errorMsg = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Error "合并失败: $($errorMsg.message)"
        return $null
    }
}

# 使用
Merge-GitHubBranch -Base "main" -Head "feature/new-feature" -CommitMessage "合并新功能"
```

#### Python 示例

```python
def merge_branch(owner, repo, base, head, commit_message=None):
    """合并分支"""
    url = f"https://api.github.com/repos/{owner}/{repo}/merges"
    
    if not commit_message:
        commit_message = f"Merge {head} into {base}"
    
    data = {
        "base": base,
        "head": head,
        "commit_message": commit_message
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 204:
        raise Exception("无需合并 (Already up to date)")
    elif response.status_code == 409:
        raise Exception("合并冲突，需要手动解决")
    elif response.status_code == 404:
        raise Exception("分支不存在")
    else:
        raise Exception(f"合并失败: {response.text}")

# 使用
try:
    result = merge_branch(OWNER, REPO, "main", "feature-branch")
    print(f"合并成功: {result['commit']['message']}")
except Exception as e:
    print(f"合并失败: {e}")
```

---

### 🗑️ 删除分支

**API 端点:**
```
DELETE /repos/{owner}/{repo}/git/refs/heads/{branch}
```

#### PowerShell 示例

```powershell
function Remove-GitHubBranch {
    param(
        [string]$BranchName
    )
    
    $Owner = $env:GITHUB_OWNER
    $Repo = $env:GITHUB_REPO
    $Token = $env:GITHUB_TOKEN
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
    }
    
    Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Owner/$Repo/git/refs/heads/$BranchName" `
        -Headers $headers -Method DELETE
    
    Write-Host "✅ 分支 '$BranchName' 已删除"
}

# 使用 (合并后删除)
Remove-GitHubBranch -BranchName "feature/old-feature"
```

#### Python 示例

```python
def delete_branch(owner, repo, branch):
    """删除分支"""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 204:
        print(f"分支 {branch} 已删除")
        return True
    else:
        raise Exception(f"删除失败: {response.status_code}")

# 使用
delete_branch(OWNER, REPO, "feature/completed")
```

---

## 完整示例脚本

### PowerShell: 完整自动化模块

```powershell
# GitHubAutomation.psm1
# GitHub API 自动化完整模块

$script:Config = @{
    Owner = $env:GITHUB_OWNER
    Repo = $env:GITHUB_REPO
    Token = $env:GITHUB_TOKEN
    BaseUrl = "https://api.github.com"
}

function Get-AuthHeaders {
    return @{
        "Authorization" = "Bearer $($script:Config.Token)"
        "Accept" = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
}

# ===== 文件操作 =====

function Get-GitHubFile {
    param([string]$Path)
    
    $url = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/contents/$Path"
    $response = Invoke-RestMethod -Uri $url -Headers (Get-AuthHeaders) -Method GET
    
    $content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content))
    return [PSCustomObject]@{
        Content = $content
        SHA = $response.sha
        Path = $response.path
        Size = $response.size
        Raw = $response
    }
}

function Set-GitHubFile {
    param(
        [string]$Path,
        [string]$Message,
        [string]$Content,
        [string]$Branch = "main",
        [string]$SHA = $null
    )
    
    $url = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/contents/$Path"
    
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $encoded = [System.Convert]::ToBase64String($bytes)
    
    $body = @{
        message = $Message
        content = $encoded
        branch = $Branch
    }
    if ($SHA) { $body['sha'] = $SHA }
    
    $response = Invoke-RestMethod -Uri $url -Headers (Get-AuthHeaders) -Method PUT `
        -Body ($body | ConvertTo-Json) -ContentType "application/json"
    
    return $response.content.sha
}

# ===== Issue 管理 =====

function New-GitHubIssue {
    param(
        [string]$Title,
        [string]$Body = "",
        [string[]]$Labels = @()
    )
    
    $url = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/issues"
    
    $bodyData = @{ title = $Title; body = $Body }
    if ($Labels.Count -gt 0) { $bodyData['labels'] = $Labels }
    
    $response = Invoke-RestMethod -Uri $url -Headers (Get-AuthHeaders) -Method POST `
        -Body ($bodyData | ConvertTo-Json) -ContentType "application/json"
    
    return [PSCustomObject]@{
        Number = $response.number
        URL = $response.html_url
        Title = $response.title
    }
}

function New-GuestbookEntry {
    param(
        [string]$Username,
        [string]$Message,
        [string]$Contact = ""
    )
    
    $title = "💬 留言 - $Username - $(Get-Date -Format 'yyyy-MM-dd')"
    $body = @"
## 留言详情

| 项目 | 内容 |
|------|------|
| **留言者** | @$Username |
| **时间** | $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') |

### 内容

$Message

---

$(if($Contact){"**联系方式:** $Contact"})
"@
    
    return New-GitHubIssue -Title $title -Body $body -Labels @("guestbook")
}

# ===== 分支管理 =====

function New-FeatureBranch {
    param(
        [string]$FeatureName,
        [string]$FromBranch = "main"
    )
    
    $branchName = "feature/$FeatureName"
    
    # 获取源分支 SHA
    $refUrl = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/git/refs/heads/$FromBranch"
    $ref = Invoke-RestMethod -Uri $refUrl -Headers (Get-AuthHeaders) -Method GET
    
    # 创建分支
    $createUrl = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/git/refs"
    $body = @{
        ref = "refs/heads/$branchName"
        sha = $ref.object.sha
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri $createUrl -Headers (Get-AuthHeaders) -Method POST `
        -Body $body -ContentType "application/json"
    
    Write-Host "✅ 分支 '$branchName' 已创建"
    return $branchName
}

function Merge-And-Delete {
    param(
        [string]$FeatureBranch,
        [string]$TargetBranch = "main"
    )
    
    # 合并
    $mergeUrl = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/merges"
    $body = @{
        base = $TargetBranch
        head = $FeatureBranch
        commit_message = "Merge $FeatureBranch into $TargetBranch"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri $mergeUrl -Headers (Get-AuthHeaders) -Method POST `
        -Body $body -ContentType "application/json"
    
    Write-Host "✅ 已合并到 $TargetBranch"
    
    # 删除
    $deleteUrl = "$($script:Config.BaseUrl)/repos/$($script:Config.Owner)/$($script:Config.Repo)/git/refs/heads/$FeatureBranch"
    Invoke-RestMethod -Uri $deleteUrl -Headers (Get-AuthHeaders) -Method DELETE
    
    Write-Host "✅ 分支 '$FeatureBranch' 已删除"
}

# 导出函数
Export-ModuleMember -Function *-GitHub*, *-FeatureBranch, Merge-And-Delete, New-GuestbookEntry
```

### Python: 完整自动化类

```python
"""
github_automation.py
GitHub API 自动化完整封装
"""

import base64
import os
from datetime import datetime
from typing import List, Dict, Optional
import requests


class GitHubAutomation:
    """GitHub API 自动化操作类"""
    
    API_VERSION = "2022-11-28"
    BASE_URL = "https://api.github.com"
    
    def __init__(self, owner: str, repo: str, token: str = None):
        self.owner = owner
        self.repo = repo
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION
        })
    
    # ========== 文件操作 ==========
    
    def read_file(self, path: str) -> Optional[Dict]:
        """读取文件内容"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/contents/{path}"
        response = self.session.get(url)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        return {
            'content': base64.b64decode(data['content']).decode('utf-8'),
            'sha': data['sha'],
            'path': data['path'],
            'size': data['size'],
            'url': data['html_url']
        }
    
    def write_file(self, path: str, content: str, message: str, 
                   branch: str = "main", sha: str = None) -> Dict:
        """创建或更新文件"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/contents/{path}"
        
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        data = {
            "message": message,
            "content": encoded,
            "branch": branch
        }
        if sha:
            data["sha"] = sha
        
        response = self.session.put(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        return {
            'commit_sha': result['commit']['sha'],
            'content_sha': result['content']['sha'],
            'url': result['content']['html_url']
        }
    
    def delete_file(self, path: str, message: str, sha: str, branch: str = "main"):
        """删除文件"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/contents/{path}"
        response = self.session.delete(url, json={
            "message": message,
            "sha": sha,
            "branch": branch
        })
        response.raise_for_status()
        return response.json()
    
    # ========== Issue 管理 ==========
    
    def create_issue(self, title: str, body: str = "", 
                     labels: List[str] = None, assignees: List[str] = None) -> Dict:
        """创建 Issue"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/issues"
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        return {
            'number': result['number'],
            'title': result['title'],
            'url': result['html_url'],
            'state': result['state']
        }
    
    def create_guestbook_entry(self, username: str, message: str, 
                               contact: str = "") -> Dict:
        """创建留言板条目"""
        title = f"💬 留言 - {username} - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""## 留言详情

| 项目 | 内容 |
|------|------|
| **留言者** | @{username} |
| **时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

### 内容

{message}

---
"""
        if contact:
            body += f"\n**联系方式:** {contact}"
        
        return self.create_issue(title, body, labels=["guestbook", "feedback"])
    
    def list_issues(self, state: str = "open", labels: List[str] = None,
                    per_page: int = 30) -> List[Dict]:
        """列出 Issues"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/issues"
        params = {"state": state, "per_page": per_page}
        if labels:
            params["labels"] = ",".join(labels)
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        issues = response.json()
        # 过滤掉 Pull Requests
        return [i for i in issues if 'pull_request' not in i]
    
    def add_comment(self, issue_number: int, body: str) -> Dict:
        """添加评论"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
        response = self.session.post(url, json={"body": body})
        response.raise_for_status()
        return response.json()
    
    # ========== 分支管理 ==========
    
    def list_branches(self) -> List[Dict]:
        """列出分支"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/branches"
        response = self.session.get(url)
        response.raise_for_status()
        
        return [
            {"name": b['name'], "sha": b['commit']['sha'][:7]}
            for b in response.json()
        ]
    
    def create_branch(self, name: str, from_branch: str = "main") -> Dict:
        """创建分支"""
        # 获取源分支 SHA
        ref_url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/git/refs/heads/{from_branch}"
        ref_response = self.session.get(ref_url)
        ref_response.raise_for_status()
        sha = ref_response.json()['object']['sha']
        
        # 创建新分支
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/git/refs"
        response = self.session.post(url, json={
            "ref": f"refs/heads/{name}",
            "sha": sha
        })
        response.raise_for_status()
        return response.json()
    
    def merge_branch(self, base: str, head: str, message: str = None) -> Dict:
        """合并分支"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/merges"
        data = {
            "base": base,
            "head": head,
            "commit_message": message or f"Merge {head} into {base}"
        }
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 204:
            raise Exception("Already up to date")
        elif response.status_code == 409:
            raise Exception("Merge conflict")
        
        response.raise_for_status()
        return response.json()
    
    def delete_branch(self, name: str):
        """删除分支"""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/git/refs/heads/{name}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.status_code == 204
    
    def merge_and_cleanup(self, feature_branch: str, target: str = "main"):
        """合并并清理分支"""
        self.merge_branch(target, feature_branch)
        self.delete_branch(feature_branch)
        return True


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 初始化
    gh = GitHubAutomation(
        owner=os.environ.get('GITHUB_OWNER'),
        repo=os.environ.get('GITHUB_REPO'),
        token=os.environ.get('GITHUB_TOKEN')
    )
    
    # 1. 创建留言
    entry = gh.create_guestbook_entry(
        username="DemoUser",
        message="这个自动化工具太棒了！",
        contact="demo@example.com"
    )
    print(f"留言已创建: {entry['url']}")
    
    # 2. 写入文件
    result = gh.write_file(
        path="automation/log.md",
        content=f"# 操作日志\n\n时间: {datetime.now()}\n",
        message="添加操作日志"
    )
    print(f"文件已写入: {result['url']}")
    
    # 3. 分支操作
    gh.create_branch("feature/test")
    # ... 进行一些修改 ...
    gh.merge_and_cleanup("feature/test")
    print("分支合并并清理完成")
```

---

## 常见问题

### Q1: 遇到 404 错误？

- 检查 Token 是否有足够的权限
- 确认仓库名称和所有者正确
- 确认仓库不是私有的 (或 Token 有权限访问私有仓库)

### Q2: 内容编码问题？

GitHub API 要求内容使用 Base64 编码：
```python
# Python
import base64
encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
```

```powershell
# PowerShell
$bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
$encoded = [System.Convert]::ToBase64String($bytes)
```

### Q3: 如何更新文件？

必须先读取文件获取 `sha`，然后在 PUT 请求中提供：
1. 调用 GET 读取文件 → 获取 sha
2. 调用 PUT 更新文件 → 提供 sha

### Q4: 速率限制？

- 认证用户: 5000 请求/小时
- 检查限制: `GET /rate_limit`
- 响应头中查看: `X-RateLimit-Remaining`

---

## 参考文档

- [GitHub REST API 文档](https://docs.github.com/en/rest)
- [GitHub API 变更日志](https://docs.github.com/en/rest/overview/api-versions)
- [GitHub GraphQL API](https://docs.github.com/en/graphql) (更强大的查询能力)

---

*最后更新: 2025-02-13*
