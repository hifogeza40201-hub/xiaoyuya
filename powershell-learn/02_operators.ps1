# PowerShell 基础学习脚本 - 运算符
Write-Host '=== 算术运算符 ===' -ForegroundColor Yellow
$a = 10
$b = 3
"$a + $b = $($a + $b)"
"$a - $b = $($a - $b)"
"$a * $b = $($a * $b)"
"$a / $b = $($a / $b)"     # 自动转换为浮点数
"$a % $b = $($a % $b)"     # 取模
""

Write-Host '=== 比较运算符 ===' -ForegroundColor Cyan
"$a -eq $b = $($a -eq $b)"   # 等于
"$a -ne $b = $($a -ne $b)"   # 不等于
"$a -gt $b = $($a -gt $b)"   # 大于
"$a -lt $b = $($a -lt $b)"   # 小于
"$a -ge $b = $($a -ge $b)"   # 大于等于
"$a -le $b = $($a -le $b)"   # 小于等于
""

Write-Host '=== 字符串比较 ===' -ForegroundColor Green
$str = 'Hello PowerShell'
"原始字符串: $str"
"-like 通配符: '$str' -like '*Power*' = $($str -like '*Power*')"
"-match 正则: '$str' -match 'Power.*' = $($str -match 'Power.*')"
"-contains (数组): @(1,2,3) -contains 2 = $(@(1,2,3) -contains 2)"
"-in (反向): 2 -in @(1,2,3) = $(2 -in @(1,2,3))"
""

Write-Host '=== 逻辑运算符 ===' -ForegroundColor Magenta
"($a -gt 5) -and ($b -lt 5) = $(( $a -gt 5 ) -and ( $b -lt 5 ))"
"($a -lt 5) -or ($b -lt 5) = $(( $a -lt 5 ) -or ( $b -lt 5 ))"
"-not (`$true) = $(-not $true)"
"!(`$true) = $(!$true)"
""

Write-Host '=== 其他运算符 ===' -ForegroundColor Blue
# 类型运算符
$x = 100
"$x -is [int] = $($x -is [int])"
"$x -is [string] = $($x -is [string])"
"$x -as [string] = '$($x -as [string])' (类型转换)"

# 范围运算符
"1..5 = $(1..5)"
"'a'..'e' = $('a'..'e')"
