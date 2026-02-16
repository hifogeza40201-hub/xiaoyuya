# PowerShell 速查卡片

> 📚 基于2026-02-16深度学习整理  
> 🎯 快速参考，即查即用

---

## 📇 卡片1：模块系统

### 创建模块 - 3步曲
```powershell
# 1. 创建目录
New-Item -ItemType Directory -Path MyModule

# 2. 编写模块文件 MyModule.psm1
function Get-MyData {
    param([string]$Name)
    "Hello, $Name!"
}
Export-ModuleMember -Function Get-MyData

# 3. 创建清单 MyModule.psd1
New-ModuleManifest -Path MyModule.psd1 `
    -RootModule MyModule.psm1 `
    -ModuleVersion 1.0.0 `
    -FunctionsToExport Get-MyData
```

### 模块操作速查
| 操作 | 命令 |
|------|------|
| 导入模块 | `Import-Module MyModule` |
| 移除模块 | `Remove-Module MyModule` |
| 查看已加载 | `Get-Module` |
| 查看可用 | `Get-Module -ListAvailable` |
| 查看路径 | `$env:PSModulePath` |

---

## 📇 卡片2：错误处理

### Try-Catch-Finally 模板
```powershell
try {
    # 可能出错的代码
    $result = 1 / $divisor
} catch [System.DivideByZeroException] {
    # 特定异常
    Write-Error "除零错误"
} catch {
    # 通用异常 ($_ 表示错误对象)
    Write-Error "错误: $_"
} finally {
    # 清理代码（始终执行）
    Write-Host "清理完成"
}
```

### ErrorAction 参数
```powershell
# 静默忽略
Get-Item ".\不存在的文件" -ErrorAction SilentlyContinue

# 终止执行
Get-Item ".\不存在的文件" -ErrorAction Stop

# 全局设置
$ErrorActionPreference = 'Stop'  # Continue | SilentlyContinue | Stop | Inquire
```

### $Error 变量
```powershell
# 最近的错误
$Error[0]

# 错误详情
$Error[0].Exception.Message
$Error[0].Exception.StackTrace

# 清空错误
$Error.Clear()
```

---

## 📇 卡片3：高级函数

### 完整函数模板
```powershell
function Invoke-MyFunction {
    [CmdletBinding(
        SupportsShouldProcess = $true,  # 支持 -WhatIf/-Confirm
        ConfirmImpact = 'Medium'        # 影响级别
    )]
    [OutputType([PSCustomObject])]      # 输出类型声明
    
    param(
        [Parameter(
            Mandatory = $true,          # 必填
            Position = 0,               # 位置参数
            ValueFromPipeline = $true,  # 支持管道
            HelpMessage = "提示信息"      # 帮助文本
        )]
        [ValidateNotNullOrEmpty()]      # 验证非空
        [string[]]$InputObject,

        [Parameter()]
        [ValidateSet('Option1', 'Option2')]  # 枚举验证
        [string]$Mode = 'Option1',

        [switch]$Force                  # 开关参数
    )

    begin {
        # 初始化（管道开始时执行一次）
        Write-Verbose "开始处理..."
    }

    process {
        # 处理每个输入对象
        foreach ($item in $InputObject) {
            if ($PSCmdlet.ShouldProcess($item, "执行操作")) {
                # 实际操作
                [PSCustomObject]@{
                    Input = $item
                    Result = "Success"
                }
            }
        }
    }

    end {
        # 清理（管道结束时执行一次）
        Write-Verbose "处理完成"
    }
}
```

### 参数验证属性
```powershell
[ValidateLength(1, 100)]          # 长度范围
[ValidateRange(1, 999)]           # 数值范围
[ValidatePattern('^\d{4}$')]      # 正则匹配
[ValidateScript({ $_ -gt 0 })]    # 脚本验证
[ValidateCount(1, 10)]            # 数组元素数量
[AllowNull()]                     # 允许null
[Alias('Name', 'N')]              # 参数别名
```

---

## 📇 卡片4：管道处理

### 管道输入模式
```powershell
function Process-Pipeline {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [string]$InputItem
    )

    begin {
        $results = @()
    }

    process {
        # 每个管道对象都会执行这里
        $results += $InputItem.ToUpper()
    }

    end {
        # 返回聚合结果
        $results
    }
}

