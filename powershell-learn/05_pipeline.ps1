# PowerShell 基础学习脚本 - 管道和常用命令
Write-Host '=== PowerShell 管道 (Pipeline) ===' -ForegroundColor Green
"管道将对象传递给下一个命令:"
Get-Process | Where-Object { $_.WorkingSet -gt 100MB } | Select-Object -First 3 Name, WorkingSet
""

Write-Host '=== Where-Object 过滤 ===' -ForegroundColor Cyan
"筛选进程名包含 'powershell' 的:"
Get-Process | Where-Object Name -Like '*powershell*' | Select-Object Name, Id
""

Write-Host '=== Select-Object 选择属性 ===' -ForegroundColor Yellow
"选择前3个进程的指定属性:"
Get-Process | Select-Object -First 3 Name, Id, CPU | Format-Table
""

Write-Host '=== Sort-Object 排序 ===' -ForegroundColor Magenta
"按CPU使用率排序 (Top 5):"
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU | Format-Table
""

Write-Host '=== Group-Object 分组 ===' -ForegroundColor Blue
"按进程名分组统计:"
Get-Process | Group-Object Name | Where-Object Count -gt 1 | Select-Object -First 5
""

Write-Host '=== Measure-Object 统计 ===' -ForegroundColor Red
"统计进程的内存使用:"
Get-Process | Measure-Object WorkingSet -Sum -Average -Maximum -Minimum | Select-Object Count, Sum, Average, Maximum, Minimum
""

Write-Host '=== ForEach-Object 遍历 ===' -ForegroundColor Green
"计算平方值:"
1..5 | ForEach-Object { "$_^2 = $([math]::Pow($_, 2))" }
""

Write-Host '=== Tee-Object 分支输出 ===' -ForegroundColor Cyan
"同时输出到文件和控制台:"
'line1', 'line2', 'line3' | Tee-Object -FilePath "$env:TEMP\test_output.txt"
""

Write-Host '=== 文件操作命令 ===' -ForegroundColor Yellow
# 获取当前目录
test-path . -PathType Container

# 创建测试目录
$testDir = "$env:TEMP\ps_test_$(Get-Random)"
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
"创建目录: $testDir"

# 创建测试文件
$testFile = "$testDir\test.txt"
'Sample content line 1' | Out-File -FilePath $testFile
'Another line' | Out-File -FilePath $testFile -Append
"创建文件: $testFile"

# 读取文件
"文件内容:"
Get-Content $testFile | ForEach-Object { "  > $_" }

# 清理
Remove-Item -Path $testDir -Recurse -Force
"清理完成"
