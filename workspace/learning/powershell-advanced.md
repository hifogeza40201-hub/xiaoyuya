# PowerShell 高级技术笔记

> 研究日期: 2026-02-16  
> 研究主题: PowerShell 错误处理、模块开发与 .NET 互操作

---

## 目录
1. [错误处理与异常捕获](#一错误处理与异常捕获)
2. [模块创建与发布](#二模块创建与发布)
3. [PowerShell 与 .NET 互操作](#三powershell-与-net-互操作)
4. [核心收获总结](#四核心收获总结)

---

## 一、错误处理与异常捕获

### 1.1 基础概念

PowerShell 中的错误分为两类：
- **终止错误 (Terminating Error)**: 会停止脚本执行，可以被 `try/catch` 捕获
- **非终止错误 (Non-terminating Error)**: 默认只输出到错误流，不停止执行

> 💡 **自动化任务要点**: 自动化脚本中，建议将关键操作转换为终止错误以确保异常被捕获。

### 1.2 Try/Catch/Finally 语法

```powershell
try {
    # 可能引发异常的代码
    $result = 1 / 0
}
catch [System.DivideByZeroException] {
    # 捕获特定异常类型
    Write-Host "除零错误: $_" -ForegroundColor Red
}
catch {
    # 捕获所有其他异常
    Write-Host "发生错误: $($_.Exception.Message)" -ForegroundColor Yellow
    # 访问异常对象
    Write-Host "错误类型: $($_.Exception.GetType().FullName)"
}
finally {
    # 无论是否发生异常都会执行
    # 用于清理资源（关闭文件、释放连接等）
    Write-Host "清理资源完成"
}
```

### 1.3 强制非终止错误转为终止错误

```powershell
# 方法1: 使用 -ErrorAction Stop
try {
    Get-Item -Path "C:\不存在的路径" -ErrorAction Stop
}
catch {
    Write-Host "文件未找到: $($_.Exception.Message)"
}

# 方法2: 设置全局偏好变量
$ErrorActionPreference = 'Stop'

# 方法3: 使用 Throw 主动抛出异常
function Test-Connection {
    param([string]$ComputerName)
    
    if (-not (Test-Connection -ComputerName $ComputerName -Count 1 -Quiet)) {
        throw "无法连接到 $ComputerName"
    }
    
    return "连接成功"
}
```

### 1.4 自定义异常类 (PowerShell 5.0+)

```powershell
# 定义自定义异常类
class MyAutomationException : Exception {
    [string]$ErrorCode
    
    MyAutomationException([string]$message, [string]$code) : base($message) {
        $this.ErrorCode = $code
    }
}

# 使用自定义异常
try {
    throw [MyAutomationException]::new("配置验证失败", "ERR_CONFIG_001")
}
catch [MyAutomationException] {
    Write-Host "业务错误代码: $($_.Exception.ErrorCode)"
}
```

### 1.5 错误记录与日志最佳实践

```powershell
function Invoke-AutomatedTask {
    param(
        [string]$ConfigPath,
        [string]$LogPath = ".\automation.log"
    )
    
    $ErrorLog = @()
    
    try {
        # 记录开始
        Add-Content -Path $LogPath -Value "[$(Get-Date)] 任务开始"
        
        # 加载配置
        $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    }
    catch [System.IO.FileNotFoundException] {
        $msg = "配置文件未找到: $ConfigPath"
        Add-Content -Path $LogPath -Value "[$(Get-Date)] 错误: $msg"
        throw $msg  # 重新抛出供上层处理
    }
    catch {
        $msg = "未知错误: $($_.Exception.Message)"
        Add-Content -Path $LogPath -Value "[$(Get-Date)] 错误: $msg"
        throw
    }
    finally {
        Add-Content -Path $LogPath -Value "[$(Get-Date)] 任务结束"
    }
}
```

### 1.6 作用域与错误传播

```powershell
# 函数内的错误可以传播到调用者
function Outer-Function {
    try {
        Inner-Function
    }
    catch {
        Write-Host "在 Outer 中捕获: $($_.Exception.Message)"
    }
}

function Inner-Function {
    throw "内部错误"
}

# 使用 $Error 自动变量访问最近的错误
$Error[0]  # 最新的错误
$Error[0..2]  # 最近3个错误
```

> ⚠️ **注意**: `Write-Error` 默认不会触发 `catch` 块，必须配合 `-ErrorAction Stop` 或设置 `$ErrorActionPreference = 'Stop'`。

---

## 二、模块创建与发布

### 2.1 模块结构

推荐的标准模块目录结构：

```
MyModule/
├── MyModule.psd1          # 模块清单（必需）
├── MyModule.psm1          # 根模块脚本
├── Public/                # 导出的函数
│   ├── Get-MyData.ps1
│   └── Set-MyData.ps1
├── Private/               # 内部辅助函数
│   └── Helper.ps1
├── Classes/               # 类定义（PS 5.0+）
│   └── MyClass.ps1
├── en-US/                 # 帮助文档
│   └── about_MyModule.help.txt
└── Tests/                 # Pester 测试
    └── MyModule.Tests.ps1
```

### 2.2 创建模块清单 (Module Manifest)

```powershell
# 使用 New-ModuleManifest 创建清单
New-ModuleManifest -Path ".\MyAutomationModule\MyAutomationModule.psd1" `
    -RootModule "MyAutomationModule.psm1" `
    -ModuleVersion "1.0.0" `
    -GUID (New-Guid).Guid `
    -Author "你的名字" `
    -CompanyName "你的公司" `
    -Description "自动化任务模块 - 提供文件处理和报告生成功能" `
    -PowerShellVersion "5.1" `
    -FunctionsToExport @('Get-AutomationReport', 'Invoke-AutomationTask') `
    -CmdletsToExport @() `
    -VariablesToExport @() `
    -AliasesToExport @() `
    -RequiredModules @('Pester') `
    -Tags @('Automation', 'Reporting', 'Windows') `
    -ProjectUri "https://github.com/yourname/MyAutomationModule" `
    -LicenseUri "https://opensource.org/licenses/MIT" `
    -ReleaseNotes "初始版本，包含基本报告功能"
```

### 2.3 模块脚本 (PSM1) 最佳实践

```powershell
# MyAutomationModule.psm1

# 获取模块根路径
$ModuleRoot = $PSScriptRoot

# 加载类定义（必须在函数之前）
$classFiles = Get-ChildItem -Path "$ModuleRoot\Classes" -Filter "*.ps1" -ErrorAction SilentlyContinue
foreach ($file in $classFiles) {
    . $file.FullName
}

# 加载私有函数
$privateFiles = Get-ChildItem -Path "$ModuleRoot\Private" -Filter "*.ps1" -ErrorAction SilentlyContinue
foreach ($file in $privateFiles) {
    . $file.FullName
}

# 加载并导出公共函数
$publicFiles = Get-ChildItem -Path "$ModuleRoot\Public" -Filter "*.ps1" -ErrorAction SilentlyContinue
$publicFunctions = @()
foreach ($file in $publicFiles) {
    . $file.FullName
    $publicFunctions += $file.BaseName
}

# 导出公共函数
Export-ModuleMember -Function $publicFunctions
```

### 2.4 高级函数示例 (Public/Get-AutomationReport.ps1)

```powershell
function Get-AutomationReport {
    <#
    .SYNOPSIS
        生成自动化任务执行报告
    
    .DESCRIPTION
        分析自动化日志文件并生成HTML格式的执行报告
    
    .PARAMETER LogPath
        日志文件路径
    
    .PARAMETER OutputPath
        报告输出路径
    
    .PARAMETER Format
        输出格式: HTML, CSV, JSON
    
    .EXAMPLE
        Get-AutomationReport -LogPath ".\logs" -OutputPath ".\report.html"
    
    .NOTES
        版本: 1.0
        作者: Automation Team
    #>
    [CmdletBinding()]
    [OutputType([System.IO.FileInfo])]
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [ValidateScript({Test-Path $_})]
        [string]$LogPath,
        
        [Parameter(Mandatory=$true)]
        [string]$OutputPath,
        
        [Parameter()]
        [ValidateSet('HTML', 'CSV', 'JSON')]
        [string]$Format = 'HTML'
    )
    
    begin {
        Write-Verbose "开始生成报告..."
        $logFiles = Get-ChildItem -Path $LogPath -Filter "*.log"
    }
    
    process {
        $reportData = foreach ($file in $logFiles) {
            # 解析日志内容
            $content = Get-Content $file.FullName
            [PSCustomObject]@{
                FileName = $file.Name
                EntryCount = ($content | Measure-Object).Count
                Errors = ($content | Select-String "错误|Error").Count
                SizeKB = [math]::Round($file.Length / 1KB, 2)
            }
        }
        
        # 根据格式输出
        switch ($Format) {
            'HTML' { $reportData | ConvertTo-Html | Out-File $OutputPath }
            'CSV'  { $reportData | Export-Csv $OutputPath -NoTypeInformation }
            'JSON' { $reportData | ConvertTo-Json | Out-File $OutputPath }
        }
    }
    
    end {
        Write-Verbose "报告已保存到: $OutputPath"
        Get-Item $OutputPath
    }
}
```

### 2.5 发布到 PowerShell Gallery

```powershell
# 1. 创建 API 密钥（在 PowerShell Gallery 网站上获取）
# 访问: https://www.powershellgallery.com/account/apikeys

# 2. 测试模块清单
Test-ModuleManifest -Path ".\MyAutomationModule\MyAutomationModule.psd1"

# 3. 发布模块
Publish-Module `
    -Path ".\MyAutomationModule" `
    -NuGetApiKey "你的-api-key" `
    -Repository PSGallery `
    -ReleaseNotes "修复了报告生成中的日期格式问题"

# 4. 安装已发布的模块
Install-Module -Name MyAutomationModule -Scope CurrentUser
```

### 2.6 模块版本管理

遵循语义化版本 (Semantic Versioning): `主版本.次版本.修订号`

```powershell
# 在清单中指定版本
ModuleVersion = '1.2.3'

# 预发布版本（PowerShellGet 2.0+）
PrivateData = @{
    PSData = @{
        Prerelease = 'beta1'
    }
}

# 强制安装特定版本
Install-Module MyModule -RequiredVersion 1.2.3

# 更新模块
Update-Module MyModule
```

> 💡 **自动化任务要点**: 在 CI/CD 管道中，使用 `Test-ModuleManifest` 验证模块，确保发布前清单文件完整无误。

---

## 三、PowerShell 与 .NET 互操作

### 3.1 使用 .NET 类和方法

```powershell
# 直接使用 .NET 类
$dateTime = [System.DateTime]::Now
$fileInfo = [System.IO.FileInfo]::new("C:\Windows\System32\notepad.exe")

# 访问静态属性和方法
[System.Environment]::MachineName
[System.Environment]::GetEnvironmentVariable("PATH")

# 创建 .NET 对象并调用方法
$sb = [System.Text.StringBuilder]::new()
$sb.AppendLine("第一行")
$sb.AppendLine("第二行")
$string = $sb.ToString()

# 使用 .NET 泛型集合
$list = [System.Collections.Generic.List[string]]::new()
$list.Add("Item1")
$list.AddRange(@("Item2", "Item3"))

# 字典
$dict = [System.Collections.Generic.Dictionary[string, int]]::new()
$dict.Add("Key1", 100)
$dict["Key2"] = 200
```

### 3.2 异步操作与 Task

```powershell
# 运行异步任务并等待结果
$task = [System.IO.File]::ReadAllTextAsync("C:\config.json")
$content = $task.GetAwaiter().GetResult()

# 并行执行任务（适合批量处理）
$files = Get-ChildItem -Path "C:\Logs" -Filter "*.log"
$tasks = foreach ($file in $files) {
    [System.IO.File]::ReadAllLinesAsync($file.FullName)
}

# 等待所有任务完成
$results = [System.Threading.Tasks.Task]::WhenAll($tasks).Result
```

### 3.3 使用 .NET 进行高级文件操作

```powershell
# 文件流操作 - 大文件高效处理
$streamReader = [System.IO.StreamReader]::new("C:\huge-file.log")
try {
    while ($null -ne ($line = $streamReader.ReadLine())) {
        if ($line -match "ERROR") {
            Write-Host $line -ForegroundColor Red
        }
    }
}
finally {
    $streamReader.Close()
    $streamReader.Dispose()
}

# 使用 FileSystemWatcher 监控文件变化
$watcher = [System.IO.FileSystemWatcher]::new("C:\WatchFolder")
$watcher.Filter = "*.txt"
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite

# 注册事件处理
Register-ObjectEvent -InputObject $watcher -EventName Changed -Action {
    Write-Host "文件已更改: $($Event.SourceEventArgs.FullPath)"
}

$watcher.EnableRaisingEvents = $true
```

### 3.4 PowerShell 类与 .NET 集成

```powershell
# 定义一个继承 .NET 接口的类
class LogProcessor : IDisposable {
    [string]$LogPath
    [System.IO.StreamWriter]$Writer
    
    LogProcessor([string]$path) {
        $this.LogPath = $path
        $this.Writer = [System.IO.StreamWriter]::new($path, $true)
    }
    
    [void] WriteLog([string]$message) {
        $timestamp = [DateTime]::Now.ToString("yyyy-MM-dd HH:mm:ss")
        $this.Writer.WriteLine("[$timestamp] $message")
    }
    
    [void] Dispose() {
        if ($this.Writer) {
            $this.Writer.Flush()
            $this.Writer.Close()
            $this.Writer.Dispose()
        }
    }
}

# 使用 using 确保资源释放
$processor = $null
try {
    $processor = [LogProcessor]::new("C:\app.log")
    $processor.WriteLog("应用启动")
}
finally {
    if ($processor) { $processor.Dispose() }
}
```

### 3.5 调用 Windows API (P/Invoke)

```powershell
# 使用 Add-Type 定义 P/Invoke 签名
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class WinAPI {
    [DllImport("kernel32.dll")]
    public static extern uint GetLastError();
    
    [DllImport("user32.dll")]
    public static extern bool MessageBeep(uint uType);
}
"@

# 调用 Windows API
[WinAPI]::MessageBeep(0)

# 获取 Windows 错误代码
$errorCode = [WinAPI]::GetLastError()
```

### 3.6 使用 .NET 进行网络操作

```powershell
# HTTP 请求（比 Invoke-RestMethod 更灵活）
$httpClient = [System.Net.Http.HttpClient]::new()
$httpClient.DefaultRequestHeaders.Add("Authorization", "Bearer token123")

$response = $httpClient.GetAsync("https://api.example.com/data").Result
$content = $response.Content.ReadAsStringAsync().Result
$data = $content | ConvertFrom-Json

# 发送 JSON POST 请求
$jsonBody = @{ name = "test"; value = 123 } | ConvertTo-Json
$contentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::new("application/json")
$stringContent = [System.Net.Http.StringContent]::new($jsonBody)
$stringContent.Headers.ContentType = $contentType

$postResponse = $httpClient.PostAsync("https://api.example.com/submit", $stringContent).Result
```

### 3.7 性能优化技巧

```powershell
# 使用 StringBuilder 替代字符串拼接（大量数据时）
$sb = [System.Text.StringBuilder]::new()
for ($i = 0; $i -lt 10000; $i++) {
    $sb.AppendLine("Line $i")
}
$result = $sb.ToString()

# 使用并行处理 (Parallel.ForEach)
$items = 1..100
[System.Threading.Tasks.Parallel]::ForEach($items, [Action[object]]{
    param($item)
    # 处理每个项目
    Start-Sleep -Milliseconds 10
    Write-Host "处理: $item"
})

# 内存流操作
$memoryStream = [System.IO.MemoryStream]::new()
$writer = [System.IO.StreamWriter]::new($memoryStream)
$writer.Write("数据内容")
$writer.Flush()
$memoryStream.Position = 0
$reader = [System.IO.StreamReader]::new($memoryStream)
$content = $reader.ReadToEnd()
```

> 💡 **自动化任务要点**: 
> - 处理大文件时优先使用 `StreamReader/StreamWriter` 而非 `Get-Content`
> - 批量网络请求使用 `HttpClient` 并复用连接
> - 使用 `StringBuilder` 处理大量字符串拼接操作

---

## 四、核心收获总结

> **核心收获**: PowerShell 的 `try/catch/finally` 配合 `-ErrorAction Stop` 是构建可靠自动化脚本的基础，而模块化管理与 .NET 互操作能力的结合，使 PowerShell 能够从简单的脚本工具升级为可维护、高性能的企业级自动化平台。

### 对自动化任务最关键的技术要点：

| 技术领域 | 关键实践 | 应用场景 |
|---------|---------|---------|
| 错误处理 | `try/catch/finally` + `-ErrorAction Stop` | 确保自动化任务失败时能被正确捕获和记录 |
| 模块开发 | 标准目录结构 + 清单文件 | 代码复用、团队协作、版本管理 |
| .NET 互操作 | `StreamReader/HttpClient` | 大文件处理、高性能网络请求 |
| 类定义 | 自定义异常类 | 精细化错误分类和处理 |

---

## 参考资源

- [about_Try_Catch_Finally](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_try_catch_finally)
- [PowerShell Gallery Publishing Guidelines](https://learn.microsoft.com/en-us/powershell/gallery/concepts/publishing-guidelines)
- [about_Classes](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_classes)
- [Everything about Exceptions](https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/everything-about-exceptions)
