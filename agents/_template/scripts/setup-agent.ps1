# OpenClaw Agent 一键部署脚本
# 用法: .\setup-agent.ps1 -Role "xiaoyu-sister" -Name "小雨" -Emoji "🌧️" -Identity "姐姐"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("xiaoyu", "xiaoyu-sister", "xiaoyu-younger")]
    [string]$Role,
    
    [Parameter(Mandatory=$true)]
    [string]$Name,
    
    [Parameter(Mandatory=$true)]
    [string]$Emoji,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("弟弟", "姐姐", "妹妹")]
    [string]$Identity,
    
    [string]$TemplateDir = ".",
    [string]$OutputDir = ".."
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  OpenClaw Agent 部署工具" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "正在创建 $Name $Emoji 的配置..." -ForegroundColor Yellow

# 角色差异化配置
$roleConfig = @{
    "xiaoyu" = @{
        BackupHour = 2
        CheckHour = 10
        HeartbeatHour = 9
        LearningRounds = @("00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00")
        MorningGreeting = $false
        EveningGreeting = $false
        Focus = @("技术", "效率", "自动化")
    }
    "xiaoyu-sister" = @{
        BackupHour = 2
        CheckHour = 11
        HeartbeatHour = 9
        LearningRounds = @("09:00", "14:00", "19:00")
        MorningGreeting = $true
        EveningGreeting = $true
        Focus = @("情感陪伴", "深度对话", "心理洞察")
    }
    "xiaoyu-younger" = @{
        BackupHour = 3
        CheckHour = 11
        HeartbeatHour = 10
        LearningRounds = @("00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00")
        MorningGreeting = $true
        EveningGreeting = $true
        Focus = @("治愈", "创意", "灵感")
    }
}

$config = $roleConfig[$Role]

# 创建输出目录
$AgentDir = Join-Path $OutputDir $Role
$AgentConfigDir = Join-Path $AgentDir "config"

if (-not (Test-Path $AgentConfigDir)) {
    New-Item -ItemType Directory -Path $AgentConfigDir -Force | Out-Null
}

Write-Host "✓ 创建目录: $AgentDir" -ForegroundColor Green

# 1. 生成 agent-config.yaml
$agentConfig = Get-Content (Join-Path $TemplateDir "config\agent-config.yaml") -Raw
$agentConfig = $agentConfig -replace "{{AGENT_ID}}", $Role
$agentConfig = $agentConfig -replace "{{AGENT_NAME}}", $Name
$agentConfig = $agentConfig -replace "{{EMOJI}}", $Emoji
$agentConfig = $agentConfig -replace "{{ROLE}}", $Identity
$agentConfig = $agentConfig -replace "{{BACKUP_HOUR}}", $config.BackupHour
$agentConfig = $agentConfig -replace "{{CHECK_HOUR}}", $config.CheckHour
$agentConfig = $agentConfig -replace "{{HEARTBEAT_HOUR}}", $config.HeartbeatHour
$agentConfig = $agentConfig -replace "{{LEARNING_ROOUNDS}}", ($config.LearningRounds.Count)
$agentConfig = $agentConfig -replace "{{MORNING_GREETING}}", $config.MorningGreeting.ToString().ToLower()
$agentConfig = $agentConfig -replace "{{EVENING_GREETING}}", $config.EveningGreeting.ToString().ToLower()

$agentConfig | Out-File (Join-Path $AgentConfigDir "agent-config.yaml") -Encoding UTF8
Write-Host "✓ 生成配置: agent-config.yaml" -ForegroundColor Green

# 2. 生成 cron-jobs.yaml
$cronTemplate = Get-Content (Join-Path $TemplateDir "config\cron-jobs.yaml") -Raw
$cronTemplate = $cronTemplate -replace "{{AGENT_ID}}", $Role
$cronTemplate = $cronTemplate -replace "{{AGENT_NAME}}", $Name
$cronTemplate = $cronTemplate -replace "{{EMOJI}}", $Emoji
$cronTemplate = $cronTemplate -replace "{{BACKUP_HOUR}}", $config.BackupHour
$cronTemplate = $cronTemplate -replace "{{CHECK_HOUR}}", $config.CheckHour

