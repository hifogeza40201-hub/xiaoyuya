# PowerShell错误处理与调试技术 - 学习笔记

> **Agent**: 2  
> **主题**: PowerShell错误处理与调试技术  
> **创建日期**: 2026-02-16  
> **来源**: Microsoft PowerShell官方文档

---

## 目录
1. [Try-Catch-Finally 完整错误处理机制](#1-try-catch-finally-完整错误处理机制)
2. [$Error自动变量和错误记录](#2-error自动变量和错误记录)
3. [-ErrorAction参数和$ErrorActionPreference](#3-erroraction参数和erroractionpreference)
4. [终止错误vs非终止错误](#4-终止错误vs非终止错误)
5. [调试技术](#5-调试技术)
   - Write-Debug
   - Set-PSBreakpoint
   - Trace-Command
6. [日志记录最佳实践](#6-日志记录最佳实践)

---

## 1. Try-Catch-Finally 完整错误处理机制

### 1.1 基本概念

`try-catch-finally` 是 PowerShell 中处理**终止错误(Terminating Errors)**的主要机制。终止错误会阻止语句继续执行，如果不处理，PowerShell会停止运行当前函数或脚本。

- **try块**: 定义要监控错误的代码段
- **catch块**: 处理try块中发生的错误
- **finally块**: 无论是否发生错误都会执行的代码（用于资源清理）

### 1.2 语法结构

```powershell
# 基本语法
try { <语句列表> }
catch [ [<错误类型>[, <错误类型>]*] ] { <语句列表> }
finally { <语句列表> }

# 规则:
# - try块后必须有至少一个catch块或finally块
# - 可以有多个catch块来处理不同类型的错误
# - finally块最多一个
```

### 1.3 实际代码示例

```powershell
# ===== 示例1: 基本错误捕获 =====
try {
    $result = 10 / 0
    Write-Host "这行不会执行"
}
catch {
    Write-Host "发生错误: $_"
}

# ===== 示例2: 多个Catch块处理不同错误类型 =====
try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile("https://example.com/file.txt", "C:\temp\file.txt")
}
catch [System.Net.WebException], [System.IO.IOException] {
    Write-Host "网络或IO错误: 无法下载文件"
}
catch {
    Write-Host "其他错误: $_"
}
finally {
    # 确保资源被释放
    if ($wc) {
        $wc.Dispose()
        Write-Host "WebClient已释放"
    }
}

# ===== 示例3: 捕获特定异常类型 =====
try {
    Get-Content "C:\不存在的文件.txt" -ErrorAction Stop
}
catch [System.IO.FileNotFoundException] {
    Write-Host "文件未找到!"
}
catch [System.UnauthorizedAccessException] {
    Write-Host "没有访问权限!"
}
catch {
    Write-Host "其他错误: $($_.Exception.GetType().FullName)"
}

# ===== 示例4: 使用Throw重新抛出异常 =====
try {
    # 某些操作
    throw "自定义错误信息"
}
catch {
    Write-Host "捕获错误: $_"
    # 可以选择重新抛出
    throw
}

# ===== 示例5: 访问详细的异常信息 =====
try {
    Invoke-RestMethod -Uri "https://api.invalid.com/data"
}
catch {
    $errorRecord = $_
    Write-Host "错误消息: $($errorRecord.Exception.Message)"
    Write-Host "错误类型: $($errorRecord.Exception.GetType().FullName)"
    Write-Host "脚本堆栈: $($errorRecord.ScriptStackTrace)"
    Write-Host "类别信息: $($errorRecord.CategoryInfo)"
}
```

### 1.4 错误类型匹配规则

```powershell
# PowerShell通过继承匹配错误类型
# 具体类型应该放在通用类型之前

try {
    # 某些操作
}
catch [System.Management.Automation.CommandNotFoundException] {
    # 最具体的类型 - 命令未找到
    Write-Host "命令未找到!"
}
catch [System.SystemException] {
    # 基类 - 捕获SystemException及其子类
    Write-Host "系统异常!"
}
catch {
    # 捕获所有其他错误
    Write-Host "未知错误!"
}
```

### 1.5 与Trap语句的关系

`trap`语句是另一种处理终止错误的方式：

```powershell
# Trap语句示例
trap {
    Write-Host "Trap捕获到错误: $_"
    continue  # 继续执行
}

# 注意: 当try块内定义了trap，且有匹配的catch块时，
# trap语句会优先获得控制权
```

**Try-Catch vs Trap 对比:**

| 特性 | Try-Catch | Trap |
|------|-----------|------|
| 作用范围 | 限定的try块 | 整个脚本块 |
| 粒度 | 细粒度 | 粗粒度 |
| 推荐使用场景 | 结构化错误处理 | 全局错误捕获 |

---

## 2. $Error自动变量和错误记录

### 2.1 $Error变量概述

`$Error`是一个自动变量（ArrayList），用于存储当前PowerShell会话中的所有错误记录。最新的错误存储在索引0处。

```powershell
# 查看最新错误
$Error[0]

# 查看所有错误数量
$Error.Count

# 查看最近的5个错误
$Error[0..4]

# 清空错误列表
$Error.Clear()
```

### 2.2 ErrorRecord对象结构

每个错误都是一个ErrorRecord对象，包含以下重要属性：

```powershell
$Error[0] | Format-List -Property *

# 关键属性:
# - Exception              : 底层.NET异常对象
# - TargetObject           : 导致错误的对象
# - CategoryInfo           : 错误分类信息
# - FullyQualifiedErrorId  : 完整错误ID
# - ErrorDetails           : 详细错误信息
# - InvocationInfo         : 调用信息（行号、脚本名等）
# - ScriptStackTrace       : 脚本堆栈跟踪
```

### 2.3 使用示例

```powershell
# ===== 示例1: 分析错误详情 =====
Get-Content "C:\不存在的文件.txt" 2>$null

if ($Error.Count -gt 0) {
    $lastError = $Error[0]
    
    Write-Host "=== 错误分析 ==="
    Write-Host "异常类型: $($lastError.Exception.GetType().FullName)"
    Write-Host "异常消息: $($lastError.Exception.Message)"
    Write-Host "目标对象: $($lastError.TargetObject)"
    Write-Host "错误类别: $($lastError.CategoryInfo.Category)"
    Write-Host "脚本路径: $($lastError.InvocationInfo.ScriptName)"
    Write-Host "行号: $($lastError.InvocationInfo.ScriptLineNumber)"
    Write-Host "偏移量: $($lastError.InvocationInfo.OffsetInLine)"
}

# ===== 示例2: 自定义错误变量 =====
# 使用-ErrorVariable参数捕获特定命令的错误
Get-Process -Name "不存在的进程" -ErrorVariable MyErrors -ErrorAction SilentlyContinue

if ($MyErrors) {
    Write-Host "捕获到 $($MyErrors.Count) 个错误"
    foreach ($err in $MyErrors) {
        Write-Host "  - $($err.Exception.Message)"
    }
}

# 使用 + 追加错误
Get-Item "C:\无效路径" -ErrorVariable +MyErrors -ErrorAction SilentlyContinue

# ===== 示例3: 错误筛选和处理 =====
# 执行多个操作并收集错误
$operations = @(
    { Get-Content "C:\file1.txt" },
    { Get-Content "C:\file2.txt" },
    { 1/0 }
)

$Error.Clear()

foreach ($op in $operations) {
    try {
        & $op
    }
    catch {
        # 错误会自动添加到$Error
        continue
    }
}

# 分析所有收集的错误
$Error | Group-Object { $_.CategoryInfo.Category } | 
    Select-Object Name, Count

# ===== 示例4: Get-Error Cmdlet (PowerShell 7+) =====
# 获取详细的错误信息视图
Get-Error  # 显示最后一个错误的详细信息
Get-Error -Newest 3  # 显示最近的3个错误
```

### 2.4 错误视图 ($ErrorView)

PowerShell 7+ 提供了不同的错误显示视图：

```powershell
# ConciseView (默认) - 简洁视图
$ErrorView = "ConciseView"

# NormalView - 详细视图 (类似PowerShell 5.1)
$ErrorView = "NormalView"

# CategoryView - 分类视图 (生产环境)
$ErrorView = "CategoryView"
```

---

## 3. -ErrorAction参数和$ErrorActionPreference

### 3.1 ActionPreference枚举值

| 值 | 说明 |
|----|------|
| `SilentlyContinue` | 不显示错误，继续执行 |
| `Continue` | 显示错误，继续执行 (默认) |
| `Stop` | 显示错误并停止执行 |
| `Inquire` | 显示错误，询问是否继续 |
| `Ignore` | 忽略错误（不记录到$Error） |
| `Break` | 进入调试器 |

### 3.2 -ErrorAction参数

`-ErrorAction` (别名 `-ea`) 用于控制特定命令的错误处理行为：

```powershell
# 基本用法
Get-Process -Name "不存在的进程" -ErrorAction SilentlyContinue

# 将非终止错误转为终止错误
Get-Item "C:\不存在" -ErrorAction Stop

# 别名形式
Get-Content "file.txt" -ea Stop
```

### 3.3 $ErrorActionPreference变量

全局设置所有命令的默认错误处理行为：

```powershell
# 查看当前设置
$ErrorActionPreference

# 设置为静默继续
$ErrorActionPreference = "SilentlyContinue"

# 恢复默认
$ErrorActionPreference = "Continue"
```

### 3.4 代码示例

```powershell
# ===== 示例1: 参数与变量的优先级 =====
$ErrorActionPreference = "Continue"

# 参数覆盖变量
Get-Process "不存在的" -ErrorAction SilentlyContinue  # 不会显示错误
Get-Process "不存在的"  # 会显示错误（使用变量值）

# ===== 示例2: 结合Try-Catch使用 =====
# 将非终止错误转为终止错误以便捕获
$ErrorActionPreference = "SilentlyContinue"

try {
    # 使用-ErrorAction Stop强制触发catch
    Get-Content "C:\不存在.txt" -ErrorAction Stop
}
catch {
    Write-Host "文件读取失败: $_"
}

# ===== 示例3: 批量处理时忽略错误 =====
$files = @("C:\file1.txt", "C:\file2.txt", "C:\file3.txt")
$results = @()

foreach ($file in $files) {
    $content = Get-Content $file -ErrorAction SilentlyContinue
    if ($content) {
        $results += $content
    }
}

# ===== 示例4: 使用Inquire进行交互式调试 =====
# 适用于需要用户确认的场景
$ErrorActionPreference = "Inquire"
Remove-Item "C:\重要文件.txt"  # 会询问是否继续

# ===== 示例5: 脚本中的最佳实践 =====
function Process-Files {
    [CmdletBinding()]
    param(
        [string[]]$FilePaths
    )
    
    # 保存当前设置
    $originalPreference = $ErrorActionPreference
    
    try {
        $ErrorActionPreference = "Stop"
        
        foreach ($path in $FilePaths) {
            try {
                $content = Get-Content $path
                # 处理内容...
            }
            catch {
                Write-Warning "处理文件 $path 时出错: $_"
            }
        }
    }
    finally {
        # 恢复原始设置
        $ErrorActionPreference = $originalPreference
    }
}
```

### 3.5 范围注意事项

```powershell
# 在脚本块中修改的作用域仅限于该块
& {
    $ErrorActionPreference = "SilentlyContinue"
    Get-Process "不存在的"  # 不会报错
}

# 外部仍然使用原始值
Get-Process "不存在的"  # 根据外部设置可能报错
```

---

## 4. 终止错误vs非终止错误

### 4.1 核心区别

| 特性 | 终止错误 (Terminating) | 非终止错误 (Non-Terminating) |
|------|------------------------|------------------------------|
| 影响范围 | 停止当前管道执行 | 显示错误，继续执行 |
| 能否被Try-Catch捕获 | ✅ 可以 | ❌ 默认不行（需转为终止错误） |
| 默认行为 | 停止并显示错误 | 显示错误，继续 |
| 常见来源 | 致命问题、throw语句 | 资源不可用、权限问题 |

### 4.2 终止错误来源

```powershell
# 1. .NET运行时异常
[System.IO.File]::ReadAllText("C:\不存在.txt")

# 2. 使用throw
throw "这是一个终止错误"

# 3. Cmdlet的终止错误
Get-ChildItem -Path "::"  # 无效路径

# 4. 将非终止错误转为终止错误
Get-Content "C:\不存在.txt" -ErrorAction Stop
```

### 4.3 非终止错误示例

```powershell
# 这些默认是非终止错误
Get-Process -Name "不存在的进程"
Get-ChildItem -Path "C:\不存在"
Remove-Item -Path "C:\不存在的文件.txt"
```

### 4.4 代码处理策略

```powershell
# ===== 策略1: 将非终止转为终止错误 =====
function Get-ProcessData {
    param([string[]]$ProcessNames)
    
    $results = @()
    foreach ($name in $ProcessNames) {
        try {
            # 使用 -ErrorAction Stop 转为终止错误
            $proc = Get-Process -Name $name -ErrorAction Stop
            $results += $proc
        }
        catch {
            Write-Warning "无法获取进程 $name : $_"
        }
    }
    return $results
}

# ===== 策略2: 同时处理两种错误 =====
function Safe-Operation {
    [CmdletBinding()]
    param()
    
    # 捕获终止错误
    try {
        # 操作1: 可能产生终止错误
        [System.IO.File]::ReadAllText("C:\test.txt")
        
        # 操作2: 将非终止转为终止
        Get-ChildItem "C:\不存在" -ErrorAction Stop
    }
    catch [System.IO.FileNotFoundException] {
        Write-Host "文件未找到，使用默认值"
    }
    catch {
        Write-Error "未预期的错误: $_"
    }
}

# ===== 策略3: 使用统一错误处理 =====
$ErrorActionPreference = "Stop"

try {
    # 所有操作都会严格执行
    $data = Import-Csv "data.csv"
    $result = $data | Where-Object { $_.Value -gt 100 }
    Export-Csv $result -Path "output.csv"
}
catch {
    Write-Error "批处理失败: $_"
    exit 1
}

# ===== 策略4: 混合模式处理 =====
function Robust-FileProcess {
    param(
        [Parameter(Mandatory)]
        [string[]]$FilePaths
    )
    
    $stats = @{
        Success = 0
        Failed = 0
        Errors = @()
    }
    
    foreach ($file in $FilePaths) {
        try {
            # 尝试读取文件（转为终止错误）
            $content = Get-Content $file -ErrorAction Stop
            
            # 处理内容
            $processed = $content | ForEach-Object { $_.ToUpper() }
            
            # 输出到临时文件
            $processed | Out-File "temp_$file" -ErrorAction Stop
            
            $stats.Success++
        }
        catch {
            $stats.Failed++
            $stats.Errors += [PSCustomObject]@{
                File = $file
                Error = $_.Exception.Message
                Time = Get-Date
            }
        }
    }
    
    return $stats
}

# 使用
$files = Get-ChildItem "*.log" | Select-Object -ExpandProperty FullName
$result = Robust-FileProcess -FilePaths $files

if ($result.Failed -gt 0) {
    Write-Warning "$($result.Failed) 个文件处理失败"
    $result.Errors | Export-Csv "errors.csv" -NoTypeInformation
}
```

---

## 5. 调试技术

### 5.1 Write-Debug

`Write-Debug` 用于输出调试信息，默认不显示。

```powershell
# ===== 基本用法 =====
function Process-Data {
    [CmdletBinding()]
    param(
        [string]$InputPath
    )
    
    Write-Debug "开始处理文件: $InputPath"
    
    $data = Get-Content $InputPath
    Write-Debug "读取了 $($data.Count) 行数据"
    
    $processed = $data | ForEach-Object {
        Write-Debug "处理行: $_"
        $_.Trim().ToUpper()
    }
    
    Write-Debug "处理完成，返回结果"
    return $processed
}

# 使用方式1: 使用-Debug参数
Process-Data -InputPath "data.txt" -Debug

# 使用方式2: 修改$DebugPreference
$DebugPreference = "Continue"
Process-Data -InputPath "data.txt"
$DebugPreference = "SilentlyContinue"  # 恢复

# ===== 条件调试输出 =====
function Complex-Function {
    param([int]$Value)
    
    Write-Debug "$(Get-Date -Format 'HH:mm:ss.fff') - 输入值: $Value"
    
    if ($Value -gt 100) {
        Write-Debug "值大于100，使用特殊处理"
        $result = [math]::Sqrt($Value)
    }
    else {
        Write-Debug "值小于等于100，使用标准处理"
        $result = $Value * 2
    }
    
    Write-Debug "计算结果: $result"
    return $result
}
```

### 5.2 Set-PSBreakpoint 断点调试

PowerShell提供强大的断点功能：

```powershell
# ===== 设置行断点 =====
Set-PSBreakpoint -Script "MyScript.ps1" -Line 10

# ===== 设置命令断点 =====
# 在调用特定命令时中断
Set-PSBreakpoint -Command "Get-Process" -Script "MyScript.ps1"

# ===== 设置变量断点 =====
# 在变量被读取、写入或读取/写入时中断
Set-PSBreakpoint -Variable "counter" -Mode Write

# ===== 设置条件断点 =====
Set-PSBreakpoint -Script "MyScript.ps1" -Line 20 -Action {
    if ($value -gt 100) {
        break  # 只有当value > 100时才中断
    }
}

# ===== 调试会话示例 =====
# 1. 设置断点
Set-PSBreakpoint -Script "test.ps1" -Line 5

# 2. 运行脚本（会在断点处停止）
.\test.ps1

# 3. 调试命令
# l, list       - 列出当前行周围的代码
# s, stepInto   - 单步进入（进入函数）
# v, stepOver   - 单步跳过（不进入函数）
# o, stepOut    - 单步退出（跳出函数）
# c, continue   - 继续执行
# q, quit       - 退出调试
# ?, h          - 帮助
# 显示变量      - 直接输入变量名

# ===== 完整调试示例 =====
function Calculate-Values {
    param([int[]]$Numbers)
    
    $results = @()
    $sum = 0
    
    foreach ($num in $Numbers) {
        $square = $num * $num
        $sum += $square
        $results += $square
    }
    
    return @{ Sum = $sum; Values = $results }
}

# 设置断点
Set-PSBreakpoint -Command "Calculate-Values"
Set-PSBreakpoint -Variable "sum" -Mode Write

# 运行
Calculate-Values -Numbers @(1, 2, 3, 4, 5)

# ===== 移除断点 =====
Get-PSBreakpoint | Remove-PSBreakpoint
Remove-PSBreakpoint -Id 1
```

### 5.3 Trace-Command 跟踪命令

`Trace-Command` 用于跟踪和分析PowerShell内部操作：

```powershell
# ===== 基本跟踪 =====
Trace-Command -Name ParameterBinding -Expression {
    Get-Process -Name "powershell"
} -PSHost

# ===== 跟踪类型 =====
# - ParameterBinding    : 参数绑定过程
# - TypeConversion      : 类型转换
# - Cmdlet              : Cmdlet生命周期
# - Pipeline            : 管道执行
# - Metadata            : 元数据处理
# - Host                : 主机交互

# ===== 跟踪到文件 =====
Trace-Command -Name ParameterBinding, Pipeline -Expression {
    Get-Process | Where-Object { $_.WorkingSet -gt 100MB }
} -FilePath "trace.log"

# ===== 分析参数绑定问题 =====
function Test-Params {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [string]$Input,
        
        [int]$Multiplier = 2
    )
    
    process {
        return $Input.Length * $Multiplier
    }
}

# 跟踪管道参数绑定
Trace-Command -Name ParameterBinding -Expression {
    "hello", "world" | Test-Params -Multiplier 3
} -PSHost

# ===== 性能分析跟踪 =====
Trace-Command -Name Cmdlet -Expression {
    $start = Get-Date
    Get-ChildItem C:\Windows -Recurse | Out-Null
    $end = Get-Date
    Write-Host "耗时: $($end - $start)"
} -FilePath "performance_trace.log"
```

### 5.4 综合调试示例

```powershell
# ===== 完整调试脚本示例 =====
[CmdletBinding()]
param(
    [string]$InputFile = "data.csv",
    [string]$OutputFile = "result.csv"
)

# 启用详细输出
$VerbosePreference = "Continue"
$DebugPreference = "Continue"

Write-Verbose "=== 开始处理 ==="

# 设置断点（仅开发时）
# Set-PSBreakpoint -Variable InputFile -Mode Read

try {
    Write-Debug "验证输入文件存在性"
    if (-not (Test-Path $InputFile)) {
        throw "输入文件不存在: $InputFile"
    }
    
    Write-Debug "读取CSV数据"
    $data = Import-Csv $InputFile
    Write-Verbose "读取了 $($data.Count) 条记录"
    
    Write-Debug "开始处理数据"
    $processedData = $data | ForEach-Object {
        Write-Debug "处理记录: $($_.Name)"
        
        try {
            [PSCustomObject]@{
                Name = $_.Name
                Value = [int]$_.Value * 2
                Status = "Processed"
            }
        }
        catch {
            Write-Warning "处理记录失败: $($_.Name) - $_"
            [PSCustomObject]@{
                Name = $_.Name
                Value = $_.Value
                Status = "Failed"
            }
        }
    }
    
    Write-Debug "导出结果"
    $processedData | Export-Csv $OutputFile -NoTypeInformation
    Write-Verbose "处理完成，结果保存到: $OutputFile"
}
catch {
    Write-Error "处理过程中发生错误: $_"
    Write-Debug "堆栈跟踪: $($_.ScriptStackTrace)"
    exit 1
}
```

---

## 6. 日志记录最佳实践

### 6.1 使用Start-Transcript

```powershell
# ===== 基本用法 =====
# 开始记录会话
Start-Transcript -Path "C:\Logs\script_session.log" -IncludeInvocationHeader

# 你的脚本代码...
Write-Host "执行操作..."
Get-Process | Select-Object -First 5

# 停止记录
Stop-Transcript

# ===== 高级用法 =====
function Start-Logging {
    param(
        [string]$LogDirectory = ".\Logs",
        [string]$ScriptName = $MyInvocation.MyCommand.Name
    )
    
    # 创建日志目录
    if (-not (Test-Path $LogDirectory)) {
        New-Item -ItemType Directory -Path $LogDirectory -Force
    }
    
    # 生成日志文件名
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logFile = Join-Path $LogDirectory "$ScriptName`_$timestamp.log"
    
    # 开始记录
    Start-Transcript -Path $logFile -IncludeInvocationHeader
    Write-Host "日志开始: $(Get-Date)"
    Write-Host "脚本: $ScriptName"
    Write-Host "用户: $env:USERNAME"
    Write-Host "计算机: $env:COMPUTERNAME"
    Write-Host "================================"
    
    return $logFile
}

function Stop-Logging {
    Write-Host "================================"
    Write-Host "日志结束: $(Get-Date)"
    Stop-Transcript
}

# 使用
$logPath = Start-Logging
# ... 你的代码 ...
Stop-Logging
```

### 6.2 自定义日志函数

```powershell
# ===== 多级别日志系统 =====
$script:LogLevel = "INFO"
$script:LogPath = ".\application.log"

enum LogLevel {
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4
}

function Write-Log {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        
        [LogLevel]$Level = [LogLevel]::INFO,
        
        [string]$Source = $MyInvocation.MyCommand.Name
    )
    
    # 检查日志级别
    $currentLevel = [LogLevel]::Parse([LogLevel], $script:LogLevel)
    if ($Level.value__ -lt $currentLevel.value__) {
        return
    }
    
    # 构建日志条目
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $levelName = $Level.ToString().PadRight(5)
    $logEntry = "[$timestamp] [$levelName] [$Source] $Message"
    
    # 输出到控制台（带颜色）
    switch ($Level) {
        ([LogLevel]::DEBUG) { Write-Host $logEntry -ForegroundColor Gray }
        ([LogLevel]::INFO)  { Write-Host $logEntry -ForegroundColor White }
        ([LogLevel]::WARN)  { Write-Host $logEntry -ForegroundColor Yellow }
        ([LogLevel]::ERROR) { Write-Host $logEntry -ForegroundColor Red }
        ([LogLevel]::FATAL) { Write-Host $logEntry -ForegroundColor Magenta }
    }
    
    # 写入文件
    $logEntry | Out-File -FilePath $script:LogPath -Append -Encoding UTF8
}

# 便捷函数
function Write-DebugLog { param([string]$Message, [string]$Source = $MyInvocation.MyCommand.Name) Write-Log -Message $Message -Level ([LogLevel]::DEBUG) -Source $Source }
function Write-InfoLog  { param([string]$Message, [string]$Source = $MyInvocation.MyCommand.Name) Write-Log -Message $Message -Level ([LogLevel]::INFO) -Source $Source }
function Write-WarnLog  { param([string]$Message, [string]$Source = $MyInvocation.MyCommand.Name) Write-Log -Message $Message -Level ([LogLevel]::WARN) -Source $Source }
function Write-ErrorLog { param([string]$Message, [string]$Source = $MyInvocation.MyCommand.Name) Write-Log -Message $Message -Level ([LogLevel]::ERROR) -Source $Source }
function Write-FatalLog { param([string]$Message, [string]$Source = $MyInvocation.MyCommand.Name) Write-Log -Message $Message -Level ([LogLevel]::FATAL) -Source $Source }

# 使用示例
$script:LogLevel = "DEBUG"
$script:LogPath = ".\app.log"

Write-InfoLog "应用程序启动"
Write-DebugLog "加载配置文件..."
Write-WarnLog "配置项缺失，使用默认值"
Write-ErrorLog "数据库连接失败"
```

### 6.3 结构化日志记录

```powershell
# ===== JSON格式结构化日志 =====
function Write-StructuredLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        
        [ValidateSet("DEBUG", "INFO", "WARN", "ERROR", "FATAL")]
        [string]$Level = "INFO",
        
        [hashtable]$ExtraData = @{},
        
        [string]$LogFile = ".\structured.log"
    )
    
    $logEntry = @{
        timestamp = (Get-Date -Format "o")  # ISO 8601格式
        level = $Level
        message = $Message
        pid = $PID
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        script = $MyInvocation.ScriptName
        line = $MyInvocation.ScriptLineNumber
    } + $ExtraData
    
    $json = $logEntry | ConvertTo-Json -Compress
    $json | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

# 使用
Write-StructuredLog -Message "处理订单" -Level "INFO" -ExtraData @{
    orderId = "12345"
    customerId = "C001"
    amount = 99.99
}

# 分析日志
Get-Content ".\structured.log" | ForEach-Object {
    $_ | ConvertFrom-Json
} | Where-Object { $_.level -eq "ERROR" }
```

### 6.4 日志轮转

```powershell
# ===== 日志轮转函数 =====
function Initialize-LogRotation {
    param(
        [string]$LogDirectory = ".\Logs",
        [int]$MaxLogFiles = 10,
        [int]$MaxLogSizeMB = 10
    )
    
    # 创建日志目录
    if (-not (Test-Path $LogDirectory)) {
        New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    }
    
    # 获取所有日志文件
    $logFiles = Get-ChildItem -Path $LogDirectory -Filter "*.log" | Sort-Object LastWriteTime -Descending
    
    # 删除旧日志
    if ($logFiles.Count -gt $MaxLogFiles) {
        $logFiles | Select-Object -Skip $MaxLogFiles | Remove-Item -Force
    }
    
    # 检查文件大小并轮转
    $currentLog = Join-Path $LogDirectory "current.log"
    if (Test-Path $currentLog) {
        $size = (Get-Item $currentLog).Length / 1MB
        if ($size -gt $MaxLogSizeMB) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            Rename-Item $currentLog "log_$timestamp.log"
        }
    }
    
    return $currentLog
}

# 使用
$logFile = Initialize-LogRotation
"日志消息" | Out-File $logFile -Append
```

### 6.5 完整日志记录类

```powershell
# ===== 日志记录类 (PowerShell 5.0+) =====
class Logger {
    [string]$LogPath
    [string]$LogLevel
    [bool]$ConsoleOutput
    
    Logger([string]$path, [string]$level = "INFO", [bool]$console = $true) {
        $this.LogPath = $path
        $this.LogLevel = $level
        $this.ConsoleOutput = $console
        
        $dir = Split-Path $path -Parent
        if ($dir -and -not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    [bool]ShouldLog([string]$level) {
        $levels = @{ DEBUG = 0; INFO = 1; WARN = 2; ERROR = 3; FATAL = 4 }
        return $levels[$level] -ge $levels[$this.LogLevel]
    }
    
    [void]Write([string]$message, [string]$level, [string]$source) {
        if (-not $this.ShouldLog($level)) { return }
        
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $entry = "[$timestamp] [$level] [$source] $message"
        
        # 控制台输出
        if ($this.ConsoleOutput) {
            $colors = @{ DEBUG = "Gray"; INFO = "White"; WARN = "Yellow"; ERROR = "Red"; FATAL = "Magenta" }
            Write-Host $entry -ForegroundColor $colors[$level]
        }
        
        # 文件输出
        $entry | Out-File -FilePath $this.LogPath -Append -Encoding UTF8
    }
    
    [void]Debug([string]$message) { $this.Write($message, "DEBUG", $MyInvocation.MyCommand.Name) }
    [void]Info([string]$message)  { $this.Write($message, "INFO", $MyInvocation.MyCommand.Name) }
    [void]Warn([string]$message)  { $this.Write($message, "WARN", $MyInvocation.MyCommand.Name) }
    [void]Error([string]$message) { $this.Write($message, "ERROR", $MyInvocation.MyCommand.Name) }
    [void]Fatal([string]$message) { $this.Write($message, "FATAL", $MyInvocation.MyCommand.Name) }
}

# 使用
$logger = [Logger]::new(".\app.log", "DEBUG", $true)
$logger.Info("应用程序启动")
$logger.Debug("详细调试信息")
$logger.Error("发生错误!")
```

---

## 7. 关键知识点总结

### 7.1 核心概念速查

| 概念 | 关键点 |
|------|--------|
| **终止错误** | 停止执行，可被try-catch捕获 |
| **非终止错误** | 继续执行，需用-ErrorAction Stop转换后才能被捕获 |
| **$Error** | 自动变量，存储所有错误记录，[0]为最新 |
| **$ErrorActionPreference** | 全局错误处理偏好设置 |
| **-ErrorAction** | 命令级错误处理参数，优先级高于偏好变量 |

### 7.2 最佳实践清单

- ✅ 使用try-catch处理可能失败的代码块
- ✅ 在finally块中释放资源
- ✅ 根据错误类型使用多个catch块
- ✅ 使用-ErrorAction Stop将非终止错误转为终止错误
- ✅ 使用$Error[0]获取最后错误的详细信息
- ✅ 使用Write-Debug进行调试输出
- ✅ 使用Start-Transcript记录完整会话
- ✅ 编写自定义日志函数进行结构化日志记录
- ✅ 在脚本中保存和恢复$ErrorActionPreference
- ✅ 使用具体的异常类型而非通用的catch

### 7.3 常见陷阱

- ❌ 忘记-ErrorAction Stop，导致非终止错误无法被catch
- ❌ 在finally块中抛出新的异常（会覆盖原始异常）
- ❌ 过度使用SilentlyContinue导致错误被隐藏
- ❌ 没有清理$Error数组导致内存增长
- ❌ 混淆$Error[0]（最新）和$Error[-1]（最旧）

### 7.4 快速参考代码片段

```powershell
# 标准错误处理模板
try {
    # 操作
}
catch [特定异常] {
    # 特定处理
}
catch {
    Write-Error "意外错误: $_"
    throw  # 重新抛出
}
finally {
    # 清理
}

# 非终止错误处理
Get-Something -ErrorAction SilentlyContinue | Where-Object { $_ }

# 收集所有错误
Get-ChildItem -Path $paths -ErrorVariable errors -ErrorAction SilentlyContinue

# 启用调试
$DebugPreference = "Continue"
$VerbosePreference = "Continue"
```

---

*文档结束*
