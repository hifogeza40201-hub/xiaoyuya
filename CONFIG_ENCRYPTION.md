# 🔐 配置加密说明

## 加密完成时间
2026-02-11 17:58

## 加密内容
- ✅ 钉钉渠道配置（clientSecret等）
- ✅ 认证信息（API密钥）
- ✅ 插件配置（敏感数据）

## 文件位置

| 文件 | 位置 | 说明 |
|------|------|------|
| 加密配置 | `~/.openclaw/openclaw.json.enc` | 敏感字段加密存储 |
| 密钥文件 | `~/.openclaw/.secure_key` | **重要：请备份此文件** |
| 公开配置 | `~/.openclaw/openclaw.json` | 非敏感配置，可提交GitHub |
| 加密脚本 | `workspace/scripts/encrypt-config.js` | 重新加密 |
| 解密脚本 | `workspace/scripts/decrypt-config.js` | 恢复完整配置 |

## 使用方法

### 解密配置（需要时运行）
```bash
node scripts/decrypt-config.js
```

### 重新加密（修改配置后）
```bash
node scripts/encrypt-config.js
```

## 安全提醒 ⚠️

1. **备份密钥文件**
   - `.secure_key` 文件是解密的唯一钥匙
   - 请复制到安全位置（U盘、其他电脑等）
   - **丢失将无法恢复配置**

2. **不要上传密钥**
   - `.secure_key` 已添加到 .gitignore
   - 永远不要提交到GitHub

3. **加密算法**
   - AES-256-GCM（军用级加密）
   - 256位密钥，暴力破解几乎不可能

4. **恢复流程**
   - 如果密钥丢失，需要：
     1. 从旧电脑或备份恢复 .secure_key
     2. 或重新配置所有API密钥

## 当前状态
✅ 敏感配置已加密保护
✅ 密钥文件已生成
✅ 解密脚本已准备

**小雨的配置现在安全了！** 🛡️
