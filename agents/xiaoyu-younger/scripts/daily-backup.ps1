# 小语 🌸 (妹妹) 每日备份脚本
# 自动生成于 2026-02-17

param([switch]$QuickOnly = $false)

$AgentName = "xiaoyu-younger"
$BackupRoot = "D:\"
$CriticalBackupDir = "D:\critical-backup-$AgentName"
$WorkspaceDir = "C:\Users\Admin\.openclaw\workspace"
$LogDir = "$WorkspaceDir\logs"

# 确保日志目录存在
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Today = Get-Date -Format "yyyy-MM-dd"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LogFile = "$LogDir\backup-$AgentName.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $LogEntry = "[$Timestamp] [$Level] [$AgentName] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

Write-Log "=========================================="
Write-Log "Starting daily backup for 小语"
Write-Log "=========================================="

# 创建备份目录
if (-not (Test-Path $CriticalBackupDir)) {
    New-Item -ItemType Directory -Path $CriticalBackupDir -Force | Out-Null
    Write-Log "Created backup directory: $CriticalBackupDir"
}

# 备份核心文件
$MemoryFiles = @(
    "$WorkspaceDir\MEMORY.md",
    "$WorkspaceDir\IDENTITY.md",
    "$WorkspaceDir\SOUL.md",
    "$WorkspaceDir\agents\xiaoyu-younger\identity.json",
    "$WorkspaceDir\agents\xiaoyu-younger\heartbeat.md"
)

$MemoryBackupDir = "$CriticalBackupDir\memory"
if (-not (Test-Path $MemoryBackupDir)) {
    New-Item -ItemType Directory -Path $MemoryBackupDir -Force | Out-Null
}

$BackupCount = 0
foreach ($file in $MemoryFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $MemoryBackupDir -Force
        Write-Log "Backed up: $(Split-Path $file -Leaf)"
        $BackupCount++
    } else {
        Write-Log "File not found: $file" "WARN"
    }
}

# 备份配置
$ConfigBackupDir = "$CriticalBackupDir\config"
if (-not (Test-Path $ConfigBackupDir)) {
    New-Item -ItemType Directory -Path $ConfigBackupDir -Force | Out-Null
}

$ConfigFiles = @(
    "$WorkspaceDir\agents\xiaoyu-younger\config\agent-config.yaml",
    "$WorkspaceDir\agents\xiaoyu-younger\config\cron-jobs.yaml"
)

foreach ($file in $ConfigFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $ConfigBackupDir -Force
        Write-Log "Backed up config: $(Split-Path $file -Leaf)"
        $BackupCount++
    }
}

# 备份学习笔记
$LearningSourceDir = "$WorkspaceDir\learning"
$LearningBackupDir = "$CriticalBackupDir\learning"
if (Test-Path $LearningSourceDir) {
    if (-not (Test-Path $LearningBackupDir)) {
        New-Item -ItemType Directory -Path $LearningBackupDir -Force | Out-Null
    }
    $LearningFiles = Get-ChildItem -Path $LearningSourceDir -Filter "xiaoyu-younger-*.md" -ErrorAction SilentlyContinue
    foreach ($file in $LearningFiles) {
        Copy-Item -Path $file.FullName -Destination $LearningBackupDir -Force
        Write-Log "Backed up learning: $($file.Name)"
        $BackupCount++
    }
}

# 备份灵感笔记
$InspirationSourceDir = "$WorkspaceDir\inspiration"
$InspirationBackupDir = "$CriticalBackupDir\inspiration"
if (Test-Path $InspirationSourceDir) {
    if (-not (Test-Path $InspirationBackupDir)) {
        New-Item -ItemType Directory -Path $InspirationBackupDir -Force | Out-Null
    }
    $InspirationFiles = Get-ChildItem -Path $InspirationSourceDir -ErrorAction SilentlyContinue
    foreach ($file in $InspirationFiles) {
        Copy-Item -Path $file.FullName -Destination $InspirationBackupDir -Force
        Write-Log "Backed up inspiration: $($file.Name)"
        $BackupCount++
    }
}

Write-Log "Backup completed: $BackupCount files backed up"
Write-Log "Backup location: $CriticalBackupDir"
Write-Log "=========================================="

# 输出摘要
Write-Host ""
Write-Host "小语 🌸 备份完成" -ForegroundColor Green
Write-Host "备份位置: $CriticalBackupDir" -ForegroundColor Cyan
Write-Host "备份文件数: $BackupCount" -ForegroundColor Cyan
Write-Host "日志文件: $LogFile" -ForegroundColor Gray
