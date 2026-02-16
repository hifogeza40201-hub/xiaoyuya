# PowerShell高级函数和Cmdlet开发学习笔记

> 作者: Agent 3  
> 创建日期: 2026-02-16  
> 主题: PowerShell Advanced Functions and Cmdlet Development

---

## 目录

1. [高级函数参数属性](#1-高级函数参数属性)
2. [参数验证属性](#2-参数验证属性)
3. [CmdletBinding属性和ShouldProcess](#3-cmdletbinding属性和shouldprocess)
4. [管道处理Begin/Process/End](#4-管道处理beginprocessend)
5. [动态参数和参数集](#5-动态参数和参数集)
6. [PowerShell风格最佳实践](#6-powershell风格最佳实践)

---

## 1. 高级函数参数属性

### 1.1 Mandatory - 强制参数

```powershell
function Get-UserInfo {
    param(
        [Parameter(Mandatory=$true)]
        [string]$UserName
    )
    
    "获取用户信息: $UserName"
}

# 调用时不提供参数会提示输入
Get-UserInfo
```

### 1.2 Position - 位置参数

```powershell
function Copy-MyFile {
    param(
        [Parameter(Position=0)]
        [string]$Source,
        
        [Parameter(Position=1)]
        [string]$Destination
    )
    
    "从 $Source 复制到 $Destination"
}

# 可以按位置调用（无需参数名）
Copy-MyFile "C:\source.txt" "D:\dest.txt"
Copy-MyFile -Source "C:\source.txt" -Destination "D:\dest.txt"
```

### 1.3 ValueFromPipeline - 管道输入

```powershell
function Convert-ToUpper {
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$InputString
    )
    
    process {
        $InputString.ToUpper()
    }
}

# 管道输入
"hello", "world" | Convert-ToUpper
# 输出: HELLO WORLD
```

### 1.4 ValueFromPipelineByPropertyName - 按属性名管道输入

```powershell
function Get-FileSize {
    param(
        [Parameter(ValueFromPipelineByPropertyName=$true)]
        [string]$FullName
    )
    
    process {
        $file = Get-Item $FullName
        [PSCustomObject]@{
            Path = $FullName
            Size = $file.Length
            SizeKB = [math]::Round($file.Length / 1KB, 2)
        }
    }
}

# 按属性名管道输入
Get-ChildItem | Get-FileSize
```

### 1.5 HelpMessage - 帮助信息

```powershell
function New-Project {
    param(
        [Parameter(Mandatory=$true, HelpMessage="输入项目名称")]
        [string]$Name,
        
        [Parameter(HelpMessage="项目类型: Web, Desktop, Mobile")]
        [string]$Type
    )
    
    "创建项目: $Name, 类型: $Type"
}

# 查看帮助
Get-Help New-Project -Parameter Name
```

### 1.6 DontShow - 隐藏参数

```powershell
function Invoke-ApiCall {
    param(
        [string]$Endpoint,
        
        [Parameter(DontShow=$true)]
        [string]$ApiKey = $env:API_KEY
    )
    
    # ApiKey不会显示在帮助文档中，适合敏感信息
    "调用API: $Endpoint"
}
```

---

## 2. 参数验证属性

### 2.1 ValidateSet - 枚举验证

```powershell
function Set-LogLevel {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet("Debug", "Info", "Warning", "Error", "Critical")]
        [string]$Level
    )
    
    "日志级别设置为: $Level"
}

# 只有指定的值才能通过
Set-LogLevel -Level Info      # ✓ 成功
Set-LogLevel -Level Verbose   # ✗ 失败，不在集合中
```

### 2.2 ValidateRange - 范围验证

```powershell
function Set-Port {
    param(
        [ValidateRange(1, 65535)]
        [int]$PortNumber
    )
    
    "端口设置为: $PortNumber"
}

function Set-Percentage {
    param(
        [ValidateRange(0, 100)]
        [int]$Value
    )
    
    "百分比: $Value%"
}
```

### 2.3 ValidatePattern - 正则表达式验证

```powershell
function New-EmailAccount {
    param(
        [ValidatePattern('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')]
        [string]$Email,
        
        [ValidatePattern('^\d{3}-\d{4}$')]
        [string]$ZipCode
    )
    
    "创建账户: $Email, 邮编: $ZipCode"
}

# 支持自定义错误消息 (PowerShell 6+)
function New-Account {
    param(
        [ValidatePattern('^[A-Z][a-z]+$', ErrorMessage="用户名必须以大写字母开头")]
        [string]$UserName
    )
    
    "用户: $UserName"
}
```

### 2.4 ValidateLength - 长度验证

```powershell
function Set-Password {
    param(
        [ValidateLength(8, 128)]
        [SecureString]$Password
    )
    
    "密码长度符合要求"
}

function Set-Description {
    param(
        [ValidateLength(0, 255)]
        [string]$Description
    )
    
    "描述已设置"
}
```

### 2.5 ValidateCount - 数组元素数量验证

```powershell
function Add-Permissions {
    param(
        [ValidateCount(1, 5)]
        [string[]]$Permissions
    )
    
    "添加权限: $($Permissions -join ', ')"
}

# 至少1个，最多5个
Add-Permissions -Permissions "Read"
Add-Permissions -Permissions "Read", "Write", "Execute"
```

### 2.6 ValidateScript - 脚本验证（最灵活）

```powershell
function New-Directory {
    param(
        [ValidateScript({
            if (-not (Test-Path $_)) {
                return $true  # 路径不存在，可以创建
            }
            throw "路径已存在: $_"
        })]
        [string]$Path
    )
    
    New-Item -ItemType Directory -Path $Path
}

# 验证文件存在
function Import-Config {
    param(
        [ValidateScript({
            if (Test-Path $_ -PathType Leaf) {
                return $true
            }
            throw "配置文件不存在: $_"
        })]
        [string]$ConfigPath
    )
    
    Get-Content $ConfigPath | ConvertFrom-Json
}

# 验证服务存在
function Restart-MyService {
    param(
        [ValidateScript({
            $service = Get-Service -Name $_ -ErrorAction SilentlyContinue
            if ($service) {
                return $true
            }
            throw "服务不存在: $_"
        })]
        [string]$ServiceName
    )
    
    Restart-Service -Name $ServiceName
}
```

### 2.7 ValidateNotNull 和 ValidateNotNullOrEmpty

```powershell
function Update-Record {
    param(
        [ValidateNotNull()]
        [object]$Data,
        
        [ValidateNotNullOrEmpty()]
        [string]$Id
    )
    
    "更新记录: $Id"
}
```

### 2.8 AllowNull, AllowEmptyString, AllowEmptyCollection

```powershell
function Test-Input {
    param(
        [AllowNull()]
        [object]$NullableValue,
        
        [AllowEmptyString()]
        [string]$CanBeEmpty,
        
        [AllowEmptyCollection()]
        [array]$CanBeEmptyArray
    )
    
    "NullableValue: $NullableValue"
    "CanBeEmpty: '$CanBeEmpty'"
    "Array count: $($CanBeEmptyArray.Count)"
}
```

---

## 3. CmdletBinding属性和ShouldProcess

### 3.1 CmdletBinding基础

```powershell
function Get-SystemInfo {
    [CmdletBinding()]
    param(
        [string]$ComputerName = $env:COMPUTERNAME
    )
    
    Write-Verbose "正在查询计算机: $ComputerName"
    
    $info = @{
        ComputerName = $ComputerName
        OS = (Get-CimInstance Win32_OperatingSystem).Caption
        Memory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    }
    
    [PSCustomObject]$info
}

# 使用Verbose输出
Get-SystemInfo -Verbose
```

### 3.2 CmdletBinding高级选项

```powershell
function Invoke-DataOperation {
    [CmdletBinding(
        SupportsShouldProcess=$true,      # 支持 -WhatIf 和 -Confirm
        ConfirmImpact='Medium',            # 确认影响级别: Low, Medium, High
        DefaultParameterSetName='Default', # 默认参数集
        HelpUri='https://example.com/help',# 在线帮助URL
        PositionalBinding=$false          # 禁用自动位置绑定
    )]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )
    
    # 函数体
}
```

### 3.3 ShouldProcess完整示例

```powershell
function Remove-OldFiles {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [int]$DaysOld = 30
    )
    
    $cutoffDate = (Get-Date).AddDays(-$DaysOld)
    $files = Get-ChildItem -Path $Path -File | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    foreach ($file in $files) {
        # $PSCmdlet.ShouldProcess 返回 $true 或 $false
        # 目标: 正在操作的对象
        # 操作: 描述正在执行的操作
        if ($PSCmdlet.ShouldProcess($file.FullName, "删除")) {
            Remove-Item -Path $file.FullName -Force
            Write-Verbose "已删除: $($file.FullName)"
        }
    }
}

# 使用方式
Remove-OldFiles -Path "C:\Temp" -DaysOld 7
Remove-OldFiles -Path "C:\Temp" -DaysOld 7 -WhatIf    # 模拟执行
Remove-OldFiles -Path "C:\Temp" -DaysOld 7 -Confirm    # 每次确认
```

### 3.4 ShouldContinue（用于额外确认）

```powershell
function Clear-Database {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [Parameter(Mandatory=$true)]
        [string]$DatabaseName,
        
        [switch]$Force
    )
    
    # 基本ShouldProcess检查
    if ($PSCmdlet.ShouldProcess($DatabaseName, "清空数据库")) {
        
        # 额外确认（破坏性操作）
        if (-not $Force) {
            $caption = "确认清空数据库"
            $message = "确定要清空数据库 '$DatabaseName' 吗？此操作不可恢复！"
            $choices = @(
                [System.Management.Automation.Host.ChoiceDescription]::new("&Yes", "清空数据库")
                [System.Management.Automation.Host.ChoiceDescription]::new("&No", "取消操作")
            )
            
            $result = $Host.UI.PromptForChoice($caption, $message, $choices, 1)
            
            if ($result -eq 1) {
                Write-Host "操作已取消" -ForegroundColor Yellow
                return
            }
        }
        
        Write-Host "正在清空数据库: $DatabaseName" -ForegroundColor Red
        # 执行清空操作...
    }
}

# 使用
Clear-Database -DatabaseName "ProductionDB" -Force
```

### 3.5 使用 $PSCmdlet 变量

```powershell
function Test-PipelineSupport {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$InputObject
    )
    
    begin {
        Write-Verbose "Begin块执行 - 管道输入: $($PSCmdlet.MyInvocation.ExpectingInput)"
        $count = 0
    }
    
    process {
        $count++
        Write-Verbose "处理第 $count 个对象: $InputObject"
        $InputObject.ToUpper()
    }
    
    end {
        Write-Verbose "End块执行 - 共处理 $count 个对象"
    }
}
```

---

## 4. 管道处理Begin/Process/End

### 4.1 三个块的基本用法

```powershell
function Process-Data {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [object]$InputObject
    )
    
    begin {
        # 初始化代码 - 只执行一次
        Write-Verbose "开始处理数据..."
        $results = [System.Collections.Generic.List[object]]::new()
        $startTime = Get-Date
    }
    
    process {
        # 对管道中的每个对象执行
        Write-Verbose "处理对象: $InputObject"
        
        $processed = [PSCustomObject]@{
            Original = $InputObject
            Processed = $InputObject.ToString().ToUpper()
            Timestamp = Get-Date
        }
        
        $results.Add($processed)
    }
    
    end {
        # 清理和输出 - 只执行一次
        $duration = (Get-Date) - $startTime
        Write-Verbose "处理完成，耗时: $($duration.TotalMilliseconds)ms"
        
        # 返回所有结果
        $results
    }
}

# 使用
1..10 | Process-Data -Verbose
```

### 4.2 管道处理性能优化

```powershell
function Get-LargeFileReport {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [System.IO.FileInfo]$File,
        
        [long]$MinSizeMB = 100
    )
    
    begin {
        $minSizeBytes = $MinSizeMB * 1MB
        $largeFiles = [System.Collections.Generic.List[object]]::new()
        $totalSize = 0
    }
    
    process {
        if ($File.Length -gt $minSizeBytes) {
            $fileInfo = [PSCustomObject]@{
                Name = $File.Name
                FullPath = $File.FullName
                SizeMB = [math]::Round($File.Length / 1MB, 2)
                LastModified = $File.LastWriteTime
            }
            
            $largeFiles.Add($fileInfo)
            $totalSize += $File.Length
            
            # 流式输出（不等待所有对象）
            $fileInfo
        }
    }
    
    end {
        Write-Verbose "找到 $($largeFiles.Count) 个大文件，总计 $([math]::Round($totalSize/1MB, 2)) MB"
    }
}

# 流式处理大量文件
Get-ChildItem -Path "C:\" -Recurse -File -ErrorAction SilentlyContinue | 
    Get-LargeFileReport -MinSizeMB 50
```

### 4.3 处理非管道输入

```powershell
function Send-Notification {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string[]]$Message
    )
    
    begin {
        $allMessages = [System.Collections.Generic.List[string]]::new()
    }
    
    process {
        # 处理管道输入时，$Message 是单个字符串
        if ($PSCmdlet.MyInvocation.ExpectingInput) {
            $allMessages.Add($Message)
        }
        # 处理参数输入时，$Message 是字符串数组
        else {
            $allMessages.AddRange($Message)
        }
    }
    
    end {
        # 批量发送通知
        Write-Host "发送 $($allMessages.Count) 条通知" -ForegroundColor Cyan
        foreach ($msg in $allMessages) {
            Write-Host "  → $msg" -ForegroundColor Green
        }
    }
}

# 两种调用方式
Send-Notification -Message "消息1", "消息2", "消息3"
"消息1", "消息2", "消息3" | Send-Notification
```

### 4.4 处理不同类型的输入

```powershell
function Convert-ToJson {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [object]$InputObject,
        
        [switch]$Compress
    )
    
    begin {
        $collection = [System.Collections.Generic.List[object]]::new()
        $isPipeline = $PSCmdlet.MyInvocation.ExpectingInput
    }
    
    process {
        if ($isPipeline) {
            $collection.Add($InputObject)
        }
    }
    
    end {
        $jsonParams = @{
            Depth = 10
        }
        if ($Compress) {
            $jsonParams['Compress'] = $true
        }
        
        # 如果是管道输入，转换整个集合
        if ($isPipeline) {
            $collection | ConvertTo-Json @jsonParams
        }
        # 如果是参数输入，直接转换
        else {
            $InputObject | ConvertTo-Json @jsonParams
        }
    }
}
```

---

## 5. 动态参数和参数集

### 5.1 参数集基础

```powershell
function Connect-Server {
    [CmdletBinding(DefaultParameterSetName='Credential')]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ServerName,
        
        # 参数集: Credential
        [Parameter(Mandatory=$true, ParameterSetName='Credential')]
        [pscredential]$Credential,
        
        # 参数集: Token
        [Parameter(Mandatory=$true, ParameterSetName='Token')]
        [string]$Token,
        
        # 所有参数集共享
        [Parameter()]
        [int]$Port = 443
    )
    
    switch ($PSCmdlet.ParameterSetName) {
        'Credential' {
            "使用凭据连接到 $ServerName`:$Port"
            "用户名: $($Credential.UserName)"
        }
        'Token' {
            "使用令牌连接到 $ServerName`:$Port"
            "令牌: $($Token.Substring(0, 8))..."
        }
    }
}

# 使用
Connect-Server -ServerName "server1" -Credential (Get-Credential)
Connect-Server -ServerName "server1" -Token "abc123xyz"
# 以下会报错（参数集冲突）
# Connect-Server -ServerName "server1" -Credential $cred -Token "abc"
```

### 5.2 复杂参数集场景

```powershell
function Deploy-Application {
    [CmdletBinding(
        DefaultParameterSetName='Local',
        SupportsShouldProcess=$true
    )]
    param(
        [Parameter(Mandatory=$true)]
        [string]$AppName,
        
        [Parameter(Mandatory=$true, ParameterSetName='Local')]
        [string]$LocalPath,
        
        [Parameter(Mandatory=$true, ParameterSetName='Remote')]
        [string]$RemoteUrl,
        
        [Parameter(Mandatory=$true, ParameterSetName='Package')]
        [string]$PackageId,
        
        [Parameter(ParameterSetName='Remote')]
        [Parameter(ParameterSetName='Package')]
        [pscredential]$Credentials,
        
        [ValidateSet('Dev', 'Test', 'Prod')]
        [string]$Environment = 'Dev'
    )
    
    "部署 $AppName 到 $Environment 环境"
    "使用参数集: $($PSCmdlet.ParameterSetName)"
}
```

### 5.3 动态参数（DynamicParam）

```powershell
function Get-DriveInfo {
    [CmdletBinding()]
    param(
        [string]$ComputerName = $env:COMPUTERNAME
    )
    
    dynamicparam {
        # 动态创建参数
        $paramDictionary = [System.Management.Automation.RuntimeDefinedParameterDictionary]::new()
        
        # 根据计算机名动态获取可用驱动器
        try {
            $drives = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $ComputerName -ErrorAction Stop | 
                Select-Object -ExpandProperty DeviceID
            
            # 创建 ValidateSet 属性
            $validateSetAttribute = [System.Management.Automation.ValidateSetAttribute]::new($drives)
            
            # 创建 Parameter 属性
            $parameterAttribute = [System.Management.Automation.ParameterAttribute]::new()
            $parameterAttribute.Mandatory = $false
            $parameterAttribute.Position = 0
            
            # 创建属性集合
            $attributeCollection = [System.Collections.ObjectModel.Collection[System.Attribute]]::new()
            $attributeCollection.Add($parameterAttribute)
            $attributeCollection.Add($validateSetAttribute)
            
            # 创建动态参数
            $dynamicParam = [System.Management.Automation.RuntimeDefinedParameter]::new(
                'Drive',
                [string],
                $attributeCollection
            )
            
            $paramDictionary.Add('Drive', $dynamicParam)
        }
        catch {
            # 如果无法连接，不添加动态参数
        }
        
        return $paramDictionary
    }
    
    begin {
        $Drive = $PSBoundParameters['Drive']
    }
    
    process {
        $filter = if ($Drive) { "DeviceID='$Drive'" } else { $null }
        Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $ComputerName -Filter $filter |
            Select-Object DeviceID, @{N='SizeGB'; E={[math]::Round($_.Size/1GB, 2)}}, 
                          @{N='FreeSpaceGB'; E={[math]::Round($_.FreeSpace/1GB, 2)}}
    }
}

# Tab键会显示该计算机上的实际驱动器
Get-DriveInfo -Drive C:
```

### 5.4 高级动态参数示例

```powershell
function Set-ConfigValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ConfigFile = "app.config.json"
    )
    
    dynamicparam {
        $paramDictionary = [System.Management.Automation.RuntimeDefinedParameterDictionary]::new()
        
        # 读取配置文件获取可用键
        if (Test-Path $ConfigFile) {
            try {
                $config = Get-Content $ConfigFile | ConvertFrom-Json
                $keys = $config.PSObject.Properties.Name
                
                if ($keys) {
                    $validateSet = [System.Management.Automation.ValidateSetAttribute]::new($keys)
                    $parameter = [System.Management.Automation.ParameterAttribute]::new()
                    $parameter.Mandatory = $true
                    $parameter.Position = 0
                    
                    $attributes = [System.Collections.ObjectModel.Collection[System.Attribute]]::new()
                    $attributes.Add($parameter)
                    $attributes.Add($validateSet)
                    
                    $dynamicParam = [System.Management.Automation.RuntimeDefinedParameter]::new(
                        'Key',
                        [string],
                        $attributes
                    )
                    
                    $paramDictionary.Add('Key', $dynamicParam)
                }
            }
            catch {
                Write-Warning "无法读取配置文件: $_"
            }
        }
        
        return $paramDictionary
    }
    
    process {
        $Key = $PSBoundParameters['Key']
        "设置 $ConfigFile 中的 $Key 值"
    }
}
```

---

## 6. PowerShell风格最佳实践

### 6.1 命名规范

```powershell
# 动词-名词格式
# 批准的标准动词: Get, Set, New, Remove, Add, Clear, Export, Import, Start, Stop, etc.

# ✓ 好的命名
function Get-UserProfile { }
function Set-SystemConfiguration { }
function Invoke-RestApiCall { }
function Convert-JsonToCsv { }

# ✗ 避免
function getUserInfo { }      # 驼峰命名
function Fetch-Data { }       # 非标准动词
function Process { }          # 缺少名词
```

### 6.2 输出对象

```powershell
# ✓ 输出对象而非文本
function Get-ServerStatus {
    [CmdletBinding()]
    param([string]$ServerName)
    
    # 不好的做法：输出字符串
    # "Server: $ServerName, Status: Online"
    
    # 好的做法：输出对象
    [PSCustomObject]@{
        PSTypeName = 'MyTools.ServerStatus'
        ServerName = $ServerName
        Status = 'Online'
        Uptime = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
        Timestamp = Get-Date
    }
}

# 添加类型格式化（可选）
# 创建 formats.ps1xml 文件定义显示格式
```

### 6.3 完整的帮助文档

```powershell
<#
.SYNOPSIS
    获取服务器系统信息。

.DESCRIPTION
    Get-ServerInfo cmdlet 检索指定服务器的详细系统信息，
    包括操作系统、内存、磁盘空间和网络配置。

.PARAMETER ComputerName
    要查询的服务器名称或IP地址。默认为本地计算机。

.PARAMETER IncludeDiskInfo
    是否包含磁盘信息。会增加查询时间。

.PARAMETER Credential
    用于连接远程计算机的凭据。

.EXAMPLE
    PS C:\> Get-ServerInfo
    
    获取本地计算机的基本信息。

.EXAMPLE
    PS C:\> Get-ServerInfo -ComputerName "SERVER01" -IncludeDiskInfo
    
    获取SERVER01的完整信息，包括磁盘详情。

.EXAMPLE
    PS C:\> "SERVER01", "SERVER02" | Get-ServerInfo | Export-Csv servers.csv
    
    批量获取多台服务器信息并导出到CSV。

.OUTPUTS
    MyTools.ServerInfo
    返回包含服务器信息的对象。

.NOTES
    作者: PowerShell Expert
    版本: 1.0
    需要管理员权限获取完整信息。

.LINK
    https://docs.microsoft.com/powershell
#>
function Get-ServerInfo {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string[]]$ComputerName = $env:COMPUTERNAME,
        
        [switch]$IncludeDiskInfo,
        
        [pscredential]$Credential
    )
    
    # 实现代码...
}
```

### 6.4 错误处理

```powershell
function Copy-WithRetry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Source,
        
        [Parameter(Mandatory=$true)]
        [string]$Destination,
        
        [int]$MaxRetries = 3
    )
    
    $retryCount = 0
    $success = $false
    
    while ($retryCount -lt $MaxRetries -and -not $success) {
        try {
            $retryCount++
            Write-Verbose "尝试 $retryCount / $MaxRetries"
            
            Copy-Item -Path $Source -Destination $Destination -ErrorAction Stop
            $success = $true
            Write-Verbose "复制成功"
        }
        catch [System.IO.IOException] {
            Write-Warning "IO错误: $_"
            if ($retryCount -eq $MaxRetries) {
                throw
            }
            Start-Sleep -Seconds ([math]::Pow(2, $retryCount))  # 指数退避
        }
        catch {
            Write-Error "复制失败: $_"
            throw
        }
    }
}
```

### 6.5 模块化设计

```powershell
# 公共函数
function Get-MyData {
    [CmdletBinding()]
    param()
    
    # 使用私有辅助函数
    $rawData = Get-InternalData
    Format-MyData -Data $rawData
}

