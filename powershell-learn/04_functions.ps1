# PowerShell 基础学习脚本 - 函数
Write-Host '=== 基本函数 ===' -ForegroundColor Green

function SayHello {
    Write-Host 'Hello from PowerShell!'
}
SayHello
""

function Get-Greeting {
    param(
        [string]$Name = 'World'
    )
    return "Hello, $Name!"
}
"$(Get-Greeting -Name 'Alice')"
"$(Get-Greeting)"  # 使用默认值
""

Write-Host '=== 多参数函数 ===' -ForegroundColor Cyan
function Add-Numbers {
    param(
        [int]$a,
        [int]$b = 0
    )
    $sum = $a + $b
    return $sum
}
"Add-Numbers 5 3 = $(Add-Numbers -a 5 -b 3)"
"Add-Numbers 5 = $(Add-Numbers -a 5)"
""

Write-Host '=== 高级参数属性 ===' -ForegroundColor Yellow
function Test-AdvancedParams {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RequiredParam,
        
        [Parameter()]
        [ValidateSet('Low', 'Medium', 'High')]
        [string]$Priority = 'Medium',
        
        [Parameter()]
        [ValidateRange(1, 100)]
        [int]$Score = 50,
        
        [switch]$VerboseOutput
    )
    
    "Required: $RequiredParam"
    "Priority: $Priority"
    "Score: $Score"
    "Verbose: $($VerboseOutput.IsPresent)"
}
Test-AdvancedParams -RequiredParam 'Test' -Priority 'High' -VerboseOutput
""

Write-Host '=== 管道函数 ===' -ForegroundColor Magenta
function Convert-ToUpper {
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$InputObject
    )
    process {
        $InputObject.ToUpper()
    }
}
"管道输入转换大写:"
'hello', 'world', 'powershell' | Convert-ToUpper
""

Write-Host '=== 函数返回多个值 ===' -ForegroundColor Blue
function Get-Stats {
    param([int[]]$Numbers)
    
    $sum = ($Numbers | Measure-Object -Sum).Sum
    $avg = ($Numbers | Measure-Object -Average).Average
    $max = ($Numbers | Measure-Object -Maximum).Maximum
    $min = ($Numbers | Measure-Object -Minimum).Minimum
    
    return @{
        Sum = $sum
        Average = $avg
        Max = $max
        Min = $min
        Count = $Numbers.Count
    }
}

$stats = Get-Stats -Numbers @(10, 20, 30, 40, 50)
"统计结果:"
$stats | Format-List
