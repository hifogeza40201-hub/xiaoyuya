# PowerShell 模块系统深度研究笔记

> 研究日期: 2026-02-16  
> 研究主题: PowerShell Module System Deep Dive  
> 研究范围: PowerShell 5.1 / PowerShell 7.x

---

## 目录
1. [PowerShell模块类型](#1-powershell模块类型)
2. [创建自定义模块](#2-创建自定义模块)
3. [模块清单文件(.psd1)](#3-模块清单文件psd1)
4. [模块作用域和导出控制](#4-模块作用域和导出控制)
5. [PowerShell Gallery](#5-powershell-gallery)
6. [实际可运行代码示例](#6-实际可运行代码示例)

---

## 1. PowerShell模块类型

PowerShell 支持三种主要模块类型：

### 1.1 脚本模块 (Script Module)

**定义**: 以 `.psm1` 为扩展名的PowerShell脚本文件

**特点**:
- 纯PowerShell代码编写
- 无需编译，直接运行
- 跨平台兼容（PowerShell Core）
- 适合业务逻辑、管理脚本

**适用场景**:
- 自动化任务
- 系统管理脚本
- 业务流程封装
- 团队内部工具

```powershell
# 示例: MyTools.psm1
function Get-SystemInfo {
    [CmdletBinding()]
    param()
    
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $cpu = Get-CimInstance -ClassName Win32_Processor
    
    [PSCustomObject]@{
        ComputerName = $env:COMPUTERNAME
        OS           = $os.Caption
        Version      = $os.Version
        Architecture = $os.OSArchitecture
        CPU          = $cpu.Name
        MemoryGB     = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    }
}

Export-ModuleMember -Function Get-SystemInfo
```

### 1.2 二进制模块 (Binary Module)

**定义**: 使用 .NET 语言（C#、VB.NET、F#）编译的 DLL 程序集

**特点**:
- 高性能，执行速度快
- 可访问完整的.NET Framework/Core API
- 代码保护（编译后难以逆向）
- 需要编译环境

**适用场景**:
- 性能敏感操作
- 复杂算法实现
- 需要调用Win32 API
- 商业软件模块

**创建步骤**:
1. 创建 .NET Class Library 项目
2. 添加 `System.Management.Automation` 引用
3. 继承 `Cmdlet` 或 `PSCmdlet` 类
4. 实现 `ProcessRecord()` 等方法
5. 编译为 DLL

```csharp
// 示例: C# 编写的 Cmdlet
using System.Management.Automation;

[Cmdlet(VerbsCommon.Get, "BinaryData")]
public class GetBinaryDataCommand : Cmdlet
{
    [Parameter(Mandatory = true, Position = 0)]
    public string Path { get; set; }

    protected override void ProcessRecord()
    {
        // 高性能处理逻辑
        var data = System.IO.File.ReadAllBytes(Path);
        WriteObject(data);
    }
}
```

### 1.3 清单模块 (Manifest Module)

**定义**: 使用 `.psd1` 文件描述模块元数据和依赖关系的模块

**特点**:
- 模块的"入口点"
- 描述版本、作者、依赖等信息
- 可以包含/引用其他模块
- 支持模块嵌套

**适用场景**:
- 所有正式发布的模块
- 复杂模块（包含多个子模块）
- 需要声明依赖的场景

```powershell
# 示例: MyModule.psd1
@{
    RootModule        = 'MyModule.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = '12345678-1234-1234-1234-123456789012'
    Author            = 'Your Name'
    CompanyName       = 'Your Company'
    Copyright         = '(c) 2024 Your Company. All rights reserved.'
    Description       = '这是一个示例模块清单'
    RequiredModules   = @()
    FunctionsToExport = @('Get-SystemInfo', 'Set-Configuration')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
}
```

### 模块类型对比表

| 特性 | 脚本模块 | 二进制模块 | 清单模块 |
|------|----------|------------|----------|
| 扩展名 | .psm1 | .dll | .psd1 |
| 语言 | PowerShell | C#/VB.NET/F# | PowerShell (DSL) |
| 性能 | 中等 | 高 | N/A |
| 跨平台 | ✅ | 需编译 | ✅ |
| 开发难度 | 低 | 高 | 低 |
| 代码保护 | ❌ | ✅ | N/A |
| 调试方便性 | 高 | 中等 | 高 |

---

## 2. 创建自定义模块

### 2.1 标准模块目录结构

```
MyModule/
├── MyModule.psd1          # 模块清单（必需）
├── MyModule.psm1          # 根模块脚本
├── Public/                # 公开函数
│   ├── Get-Something.ps1
│   ├── Set-Something.ps1
│   └── Remove-Something.ps1
├── Private/               # 私有函数
│   ├── Helper1.ps1
│   └── Helper2.ps1
├── Classes/               # 类定义（PS 5.0+）
│   ├── MyClass.ps1
│   └── AnotherClass.ps1
├── Data/                  # 数据文件
│   └── Config.json
├── en-US/                 # 本地化帮助文档
│   └── about_MyModule.help.txt
└── Tests/                 # Pester测试
    └── MyModule.Tests.ps1
```

### 2.2 创建步骤详解

#### 步骤 1: 创建模块目录

```powershell
# 创建用户模块目录
$modulePath = "$env:USERPROFILE\Documents\PowerShell\Modules\MyModule"
# PowerShell 5.1: $env:USERPROFILE\Documents\WindowsPowerShell\Modules\MyModule

New-Item -ItemType Directory -Path $modulePath -Force
Set-Location $modulePath

# 创建子目录
New-Item -ItemType Directory -Path @('Public', 'Private', 'Classes', 'Data', 'Tests')
```

#### 步骤 2: 创建根模块文件 (.psm1)

```powershell
# MyModule.psm1
#Requires -Version 5.1

# 获取模块根路径
$ModuleRoot = $PSScriptRoot

# 加载类文件（必须在函数之前加载）
$ClassFiles = Get-ChildItem -Path "$ModuleRoot\Classes" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $ClassFiles) {
    . $file.FullName
}

# 加载私有函数
$PrivateFiles = Get-ChildItem -Path "$ModuleRoot\Private" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $PrivateFiles) {
    . $file.FullName
}

# 加载公开函数
$PublicFiles = Get-ChildItem -Path "$ModuleRoot\Public" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $PublicFiles) {
    . $file.FullName
}

# 导出公开函数
$PublicFunctions = $PublicFiles.BaseName
Export-ModuleMember -Function $PublicFunctions

# 模块初始化代码
Write-Verbose "MyModule 模块已加载。版本: $((Test-ModuleManifest -Path "$ModuleRoot\MyModule.psd1").Version)"
```

#### 步骤 3: 创建模块清单 (.psd1)

```powershell
# 使用 New-ModuleManifest 自动生成
$manifestParams = @{
    Path              = 'MyModule.psd1'
    RootModule        = 'MyModule.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = [guid]::NewGuid()
    Author            = $env:USERNAME
    CompanyName       = 'Your Organization'
    Copyright         = "(c) $(Get-Date -Format yyyy) Your Organization. All rights reserved."
    Description       = '这是一个示例PowerShell模块，展示最佳实践'
    PowerShellVersion = '5.1'
    RequiredModules   = @()
    FunctionsToExport = @()
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
    Tags              = @('Example', 'Learning')
    ProjectUri        = 'https://github.com/yourname/MyModule'
    LicenseUri        = 'https://github.com/yourname/MyModule/LICENSE'
}

New-ModuleManifest @manifestParams
```

#### 步骤 4: 编写公开函数

```powershell
# Public\Get-SystemReport.ps1
function Get-SystemReport {
    <#
    .SYNOPSIS
        获取系统报告
    .DESCRIPTION
        收集系统信息并生成详细报告
    .PARAMETER ComputerName
        目标计算机名称，默认为本地计算机
    .PARAMETER OutputPath
        报告输出路径
    .EXAMPLE
        Get-SystemReport -OutputPath C:\Reports
        生成本地系统报告
    .NOTES
        作者: Your Name
        版本: 1.0
    #>
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline = $true)]
        [string[]]$ComputerName = $env:COMPUTERNAME,
        
        [Parameter()]
        [string]$OutputPath = "."
    )
    
    begin {
        $results = @()
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
    }
    
    process {
        foreach ($computer in $ComputerName) {
            try {
                Write-Verbose "正在收集 $computer 的信息..."
                
                # 调用私有函数获取详细信息
                $systemInfo = _GetComputerDetails -ComputerName $computer
                
                $results += [PSCustomObject]@{
                    ComputerName  = $computer
                    Timestamp     = Get-Date
                    OS            = $systemInfo.OS
                    Version       = $systemInfo.Version
                    Uptime        = $systemInfo.Uptime
                    CPU           = $systemInfo.CPU
                    TotalMemoryGB = $systemInfo.TotalMemoryGB
                    FreeMemoryGB  = $systemInfo.FreeMemoryGB
                    DiskInfo      = $systemInfo.DiskInfo
                    Status        = 'Success'
                }
            }
            catch {
                Write-Warning "无法收集 $computer 的信息: $_"
                $results += [PSCustomObject]@{
                    ComputerName = $computer
                    Timestamp    = Get-Date
                    Status       = "Failed: $_"
                }
            }
        }
    }
    
    end {
        # 生成报告文件
        $reportFile = Join-Path $OutputPath "SystemReport_$timestamp.json"
        $results | ConvertTo-Json -Depth 5 | Out-File -FilePath $reportFile
        
        Write-Host "报告已保存到: $reportFile" -ForegroundColor Green
        return $results
    }
}
```

#### 步骤 5: 编写私有函数

```powershell
# Private\_GetComputerDetails.ps1
function _GetComputerDetails {
    <#
    .SYNOPSIS
        获取计算机详细信息（私有函数）
    #>
    param([string]$ComputerName)
    
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ComputerName $ComputerName
    $cpu = Get-CimInstance -ClassName Win32_Processor -ComputerName $ComputerName
    $disks = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $ComputerName -Filter "DriveType=3"
    
    $uptime = (Get-Date) - $os.LastBootUpTime
    
    [PSCustomObject]@{
        OS            = $os.Caption
        Version       = $os.Version
        Uptime        = "$($uptime.Days) 天 $($uptime.Hours) 小时"
        CPU           = $cpu.Name
        TotalMemoryGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
        FreeMemoryGB  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
        DiskInfo      = $disks | ForEach-Object {
            [PSCustomObject]@{
                Drive    = $_.DeviceID
                SizeGB   = [math]::Round($_.Size / 1GB, 2)
                FreeGB   = [math]::Round($_.FreeSpace / 1GB, 2)
                PercentFree = [math]::Round(($_.FreeSpace / $_.Size) * 100, 2)
            }
        }
    }
}
```

### 2.3 最佳实践清单

✅ **必须遵循**:
- 使用完整的CmdletBinding属性
- 为所有公开函数编写帮助文档
- 使用参数验证（ValidateSet, ValidatePattern等）
- 错误处理（try/catch）
- 使用Write-Verbose, Write-Debug进行日志输出
- 遵循命名约定（Verb-Noun格式）
- 版本控制清单文件

✅ **推荐做法**:
- 分离Public/Private函数
- 使用类（PS 5.0+）组织复杂数据
- 编写Pester测试
- 提供示例和文档
- 使用Semantic Versioning（语义化版本）

---

## 3. 模块清单文件(.psd1)

### 3.1 完整清单配置详解

```powershell
@{
    # === 基本信息 ===
    
    # 根模块文件（.psm1 或 .dll）
    RootModule = 'MyModule.psm1'
    
    # 模块版本（遵循 Semantic Versioning: Major.Minor.Build.Revision）
    ModuleVersion = '1.2.3'
    
    # 唯一标识符（GUID）
    GUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    
    # 作者信息
    Author = 'Your Name'
    CompanyName = 'Your Company'
    Copyright = '(c) 2024 Your Company. All rights reserved.'
    
    # 模块描述（PowerShell Gallery显示）
    Description = '这是一个功能强大的PowerShell模块，用于...'
    
    # === PowerShell 版本要求 ===
    
    # 最低PowerShell版本
    PowerShellVersion = '5.1'
    
    # 最低PowerShell Core版本
    PowerShellHostName = ''
    PowerShellHostVersion = ''
    
    # 最低.NET Framework版本
    DotNetFrameworkVersion = '4.5'
    
    # 最低CLR版本
    CLRVersion = '4.0'
    
    # 处理器架构
    ProcessorArchitecture = 'None'  # 可选: None, MSIL, X86, X64, IA64, Arm
    
    # === 依赖管理 ===
    
    # 模块依赖（必须在加载当前模块之前加载）
    RequiredModules = @(
        @{ModuleName = 'Pester'; ModuleVersion = '5.0.0'; Guid = 'a5ded6a1-1132-4e95-91d4-2a0f58f61597'},
        @{ModuleName = 'PSReadLine'; RequiredVersion = '2.1.0'}
    )
    
    # 程序集依赖
    RequiredAssemblies = @('System.Web', 'System.Net.Http')
    
    # 脚本文件（加载模块前执行）
    ScriptsToProcess = @('Initialize-Environment.ps1')
    
    # 类型定义文件
    TypesToProcess = @('MyTypes.ps1xml')
    
    # 格式定义文件
    FormatsToProcess = @('MyFormats.ps1xml')
    
    # 嵌套模块
    NestedModules = @('SubModule1.psm1', 'SubModule2.dll')
    
    # === 导出控制 ===
    
    # 导出的函数（使用 * 表示全部，但建议明确列出）
    FunctionsToExport = @('Get-Something', 'Set-Something', 'Remove-Something')
    
    # 导出的Cmdlet
    CmdletsToExport = @()
    
    # 导出的变量
    VariablesToExport = @('MyModuleConfig')
    
    # 导出的别名
    AliasesToExport = @('gsi', 'ssi')
    
    # === DSC 资源（Desired State Configuration） ===
    
    DscResourcesToExport = @('MyDscResource')
    
    # === 模块列表 ===
    
    # 包含的模块（用于合并模块）
    ModuleList = @('MyModule.psm1', 'Helper.psm1')
    
    # 文件列表（用于清单验证）
    FileList = @('MyModule.psm1', 'LICENSE', 'README.md')
    
    # === 私有数据 ===
    
    PrivateData = @{
        PSData = @{
            # 标签（PowerShell Gallery搜索用）
            Tags = @('Windows', 'Automation', 'Management', 'PSEdition_Core', 'PSEdition_Desktop')
            
            # 许可证URI
            LicenseUri = 'https://github.com/yourname/MyModule/blob/main/LICENSE'
            
            # 项目URI
            ProjectUri = 'https://github.com/yourname/MyModule'
            
            # 图标URI
            IconUri = 'https://raw.githubusercontent.com/yourname/MyModule/main/icon.png'
            
            # 发布说明
            ReleaseNotes = @'
## v1.2.3
- 新增功能 X
- 修复 Bug Y
- 性能优化 Z
'@
            
            # 预发布标签（用于测试版本）
            Prerelease = 'beta1'
            
            # 是否需要许可证接受
            RequireLicenseAcceptance = $false
            
            # 外部模块依赖
            ExternalModuleDependencies = @()
        }
        
        # 自定义数据
        CustomField1 = 'Value1'
        CustomField2 = 'Value2'
    }
    
    # === 帮助信息 URI ===
    
    # 默认命令前缀（可选）
    DefaultCommandPrefix = 'My'
    
    # 可更新帮助 URI
    HelpInfoURI = 'https://github.com/yourname/MyModule/blob/main/help.xml'
}
```

### 3.2 常用清单命令

```powershell
# 创建新清单
New-ModuleManifest -Path 'MyModule.psd1' -RootModule 'MyModule.psm1' -Author 'Your Name'

# 更新清单
Update-ModuleManifest -Path 'MyModule.psd1' -ModuleVersion '1.1.0'

# 验证清单
Test-ModuleManifest -Path 'MyModule.psd1'

# 获取清单信息
Import-PowerShellDataFile -Path 'MyModule.psd1'
```

---

## 4. 模块作用域和导出控制

### 4.1 作用域层次结构

```
全局作用域 (Global)
    │
    ├── 会话作用域 (Session)
    │       │
    │       ├── 模块 A 作用域
    │       │       ├── 公开函数
    │       │       │       └── 可访问模块私有成员
    │       │       └── 私有函数（仅模块内部可见）
    │       │
    │       └── 模块 B 作用域
    │               └── ...
    │
    └── 脚本作用域 (Script)
            └── ...
```

### 4.2 导出控制详解

```powershell
# === 在 .psm1 文件中控制导出 ===

# 方法 1: 显式导出特定函数
function Public-Function1 { }
function Public-Function2 { }
function Private-Function { }

Export-ModuleMember -Function 'Public-Function1', 'Public-Function2'

# 方法 2: 使用通配符（不推荐用于生产环境）
Export-ModuleMember -Function '*' -Variable '*'

# 方法 3: 导出变量和别名
$Script:ModuleConfig = @{ Setting = 'Value' }
New-Alias -Name gf -Value Get-File

Export-ModuleMember -Function '*' -Variable 'ModuleConfig' -Alias 'gf'
```

### 4.3 作用域修饰符

```powershell
# $Global: 全局作用域（慎用）
$Global:AppConfig = @{ }

# $Script: 脚本/模块作用域（推荐）
$Script:ModuleCache = @{ }

# $Local: 局部作用域（默认）
$Local:TempValue = 42

# $Private: 私有作用域（仅当前作用域）
$Private:SecretKey = 'xxx'
```

### 4.4 模块状态管理

```powershell
# MyModule.psm1

# 模块级别的私有状态
$Script:ModuleState = @{
    Initialized = $false
    Config      = @{ }
    Cache       = @{ }
}

# 初始化函数（模块加载时自动执行）
function Initialize-Module {
    if ($Script:ModuleState.Initialized) {
        Write-Verbose "模块已初始化，跳过"
        return
    }
    
    $Script:ModuleState.Config = Get-ModuleConfiguration
    $Script:ModuleState.Initialized = $true
    
    Write-Verbose "模块初始化完成"
}

# 获取模块状态（公开函数）
function Get-ModuleState {
    return $Script:ModuleState.Clone()
}

# 清理函数
function Clear-ModuleCache {
    $Script:ModuleState.Cache.Clear()
}

# 注册模块卸载事件
$MyInvocation.MyCommand.ScriptBlock.Module.OnRemove = {
    Write-Verbose "MyModule 正在卸载，执行清理..."
    $Script:ModuleState.Clear()
}

# 执行初始化
Initialize-Module
```

### 4.5 跨模块访问

```powershell
# 访问其他模块的私有成员（高级用法，不推荐）
$otherModule = Get-Module 'OtherModule'
$privateFunction = & $otherModule { Get-Command -Name '_PrivateFunc' -Type Function }

# 使用调用操作符在指定模块上下文中执行
& $otherModule { $Script:ModuleVariable }
```

---

## 5. PowerShell Gallery

### 5.1 简介

PowerShell Gallery 是 PowerShell 模块的官方公共仓库：
- **地址**: https://www.powershellgallery.com
- **包管理器**: PowerShellGet (v1/v2) 或 PSResourceGet (v3+)
- **用途**: 发布、发现、安装 PowerShell 模块

### 5.2 安装和使用模块

```powershell
# === 查找模块 ===

# 搜索模块
Find-Module -Name 'Pester'
Find-Module -Tag 'Azure', 'Cloud'
Find-Module -Filter 'logging'

# 查看模块详情
Find-Module -Name 'Pester' | Select-Object *

# === 安装模块 ===

# 安装最新版本
Install-Module -Name 'Pester' -Scope CurrentUser

# 安装特定版本
Install-Module -Name 'Pester' -RequiredVersion '5.4.0' -Scope CurrentUser

# 安装到所有用户（需要管理员权限）
Install-Module -Name 'Pester' -Scope AllUsers

# 允许Clobber（覆盖冲突命令）
Install-Module -Name 'ModuleName' -AllowClobber

# 跳过发布者检查（开发用）
Install-Module -Name 'ModuleName' -SkipPublisherCheck

# === 更新模块 ===
Update-Module -Name 'Pester'

# === 卸载模块 ===
Uninstall-Module -Name 'Pester'

# === 列出已安装模块 ===
Get-InstalledModule
```

### 5.3 发布模块到 Gallery

#### 前置准备

1. **注册 PowerShell Gallery 账户**
   - 访问 https://www.powershellgallery.com
   - 使用 Microsoft 账户登录
   - 获取 API 密钥

2. **安装必要工具**
```powershell
# 确保 PowerShellGet 已安装
Install-Module -Name PowerShellGet -Force -SkipPublisherCheck

# 或使用 PSResourceGet (PowerShell 7+)
Install-Module -Name Microsoft.PowerShell.PSResourceGet -Force
```

#### 发布步骤

```powershell
# === 步骤 1: 准备模块 ===

# 确保清单文件完整且通过验证
$manifestPath = 'C:\Projects\MyModule\MyModule.psd1'
Test-ModuleManifest -Path $manifestPath

# 验证模块可以正常导入
Import-Module $manifestPath -Force
Get-Module -Name 'MyModule' | Select-Object Version, ExportedFunctions

# === 步骤 2: 获取 API 密钥 ===
# 从 https://www.powershellgallery.com/account/apikeys 获取
$apiKey = 'your-api-key-here'

# === 步骤 3: 发布模块 ===

# 方法 1: 使用 Publish-Module (PowerShellGet)
Publish-Module `
    -Path 'C:\Projects\MyModule' `
    -NuGetApiKey $apiKey `
    -Repository 'PSGallery' `
    -Verbose

# 方法 2: 使用 Publish-PSResource (PSResourceGet)
Publish-PSResource `
    -Path 'C:\Projects\MyModule' `
    -Repository 'PSGallery' `
    -ApiKey $apiKey `
    -Verbose

# === 步骤 4: 验证发布 ===

# 等待几分钟后搜索模块
Find-Module -Name 'MyModule'

# 测试安装
Install-Module -Name 'MyModule' -Scope CurrentUser -Force
Import-Module 'MyModule'
Get-Command -Module 'MyModule'
```

### 5.4 发布前检查清单

```powershell
# Pre-Publish-Checklist.ps1
function Test-ModulePublishReady {
    param([string]$ModulePath)
    
    $errors = @()
    $warnings = @()
    
    # 检查清单文件
    $manifestPath = Join-Path $ModulePath '*.psd1' | Get-Item | Select-Object -First 1
    if (-not $manifestPath) {
        $errors += "未找到模块清单文件(.psd1)"
    }
    
    # 验证清单
    try {
        $manifest = Test-ModuleManifest -Path $manifestPath -ErrorAction Stop
    }
    catch {
        $errors += "清单验证失败: $_"
    }
    
    # 检查必需字段
    $requiredFields = @('Author', 'Description', 'Version')
    foreach ($field in $requiredFields) {
        if (-not $manifest.$field) {
            $errors += "缺少必需字段: $field"
        }
    }
    
    # 检查版本格式
    if ($manifest.Version -match '-') {
        $warnings += "版本号包含预发布标识，将发布为预发布版本"
    }
    
    # 测试导入
    try {
        Import-Module $ModulePath -Force -ErrorAction Stop
        $module = Get-Module $manifest.Name
        if ($module.ExportedFunctions.Count -eq 0) {
            $warnings += "模块未导出任何函数"
        }
    }
    catch {
        $errors += "模块导入失败: $_"
    }
    
    # 输出结果
    if ($errors) {
        Write-Host "❌ 错误:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
    }
    
    if ($warnings) {
        Write-Host "⚠️  警告:" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    }
    
    if (-not $errors -and -not $warnings) {
        Write-Host "✅ 模块已准备好发布!" -ForegroundColor Green
        return $true
    }
    
    return ($errors.Count -eq 0)
}

# 使用示例
Test-ModulePublishReady -ModulePath 'C:\Projects\MyModule'
```

### 5.5 版本管理和更新

```powershell
# === 语义化版本控制 (SemVer) ===
# 格式: Major.Minor.Build[-PrereleaseLabel]

# Major: 不兼容的API更改
# Minor: 向后兼容的功能添加
# Build/Patch: 向后兼容的问题修复
# Prerelease: 预发布标签 (alpha, beta, rc)

# === 更新版本示例 ===
$manifestPath = 'MyModule.psd1'
$currentVersion = (Test-ModuleManifest -Path $manifestPath).Version

# 递增 Patch 版本
$newVersion = [version]::new($currentVersion.Major, $currentVersion.Minor, $currentVersion.Build + 1)

# 更新清单
Update-ModuleManifest -Path $manifestPath -ModuleVersion $newVersion

# === 预发布版本 ===
# 修改 PrivateData.PSData.Prerelease
$manifestContent = Import-PowerShellDataFile -Path $manifestPath
$manifestContent.PrivateData.PSData.Prerelease = 'beta1'

# 重新生成清单（需要手动编辑或使用脚本）
```

### 5.6 私有 Gallery

```powershell
# === 设置私有 NuGet 仓库 ===

# 注册私有仓库
Register-PSRepository `
    -Name 'MyCompanyRepo' `
    -SourceLocation 'https://nuget.mycompany.com/api/v2' `
    -PublishLocation 'https://nuget.mycompany.com/api/v2/package' `
    -InstallationPolicy Trusted

# 列出所有仓库
Get-PSRepository

# 从私有仓库安装
Install-Module -Name 'CompanyModule' -Repository 'MyCompanyRepo'

# 发布到私有仓库
Publish-Module -Path 'C:\Modules\CompanyModule' -Repository 'MyCompanyRepo' -NuGetApiKey 'xxx'
```

---

## 6. 实际可运行代码示例

### 6.1 完整模块创建脚本

```powershell
# Create-NewModule.ps1
# 一键创建新模块的完整结构

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ModuleName,
    
    [Parameter()]
    [string]$Author = $env:USERNAME,
    
    [Parameter()]
    [string]$Description = "A PowerShell module for $ModuleName",
    
    [Parameter()]
    [version]$Version = '1.0.0',
    
    [Parameter()]
    [string]$Path = (Join-Path (Split-Path $profile -Parent) 'Modules')
)

$moduleRoot = Join-Path $Path $ModuleName

# 创建目录结构
$directories = @(
    $moduleRoot
    (Join-Path $moduleRoot 'Public')
    (Join-Path $moduleRoot 'Private')
    (Join-Path $moduleRoot 'Classes')
    (Join-Path $moduleRoot 'Tests')
    (Join-Path $moduleRoot 'en-US')
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# 创建根模块文件
$psm1Content = @'
#Requires -Version 5.1

$ModuleRoot = $PSScriptRoot

# Load classes
$ClassFiles = Get-ChildItem -Path "$ModuleRoot\Classes" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $ClassFiles) { . $file.FullName }

# Load private functions
$PrivateFiles = Get-ChildItem -Path "$ModuleRoot\Private" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $PrivateFiles) { . $file.FullName }

# Load public functions
$PublicFiles = Get-ChildItem -Path "$ModuleRoot\Public" -Filter '*.ps1' -ErrorAction SilentlyContinue
foreach ($file in $PublicFiles) { . $file.FullName }

# Export public functions
Export-ModuleMember -Function $PublicFiles.BaseName
'@

$psm1Content | Out-File -FilePath (Join-Path $moduleRoot "$ModuleName.psm1") -Encoding UTF8

# 创建清单
$manifestParams = @{
    Path              = Join-Path $moduleRoot "$ModuleName.psd1"
    RootModule        = "$ModuleName.psm1"
    ModuleVersion     = $Version
    GUID              = [guid]::NewGuid()
    Author            = $Author
    Description       = $Description
    PowerShellVersion = '5.1'
    FunctionsToExport = @()
    Tags              = @('PowerShell', 'Module')
}

New-ModuleManifest @manifestParams

# 创建示例公开函数
$exampleFunction = @'
function Get-ModuleInfo {
    <#
    .SYNOPSIS
        Gets information about the current module.
    #>
    [CmdletBinding()]
    param()
    
    $module = Get-Module -Name '<MODULE_NAME>'
    return [PSCustomObject]@{
        Name        = $module.Name
        Version     = $module.Version
        Author      = $module.Author
        Description = $module.Description
        Path        = $module.ModuleBase
    }
}
'@ -replace '<MODULE_NAME>', $ModuleName

$exampleFunction | Out-File -FilePath (Join-Path $moduleRoot 'Public\Get-ModuleInfo.ps1') -Encoding UTF8

# 更新清单导出
Update-ModuleManifest -Path (Join-Path $moduleRoot "$ModuleName.psd1") -FunctionsToExport @('Get-ModuleInfo')

# 创建 Pester 测试
$testContent = @'
BeforeAll {
    Import-Module (Join-Path $PSScriptRoot '..' '<MODULE_NAME>.psd1') -Force
}

Describe 'Get-ModuleInfo' {
    It 'Returns module information' {
        $result = Get-ModuleInfo
        $result.Name | Should -Be '<MODULE_NAME>'
    }
}
'@ -replace '<MODULE_NAME>', $ModuleName

$testContent | Out-File -FilePath (Join-Path $moduleRoot 'Tests\Module.Tests.ps1') -Encoding UTF8

Write-Host "✅ Module '$ModuleName' created at: $moduleRoot" -ForegroundColor Green
Write-Host "   To load: Import-Module '$moduleRoot' -Force"
```

### 6.2 模块管理工具函数

```powershell
# Module-Tools.ps1

function Get-ModuleDependencyTree {
    <#
    .SYNOPSIS
        获取模块的依赖树
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        
        [int]$Depth = 0,
        [int]$MaxDepth = 5
    )
    
    if ($Depth -gt $MaxDepth) { return }
    
    $module = Get-Module -Name $Name -ListAvailable | Select-Object -First 1
    if (-not $module) { return }
    
    $indent = '  ' * $Depth
    Write-Host "$indent📦 $Name v$($module.Version)"
    
    if ($module.RequiredModules) {
        foreach ($req in $module.RequiredModules) {
            Get-ModuleDependencyTree -Name $req.Name -Depth ($Depth + 1) -MaxDepth $MaxDepth
        }
    }
}

function Test-ModuleHealth {
    <#
    .SYNOPSIS
        检查模块健康状况
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string[]]$Name
    )
    
    process {
        foreach ($moduleName in $Name) {
            $result = [PSCustomObject]@{
                ModuleName      = $moduleName
                Installed       = $false
                Version         = $null
                Path            = $null
                CanImport       = $false
                ExportedCmdlets = 0
                Errors          = @()
            }
            
            try {
                $module = Get-Module -Name $moduleName -ListAvailable | Select-Object -First 1
                if ($module) {
                    $result.Installed = $true
                    $result.Version = $module.Version
                    $result.Path = $module.ModuleBase
                    
                    # 尝试导入
                    Import-Module $moduleName -Force -ErrorAction Stop
                    $imported = Get-Module -Name $moduleName
                    $result.CanImport = $true
                    $result.ExportedCmdlets = ($imported.ExportedCmdlets.Count + $imported.ExportedFunctions.Count)
                }
                else {
                    $result.Errors += "Module not found"
                }
            }
            catch {
                $result.Errors += $_.Exception.Message
            }
            
            $result
        }
    }
}

function Backup-InstalledModules {
    <#
    .SYNOPSIS
        备份已安装模块列表
    #>
    param(
        [string]$OutputPath = 'InstalledModules.json'
    )
    
    $modules = Get-InstalledModule | Select-Object Name, Version, Repository
    $modules | ConvertTo-Json | Out-File $OutputPath
    
    Write-Host "✅ Backup saved to $OutputPath" -ForegroundColor Green
}

function Restore-InstalledModules {
    <#
    .SYNOPSIS
        从备份恢复模块
    #>
    param(
        [string]$BackupPath = 'InstalledModules.json'
    )
    
    $modules = Get-Content $BackupPath | ConvertFrom-Json
    foreach ($mod in $modules) {
        if (-not (Get-Module -Name $mod.Name -ListAvailable)) {
            Write-Host "Installing $($mod.Name)..."
            Install-Module -Name $mod.Name -RequiredVersion $mod.Version -Force
        }
    }
}
```

### 6.3 完整示例模块运行演示

```powershell
# Demo-CompleteModule.ps1

Write-Host "=== PowerShell 模块系统演示 ===" -ForegroundColor Cyan

# 1. 显示模块路径
Write-Host "`n1. PowerShell 模块路径:" -ForegroundColor Yellow
$env:PSModulePath -split ';' | ForEach-Object { Write-Host "   $_" }

# 2. 创建临时测试模块
Write-Host "`n2. 创建测试模块..." -ForegroundColor Yellow
$tempModulePath = Join-Path $env:TEMP 'TestDemoModule'
New-Item -ItemType Directory -Path $tempModulePath -Force | Out-Null

# 创建清单
New-ModuleManifest `
    -Path (Join-Path $tempModulePath 'TestDemoModule.psd1') `
    -RootModule 'TestDemoModule.psm1' `
    -ModuleVersion '1.0.0' `
    -Author 'Demo' `
    -Description '演示模块'

# 创建模块文件
@'
$Script:Counter = 0

function Get-DemoCounter {
    <#
    .SYNOPSIS
        获取计数器值
    #>
    [CmdletBinding()]
    param()
    return $Script:Counter
}

function Add-DemoCounter {
    <#
    .SYNOPSIS
        增加计数器
    #>
    [CmdletBinding()]
    param(
        [int]$Value = 1
    )
    $Script:Counter += $Value
    Write-Verbose "Counter incremented by $Value. New value: $Script:Counter"
}

function Reset-DemoCounter {
    <#
    .SYNOPSIS
        重置计数器
    #>
    [CmdletBinding()]
    param()
    $Script:Counter = 0
}

Export-ModuleMember -Function 'Get-DemoCounter', 'Add-DemoCounter', 'Reset-DemoCounter'
'@ | Out-File -FilePath (Join-Path $tempModulePath 'TestDemoModule.psm1') -Encoding UTF8

Write-Host "   ✅ 测试模块已创建在: $tempModulePath" -ForegroundColor Green

# 3. 导入并测试模块
Write-Host "`n3. 导入并测试模块..." -ForegroundColor Yellow
Import-Module $tempModulePath -Force -Verbose

Write-Host "   初始计数器值: $(Get-DemoCounter)"
Add-DemoCounter -Value 5
Write-Host "   增加后计数器值: $(Get-DemoCounter)"
Add-DemoCounter -Value 3
Write-Host "   再次增加后: $(Get-DemoCounter)"
Reset-DemoCounter
Write-Host "   重置后: $(Get-DemoCounter)"

# 4. 显示模块信息
Write-Host "`n4. 模块信息:" -ForegroundColor Yellow
Get-Module -Name 'TestDemoModule' | Select-Object Name, Version, ExportedCommands

# 5. 清理
Write-Host "`n5. 清理..." -ForegroundColor Yellow
Remove-Module 'TestDemoModule' -Force
Remove-Item -Path $tempModulePath -Recurse -Force
Write-Host "   ✅ 演示完成" -ForegroundColor Green
```

---

## 7. 关键知识点总结

### 核心概念

| 概念 | 说明 |
|------|------|
| **模块类型** | Script (.psm1)、Binary (.dll)、Manifest (.psd1) |
| **模块路径** | `$env:PSModulePath` 定义的查找路径 |
| **导出控制** | `Export-ModuleMember` 控制公开成员 |
| **作用域** | Global > Script > Local，使用 `$Script:` 保持模块状态 |
| **清单文件** | 模块元数据和依赖声明 |

### 快速参考命令

```powershell
# 模块发现
Get-Module                    # 已加载模块
Get-Module -ListAvailable     # 所有可用模块
Find-Module -Name 'xxx'       # 在 Gallery 搜索

# 模块操作
Import-Module 'Name' -Force   # 导入/重新导入
Remove-Module 'Name'          # 移除
Install-Module 'Name'         # 从 Gallery 安装
Update-Module 'Name'          # 更新
Publish-Module -Path '...'    # 发布到 Gallery

# 清单操作
New-ModuleManifest -Path '...'     # 创建清单
Test-ModuleManifest -Path '...'    # 验证清单
Update-ModuleManifest -Path '...'  # 更新清单
```

### 最佳实践要点

1. **始终使用清单文件** (.psd1) 正式定义模块
2. **分离 Public/Private 函数**，使用目录组织
3. **使用 `CmdletBinding()`** 为所有公开函数添加高级功能
4. **编写完整的帮助文档**（.SYNOPSIS, .DESCRIPTION, .EXAMPLE）
5. **使用 `$Script:` 作用域** 管理模块状态
6. **遵循 SemVer** 进行版本管理
7. **编写 Pester 测试** 保证代码质量
8. **使用 `Export-ModuleMember`** 显式控制导出

### 常见问题解决

| 问题 | 解决方案 |
|------|----------|
| 模块找不到 | 检查 `$env:PSModulePath` 和目录结构 |
| 函数未导出 | 检查 `FunctionsToExport` 和 `Export-ModuleMember` |
| 导入失败 | 使用 `Import-Module -Verbose` 查看详细错误 |
| 版本冲突 | 使用 `RequiredVersion` 或 `MaximumVersion` |
| 发布失败 | 检查清单验证和 API 密钥 |

---

## 参考资源

- [官方文档 - about_Modules](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_modules)
- [官方文档 - about_Module_Manifests](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_module_manifests)
- [PowerShell Gallery](https://www.powershellgallery.com)
- [Semantic Versioning](https://semver.org)

---

*文档生成时间: 2026-02-16*  
*适用版本: PowerShell 5.1+ / PowerShell 7.x*