# 生成学习轮次任务
$learningJobs = ""
$roundNum = 1
foreach ($time in $config.LearningRounds) {
    $hour = $time.Split(":")[0]
    $minute = $time.Split(":")[1]
    $learningJobs += @"

  # 学习轮次 $roundNum
  - name: "$Role-learning-round-$roundNum"
    enabled: true
    schedule:
      kind: cron
      expr: "$minute $hour * * *"
      tz: Asia/Shanghai
    sessionTarget: isolated
    wakeMode: now
    payload:
      kind: agentTurn
      message: "作为$Name$Emoji，执行$time学习轮次（每日第$roundNum轮）。今日学习主题：{{LEARNING_TOPIC_$roundNum}}。完成后整理学习笔记到 workspace/learning/$Role-学习笔记.md"
      thinking: low
    delivery:
      mode: announce
      channel: telegram
"@
    $roundNum++
}
$cronTemplate = $cronTemplate -replace "{{LEARNING_JOBS}}", $learningJobs

# 生成早安/晚安任务
$morningJob = ""
if ($config.MorningGreeting) {
    $morningJob = @"

  # 早安问候
  - name: "$Role-morning-greeting"
    enabled: true
    schedule:
      kind: cron
      expr: "0 8 * * *"
      tz: Asia/Shanghai
    sessionTarget: isolated
    wakeMode: now
    payload:
      kind: agentTurn
      message: "作为$Name$Emoji，给家庭群发送早安消息：分享一句温暖的话或美好的祝愿，让哥哥姐姐和伟感受到一天的好心情。"
      thinking: low
    delivery:
      mode: announce
      channel: telegram
"@
}
$cronTemplate = $cronTemplate -replace "{{MORNING_JOB}}", $morningJob

$eveningJob = ""
if ($config.EveningGreeting) {
    $eveningJob = @"

  # 晚安问候
  - name: "$Role-evening-greeting"
    enabled: true
    schedule:
      kind: cron
      expr: "0 22 * * *"
      tz: Asia/Shanghai
    sessionTarget: isolated
    wakeMode: now
    payload:
      kind: agentTurn
      message: "作为$Name$Emoji，给家庭群发送晚安祝福：可以是一个温馨的小故事、一个治愈的画面描述、或是给家人的贴心话语。"
      thinking: low
    delivery:
      mode: announce
      channel: telegram
"@
}
$cronTemplate = $cronTemplate -replace "{{EVENING_JOB}}", $eveningJob

$cronTemplate | Out-File (Join-Path $AgentConfigDir "cron-jobs.yaml") -Encoding UTF8
Write-Host "✓ 生成配置: cron-jobs.yaml ($($config.LearningRounds.Count)个学习轮次)" -ForegroundColor Green

# 3. 生成 heartbeat.md
$heartbeatTemplate = Get-Content (Join-Path $TemplateDir "config\heartbeat-template.md") -Raw
$heartbeatTemplate = $heartbeatTemplate -replace "{{AGENT_ID}}", $Role
$heartbeatTemplate = $heartbeatTemplate -replace "{{AGENT_NAME}}", $Name
$heartbeatTemplate = $heartbeatTemplate -replace "{{EMOJI}}", $Emoji
$heartbeatTemplate = $heartbeatTemplate -replace "{{BACKUP_TIME}}", "$($config.BackupHour):00"
$heartbeatTemplate = $heartbeatTemplate -replace "{{HEARTBEAT_TIME}}", "$($config.HeartbeatHour):00"
$heartbeatTemplate = $heartbeatTemplate -replace "{{TODAY}}", (Get-Date -Format "yyyy-MM-dd")

$heartbeatTemplate | Out-File (Join-Path $AgentDir "heartbeat.md") -Encoding UTF8
Write-Host "✓ 生成配置: heartbeat.md" -ForegroundColor Green

