#!/bin/bash
# OpenClaw Config Rollback Script
# Restores openclaw.json from latest or specified backup

BACKUP_DIR=~/.openclaw
CONFIG_FILE=$BACKUP_DIR/openclaw.json

# List available backups
echo "Available backups:"
ls -lt ${BACKUP_DIR}/openclaw.json.bak.* 2>/dev/null | head -10

# Ask user which backup to use
echo ""
echo "Usage: ./rollback.sh [backup_number]"
echo "  ./rollback.sh latest    - Restore latest backup"
echo "  ./rollback.sh 1         - Restore backup #1 (most recent)"
echo "  ./rollback.sh 2         - Restore backup #2"
