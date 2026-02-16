# OpenClaw PowerShell 自动化脚本使用说明

## 脚本列表

| 脚本 | 功能 | 类型 |
|------|------|------|
| `OpenClawBackup.psm1` | 工作区备份 | 模块 |
| `OpenClawGit.psm1` | Git自动化 | 模块 |
| `OpenClawMonitor.psm1` | 系统监控 | 模块 |

---

## 1. 工作区备份脚本 (OpenClawBackup.psm1)

### 特性
- ✅ 增量备份（时间戳/哈希两种模式）
- ✅ 完整的错误处理和日志记录
- ✅ 可配置的备份策略
- ✅ 自动清理旧备份
- ✅ 备份清单生成

### 安装与导入
```powershell
# 导入模块
Import-Module .\OpenClawBackup.psm1

# 或者使用完整路径
Import-Module "C:\Users\Admin\.openclaw\workspace\scripts\OpenClawBackup.psm1"
```

### 基本用法

#### 使用默认配置执行备份
```powershell
Start-WorkspaceBackup
```

#### 使用配置文件
```powershell
# 创建配置文件（参考 backup-config.example.json）
Start-WorkspaceBackup -ConfigPath .\backup-config.json
```

#### 命令行参数方式
```powershell
Start-WorkspaceBackup `
    -SourcePath "C:\MyProject" `
    -BackupRoot "D:\Backups" `
    -IncrementalMode Timestamp
```

#### 预览模式（-WhatIf）
```powershell
Start-WorkspaceBackup -WhatIf
```

#### 确认模式（-Confirm）
```powershell
Start-WorkspaceBackup -Confirm
```

### 查看备份历史
```powershell
Get-BackupHistory
Get-BackupHistory -BackupRoot "D:\Backups"
```

### 配置文件示例
```json
{
    "SourcePath": "C:\\Users\\Admin\\.openclaw\\workspace",
    "BackupRoot": "C:\\Users\\Admin\\Backups\\OpenClaw",
    "RetentionDays": 30,
    "ExcludePatterns": ["*.tmp", "node_modules", ".git"],
    "IncrementalMode": "Timestamp"
}
```

---

## 2. Git自动化脚本 (OpenClawGit.psm1)

### 特性
- ✅ 封装常用Git操作
- ✅ 完整的参数验证
- ✅ 管道输入支持
- ✅ ShouldProcess支持（-WhatIf, -Confirm）
- ✅ 彩色输出

### 安装与导入
```powershell
Import-Module .\OpenClawGit.psm1
```

### 命令列表

#### git-status - 查看仓库状态
```powershell
# 当前目录
git-status

# 批量检查多个仓库（管道）
Get-ChildItem -Directory | git-status

# 简短模式
git-status -Short
```

#### git-commit - 提交更改
```powershell
# 基本提交
git-commit -Message "修复登录bug"

# 提交并推送
git-commit -Message "新增功能" -Push

# 指定文件
git-commit -Message "更新配置" -Files @("config.json", "settings.xml")

# 修改最后一次提交
git-commit -Message "修正提交信息" -Amend

# 预览模式
git-commit -Message "测试" -WhatIf
```

#### git-branch - 分支管理
```powershell
# 列出分支
git-branch

# 创建分支
git-branch -Name "feature/new-ui" -Create

# 创建并切换
git-branch -Name "hotfix/bug-123" -Create -Checkout

# 删除分支（安全模式）
git-branch -Name "old-branch" -Delete

# 强制删除
git-branch -Name "old-branch" -Delete -Force

# 带确认
git-branch -Name "important-branch" -Delete -Confirm
```

#### git-log - 查看提交历史
```powershell
# 默认显示20条
git-log

# 指定数量
git-log -Count 50

# 图形化显示
git-log -Graph

# 按作者筛选
git-log -Author "zhangsan"

# 按时间范围
git-log -Since "2026-01-01" -Until "2026-02-01"
```

#### git-sync - 智能同步
```powershell
# 标准拉取
git-sync

# 使用变基
git-sync -Rebase

# 自动暂存本地更改
git-sync -Stash
```

#### git-pr - 创建Pull Request
```powershell
# 推送并生成PR链接
git-pr

# 指定目标分支
git-pr -Base "develop"

# 创建Draft PR
git-pr -Draft
```

### 管道示例
```powershell
# 批量查看多个仓库状态
Get-ChildItem D:\Projects -Directory | git-status

# 批量检查
Get-ChildItem D:\Projects -Directory | ForEach-Object {
    Write-Host "`n=== $($_.Name) ===" -ForegroundColor Cyan
    git-status -Path $_.FullName
}
```

---

## 3. 系统监控脚本 (OpenClawMonitor.psm1)

### 特性
- ✅ 监控OpenClaw运行状态
- ✅ 高级函数设计
- ✅ 结构化输出（自定义对象）
- ✅ 完整的错误处理
- ✅ 自定义格式化视图

### 安装与导入
```powershell
Import-Module .\OpenClawMonitor.psm1
```

### 命令列表

#### Get-OpenClawStatus - 获取状态
```powershell
# 基本状态
Get-OpenClawStatus