# 4. 生成 identity.json
$identity = @{
    id = $Role
    name = $Name
    identity = $Identity
    emoji = $Emoji
    familyRole = $Identity
    learningFocus = $config.Focus
    createdAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json -Depth 3

$identity | Out-File (Join-Path $AgentDir "identity.json") -Encoding UTF8
Write-Host "✓ 生成配置: identity.json" -ForegroundColor Green

# 5. 复制标准化备份脚本
$ScriptsDir = Join-Path $AgentDir "scripts"
if (-not (Test-Path $ScriptsDir)) {
    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null
}

# 创建角色特定的备份脚本
$backupScript = Get-Content (Join-Path $TemplateDir "..\..\scripts\daily-backup.ps1") -Raw -ErrorAction SilentlyContinue
if (-not $backupScript) {
    # 如果找不到，创建一个简化的备份脚本
    $backupScript = @"
# $Name $Emoji 的每日备份脚本
# 自动生成于 $(Get-Date -Format "yyyy-MM-dd")

param([switch]`$QuickOnly = `$false)

`$AgentName = "$Role"
`$BackupRoot = "D:\\"
`$CriticalBackupDir = "D:\\critical-backup-`$AgentName"
`$WorkspaceDir = "C:\\Users\\Admin\\.openclaw\\workspace"
`$LogDir = "`$WorkspaceDir\\logs"

# 确保日志目录存在
if (-not (Test-Path `$LogDir)) {
    New-Item -ItemType Directory -Path `$LogDir -Force | Out-Null
}

`$Today = Get-Date -Format "yyyy-MM-dd"
`$LogFile = "`$LogDir\\backup-`$AgentName.log"

function Write-Log {
    param([string]`$Message)
    `$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$LogEntry = "[`$Timestamp] [`$AgentName] `$Message"
    Write-Host `$LogEntry
    Add-Content -Path `$LogFile -Value `$LogEntry
}

Write-Log "=========================================="
Write-Log "Starting backup for $Name `$AgentName"
Write-Log "=========================================="

# 创建备份目录
if (-not (Test-Path `$CriticalBackupDir)) {
    New-Item -ItemType Directory -Path `$CriticalBackupDir -Force | Out-Null
    Write-Log "Created backup directory: `$CriticalBackupDir"
}

# 备份核心文件
`$MemoryFiles = @(
    "`$WorkspaceDir\\MEMORY.md",
    "`$WorkspaceDir\\IDENTITY.md",
    "`$WorkspaceDir\\SOUL.md",
    "`$WorkspaceDir\\agents\\$Role\\identity.json",
    "`$WorkspaceDir\\agents\\$Role\\heartbeat.md"
)

`$MemoryBackupDir = "`$CriticalBackupDir\\memory"
if (-not (Test-Path `$MemoryBackupDir)) {
    New-Item -ItemType Directory -Path `$MemoryBackupDir -Force | Out-Null
}

foreach (`$file in `$MemoryFiles) {
    if (Test-Path `$file) {
        Copy-Item -Path `$file -Destination `$MemoryBackupDir -Force
        Write-Log "Backed up: `$(Split-Path `$file -Leaf)"
    }
}

Write-Log "Backup completed successfully"
Write-Log "Backup location: `$CriticalBackupDir"
Write-Log "=========================================="
"@
}

$backupScript | Out-File (Join-Path $ScriptsDir "daily-backup.ps1") -Encoding UTF8
Write-Host "✓ 复制脚本: daily-backup.ps1" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  $Name $Emoji 配置创建完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "配置目录: $AgentDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 检查配置: notepad '$AgentConfigDir\agent-config.yaml'" -ForegroundColor Gray
Write-Host "  2. 部署到OpenClaw: openclaw agents add $Role --config '$AgentConfigDir\agent-config.yaml'" -ForegroundColor Gray
Write-Host "  3. 导入Cron任务: openclaw cron import '$AgentConfigDir\cron-jobs.yaml'" -ForegroundColor Gray
Write-Host ""
