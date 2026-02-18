# 🔄 Gateway重启方案 - 解决连接问题

## 当前问题
- 错误: `gateway closed (1008): unauthorized: device token mismatch`
- 可能原因: 设备令牌过期或缓存问题

## 重启步骤

### 方法1: 完整重启（推荐）

```powershell
# 1. 完全停止Gateway
openclaw gateway stop

# 等待10秒确保完全停止
Start-Sleep 10

# 2. 清除可能的问题缓存
# （可选）重命名会话存储文件
Rename-Item "C:\Users\Admin\.openclaw\agents\main\sessions\sessions.json" "sessions.json.backup"

# 3. 重新启动Gateway
openclaw gateway start

# 4. 等待启动完成
Start-Sleep 5

# 5. 检查状态
openclaw status
```

### 方法2: 快速重启

```powershell
# 一键重启
openclaw gateway restart
```

### 方法3: 强制重启（如果方法1/2失败）

```powershell
# 1. 查找并结束OpenClaw进程
Get-Process | Where-Object {$_.Name -like "*openclaw*"} | Stop-Process -Force

# 2. 等待
Start-Sleep 5

# 3. 重新启动
openclaw gateway start
```

## 重启后验证

```powershell
# 检查状态
openclaw status

# 测试cron功能
openclaw cron status

# 测试消息发送
# 向小雨发送测试消息
```

## 预期结果

✅ Gateway正常启动
✅ 设备令牌重新生成
✅ cron功能恢复正常
✅ 小雨可以接收消息

## 如果重启后仍有问题

可能需要:
1. 检查openclaw.json配置
2. 重新配置设备令牌
3. 或重新安装OpenClaw

---

**伟可以尝试以上方法重启Gateway！** 🌧️🔄