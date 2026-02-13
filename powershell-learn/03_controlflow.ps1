# PowerShell 基础学习脚本 - 流程控制
Write-Host '=== If-ElseIf-Else ===' -ForegroundColor Green
$score = 85
if ($score -ge 90) {
    "成绩: 优秀 (A)"
} elseif ($score -ge 80) {
    "成绩: 良好 (B)"
} elseif ($score -ge 70) {
    "成绩: 中等 (C)"
} else {
    "成绩: 需努力"
}
""

Write-Host '=== Switch 语句 ===' -ForegroundColor Cyan
$day = 3
switch ($day) {
    1 { "星期一"; break }
    2 { "星期二"; break }
    3 { "星期三"; break }
    4 { "星期四"; break }
    5 { "星期五"; break }
    default { "周末" }
}
""

# Switch 支持通配符和正则
$filename = "report.pdf"
switch -Wildcard ($filename) {
    "*.txt" { "文本文件" }
    "*.pdf" { "PDF文件" }
    "*.doc*" { "Word文档" }
}
""

Write-Host '=== For 循环 ===' -ForegroundColor Yellow
"for (i=1; i<=5; i++):"
for ($i = 1; $i -le 5; $i++) {
    "  i = $i"
}
""

Write-Host '=== Foreach 循环 ===' -ForegroundColor Magenta
$colors = @('Red', 'Green', 'Blue')
"遍历数组:"
foreach ($color in $colors) {
    "  Color: $color"
}
""

# Foreach-Object cmdlet (管道)
"使用管道 | ForEach-Object:"
1..3 | ForEach-Object { "  Processed: $_" }
""

Write-Host '=== While / Do-While / Do-Until ===' -ForegroundColor Blue
$count = 1
"While循环:"
while ($count -le 3) {
    "  Count: $count"
    $count++
}
""

$count = 1
"Do-While循环 (至少执行一次):"
do {
    "  Count: $count"
    $count++
} while ($count -le 0)  # 条件为假但已执行一次
""

Write-Host '=== Break / Continue ===' -ForegroundColor Red
"找到第一个偶数并退出:"
foreach ($num in 1..10) {
    if ($num % 2 -eq 0) {
        "  第一个偶数是: $num"
        break
    }
}
""

"跳过3:"
foreach ($num in 1..5) {
    if ($num -eq 3) { continue }
    "  Num: $num"
}
