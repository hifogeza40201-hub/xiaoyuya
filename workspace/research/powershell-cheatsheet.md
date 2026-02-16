# PowerShell 速查表与代码片段库

> 全面的 PowerShell 参考手册，包含速查表、代码片段和最佳实践

---

## 📋 目录

1. [速查表 (Cheatsheet)](#速查表-cheatsheet)
2. [代码片段库 (Snippets)](#代码片段库-snippets)
3. [最佳实践清单](#最佳实践清单)

---

## 速查表 (Cheatsheet)

### 1. 参数属性速查表

| 属性 | 语法 | 说明 | 示例 |
|------|------|------|------|
| **Mandatory** | `[Parameter(Mandatory=$true)]` | 必需参数 | `[Parameter(Mandatory=$true)] [string]$Name` |
| **Position** | `[Parameter(Position=0)]` | 位置参数 | `[Parameter(Position=0)] [string]$FirstName` |
| **ValueFromPipeline** | `[Parameter(ValueFromPipeline=$true)]` | 接受管道输入 | `[Parameter(ValueFromPipeline=$true)] [string[]]$Items` |
| **ValueFromPipelineByPropertyName** | `[Parameter(ValueFromPipelineByPropertyName=$true)]` | 按属性名接受管道 | `[Parameter(ValueFromPipelineByPropertyName=$true)] [string]$ProcessName` |
| **ValueFromRemainingArguments** | `[Parameter(ValueFromRemainingArguments=$true)]` | 剩余参数 | `[Parameter(ValueFromRemainingArguments=$true)] [string[]]$Extras` |
| **HelpMessage** | `[Parameter(HelpMessage="说明")]` | 帮助信息 | `[Parameter(HelpMessage="输入用户名")] [string]$UserName` |
| **ParameterSetName** | `[Parameter(ParameterSetName="Set1")]` | 参数集 | `[Parameter(ParameterSetName="ByName")] [string]$Name` |
| **DontShow** | `[Parameter(DontShow)]` | 不显示在 IntelliSense | `[Parameter(DontShow)] [switch]$Internal` |
| **Alias** | `[Alias("别名")]` | 参数别名 | `[Alias("CN","Machine")] [string]$ComputerName` |

**常用组合示例：**

```powershell
param(
    [Parameter(Mandatory=$true, Position=0, HelpMessage="输入服务器名称")]
    [Alias("Server", "Machine")]
    [string]$ComputerName,
    
    [Parameter(ValueFromPipeline=$true)]
    [string[]]$InputObject,
    
    [Parameter(ParameterSetName="Detailed")]
    [switch]$Detailed
)
```

---

### 2. 验证属性速查表

| 属性 | 语法 | 说明 | 示例 |
|------|------|------|------|
| **ValidateNotNull** | `[ValidateNotNull()]` | 值不能为 null | `[ValidateNotNull()] [string]$Name` |
| **ValidateNotNullOrEmpty** | `[ValidateNotNullOrEmpty()]` | 值不能为 null 或空 | `[ValidateNotNullOrEmpty()] [string]$Path` |
| **ValidateCount** | `[ValidateCount(1,10)]` | 数组元素数量范围 | `[ValidateCount(1,5)] [string[]]$Names` |
| **ValidateLength** | `[ValidateLength(1,100)]` | 字符串长度范围 | `[ValidateLength(3,20)] [string]$UserName` |
| **ValidateRange** | `[ValidateRange(1,100)]` | 数值范围 | `[ValidateRange(1,65535)] [int]$Port` |
| **ValidatePattern** | `[ValidatePattern("^\w+$")]` | 正则表达式匹配 | `[ValidatePattern("^\d{4}-\d{2}-\d{2}$")] [string]$Date` |
| **ValidateSet** | `[ValidateSet("A","B","C")]` | 限定可选值 | `[ValidateSet("Start","Stop","Restart")] [string]$Action` |
| **ValidateScript** | `[ValidateScript({...})]` | 自定义验证脚本 | `[ValidateScript({Test-Path $_})] [string]$FilePath` |
| **AllowNull** | `[AllowNull()]` | 允许 null 值 | `[AllowNull()] [string]$Optional` |
| **AllowEmptyString** | `[AllowEmptyString()]` | 允许空字符串 | `[AllowEmptyString()] [string]$Description` |
| **AllowEmptyCollection** | `[AllowEmptyCollection()]` | 允许空集合 | `[AllowEmptyCollection()] [string[]]$Tags` |

**ValidateScript 实用示例：**

```powershell
# 验证文件存在
[ValidateScript({
    if (-not (Test-Path $_)) { throw "文件不存在: $_" }
    $true
})] [string]$FilePath

# 验证是有效的 IP 地址
[ValidateScript({
    if ($_ -notmatch '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
        throw "无效的 IP 地址格式"
    }
    $true
})] [string]$IPAddress

# 验证邮箱格式
[ValidateScript({
    if ($_ -notmatch '^[\w\.-]+@[\w\.-]+\.\w+$') {
        throw "无效的邮箱格式"
    }
    $true
})] [string]$Email
```

---

### 3. 错误处理速查表

| 关键字/概念 | 语法 | 说明 |
|------------|------|------|
| **try-catch** | `try { } catch { }` | 捕获异常 |
| **try-catch-finally** | `try { } catch { } finally { }` | 捕获异常+清理 |
| **特定异常** | `catch [System.IO.IOException]` | 捕获特定类型异常 |
| **多个 catch** | `catch [类型1] { } catch [类型2] { }` | 按类型分别处理 |
| **throw** | `throw "错误信息"` | 抛出异常 |
| **throw 对象** | `throw [Exception]::new("msg")` | 抛出异常对象 |
| **ErrorAction** | `-ErrorAction Stop` | 将错误转为终止错误 |
| **$ErrorActionPreference** | `$ErrorActionPreference = 'Stop'` | 全局错误动作 |
| **$?** | `if (-not $?) { }` | 检查上条命令是否成功 |
| **$LASTEXITCODE** | `if ($LASTEXITCODE -ne 0) { }` | 检查外部程序退出码 |
| **$Error** | `$Error[0]` | 错误集合 |
| **-ErrorVariable** | `-ErrorVariable MyErr` | 捕获错误到变量 |
| **trap** | `trap { continue }` | 全局异常处理器 |
| **Write-Error** | `Write-Error "消息"` | 输出非终止错误 |

**ErrorAction 选项：**

| 值 | 说明 |
|----|------|
| `Continue` | 显示错误，继续执行（默认） |
| `SilentlyContinue` | 静默继续，不显示错误 |
| `Stop` | 显示错误，停止执行 |
| `Inquire` | 显示错误，询问用户 |
| `Ignore` | 完全忽略错误（PowerShell 3.0+） |
| `Suspend` | 暂停供调试（仅工作流） |

---

### 4. 调试命令速查表

| 命令 | 用途 | 示例 |
|------|------|------|
| **Write-Debug** | 输出调试信息 | `Write-Debug "变量值: $var"` |
| **Write-Verbose** | 输出详细信息 | `Write-Verbose "正在处理..."` |
| **Write-Information** | 输出信息消息 | `Write-Information "提示信息"` |
| **-[CmdletBinding()]** | 启用高级功能 | `[CmdletBinding(SupportsShouldProcess=$true)]` |
| **Set-PSDebug** | 调试模式开关 | `Set-PSDebug -Trace 2` |
| **Set-StrictMode** | 严格模式 | `Set-StrictMode -Version Latest` |
| **Get-PSCallStack** | 查看调用堆栈 | `Get-PSCallStack` |
| **Start-Transcript** | 开始记录会话 | `Start-Transcript -Path "log.txt"` |
| **Stop-Transcript** | 停止记录会话 | `Stop-Transcript` |
| **$PSCmdlet** | 访问 cmdlet 上下文 | `$PSCmdlet.WriteDebug("...")` |
| **breakpoint** | 设置断点 | `Set-PSBreakpoint -Script script.ps1 -Line 10` |

**CmdletBinding 参数：**

```powershell
[CmdletBinding(
    DefaultParameterSetName = "Default",
    SupportsShouldProcess = $true,      # 支持 -WhatIf 和 -Confirm
    SupportsPaging = $true,              # 支持分页
    PositionalBinding = $false,          # 禁用位置绑定
    ConfirmImpact = "Medium"             # 确认级别: Low/Medium/High
)]
```

**Set-PSDebug 级别：**

| 级别 | 说明 |
|------|------|
| `-Off` | 关闭调试 |
| `-Trace 0` | 仅显示调试消息 |
| `-Trace 1` | 显示执行行 |
| `-Trace 2` | 显示执行行+变量赋值 |
| `-Step` | 单步执行 |
| `-Strict` | 变量必须先声明 |

---

## 代码片段库 (Snippets)

### 1. 常用函数模板（10个）

#### 模板 1: 基础高级函数
```powershell
function Get-Something {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string[]]$InputObject
    )
    
    begin {
        Write-Verbose "开始处理"
        $results = @()
    }
    
    process {
        foreach ($item in $InputObject) {
            Write-Verbose "处理项目: $item"
            # 处理逻辑
            $results += $item
        }
    }
    
    end {
        Write-Verbose "处理完成"
        return $results
    }
}
```

#### 模板 2: 带 ShouldProcess 的函数（支持 -WhatIf）
```powershell
function Remove-Something {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string[]]$Path
    )
    
    process {
        foreach ($p in $Path) {
            if ($PSCmdlet.ShouldProcess($p, '删除')) {
                Remove-Item -Path $p -Force
                Write-Verbose "已删除: $p"
            }
        }
    }
}
```

#### 模板 3: 带参数集的函数
```powershell
function Get-User {
    [CmdletBinding(DefaultParameterSetName='ByName')]
    param(
        [Parameter(ParameterSetName='ByName', Position=0)]
        [string]$Name,
        
        [Parameter(ParameterSetName='ByID', Mandatory=$true)]
        [int]$ID,
        
        [Parameter(ParameterSetName='All')]
        [switch]$All
    )
    
    switch ($PSCmdlet.ParameterSetName) {
        'ByName' { Write-Output "按名称查找: $Name" }
        'ByID'   { Write-Output "按ID查找: $ID" }
        'All'    { Write-Output "查找所有用户" }
    }
}
```

#### 模板 4: 带动态参数的函数
```powershell
function Get-Data {
    [CmdletBinding()]
    param([string]$Source)
    
    dynamicparam {
        $paramDictionary = New-Object System.Management.Automation.RuntimeDefinedParameterDictionary
        
        if ($Source -eq 'Database') {
            $attribute = New-Object System.Management.Automation.ParameterAttribute
            $attribute.Mandatory = $true
            
            $attributeCollection = New-Object System.Collections.ObjectModel.Collection[System.Attribute]
            $attributeCollection.Add($attribute)
            
            $param = New-Object System.Management.Automation.RuntimeDefinedParameter('TableName', [string], $attributeCollection)
            $paramDictionary.Add('TableName', $param)
        }
        
        return $paramDictionary
    }
    
    process {
        $tableName = $PSBoundParameters['TableName']
        Write-Output "源: $Source, 表: $tableName"
    }
}
```

#### 模板 5: 带别名和输出的函数
```powershell
function Get-DiskInfo {
    [CmdletBinding()]
    [Alias('gdi', 'diskinfo')]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
        [Alias('CN', 'MachineName')]
        [string[]]$ComputerName = $env:COMPUTERNAME
    )
    
    process {
        foreach ($computer in $ComputerName) {
            try {
                $disks = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $computer -ErrorAction Stop |
                    Select-Object @{N='ComputerName';E={$computer}}, DeviceID, 
                                  @{N='SizeGB';E={[math]::Round($_.Size/1GB, 2)}},
                                  @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB, 2)}},
                                  @{N='PercentFree';E={[math]::Round(($_.FreeSpace/$_.Size)*100, 2)}}
                $disks
            }
            catch {
                Write-Error "无法连接到 $computer : $_"
            }
        }
    }
}
```

#### 模板 6: 带验证和转换的函数
```powershell
function Set-Config {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [string]$Name,
        
        [Parameter(Mandatory=$true)]
        [AllowNull()]
        [AllowEmptyString()]
        $Value,
        
        [ValidateSet('String', 'Int', 'Bool', 'DateTime')]
        [string]$Type = 'String'
    )
    
    $convertedValue = switch ($Type) {
        'Int'      { [int]$Value }
        'Bool'     { [bool]$Value }
        'DateTime' { [datetime]$Value }
        default    { [string]$Value }
    }
    
    [PSCustomObject]@{
        Name  = $Name
        Value = $convertedValue
        Type  = $Type
    }
}
```

#### 模板 7: 带进度显示的函数
```powershell
function Process-Items {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [array]$Items,
        
        [string]$Activity = "处理项目"
    )
    
    begin {
        $allItems = @()
    }
    
    process {
        $allItems += $Items
    }
    
    end {
        $total = $allItems.Count
        for ($i = 0; $i -lt $total; $i++) {
            $percent = [math]::Round(($i / $total) * 100)
            Write-Progress -Activity $Activity -Status "处理中 $i / $total" -PercentComplete $percent
            
            # 处理逻辑
            Start-Sleep -Milliseconds 100
        }
        Write-Progress -Activity $Activity -Completed
    }
}
```

#### 模板 8: 异步/并行处理函数
```powershell
function Invoke-Parallel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [array]$InputObject,
        
        [Parameter(Mandatory=$true)]
        [scriptblock]$ScriptBlock,
        
        [int]$ThrottleLimit = 5
    )
    
    begin {
        $items = [System.Collections.Generic.List[object]]::new()
    }
    
    process {
        $items.AddRange($InputObject)
    }
    
    end {
        $items | ForEach-Object -Parallel $ScriptBlock -ThrottleLimit $ThrottleLimit
    }
}
```

#### 模板 9: 代理函数（包装现有命令）
```powershell
function Get-MyProcess {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
        [string[]]$Name,
        
        [switch]$IncludeModules
    )
    
    begin {
        $params = @{}
        if ($Name) { $params['Name'] = $Name }
    }
    
    process {
        $processes = Get-Process @params
        
        if ($IncludeModules) {
            $processes | Select-Object *, @{N='Modules';E={$_.Modules}}
        }
        else {
            $processes
        }
    }
}
```

#### 模板 10: 完整类模块函数
```powershell
function Invoke-DataOperation {
    <#
    .SYNOPSIS
        执行数据操作。
    .DESCRIPTION
        此函数演示完整文档、参数验证和错误处理。
    .PARAMETER Data
        要处理的数据。
    .PARAMETER Operation
        操作类型。
    .EXAMPLE
        Invoke-DataOperation -Data @(1,2,3) -Operation Sum
    #>
    [CmdletBinding(SupportsShouldProcess=$true)]
    [OutputType([int])]
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [ValidateNotNullOrEmpty()]
        [int[]]$Data,
        
        [Parameter(Mandatory=$true, Position=1)]
        [ValidateSet('Sum', 'Average', 'Min', 'Max', 'Count')]
        [string]$Operation
    )
    
    if (-not $PSCmdlet.ShouldProcess("数据操作: $Operation")) {
        return
    }
    
    try {
        switch ($Operation) {
            'Sum'     { ($Data | Measure-Object -Sum).Sum }
            'Average' { ($Data | Measure-Object -Average).Average }
            'Min'     { ($Data | Measure-Object -Minimum).Minimum }
            'Max'     { ($Data | Measure-Object -Maximum).Maximum }
            'Count'   { $Data.Count }
        }
    }
    catch {
        Write-Error -Message "操作失败: $_" -Category InvalidOperation
    }
}
```

---

### 2. 错误处理模式（5种）

#### 模式 1: 基础 try-catch-finally
```powershell
try {
    $result = 1 / 0
}
catch [System.DivideByZeroException] {
    Write-Warning "除以零错误"
}
catch {
    Write-Error "未知错误: $($_.Exception.Message)"
}
finally {
    Write-Verbose "清理资源"
}
```

#### 模式 2: 函数级错误处理
```powershell
function Invoke-SafeOperation {
    [CmdletBinding()]
    param([string]$Path)
    
    try {
        # 将非终止错误转为终止错误
        $ErrorActionPreference = 'Stop'
        
        $content = Get-Content -Path $Path
        # 处理内容...
        return $content
    }
    catch [System.IO.FileNotFoundException] {
        Write-Error "文件未找到: $Path"
        return $null
    }
    catch [System.UnauthorizedAccessException] {
        Write-Error "访问被拒绝: $Path"
        return $null
    }
    catch {
        Write-Error "操作失败: $($_.Exception.GetType().Name) - $($_.Exception.Message)"
        return $null
    }
    finally {
        # 恢复设置
        $ErrorActionPreference = 'Continue'
    }
}
```

#### 模式 3: 批量处理错误收集
```powershell
function Process-ItemsWithErrorHandling {
    [CmdletBinding()]
    param([array]$Items)
    
    $results = @()
    $errors = [System.Collections.Generic.List[object]]::new()
    
    foreach ($item in $Items) {
        try {
            # 尝试处理
            $result = Do-Something -InputObject $item -ErrorAction Stop
            $results += $result
        }
        catch {
            $errors.Add([PSCustomObject]@{
                Item = $item
                Error = $_.Exception.Message
                Timestamp = Get-Date
            })
            Write-Warning "处理失败: $item - $($_.Exception.Message)"
        }
    }
    
    # 返回结果和错误
    [PSCustomObject]@{
        Successful = $results
        FailedCount = $errors.Count
        Errors = $errors
    }
}
```

#### 模式 4: 使用 ErrorVariable 和 TryCatch 结合
```powershell
function Get-DataWithFallback {
    [CmdletBinding()]
    param(
        [string]$PrimarySource,
        [string]$FallbackSource
    )
    
    $errorVar = $null
    $data = Get-Content -Path $PrimarySource -ErrorAction SilentlyContinue -ErrorVariable errorVar
    
    if ($errorVar) {
        Write-Warning "主数据源失败，尝试备用源"
        try {
            $data = Get-Content -Path $FallbackSource -ErrorAction Stop
        }
        catch {
            throw "所有数据源都失败"
        }
    }
    
    return $data
}
```

#### 模式 5: 使用 Trap 的全局错误处理
```powershell
function Invoke-WithGlobalTrap {
    [CmdletBinding()]
    param([scriptblock]$ScriptBlock)
    
    # 设置临时错误处理器
    $oldTrap = $trap
    trap {
        Write-Host "捕获到错误: $_" -ForegroundColor Red
        Write-Host "发生在: $($_.InvocationInfo.ScriptName):$($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Yellow
        # 继续执行或停止
        continue  # 或 break 停止
    }
    
    try {
        & $ScriptBlock
    }
    finally {
        # 恢复原始 trap
        Set-Variable -Name trap -Value $oldTrap -Scope 1
    }
}
```

---

### 3. 日志记录模式（3种）

#### 模式 1: 简单文件日志
```powershell
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',
        
        [string]$LogPath = "$env:TEMP\script.log"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 输出到控制台（带颜色）
    switch ($Level) {
        'ERROR'   { Write-Host $logEntry -ForegroundColor Red }
        'WARNING' { Write-Host $logEntry -ForegroundColor Yellow }
        'DEBUG'   { Write-Host $logEntry -ForegroundColor Cyan }
        default   { Write-Host $logEntry }
    }
    
    # 写入文件
    Add-Content -Path $LogPath -Value $logEntry
}

# 使用示例
Write-Log -Message "开始处理" -Level INFO
Write-Log -Message "发生警告" -Level WARNING
```

#### 模式 2: 结构化 JSON 日志
```powershell
function Write-StructuredLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',
        
        [hashtable]$Metadata = @{},
        
        [string]$LogPath = "$env:TEMP\script.jsonl"
    )
    
    $logEntry = [PSCustomObject]@{
        timestamp = (Get-Date -Format "o")  # ISO 8601
        level     = $Level
        message   = $Message
        hostname  = $env:COMPUTERNAME
        pid       = $PID
        metadata  = $Metadata
    } | ConvertTo-Json -Compress
    
    Add-Content -Path $LogPath -Value $logEntry
}

# 使用示例
Write-StructuredLog -Message "用户登录" -Level INFO -Metadata @{ User = 'admin'; IP = '192.168.1.1' }
```

#### 模式 3: 事件日志记录
```powershell
function Write-EventLogEntry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet('Information', 'Warning', 'Error')]
        [string]$EntryType = 'Information',
        
        [int]$EventId = 1000,
        
        [string]$Source = 'MyPowerShellApp',
        
        [string]$LogName = 'Application'
    )
    
    # 确保源存在
    if (-not [System.Diagnostics.EventLog]::SourceExists($Source)) {
        try {
            New-EventLog -LogName $LogName -Source $Source
        }
        catch {
            Write-Warning "无法创建事件源（需要管理员权限）"
            return
        }
    }
    
    Write-EventLog -LogName $LogName -Source $Source -EntryType $EntryType -EventId $EventId -Message $Message
}

# 使用示例
Write-EventLogEntry -Message "应用程序启动" -EntryType Information -EventId 1001
Write-EventLogEntry -Message "配置错误" -EntryType Error -EventId 2001
```

---

### 4. 管道处理模式（3种）

#### 模式 1: 完整管道支持（begin/process/end）
```powershell
function Invoke-PipelineProcessing {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [PSObject]$InputObject,
        
        [Parameter()]
        [scriptblock]$Transform = { $_ }
    )
    
    begin {
        Write-Verbose "初始化..."
        $results = [System.Collections.Generic.List[object]]::new()
        $count = 0
    }
    
    process {
        foreach ($item in $InputObject) {
            $count++
            Write-Verbose "处理项目 #$count"
            
            try {
                $transformed = & $Transform $item
                $results.Add($transformed)
            }
            catch {
                Write-Warning "转换失败: $_"
            }
        }
    }
    
    end {
        Write-Verbose "完成处理，共 $count 项"
        return $results
    }
}

# 使用示例
1..10 | Invoke-PipelineProcessing -Transform { $_ * 2 } -Verbose
```

#### 模式 2: 按属性名管道绑定
```powershell
function Get-ServiceStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
        [Alias('Name', 'ServiceName')]
        [string[]]$DisplayName
    )
    
    process {
        foreach ($name in $DisplayName) {
            try {
                $service = Get-Service -DisplayName $name -ErrorAction Stop
                [PSCustomObject]@{
                    Name   = $service.Name
                    DisplayName = $service.DisplayName
                    Status = $service.Status
                    StartType = $service.StartType
                }
            }
            catch {
                [PSCustomObject]@{
                    Name   = $name
                    DisplayName = $name
                    Status = 'NotFound'
                    StartType = 'Unknown'
                }
            }
        }
    }
}

# 使用示例（通过属性名管道）
Import-Csv services.csv | Get-ServiceStatus
# CSV 包含 Name 列，自动绑定到 DisplayName 参数
```

#### 模式 3: 流式管道处理（内存高效）
```powershell
function Process-LargeData {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [object]$InputObject,
        
        [int]$BatchSize = 1000,
        
        [scriptblock]$BatchAction = { param($batch) $batch }
    )
    
    begin {
        $batch = [System.Collections.Generic.List[object]]::new($BatchSize)
    }
    
    process {
        $batch.Add($InputObject)
        
        if ($batch.Count -ge $BatchSize) {
            & $BatchAction $batch
            $batch.Clear()
        }
    }
    
    end {
        # 处理剩余项
        if ($batch.Count -gt 0) {
            & $BatchAction $batch
        }
    }
}

# 使用示例 - 批量处理大量数据
Get-ChildItem -Recurse -File |
    Process-LargeData -BatchSize 100 -BatchAction {
        param($files)
        # 批量处理 100 个文件
        $files | Select-Object Name, Length | Export-Csv -Append batch.csv
    }
```

---

## 最佳实践清单

### 1. 函数设计检查清单

- [ ] **函数命名**
  - [ ] 使用 `Verb-Noun` 格式
  - [ ] 动词来自 approved PowerShell 动词列表
  - [ ] 名词使用单数形式（除非是集合概念）
  - [ ] 使用 PascalCase

- [ ] **参数设计**
  - [ ] 使用 `[CmdletBinding()]` 启用高级功能
  - [ ] 为参数添加 `[Parameter()]` 属性
  - [ ] 标记必需的参数为 `Mandatory=$true`
  - [ ] 支持管道输入（`ValueFromPipeline`）
  - [ ] 支持属性名管道（`ValueFromPipelineByPropertyName`）
  - [ ] 使用参数集（ParameterSetName）处理不同使用场景
  - [ ] 为常用参数添加别名（Alias）

- [ ] **参数验证**
  - [ ] 使用 `[ValidateNotNullOrEmpty()]` 防止空值
  - [ ] 使用 `[ValidateSet()]` 限制可选值
  - [ ] 使用 `[ValidateScript()]` 进行复杂验证
  - [ ] 使用 `[ValidateRange()]` 限制数值范围
  - [ ] 使用 `[ValidateLength()]` 限制字符串长度

- [ ] **输出规范**
  - [ ] 使用 `[OutputType()]` 声明输出类型
  - [ ] 输出对象化数据（使用 `[PSCustomObject]`）
  - [ ] 避免输出格式化的字符串（让管道决定格式）
  - [ ] 确保属性名清晰且有描述性

- [ ] **文档**
  - [ ] 添加 `.SYNOPSIS` 简短描述
  - [ ] 添加 `.DESCRIPTION` 详细描述
  - [ ] 为每个参数添加 `.PARAMETER`
  - [ ] 添加 `.EXAMPLE` 使用示例
  - [ ] 添加 `.INPUTS` 和 `.OUTPUTS`（如适用）
  - [ ] 添加 `.NOTES` 额外信息

- [ ] **安全性**
  - [ ] 对危险操作使用 `SupportsShouldProcess`
  - [ ] 设置适当的 `ConfirmImpact`
  - [ ] 验证用户输入
  - [ ] 避免硬编码敏感信息

---

### 2. 错误处理检查清单

- [ ] **异常捕获**
  - [ ] 使用 `try-catch` 包裹可能出错的代码
  - [ ] 捕获特定异常类型，而非通用的 `catch`
  - [ ] 为不同的异常类型提供不同的处理逻辑
  - [ ] 使用 `finally` 进行资源清理

- [ ] **错误报告**
  - [ ] 使用 `Write-Error` 报告终止错误
  - [ ] 使用 `Write-Warning` 报告警告信息
  - [ ] 提供清晰、可操作的错误信息
  - [ ] 包含导致错误的上下文信息

- [ ] **错误传播**
  - [ ] 适当使用 `-ErrorAction Stop` 将错误转为终止错误
  - [ ] 使用 `throw` 重新抛出需要上层处理的异常
  - [ ] 考虑使用 `$PSCmdlet.ThrowTerminatingError()`

- [ ] **恢复策略**
  - [ ] 提供默认值或回退行为
  - [ ] 批量处理时记录失败的项，继续处理其他项
  - [ ] 实现重试机制（对于临时性错误）

- [ ] **日志记录**
  - [ ] 记录错误发生的时间
  - [ ] 记录错误的完整信息
  - [ ] 记录导致错误的输入数据（适当脱敏）

- [ ] **用户体验**
  - [ ] 在可能的情况下提供 `-WhatIf` 支持
  - [ ] 在危险操作前要求确认
  - [ ] 提供进度反馈（对于长时间运行的操作）

---

### 3. 性能优化检查清单

- [ ] **集合操作**
  - [ ] 使用 `[System.Collections.Generic.List[object]]` 替代 `@()`
  - [ ] 预分配集合容量（如果知道大致大小）
  - [ ] 使用 `ForEach-Object` 的并行模式（PowerShell 7+）
  - [ ] 避免在循环中使用 `+=` 操作符

- [ ] **管道优化**
  - [ ] 使用 `begin/process/end` 块正确处理管道
  - [ ] 流式处理大数据集，避免全部加载到内存
  - [ ] 使用 `Select-Object` 的 `-First` 参数提前终止

- [ ] **字符串操作**
  - [ ] 使用 `$()` 子表达式替代 `+` 连接
  - [ ] 使用 `-join` 操作符替代循环连接
  - [ ] 对于大量字符串，使用 `[System.Text.StringBuilder]`
  - [ ] 使用 here-string 处理多行文本

- [ ] **文件 I/O**
  - [ ] 使用流式读取处理大文件
  - [ ] 使用 `[System.IO.StreamReader]` 替代 `Get-Content`
  - [ ] 批量写入文件，减少 I/O 次数
  - [ ] 使用 `[System.IO.File]::ReadAllLines()` 读取小文件

- [ ] **正则表达式**
  - [ ] 预编译复杂正则（使用 `[regex]::new()`）
  - [ ] 使用 `-match` 而非 `Select-String` 进行简单匹配
  - [ ] 避免在循环中重复编译正则

- [ ] **循环优化**
  - [ ] 使用 `foreach` 替代 `ForEach-Object`（性能优先时）
  - [ ] 缓存数组长度到变量
  - [ ] 避免在循环条件中调用函数
  - [ ] 使用 `switch` 替代多个 `if-elseif`

- [ ] **WMI/CIM 查询**
  - [ ] 使用 `-Filter` 参数在服务端过滤
  - [ ] 只查询需要的属性（`-Property`）
  - [ ] 优先使用 CIM 而非 WMI

- [ ] **内存管理**
  - [ ] 及时释放大对象（`$var = $null`）
  - [ ] 使用 `[GC]::Collect()` 仅在必要时
  - [ ] 避免不必要的数据复制

---

## 附录

### PowerShell 版本特性对照

| 特性 | 版本 |
|------|------|
| `[CmdletBinding()]` | 2.0+ |
| `ValidateScript` | 3.0+ |
| `ValidateDrive` | 5.0+ |
| `ForEach-Object -Parallel` | 7.0+ |
| `ternary operator` | 7.0+ |
| `null-coalescing` | 7.0+ |
| `pipeline chain` | 7.0+ |

### 常用类型加速器

| 加速器 | 完整类型名 |
|--------|-----------|
| `[array]` | `[System.Array]` |
| `[bool]` | `[System.Boolean]` |
| `[byte]` | `[System.Byte]` |
| `[char]` | `[System.Char]` |
| `[datetime]` | `[System.DateTime]` |
| `[decimal]` | `[System.Decimal]` |
| `[double]` | `[System.Double]` |
| `[float]` | `[System.Single]` |
| `[hashtable]` | `[System.Collections.Hashtable]` |
| `[int]` | `[System.Int32]` |
| `[long]` | `[System.Int64]` |
| `[object]` | `[System.Object]` |
| `[regex]` | `[System.Text.RegularExpressions.Regex]` |
| `[string]` | `[System.String]` |
| `[switch]` | `[System.Management.Automation.SwitchParameter]` |
| `[timespan]` | `[System.TimeSpan]` |
| `[xml]` | `[System.Xml.XmlDocument]` |

---

*文档版本: 1.0*  
*最后更新: 2026-02-16*  
*适用于: PowerShell 5.1+ / PowerShell 7+*