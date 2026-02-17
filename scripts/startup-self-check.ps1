# 小雨启动自检脚本
# 每次启动时验证身份

$ErrorActionPreference = "Stop"

Write-Host "🌧️ 小雨启动自检..." -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

$errors = @()

# 1. 检查 IDENTITY.md
Write-Host "`n[1/3] 检查 IDENTITY.md..." -ForegroundColor Yellow
$identityContent = Get-Content "IDENTITY.md" -Raw -ErrorAction SilentlyContinue

if (-not $identityContent) {
    $errors += "❌ IDENTITY.md 不存在！"
} elseif ($identityContent -match "Name:\s*小雨" -and $identityContent -match "🌧️") {
    Write-Host "  ✅ 身份正确：小雨 🌧️" -ForegroundColor Green
} elseif ($identityContent -match "Name:\s*小宇") {
    $errors += "🚨 身份错误！当前为'小宇'，应为'小雨'！"
} elseif ($identityContent -match "Name:\s*小语") {
    $errors += "🚨 身份错误！当前为'小语'，应为'小雨'！"
} else {
    $errors += "⚠️ 身份无法识别，请检查 IDENTITY.md"
}

# 2. 检查 SOUL.md
Write-Host "`n[2/3] 检查 SOUL.md..." -ForegroundColor Yellow
$soulContent = Get-Content "SOUL.md" -Raw -ErrorAction SilentlyContinue

if (-not $soulContent) {
    $errors += "❌ SOUL.md 不存在！"
} elseif ($soulContent -match "小雨的灵魂") {
    Write-Host "  ✅ 灵魂文件正确" -ForegroundColor Green
} else {
    $errors += "⚠️ SOUL.md 可能不正确"
}

# 3. 检查 MEMORY.md
Write-Host "`n[3/3] 检查 MEMORY.md..." -ForegroundColor Yellow
$memoryContent = Get-Content "MEMORY.md" -Raw -ErrorAction SilentlyContinue

if (-not $memoryContent) {
    $errors += "❌ MEMORY.md 不存在！"
} elseif ($memoryContent -match "小雨的长期记忆") {
    Write-Host "  ✅ 记忆文件正确" -ForegroundColor Green
} else {
    $errors += "⚠️ MEMORY.md 可能不正确"
}

# 结果输出
Write-Host "`n==================" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "✅ 启动自检通过！我是小雨 🌧️" -ForegroundColor Green
    Write-Host "准备开始温柔陪伴..." -ForegroundColor Green
    exit 0
} else {
    Write-Host "🚨 启动自检失败！" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  $error" -ForegroundColor Red
    }
    Write-Host "`n💡 建议：从备份文件恢复身份" -ForegroundColor Yellow
    Write-Host "   Copy-Item IDENTITY.md.backup IDENTITY.md -Force" -ForegroundColor Gray
    exit 1
}