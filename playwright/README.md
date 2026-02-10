# Playwright 配置目录
# 用于稳定浏览器自动化，替代 Chrome CDP

## 已安装浏览器
- Chromium v1208 (Chrome for Testing 145.0.7632.6)
- 安装路径: C:\Users\Admin\AppData\Local\ms-playwright\

## 使用方式

### 1. 快速截图
```bash
npx playwright screenshot https://example.com output.png
```

### 2. 运行自动化脚本
```bash
node scripts/open-page.js <url>
```

### 3. 代码生成（录制操作）
```bash
npx playwright codegen https://manus.im/app
```

## 注意事项
- Playwright 使用独立的 Chrome 浏览器（非系统 Chrome）
- 需要单独登录网站（不共享系统 Chrome 的登录态）
- 比 Chrome CDP 更稳定，适合 SPA 应用（React/Vue 等）
