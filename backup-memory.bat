#!/bin/bash
# Daily Memory Backup Script
# Runs at 3:00 AM China Time

cd C:\Users\Admin\.openclaw\workspace

# 添加所有更改
git add .

# 提交更改（使用日期作为消息）
DATE=$(date +%Y-%m-%d)
git commit -m "Memory backup - $DATE"

# 推送到GitHub
git push origin master

# 发送完成通知到OpenClaw
echo "Daily backup completed at $(date)"
