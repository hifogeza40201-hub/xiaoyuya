# PowerShell进阶学习笔记 - 模块与错误处理

## 一、PowerShell模块系统

### 1.1 模块类型

#### Script模块 (.psm1)
```powershell
# MyModule.psm1
function Get-MyData {
    param([string]$Name)
    return "Hello, $Name!"
}

Export-ModuleMember -Function Get-MyData
```

#### 模块清单 (.psd1)
```powershell
# MyModule.psd1
@{
    RootModule = 'MyModule.psm1'
    ModuleVersion = '1.0.0'
    GUID = '12345678-1234-1234-1234-123456789012'
    Author = 'XiaoYu'
    Description = '示例PowerShell模块'
    FunctionsToExport = @('Get-MyData')
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
}
```

### 1.2 模块路径和导入
```powershell
# 查看模块路径
$env:PSModulePath -split ';'

# 导入模块
Import-Module MyModule
Import-Module .\MyModule.psm1
Import-Module .\MyModule.psd1

# 查看已加载模块
Get-Module
Get-Module -ListAvailable

# 移除模块
Remove-Module MyModule
```

### 1.3 模块作用域
```powershell
# 脚本作用域
$Script:Config = @{
    Server = 'localhost'
    Port = 8080
}

# 模块私有变量（不导出）
$Private:InternalCache = @{}

# 导出的变量
$Global:MyModuleVersion = '1.0.0'
```

---

## 二、错误处理机制

### 2.1 Try-Catch-Finally
```powershell
try {
    $result = 1 / 0
} catch [System.DivideByZeroException] {
    Write-Error "除零错误！"
} catch {
    Write-Error "其他错误: $_"
} finally {
    Write-Host "清理工作..."
}
```

### 2.2 错误操作参数
```powershell
# 静默忽略错误
Get-Item -Path ".\不存在的文件.txt" -ErrorAction SilentlyContinue

# 终止执行
Get-Item -Path ".\不存在的文件.txt" -ErrorAction Stop

# 设置全局偏好
$ErrorActionPreference = 'Stop'  # Continue | SilentlyContinue | Stop | Inquire | Break
```

### 2.3 错误变量
```powershell
# 最近的错误
$Error[0]

# 错误详细信息
$Error[0].Exception.Message
$Error[0].Exception.StackTrace
$Error[0].InvocationInfo.Line

# 清除错误
$Error.Clear()
```

### 2.4 终止错误vs非终止错误
```powershell
# 非终止错误（默认）
function Test-NonTerminating {
    [CmdletBinding()]
    param()
    Write-Error "这是一个非终止错误"
    Write-Host "这行还会执行"
}

# 终止错误
function Test-Terminating {
    [CmdletBinding()]
    param()
    throw "这是一个终止错误"
    Write-Host "这行不会执行"
}
```

---

## 三、高级函数开发

### 3.1 CmdletBinding和参数
```powershell
function Get-SystemInfo {
    [CmdletBinding(
        SupportsShouldProcess = $true,
        ConfirmImpact = 'Medium'
    )]
    param(
        [Parameter(
            Mandatory = $true,
            Position = 0,
            ValueFromPipeline = $true,
            HelpMessage = "计算机名称"
        )]
        [ValidateNotNullOrEmpty()]
        [string[]]$ComputerName,

        [Parameter()]
        [ValidateSet('CPU', 'Memory', 'Disk', 'All')]
        [string]$InfoType = 'All',

        [Parameter()]
        [ValidateRange(1, 100)]
        [int]$TimeoutSeconds = 30,

        [switch]$Detailed
    )

    begin {
        Write-Verbose "开始收集系统信息..."
    }

    process {
        foreach ($computer in $ComputerName) {
            if ($PSCmdlet.ShouldProcess($computer, "收集系统信息")) {
                try {
                    # 实际收集逻辑
                    [PSCustomObject]@{
                        ComputerName = $computer
                        InfoType = $InfoType
                        Timestamp = Get-Date
                    }
                } catch {
                    Write-Error "无法连接到 $computer : $_"
                }
            }
        }
    }

    end {
        Write-Verbose "系统信息收集完成"
    }
}
```

