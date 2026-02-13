# PowerShell 基础学习脚本 - 变量与数据类型
Write-Host '=== 变量和数据类型 ===' -ForegroundColor Green

# 变量声明（使用 $ 前缀）
$name = 'PowerShell'
$version = 7
$pi = 3.14159
$isEnabled = $true
$items = @('apple', 'banana', 'cherry')
$hash = @{Name='John'; Age=30; City='Beijing'}

# 类型查看
"String: $name (类型: $($name.GetType().Name))"
"Int: $version (类型: $($version.GetType().Name))"
"Double: $pi (类型: $($pi.GetType().Name))"
"Bool: $isEnabled (类型: $($isEnabled.GetType().Name))"
"Array: $items (类型: $($items.GetType().Name), 元素数: $($items.Count))"
"Hashtable: $($hash.Name) from $($hash.City)"
""

# 数组操作
Write-Host '=== 数组操作 ===' -ForegroundColor Cyan
"数组索引访问: items[0] = $($items[0])"
"数组范围: items[0..1] = $($items[0..1])"
"数组添加: items += 'date' => $($items += 'date'; $items)"
"数组遍历:"
$items | ForEach-Object { "  Item: $_" }
""

# 哈希表操作
Write-Host '=== 哈希表(Hashtable) ===' -ForegroundColor Magenta
"访问键: hash['Name'] = $($hash['Name'])"
"点访问: hash.Name = $($hash.Name)"
"所有键: $($hash.Keys)"
"所有值: $($hash.Values)"
"添加键值: hash['Country'] = 'China'"
$hash['Country'] = 'China'
"现在hash: Keys = $($hash.Keys)"
