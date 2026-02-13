# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## 定时任务说明

### Gateway健康检查（Cron Job）
- **任务ID**: 7e08e919-4b54-4997-b94f-35c477104887
- **执行频率**: 每10分钟一次
- **执行方式**: Isolated Agent Turn（独立会话）
- **通知渠道**: 钉钉
- **任务内容**:
  1. 检查 `openclaw gateway status`
  2. 异常时自动重启网关
  3. 记录状态到 memory/heartbeat-state.json
  4. 重启时发送通知
