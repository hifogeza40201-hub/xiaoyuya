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

## 操作授权规则（老大设定）

### 网关操作
- **重启网关（restart gateway）**: 必须经老大同意，先发消息确认后才能执行
- **停止网关（stop gateway）**: 必须经老大同意
- **启动网关（start gateway）**: 可自动执行（非破坏性操作）

**执行流程:**
1. 收到重启/停止网关请求
2. 先给老大发消息等待确认
3. 老大同意后执行
4. 未经同意不执行

---

Add whatever helps you do your job. This is your cheat sheet.
