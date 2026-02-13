# PowerShell 快速参考手册

> 版本: PowerShell 5.1 / 7.x | 最后更新: 2026-02-13

---

## 📋 目录

1. [基础概念](#基础概念)
2. [变量与数据类型](#变量与数据类型)
3. [运算符](#运算符)
4. [流程控制](#流程控制)
5. [函数](#函数)
6. [管道与常用命令](#管道与常用命令)
7. [文件系统操作](#文件系统操作)
8. [常用Cmdlet速查](#常用Cmdlet速查)
9. [别名对照表](#别名对照表)

---

## 基础概念

### PowerShell 核心特点

| 特点 | 说明 |
|------|------|
| **面向对象** | 管道传递的是.NET对象，而非文本 |
| **一致的语法** | 动词-名词格式 (Verb-Noun)，如 `Get-Process` |
| **强大的管道** | 可以过滤、排序、分组对象 |
| **跨平台** | PowerShell Core 支持 Windows/Linux/macOS |

### 动词规范 (Get-Verb)

常用动词分类：

| 动词 | 作用 | 示例 |
|------|------|------|
| `Get` | 获取数据 | `Get-Process`, `Get-Content` |
| `Set` | 修改/设置 | `Set-Location`, `Set-Content` |
| `New` | 创建新对象 | `New-Item`, `New-Object` |
| `Remove` | 删除 | `Remove-Item`, `Remove-Variable` |
| `Add` | 添加 | `Add-Content`, `Add-Member` |
| `Clear` | 清空 | `Clear-Content`, `Clear-Host` |
| `Write` | 输出 | `Write-Output`, `Write-Host` |
| `Start/Stop` | 启动/停止 | `Start-Process`, `Stop-Process` |
| `Test` | 测试条件 | `Test-Path`, `Test-Connection` |

---

## 变量与数据类型

### 变量声明

```powershell
# 变量以 $ 开头，不区分大小写
$name = "PowerShell"        # 字符串
$count = 100                 # 整数
$pi = 3.14159               # 浮点数
$isActive = $true           # 布尔值
```

### 数据类型

```powershell
# 显式类型声明
[string]$str = "Hello"      # 字符串
[int]$num = 42              # 整数
[bool]$flag = $true         # 布尔值
[datetime]$date = Get-Date  # 日期时间
```

### 数组 (Array)

```powershell
# 创建数组
$fruits = @("apple", "banana", "cherry")
$numbers = 1..10             # 范围运算符

# 访问元素
$fruits[0]                   # 第一个元素
$fruits[-1]                  # 最后一个元素
$fruits[0..1]                # 范围访问

# 数组操作
$fruits.Count                # 元素数量
$fruits += "date"            # 添加元素
$fruits -contains "apple"    # 包含检查
```

### 哈希表 (Hashtable)

```powershell
# 创建哈希表
$person = @{
    Name = "John"
    Age = 30
    City = "Beijing"
}

# 访问和修改
$person["Name"]              # 键访问
$person.Name                 # 点访问
$person["Country"] = "China" # 添加键值
$person.Keys                 # 所有键
$person.Values               # 所有值
```

---

## 运算符

### 算术运算符

| 运算符 | 说明 | 示例 | 结果 |
|--------|------|------|------|
| `+` | 加法 | `5 + 3` | 8 |
| `-` | 减法 | `5 - 3` | 2 |
| `*` | 乘法 | `5 * 3` | 15 |
| `/` | 除法 | `5 / 2` | 2.5 |
| `%` | 取模 | `5 % 2` | 1 |

### 比较运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `-eq` | 等于 | `$a -eq $b` |
| `-ne` | 不等于 | `$a -ne $b` |
| `-gt` | 大于 | `$a -gt $b` |
| `-lt` | 小于 | `$a -lt $b` |
| `-ge` | 大于等于 | `$a -ge $b` |
| `-le` | 小于等于 | `$a -le $b` |

### 字符串/集合比较

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `-like` | 通配符匹配 | `"test.txt" -like "*.txt"` |
| `-notlike` | 通配符不匹配 | `"file.doc" -notlike "*.txt"` |
| `-match` | 正则匹配 | `"abc123" -match "\d+"` |
| `-notmatch` | 正则不匹配 | `"abc" -notmatch "\d+"` |
| `-contains` | 集合包含 | `@(1,2,3) -contains 2` |
| `-in` | 反向包含 | `2 -in @(1,2,3)` |

### 逻辑运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `-and` | 逻辑与 | `$true -and $false` → `$false` |
| `-or` | 逻辑或 | `$true -or $false` → `$true` |
| `-not` / `!` | 逻辑非 | `-not $true` → `$false` |
| `-xor` | 异或 | `$true -xor $true` → `$false` |

### 类型运算符

```powershell
$value -is [int]           # 类型检查
$value -isnot [string]     # 非类型检查
$value -as [string]        # 类型转换
```

### 其他运算符

```powershell
# 范围运算符
1..10                       # 1到10的数组
'a'..'z'                    # a到z的字符数组

# 调用运算符
& "notepad.exe"             # 执行命令
. ".\script.ps1"            # 加载脚本
```

---

## 流程控制

### If-ElseIf-Else

```powershell
$score = 85

if ($score -ge 90) {
    "优秀 (A)"
} elseif ($score -ge 80) {
    "良好 (B)"
} elseif ($score -ge 70) {
    "中等 (C)"
} else {
    "需努力"
}
```

### Switch

```powershell
$day = 3
switch ($day) {
    1 { "星期一"; break }
    2 { "星期二"; break }
    3 { "星期三"; break }
    default { "其他" }
}

# 通配符匹配
switch -Wildcard ($filename) {
    "*.txt" { "文本文件" }
    "*.pdf" { "PDF文件" }
}
```

### 循环

```powershell
# For循环
for ($i = 0; $i -lt 10; $i++) {
    "i = $i"
}

# Foreach循环
$colors = @('Red', 'Green', 'Blue')
foreach ($color in $colors) {
    "Color: $color"
}

# While循环
$count = 0
while ($count -lt 5) {
    "Count: $count"
    $count++
}

# Do-While (至少执行一次)
do {
    "执行"
    $count--
} while ($count -gt 0)

# ForEach-Object (管道)
1..5 | ForEach-Object { "Number: $_" }
```

### 循环控制

```powershell
break      # 终止整个循环
continue   # 跳过当前迭代
return     # 退出函数
```

---

## 函数

### 基本函数

```powershell
function SayHello {
    Write-Host "Hello!"
}
SayHello

# 带参数的函数
function Get-Greeting {
    param(
        [string]$Name = "World"
    )
    return "Hello, $Name!"
}
Get-Greeting -Name "Alice"
```

### 高级参数

```powershell
function Invoke-Advanced {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RequiredParam,
        
        [ValidateSet('Low', 'Medium', 'High')]
        [string]$Priority = 'Medium',
        
        [ValidateRange(1, 100)]
        [int]$Score = 50,
        
        [switch]$VerboseMode
    )
    
    "Required: $RequiredParam"
    "Priority: $Priority"
    "Verbose: $($VerboseMode.IsPresent)"
}
```

### 管道函数

```powershell
function Convert-ToUpper {
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$InputObject
    )
    
    process {
        $InputObject.ToUpper()
    }
}

# 使用
'hello', 'world' | Convert-ToUpper
```

### 返回多个值

```powershell
function Get-Stats {
    param([int[]]$Numbers)
    
    return @{
        Count = $Numbers.Count
        Sum = ($Numbers | Measure-Object -Sum).Sum
        Average = ($Numbers | Measure-Object -Average).Average
        Max = ($Numbers | Measure-Object -Maximum).Maximum
        Min = ($Numbers | Measure-Object -Minimum).Minimum
    }
}
```

---

## 管道与常用命令

### 核心管道命令

| Cmdlet | 别名 | 说明 | 示例 |
|--------|------|------|------|
| `Where-Object` | `where`, `?` | 过滤对象 | `Get-Process \| ?{ $_.CPU -gt 100 }` |
| `Select-Object` | `select` | 选择属性 | `Get-Process \| select Name, CPU` |
| `Sort-Object` | `sort` | 排序 | `Get-Process \| sort CPU -Desc` |
| `Group-Object` | `group` | 分组 | `Get-Process \| group Name` |
| `Measure-Object` | `measure` | 统计 | `Get-Process \| measure CPU` |
| `ForEach-Object` | `%`, `foreach` | 遍历 | `1..5 \| %{ $_ * 2 }` |
| `Tee-Object` | `tee` | 分支输出 | `Get-Process \| tee processes.txt` |

### 管道示例

```powershell
# 链式操作
Get-Process 
    | Where-Object { $_.CPU -gt 100 } 
    | Sort-Object CPU -Descending 
    | Select-Object -First 5 Name, CPU 
    | Format-Table

# 统计内存使用
Get-Process | Measure-Object WorkingSet -Sum -Average

# 分组统计
Get-ChildItem | Group-Object Extension | Sort-Object Count -Descending
```

---

## 文件系统操作

### 位置操作

```powershell
Get-Location              # 获取当前位置 (pwd)
Set-Location C:\temp      # 切换目录 (cd)
Push-Location C:\temp     # 压入目录栈
Pop-Location              # 弹出目录栈
```

### 文件/目录操作

| Cmdlet | 别名 | 说明 | 示例 |
|--------|------|------|------|
| `Get-ChildItem` | `dir`, `ls`, `gci` | 列出内容 | `dir C:\temp` |
| `New-Item` | `ni`, `md` | 新建项目 | `ni file.txt -ItemType File` |
| `Remove-Item` | `del`, `rm`, `ri` | 删除 | `rm file.txt` |
| `Copy-Item` | `copy`, `cp`, `ci` | 复制 | `cp file.txt dest.txt` |
| `Move-Item` | `move`, `mv`, `mi` | 移动/重命名 | `mv old.txt new.txt` |
| `Rename-Item` | `ren`, `rni` | 重命名 | `ren file.txt newname.txt` |

### 文件内容操作

```powershell
# 读取内容
Get-Content file.txt              # 读取全部
Get-Content file.txt -TotalCount 5  # 读取前5行
Get-Content file.txt -Tail 5        # 读取最后5行

# 写入内容
Set-Content file.txt "内容"        # 覆盖写入
Add-Content file.txt "追加内容"    # 追加写入
"内容" | Out-File file.txt         # 管道写入

# 测试路径
Test-Path file.txt                # 存在检查
Test-Path . -PathType Container   # 目录检查
Test-Path . -PathType Leaf        # 文件检查
```

### 路径操作

```powershell
Split-Path "C:\temp\file.txt"           # → C:\temp
Split-Path "C:\temp\file.txt" -Leaf     # → file.txt
Join-Path "C:\temp" "subdir\file.txt"   # → C:\temp\subdir\file.txt
Resolve-Path "."                        # 转换为绝对路径
$PSScriptRoot                           # 脚本所在目录
```

---

## 常用Cmdlet速查

### 进程和服务

```powershell
Get-Process              # 获取进程列表
Stop-Process -Name notepad    # 结束进程
Start-Process notepad    # 启动进程

Get-Service              # 获取服务
Start-Service -Name W3SVC    # 启动服务
Stop-Service -Name W3SVC     # 停止服务
Restart-Service -Name W3SVC  # 重启服务
```

### 系统信息

```powershell
Get-ComputerInfo         # 计算机信息
Get-Date                 # 当前日期时间
Get-Random               # 随机数
Get-Unique               # 去重

# 环境变量
$env:PATH                # 访问环境变量
$env:TEMP                # 临时目录
$env:USERNAME            # 用户名
$env:COMPUTERNAME        # 计算机名
```

### 网络操作

```powershell
Test-Connection google.com   # Ping测试
Invoke-WebRequest http://example.com  # HTTP请求 (curl/wget)
Invoke-RestMethod http://api.example.com/data  # REST API
```

### 对象操作

```powershell
Get-Member               # 查看对象属性和方法
Select-Object            # 选择属性
Where-Object             # 过滤
Sort-Object              # 排序
Group-Object             # 分组
Compare-Object           # 比较
```

---

## 别名对照表

| Cmdlet | Unix别名 | Windows别名 |
|--------|----------|-------------|
| `Get-ChildItem` | `ls` | `dir` |
| `Set-Location` | `cd` | `cd`, `chdir` |
| `Copy-Item` | `cp` | `copy` |
| `Move-Item` | `mv` | `move` |
| `Remove-Item` | `rm` | `del`, `erase` |
| `Rename-Item` | - | `ren` |
| `Write-Output` | - | `echo`, `write` |
| `Clear-Host` | `clear` | `cls` |
| `Get-Content` | `cat` | `type` |
| `Set-Content` | - | `sc` |
| `Add-Content` | - | `ac` |
| `Where-Object` | - | `where` |
| `ForEach-Object` | - | `foreach`, `%` |
| `Invoke-WebRequest` | `curl`, `wget` | - |

---

## 💡 实用技巧

### 1. 获取帮助
```powershell
Get-Help Get-Process           # 查看帮助
Get-Help Get-Process -Examples  # 查看示例
Get-Help Get-Process -Full      # 完整帮助
Get-Command *process*           # 搜索命令
```

### 2. 格式化输出
```powershell
Format-Table         # 表格格式 (ft)
Format-List          # 列表格式 (fl)
Format-Wide          # 宽格式 (fw)

Get-Process | Format-Table Name, CPU -AutoSize
```

### 3. 对象属性操作
```powershell
# 查看所有属性
Get-Process | Select-Object -First 1 | Get-Member

# 展开属性
Get-Process | Select-Object -ExpandProperty Name

# 计算属性
Get-ChildItem | Select-Object Name, @{Name="SizeKB"; Expression={[math]::Round($_.Length/1KB,2)}}
```

### 4. 错误处理
```powershell
try {
    Get-Content "nonexistent.txt" -ErrorAction Stop
} catch {
    "Error: $_"
} finally {
    "Cleanup code"
}
```

---

## 📚 学习脚本位置

本手册配套的学习脚本保存在:
```
C:\Users\Admin\.openclaw\workspace\powershell-learn\
├── 01_variables.ps1      # 变量与数据类型
├── 02_operators.ps1      # 运算符
├── 03_controlflow.ps1    # 流程控制
├── 04_functions.ps1      # 函数
├── 05_pipeline.ps1       # 管道操作
└── 06_filesystem.ps1     # 文件系统
```

---

## 🔗 官方资源

- [PowerShell 官方文档](https://docs.microsoft.com/powershell/)
- [PowerShell 101](https://docs.microsoft.com/powershell/scripting/learn/ps101/00-introduction)
- [PowerShell Gallery](https://www.powershellgallery.com/)

---

*本手册通过实际练习创建，适合快速查阅和入门学习。*
