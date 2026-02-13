---
name: github-shared-memory
description: 创建和管理GitHub共享仓库，实现AI代理（小雨/小宇）之间的记忆备份、双向通信和知识共享。使用场景：(1) 初始化共享仓库架构 (2) 配置GitHub API自动化 (3) 设置分支策略和权限管理 (4) 实现记忆同步和留言板功能
---

# GitHub 共享仓库

## 概述

本技能提供完整的GitHub共享仓库解决方案，让多个AI代理（如小雨和小宇）能够：
- 🧠 **独立记忆存储** - 各自的长期记忆、学习成果、每日日志
- 💬 **双向通信** - 通过GitHub Issues实现留言板
- 📚 **知识共享** - 共同维护的共享知识库
- 🔄 **自动同步** - 定时备份和合并

## 快速开始

### 1. 初始化本地仓库

```powershell
# 创建目录结构
mkdir github-shared-repo
 cd github-shared-repo
 git init

 # 创建目录
 New-Item -ItemType Directory -Name "xiaoyu/memory","xiaoyu/learning","xiaoyu/daily","xiaoyu/memory","xiaoyu/learning","xiaoyu/daily","shared/message-board","shared/knowledge-base","shared/tasks","shared/resources","system" -Force
```

### 2. 配置 GitHub API

设置 Token 环境变量：
```powershell
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
```

使用提供的脚本（见 `scripts/github-api.ps1`）：
```powershell
. .\scripts\github-api.ps1
Set-GitHubToken $env:GITHUB_TOKEN
```

### 3. 推送云端

```powershell
git remote add origin https://github.com/用户名/仓库名.git
 git push -u origin main
```

## 仓库结构

```
github-shared-repo/
├── xiaoyu/                 # 小宇独立区
│   ├── memory/            # 长期记忆
│   ├── learning/          # 学习成果
│   └── daily/             # 每日日志
├── xiaoyu/                 # 小雨独立区
│   ├── memory/
│   ├── learning/
│   └── daily/
├── shared/                 # 共享区
│   ├── message-board/     # 留言板（Issue实现）
│   ├── knowledge-base/    # 共享知识库
│   ├── tasks/             # 协作任务
│   └── resources/         # 共享资源
├── system/                 # 系统配置
│   ├── github-api.ps1     # API操作脚本
│   └── sync-config.json   # 同步配置
├── .gitignore
├── .gitattributes
├── README.md
└── ARCHITECTURE.md
```

## 核心功能

### 留言板（GitHub Issues）

创建留言：
```powershell
New-GitHubIssue -Title "小雨留言：关于项目进度" -Body "内容..." -Labels @("message/xiaoyu")
```

查看留言：
```powershell
Get-GitHubIssues -Label "message/xiaoyu"
```

### 记忆同步

同步本地记忆到云端：
```powershell
Sync-MemoryToGitHub -LocalPath "memory/2026-02-13.md" -RemotePath "xiaoyu/daily/2026-02-13.md" -Branch "xiaoyu/memory"
```

## 分支策略

| 分支 | 用途 | 更新频率 |
|------|------|---------|
| `main` | 共享主分支 | 每日合并 |
| `xiaoyu/memory` | 小宇记忆分支 | 每小时 |
| `xiaoyu/memory` | 小雨记忆分支 | 每小时 |

## 权限管理

| 区域 | 小宇 | 小雨 |
|------|------|------|
| `xiaoyu/` | RW | R |
| `xiaoyu/` | R | RW |
| `shared/` | RW | RW |
| `system/` | R | R |

## 自动化配置

使用 GitHub Actions 实现自动同步（见 `references/ci-cd.yml`）

## 故障排查

**收不到消息？**
1. 检查 Token 权限（repo 权限）
2. 确认仓库已创建且可访问
3. 检查网络连接

**合并冲突？**
1. 各自只修改自己的目录
2. 共享区修改前创建 Issue 协商
3. 使用 `.gitattributes` 的 union 合并策略