# 使用管道
"a", "b", "c" | Process-Pipeline
```

### 属性名绑定
```powershell
param(
    [Parameter(ValueFromPipelineByPropertyName)]
    [string]$Name,    # 自动绑定输入对象的Name属性

    [Parameter(ValueFromPipelineByPropertyName)]
    [int]$Id          # 自动绑定输入对象的Id属性
)
```

---

## 📇 卡片5：日志记录

### 分级日志函数
```powershell
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',

        [string]$LogFile = ".\logs\app.log"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 确保目录存在
    $logDir = Split-Path $LogFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # 写入文件
    Add-Content -Path $LogFile -Value $logEntry
    
    # 控制台输出
    switch ($Level) {
        'ERROR' { Write-Host $logEntry -ForegroundColor Red }
        'WARN'  { Write-Host $logEntry -ForegroundColor Yellow }
        'DEBUG' { Write-Host $logEntry -ForegroundColor Gray }
        default { Write-Host $logEntry }
    }
}
```

---

## 📇 卡片6：调试技术

### 调试命令
```powershell
# 输出调试信息（需设置 $DebugPreference = 'Continue'）
Write-Debug "调试信息"

# 详细输出（需设置 $VerbosePreference = 'Continue'）
Write-Verbose "详细信息"

# 设置断点
Set-PSBreakpoint -Script script.ps1 -Line 10
Set-PSBreakpoint -Variable "ErrorCount" -Mode Write
Set-PSBreakpoint -Command "Get-Process"

# 查看/移除断点
Get-PSBreakpoint
Remove-PSBreakpoint -Id 1

# 跟踪命令执行
Trace-Command -Name ParameterBinding -Expression { Get-Process chrome } -PSHost
```

### 调试偏好设置
```powershell
$DebugPreference = 'Continue'      # 显示Write-Debug
$VerbosePreference = 'Continue'    # 显示Write-Verbose
$ErrorActionPreference = 'Stop'    # 遇到错误停止
```

---

## 📇 卡片7：常用Cmdlet

### 文件操作
```powershell
# 读写文件
$content = Get-Content file.txt -Raw
Set-Content file.txt -Value "内容" -Encoding UTF8
Add-Content file.txt -Value "追加内容"

# JSON处理
$json = Get-Content data.json | ConvertFrom-Json
$object | ConvertTo-Json -Depth 3 | Set-Content data.json

# 路径操作
Join-Path "C:\Dir" "file.txt"
Split-Path "C:\Dir\file.txt" -Parent    # C:\Dir
Split-Path "C:\Dir\file.txt" -Leaf      # file.txt
Test-Path "C:\Dir\file.txt"
```

### 集合操作
```powershell
# 过滤
$items | Where-Object { $_.Size -gt 100 }
$items | ?{ $_.Name -like "*test*" }

# 排序
$items | Sort-Object -Property Size -Descending

# 选择属性
$items | Select-Object -First 10 -Property Name, Size

# 分组
$items | Group-Object -Property Category

# 统计
$items | Measure-Object -Property Size -Sum -Average
```

---

## 📇 卡片8：OpenClaw集成

### 工作区备份脚本
```powershell
[CmdletBinding()]
param(
    [string]$Source = "$env:USERPROFILE\.openclaw\workspace",
    [string]$BackupDir = "D:\Backups",
    [int]$KeepVersions = 7
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupName = "workspace_$timestamp.zip"

Compress-Archive -Path $Source -DestinationPath (Join-Path $BackupDir $backupName)

# 清理旧版本
Get-ChildItem $BackupDir -Filter "workspace_*.zip" |
    Sort-Object CreationTime -Descending |
    Select-Object -Skip $KeepVersions |
    Remove-Item -Force
```

### Git自动化
```powershell
function git-sync {
    [CmdletBinding()]
    param([string]$Message = "Update $(Get-Date -Format 'yyyy-MM-dd')")
    
    git add .
    git commit -m $Message
    git pull
    git push
}
```

---

## 🎯 快速记忆口诀

### 函数设计五要素
1. **CmdletBinding** - 必须加，支持高级特性
2. **参数验证** - Validate* 防垃圾输入
3. **管道支持** - ValueFromPipeline 提升灵活性
4. **错误处理** - Try-Catch 保健壮
5. **日志记录** - 分级日志便调试

### 错误处理三步走
1. **Try** - 包可能出错的代码
2. **Catch** - 处理异常（特定→通用）
3. **Finally** - 清理资源（必定执行）

### 模块开发三板斧
1. **psm1** - 写功能代码
2. **psd1** - 配置元数据
3. **Import** - 导入使用

---

## 📖 使用建议

1. **新手**：按卡片1→2→3顺序学习
2. **进阶**：重点看卡片3、4、5
3. **调试**：收藏卡片6
4. **实战**：参考卡片7、8

---

*整理时间: 2026-02-16 01:54-02:00*  
*基于: 175KB深度学习成果*  
*整理者: 小宇 ⛰️*
