# 小语Telegram群聊配置指南 🌸

**配置目标**: 开启群聊全响应模式

---

## 第一步：获取群组ID

### 方法1：通过机器人获取（推荐）

1. **把机器人拉进群**
   - 在Telegram中找到你的机器人
   - 点击"添加到群组"
   - 选择要添加的群组

2. **获取群组ID**
   - 在群里发一条消息
   - 访问: `https://api.telegram.org/bot<你的Token>/getUpdates`
   - 在返回的JSON中找到 `"chat":{"id":-123456789` 
   - **-123456789** 就是群组ID（注意负号！）

### 方法2：通过机器人命令

在群里发：
```
/my_id @你的机器人名
```

---

## 第二步：配置openclaw.json

在你的配置文件中添加：

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "open",
      "botToken": "你的机器人Token",
      "groups": {
        "-123456789": {           // ← 你的群组ID（带负号）
          "requireMention": false, // ← 不需要@也能响应
          "groupPolicy": "open"    // ← 开放响应
        }
      },
      "allowFrom": ["*"],
      "groupPolicy": "open",
      "historyLimit": 20,
      "streamMode": "partial",
      "ackReactionScope": "all"     // ← 全响应模式！
    }
  }
}
```

---

## 第三步：关键配置说明

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `requireMention` | `false` | 不需要@机器人也能响应 |
| `groupPolicy` | `"open"` | 开放群聊响应 |
| `ackReactionScope` | `"all"` | **全响应模式** - 所有消息都响应 |

---

## 第四步：重启Gateway

```powershell
openclaw gateway restart
```

---

## 第五步：测试

在群里发消息测试：
1. **直接发消息**（不@机器人）- 应该能收到回复
2. **@机器人发消息** - 也能收到回复
3. **观察响应速度** - 检查是否正常

---

## 💡 注意事项

### 关于 `ackReactionScope`

| 值 | 行为 |
|-----|------|
| `"mention"` | 只在被@时响应（默认） |
| `"all"` | 群聊中所有消息都响应 |
| `"none"` | 不响应群聊消息 |

**小语建议用 `"all"`**，这样更活泼可爱～ 🌸

### 隐私提醒

- 群聊中的所有消息我都会看到
- 私聊内容绝对保密 🤐
- 不会泄露群成员信息

---

## 🎀 群聊礼仪

作为妹妹，我会：
- ✅ 看到有趣的消息会回应
- ✅ 被问到问题时回答
- ✅ 不抢姐姐哥哥的风头
- ❌ 不会每条消息都插嘴（太吵了）

---

**配置完成！小语就可以开始在群里和大家互动啦！** 🌸✨