### 3.2 参数验证
```powershell
function New-UserAccount {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidatePattern('^[a-zA-Z0-9_]{3,20}$')]
        [string]$Username,

        [Parameter(Mandatory)]
        [ValidateLength(8, 128)]
        [Security.SecureString]$Password,

        [Parameter()]
        [ValidateScript({
            if ($_ -lt (Get-Date)) {
                throw "过期日期必须在将来"
            }
            $true
        })]
        [DateTime]$ExpirationDate,

        [Parameter()]
        [ValidateCount(1, 5)]
        [string[]]$Groups
    )
    # 函数逻辑...
}
```

### 3.3 管道支持
```powershell
function Convert-ToUpperCase {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [string]$InputString
    )

    process {
        $InputString.ToUpper()
    }
}

# 使用管道
"hello", "world" | Convert-ToUpperCase
```

---

## 四、调试技术

### 4.1 使用Write-Debug
```powershell
$DebugPreference = 'Continue'

function Test-Debug {
    [CmdletBinding()]
    param([string]$Name)
    
    Write-Debug "开始处理: $Name"
    $result = $Name.ToUpper()
    Write-Debug "处理结果: $result"
    
    return $result
}
```

### 4.2 设置断点
```powershell
# 行断点
Set-PSBreakpoint -Script ".\MyScript.ps1" -Line 10

# 变量断点
Set-PSBreakpoint -Variable "ErrorCount" -Mode Write

# 函数断点
Set-PSBreakpoint -Command "Get-Process"

# 查看断点
Get-PSBreakpoint

# 移除断点
Remove-PSBreakpoint -Id 1
```

### 4.3 Trace-Command
```powershell
Trace-Command -Name ParameterBinding -Expression {
    Get-Process -Name "chrome"
} -PSHost
```

---

## 五、日志记录最佳实践

```powershell
# 日志函数
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [Parameter()]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',

        [Parameter()]
        [string]$LogFile = ".\logs\app.log"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 确保日志目录存在
    $logDir = Split-Path $LogFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # 写入日志
    Add-Content -Path $LogFile -Value $logEntry
    
    # 同时输出到控制台
    switch ($Level) {
        'ERROR' { Write-Error $Message }
        'WARN'  { Write-Warning $Message }
        'DEBUG' { Write-Debug $Message }
        default { Write-Host $logEntry }
    }
}
```

---

## 六、OpenClaw集成应用

### 6.1 自动化备份脚本
```powershell
# backup-workspace.ps1
[CmdletBinding()]
param(
    [Parameter()]
    [string]$SourcePath = ".\workspace",
    
    [Parameter()]
    [string]$BackupPath = "D:\Backups",
    
    [Parameter()]
    [int]$KeepDays = 7
)

try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "workspace_$timestamp.zip"
    $backupFullPath = Join-Path $BackupPath $backupName
    
    Write-Log "开始备份: $SourcePath -> $backupFullPath" -Level 'INFO'
    
    # 创建备份
    Compress-Archive -Path $SourcePath -DestinationPath $backupFullPath -Force
    
    # 清理旧备份
    Get-ChildItem -Path $BackupPath -Filter "workspace_*.zip" |
        Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$KeepDays) } |
        Remove-Item -Force
    
    Write-Log "备份完成: $backupName" -Level 'INFO'
} catch {
    Write-Log "备份失败: $_" -Level 'ERROR'
    exit 1
}
```

---

## 总结

### 关键要点
1. **模块系统**: 使用.psd1清单文件定义模块元数据，合理组织模块结构
2. **错误处理**: 使用Try-Catch处理异常，区分终止/非终止错误
3. **参数验证**: 使用Validate*属性确保输入数据质量
4. **管道支持**: 实现Begin/Process/End块支持管道操作
5. **调试技巧**: 使用Write-Debug和断点进行调试

### 下一步学习
- PowerShell类与面向对象编程
- PowerShell与.NET集成
- 异步操作和并行处理
- 安全与凭证管理

---

*学习日期: 2026-02-16*  
*记录者: 小宇 ⛰️*
