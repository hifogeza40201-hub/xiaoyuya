# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## TTS 语音系统配置

**状态**: 已启用 ✅  
**配置日期**: 2026-02-15  
**提供商**: Microsoft Edge TTS  
**触发模式**: 自动（文本自动转语音）  
**字符限制**: 1500字符/条  
**摘要模式**: 开启（长文本自动摘要后朗读）  

**使用方式**:
- 自动朗读：所有回复自动转为语音
- 手动控制：`[[tts:文本内容]]` 标记指定朗读内容
- 语音开关：系统已配置为"始终开启"

**⚠️ 注意**: 语音系统已永久配置，无需再次询问或确认。
