# PowerShell 基础学习脚本 - 文件和系统操作
Write-Host '=== 文件系统操作 ===' -ForegroundColor Green

# 当前位置
"当前位置: $(Get-Location)"
"当前位置: $PWD"
""

# 列出文件
Write-Host 'Get-ChildItem (dir/ls) 示例:' -ForegroundColor Cyan
"当前目录文件数: $((Get-ChildItem -File).Count)"
"最近修改的文件:"
Get-ChildItem -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name, LastWriteTime | Format-Table
""

Write-Host '=== 文件/目录操作 ===' -ForegroundColor Yellow
$testPath = "$env:TEMP\ps_ref_test"

# 创建目录
New-Item -ItemType Directory -Path $testPath -Force | Out-Null
"创建目录: $testPath"

# 创建多个文件
1..3 | ForEach-Object {
    $content = "This is file $_`nCreated at $(Get-Date)"
    Set-Content -Path "$testPath\file$_.txt" -Value $content
}
"创建测试文件完成"

# 列出文件
"目录内容:"
Get-ChildItem $testPath | Select-Object Name, Length, LastWriteTime | Format-Table

# 复制文件
Copy-Item "$testPath\file1.txt" "$testPath\file1_backup.txt" -Force
"复制 file1.txt -> file1_backup.txt"

# 重命名
Rename-Item "$testPath\file2.txt" "$testPath\renamed_file.txt" -Force
"重命名 file2.txt -> renamed_file.txt"

# 删除文件
Remove-Item "$testPath\file3.txt" -Force
"删除 file3.txt"

# 查看结果
"操作后目录内容:"
Get-ChildItem $testPath | Select-Object Name | ForEach-Object { "  - $($_.Name)" }

# 清理
Remove-Item $testPath -Recurse -Force
"清理测试目录"
""

Write-Host '=== 路径操作 ===' -ForegroundColor Magenta
$fullPath = 'C:\Windows\System32\drivers\etc\hosts'
"原始路径: $fullPath"
"Split-Path (目录): $(Split-Path $fullPath)"
"Split-Path -Leaf (文件名): $(Split-Path $fullPath -Leaf)"
"Split-Path -Extension (扩展名): $(Split-Path $fullPath -Extension)"
"Get-FileName (无扩展名): $([System.IO.Path]::GetFileNameWithoutExtension($fullPath))"
"Join-Path: $(Join-Path 'C:\temp' 'subdir\file.txt')"
"Resolve-Path: $(Resolve-Path '.')"
"Test-Path (exists): $(Test-Path 'C:\Windows')"
""

Write-Host '=== 系统信息 ===' -ForegroundColor Blue
"计算机名: $env:COMPUTERNAME"
"用户名: $env:USERNAME"
"操作系统: $env:OS"
"PowerShell版本: $($PSVersionTable.PSVersion)"
"PowerShell路径: $PSHOME"
""

Write-Host '=== 环境变量 ===' -ForegroundColor Red
"常用环境变量:"
"TEMP: $env:TEMP"
"SystemRoot: $env:SystemRoot"
"PATH (前100字符): $($env:PATH.Substring(0, [Math]::Min(100, $env:PATH.Length)))..."
""

Write-Host '=== 系统服务 ===' -ForegroundColor Green
"运行中的服务 (前5个):"
Get-Service | Where-Object Status -eq 'Running' | Select-Object -First 5 Name, DisplayName | Format-Table
