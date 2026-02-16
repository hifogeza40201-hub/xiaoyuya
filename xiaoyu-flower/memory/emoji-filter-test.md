# Emoji过滤测试

测试目的：解决TTS语音朗读时emoji被读出（如🛠️读成"锤子"）的问题

## 方案一：使用tts:text标签分离文字和语音内容

原理：
- 文字显示内容：保留emoji
- 语音内容：用[[tts:text]]...[[/tts:text]]包裹，过滤emoji

## 方案二：检查OpenClaw是否支持自动emoji过滤

查看是否有配置项：`tts.filterEmoji` 或类似选项

## 测试记录

### 测试1 - 使用tts:text标签
输入：
```
文字显示：🛠️ 小宇收到
语音：[[tts:text]]小宇收到[[/tts:text]]
```

预期：
- 文字显示带锤子emoji
- 语音只读"小宇收到"

---
测试时间：2026-02-14
