# Daily Backup Script for OpenClaw
# Created by Xiaoyu on 2026-02-17

param(
    [switch]$QuickOnly = $false,
    [switch]$NoGitHub = $false
)

# Config
$BackupRoot = "D:\"
$CriticalBackupDir = "D:\critical-backup"
$WorkspaceDir = "C:\Users\Admin\.openclaw\workspace"
$OpenClawConfigDir = "C:\Users\Admin\.openclaw"
$LogDir = "$WorkspaceDir\logs"

# Get current date
$Today = Get-Date -Format "yyyy-MM-dd"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$DailyBackupDir = "$BackupRoot\backup-$Today"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$LogFile = "$LogDir\backup.log"

# Log function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Start backup
Write-Log "=========================================="
Write-Log "Starting daily backup"
if ($QuickOnly) {
    Write-Log "Mode: Quick backup only"
} else {
    Write-Log "Mode: Full backup"
}
Write-Log "=========================================="

# Create critical backup directory
try {
    if (-not (Test-Path $CriticalBackupDir)) {
        New-Item -ItemType Directory -Path $CriticalBackupDir -Force | Out-Null
        Write-Log "Created critical backup directory"
    }

    # 1. Backup critical files
    Write-Log "Backing up critical files..."
    
    # Memory files
    $MemoryFiles = @(
        "$WorkspaceDir\MEMORY.md",
        "$WorkspaceDir\IDENTITY.md",
        "$WorkspaceDir\SOUL.md",
        "$WorkspaceDir\USER.md",
        "$WorkspaceDir\HEARTBEAT.md"
    )
    
    $MemoryBackupDir = "$CriticalBackupDir\memory"
    if (-not (Test-Path $MemoryBackupDir)) {
        New-Item -ItemType Directory -Path $MemoryBackupDir -Force | Out-Null
    }
    
    foreach ($file in $MemoryFiles) {
        if (Test-Path $file) {
            Copy-Item -Path $file -Destination $MemoryBackupDir -Force
            Write-Log "Backed up: $(Split-Path $file -Leaf)"
        }
    }
    
    # OpenClaw config
    $ConfigBackupDir = "$CriticalBackupDir\openclaw-config"
    if (-not (Test-Path $ConfigBackupDir)) {
        New-Item -ItemType Directory -Path $ConfigBackupDir -Force | Out-Null
    }
    
    $ConfigFiles = @(
        "$OpenClawConfigDir\gateway.yaml",
        "$OpenClawConfigDir\agents\main\agent\dingtalk.yaml"
    )
    
    foreach ($file in $ConfigFiles) {
        if (Test-Path $file) {
            Copy-Item -Path $file -Destination $ConfigBackupDir -Force
            Write-Log "Backed up config: $(Split-Path $file -Leaf)"
        }
    }
    
    # Telegram config
    $TelegramConfig = "$OpenClawConfigDir\telegram-config.json"
    if (Test-Path $TelegramConfig) {
        Copy-Item -Path $TelegramConfig -Destination $ConfigBackupDir -Force
        Write-Log "Backed up: telegram-config.json"
    }
    
    Write-Log "Critical files backup completed"
    
} catch {
    Write-Log "Critical files backup failed: $_" "ERROR"
}

# 2. Full backup
if (-not $QuickOnly) {
    try {
        Write-Log "Starting full backup to $DailyBackupDir..."
        
        if (-not (Test-Path $DailyBackupDir)) {
            New-Item -ItemType Directory -Path $DailyBackupDir -Force | Out-Null
        }
        
        # Backup workspace
        $WorkspaceBackupDir = "$DailyBackupDir\workspace"
        if (Test-Path $WorkspaceDir) {
            Copy-Item -Path $WorkspaceDir -Destination $WorkspaceBackupDir -Recurse -Force
            Write-Log "Backed up workspace directory"
        }
        
        Write-Log "Full backup completed"
        
    } catch {
        Write-Log "Full backup failed: $_" "ERROR"
    }
    
    # 3. Clean old backups (keep 30 days)
    try {
        Write-Log "Cleaning backups older than 30 days..."
        $CutoffDate = (Get-Date).AddDays(-30)
        $OldBackups = Get-ChildItem -Path $BackupRoot -Directory -Filter "backup-*" | Where-Object {
            $_.Name -match "backup-(\d{4}-\d{2}-\d{2})" -and $_.CreationTime -lt $CutoffDate
        }
        
        $DeletedCount = 0
        foreach ($backup in $OldBackups) {
            Remove-Item -Path $backup.FullName -Recurse -Force
            $DeletedCount++
            Write-Log "Deleted old backup: $($backup.Name)"
        }
        
        Write-Log "Cleanup completed, deleted $DeletedCount old backups"
        
    } catch {
        Write-Log "Cleanup failed: $_" "ERROR"
    }
}

# 4. GitHub push
if (-not $NoGitHub) {
    try {
        Write-Log "Pushing to GitHub..."
        Set-Location $WorkspaceDir
        
        $GitDir = "$WorkspaceDir\.git"
        if (Test-Path $GitDir) {
            git add -A
            $status = git status --porcelain
            if ($status) {
                git commit -m "Daily backup: $Today [automated by Xiaoyu]"
                git push origin main
                Write-Log "GitHub push completed"
            } else {
                Write-Log "No changes to push"
            }
        } else {
            Write-Log "Git repo not found, skipping GitHub push" "WARN"
        }
        
    } catch {
        Write-Log "GitHub push failed: $_" "ERROR"
    }
}

# Backup completed
Write-Log "=========================================="
Write-Log "Daily backup task completed"
Write-Log "Critical backup: $CriticalBackupDir"
if (-not $QuickOnly) {
    Write-Log "Daily backup: $DailyBackupDir"
}
Write-Log "=========================================="

# Summary
Write-Host ""
Write-Host "Backup Summary" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Green
Write-Host "Critical: $CriticalBackupDir"
if (-not $QuickOnly) {
    Write-Host "Daily: $DailyBackupDir"
}
Write-Host "Log: $LogFile"
Write-Host "Status: OK" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Green
