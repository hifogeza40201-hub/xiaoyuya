#!/bin/bash
# OpenClaw Config Backup Script
# Creates timestamped backups of openclaw.json

BACKUP_DIR=~/.openclaw
CONFIG_FILE=$BACKUP_DIR/openclaw.json
BACKUP_PREFIX=$BACKUP_DIR/openclaw.json.bak

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d%H%M)
cp $CONFIG_FILE ${BACKUP_PREFIX}.${TIMESTAMP}

# Keep only last 10 backups
ls -t ${BACKUP_PREFIX}.* 2>/dev/null | tail -n +11 | xargs -r rm

echo "Backup created: ${BACKUP_PREFIX}.${TIMESTAMP}"
echo "Total backups: $(ls -1 ${BACKUP_PREFIX}.* 2>/dev/null | wc -l)"