# 详细模式（包含系统信息）
Get-OpenClawStatus -Detailed

# 指定网关地址
Get-OpenClawStatus -GatewayUrl "http://localhost:3939"

# 格式化输出
Get-OpenClawStatus | Format-List
```

#### Watch-OpenClawHealth - 持续监控
```powershell
# 每5秒监控一次，持续60秒
Watch-OpenClawHealth -Interval 5 -Duration 60

# 保存到日志文件
Watch-OpenClawHealth -Interval 10 -LogFile "C:\Logs\openclaw-health.log"

# 出错时警报
Watch-OpenClawHealth -AlertOnError -Interval 5

# 长时间监控
Watch-OpenClawHealth -Interval 30 -Duration 3600
```

#### Get-SystemHealthReport - 系统健康报告
```powershell
# 基本报告
Get-SystemHealthReport

# 包含进程信息
Get-SystemHealthReport -IncludeProcesses

# 包含网络信息
Get-SystemHealthReport -IncludeNetwork

# 导出为CSV
Get-SystemHealthReport | Export-Csv -Path "report.csv" -NoTypeInformation

# 导出为JSON
Get-SystemHealthReport | ConvertTo-Json -Depth 3 | Out-File "report.json"
```

#### Repair-OpenClawService - 修复服务
```powershell
# 自动检测并修复
Repair-OpenClawService

# 强制重启
Repair-OpenClawService -Force

# 预览模式
Repair-OpenClawService -WhatIf
```

#### Get-SystemInfo - 获取系统信息
```powershell
Get-SystemInfo

# 查看内存使用率
Get-SystemInfo | Select-Object MemoryUsagePercent, FreeMemoryGB

# 查看磁盘使用率
Get-SystemInfo | Select-Object DiskUsagePercent, DiskFreeGB
```

### 监控示例

#### 实时监控脚本
```powershell
# 持续监控并记录到文件
$logFile = "C:\Logs\openclaw-$(Get-Date -Format 'yyyyMMdd').log"

while ($true) {
    $status = Get-OpenClawStatus
    
    if ($status.OverallHealth -ne 'Healthy') {
        Write-Host "警告: OpenClaw状态异常!" -ForegroundColor Red
        # 发送通知（如果有通知模块）
    }
    
    $status | ConvertTo-Json -Compress | Add-Content $logFile
    Start-Sleep -Seconds 60
}
```

#### 定时健康检查
```powershell
# 每小时检查一次
function Test-OpenClawScheduled {
    $status = Get-OpenClawStatus
    
    if ($status.OverallHealth -eq 'Critical') {
        # 尝试自动修复
        Repair-OpenClawService -Confirm:$false
    }
    
    return $status
}

# 添加到计划任务
# schtasks /create /tn "OpenClawHealth" /tr "powershell -Command Test-OpenClawScheduled" /sc hourly
```

---

## 综合示例

### 日常开发工作流
```powershell
# 1. 检查OpenClaw状态
$status = Get-OpenClawStatus
if ($status.OverallHealth -ne 'Healthy') {
    Write-Error "OpenClaw未正常运行!"
    return
}

# 2. 检查Git状态
git-status

# 3. 同步代码
git-sync -Stash

# 4. 开发工作...

# 5. 提交更改
git-commit -Message "完成今日开发" -Push

# 6. 备份工作区
Start-WorkspaceBackup -ConfigPath .\backup-config.json
```

### 自动化脚本示例
```powershell
# daily-maintenance.ps1
param(
    [string]$BackupConfig = ".\backup-config.json"
)

Write-Host "=== 开始日常维护任务 ===" -ForegroundColor Cyan

# 1. 检查系统状态
$status = Get-OpenClawStatus
if ($status.OverallHealth -eq 'Critical') {
    Write-Host "尝试修复OpenClaw..." -ForegroundColor Yellow
    Repair-OpenClawService
}

# 2. 执行备份
Write-Host "`n执行备份..." -ForegroundColor Cyan
$result = Start-WorkspaceBackup -ConfigPath $BackupConfig

# 3. 生成报告
Write-Host "`n生成健康报告..." -ForegroundColor Cyan
$report = Get-SystemHealthReport
$report | ConvertTo-Json -Depth 3 | Out-File ".\health-report.json"

Write-Host "`n=== 维护任务完成 ===" -ForegroundColor Green
```

---

## 故障排除

### 模块导入失败
```powershell
# 检查执行策略
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 检查文件路径
Test-Path .\OpenClawBackup.psm1
```

### Git命令失败
```powershell
# 检查Git安装
Get-Command git

# 检查当前目录是否为Git仓库
Test-Path .\.git -PathType Container
```

### 监控无数据
```powershell
# 检查OpenClaw网关是否运行
Invoke-WebRequest http://localhost:3939/status

# 检查端口监听
Get-NetTCPConnection -LocalPort 3939
```

---

## 许可证

MIT License - OpenClaw Automation Scripts
