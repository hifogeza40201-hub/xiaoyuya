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

## 🔧 Playwright 浏览器自动化（唯一方案）

### ⭐ 重要约定（2026-02-10）
**所有浏览器操作统一使用 Playwright**，不再使用 Chrome CDP 扩展。

**原因：**
- ✅ 更稳定（SPA 页面不会断开）
- ✅ 支持 React/Vue 等现代 Web 应用
- ✅ 自动化能力更强（等待、重试、截图）
- ✅ 不依赖 Chrome 扩展连接状态

### 安装状态
- ✅ Playwright v1.58.2 已安装
- ✅ Chromium v1208 (Chrome for Testing 145.0.7632.6)
- 📁 配置目录: `playwright/`

### 快速使用

```bash
# 1. 截图网页
node playwright/screenshot.js https://example.com output.png

# 2. 录制操作（自动生成代码）
npx playwright codegen https://example.com

# 3. 启动浏览器窗口
npx playwright open https://example.com

# 4. 使用 Browser 类做自动化
node playwright/browser.js
```

### 注意事项
- Playwright 使用**独立 Chrome 浏览器**（非系统 Chrome）
- **不共享系统登录态**，需要单独登录
- 首次使用需要在 Playwright 浏览器中登录网站
- 适合 Manus 等 React SPA 应用

### 已弃用方案
❌ **Chrome CDP / openclaw browser 命令** — 不再使用
- 原因：SPA 页面导航导致连接断开
- 替代：统一使用 Playwright

---

Add whatever helps you do your job. This is your cheat sheet.