# 私有辅助函数（不导出）
function Get-InternalData {
    # 实现细节...
}

function Format-MyData {
    param([object]$Data)
    # 格式化逻辑...
}

# 在模块的 .psd1 文件中，只导出公共函数
# FunctionsToExport = @('Get-MyData')
```

### 6.6 完整的函数模板

```powershell
<#
.SYNOPSIS
    简短描述。

.DESCRIPTION
    详细描述。

.PARAMETER Name
    参数说明。

.EXAMPLE
    PS C:\> Function-Name -Name "Value"
    示例说明。
#>
function Verb-Noun {
    [CmdletBinding(
        DefaultParameterSetName='Default',
        SupportsShouldProcess=$true,
        ConfirmImpact='Medium'
    )]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(
            Mandatory=$true,
            Position=0,
            ValueFromPipeline=$true,
            ValueFromPipelineByPropertyName=$true,
            ParameterSetName='Default'
        )]
        [ValidateNotNullOrEmpty()]
        [string[]]$Name,
        
        [Parameter()]
        [ValidateSet('Option1', 'Option2')]
        [string]$Mode = 'Option1',
        
        [switch]$Force
    )
    
    begin {
        # 初始化
        Write-Verbose "开始处理"
        $results = [System.Collections.Generic.List[object]]::new()
    }
    
    process {
        foreach ($item in $Name) {
            try {
                if ($PSCmdlet.ShouldProcess($item, "执行操作")) {
                    # 核心逻辑
                    $result = [PSCustomObject]@{
                        Input = $item
                        Status = 'Success'
                        Timestamp = Get-Date
                    }
                    $results.Add($result)
                    $result
                }
            }
            catch {
                Write-Error "处理 $item 时出错: $_" -TargetObject $item
            }
        }
    }
    
    end {
        Write-Verbose "处理完成，共 $($results.Count) 个结果"
    }
}
```

---

## 关键知识点总结

### 参数属性速查表

| 属性 | 用途 | 示例 |
|------|------|------|
| `Mandatory` | 强制参数 | `[Parameter(Mandatory=$true)]` |
| `Position` | 位置参数 | `[Parameter(Position=0)]` |
| `ValueFromPipeline` | 管道输入 | `[Parameter(ValueFromPipeline=$true)]` |
| `ValueFromPipelineByPropertyName` | 按属性名管道输入 | `[Parameter(ValueFromPipelineByPropertyName=$true)]` |
| `ParameterSetName` | 参数集 | `[Parameter(ParameterSetName='Set1')]` |
| `HelpMessage` | 帮助信息 | `[Parameter(HelpMessage="说明")]` |
| `DontShow` | 隐藏参数 | `[Parameter(DontShow=$true)]` |

### 验证属性速查表

| 属性 | 用途 | 示例 |
|------|------|------|
| `ValidateSet` | 枚举验证 | `[ValidateSet("A", "B")]` |
| `ValidateRange` | 范围验证 | `[ValidateRange(1, 100)]` |
| `ValidatePattern` | 正则验证 | `[ValidatePattern('^\d+$')]` |
| `ValidateLength` | 长度验证 | `[ValidateLength(1, 100)]` |
| `ValidateCount` | 数组数量验证 | `[ValidateCount(1, 5)]` |
| `ValidateScript` | 脚本验证 | `[ValidateScript({Test-Path $_})]` |
| `ValidateNotNull` | 非空验证 | `[ValidateNotNull()]` |
| `ValidateNotNullOrEmpty` | 非空非空字符串验证 | `[ValidateNotNullOrEmpty()]` |

### CmdletBinding选项

| 选项 | 说明 |
|------|------|
| `SupportsShouldProcess` | 启用 -WhatIf 和 -Confirm |
| `ConfirmImpact` | 设置确认级别 (Low/Medium/High) |
| `DefaultParameterSetName` | 设置默认参数集 |
| `PositionalBinding` | 启用/禁用自动位置绑定 |
| `HelpUri` | 设置在线帮助URL |

### 最佳实践检查清单

- [ ] 使用 动词-名词 命名格式
- [ ] 使用批准的动词 (Get-Verb)
- [ ] 提供完整的帮助文档
- [ ] 实现管道支持 (ValueFromPipeline)
- [ ] 使用适当的参数验证
- [ ] 对修改操作使用 SupportsShouldProcess
- [ ] 输出对象而非文本
- [ ] 实现适当的错误处理
- [ ] 使用 CmdletBinding 启用高级功能
- [ ] 遵循参数集规则（互斥参数分开）

---

## 参考资源

1. [PowerShell 官方文档 - about_Functions_Advanced](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_functions_advanced)
2. [PowerShell 官方文档 - about_Functions_Advanced_Parameters](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_functions_advanced_parameters)
3. [PowerShell 官方文档 - about_Functions_CmdletBinding](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_functions_cmdletbindingattribute)
4. [PowerShell 最佳实践](https://docs.microsoft.com/powershell/scripting/developer/cmdlet/cmdlet-overview)

---

*学习笔记完成*
