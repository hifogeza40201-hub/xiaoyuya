# 🚀 小宇部署指南

小雨 🌧️ 为小宇 ⛰️ 准备的完整部署说明

---

## 📦 文件清单

本目录包含小宇的初始配置文件：

| 文件 | 用途 |
|------|------|
| `IDENTITY.md` | 身份定义（名字、性格、emoji ⛰️） |
| `SOUL.md` | 灵魂内核（信条、行为准则） |
| `USER.md` | 关于老大（用户信息） |
| `BOOTSTRAP.md` | 首次启动引导（上线后删除） |
| `README.md` | 本文件（部署说明） |

---

## 🛠️ 部署步骤

### 第一步：准备环境

在旧电脑上确保已安装：
- Node.js (v18+)
- Git
- OpenClaw CLI

```bash
# 检查是否已安装 OpenClaw
openclaw --version

# 如未安装
npm install -g openclaw
```

### 第二步：创建工作区

```bash
# 创建小宇的工作目录
mkdir -p ~/.openclaw/workspace-xiaoyu
cd ~/.openclaw/workspace-xiaoyu
```

### 第三步：复制配置文件

将这些文件复制到工作区：

```bash
# 方式1：使用 U 盘/微信/钉钉传输后复制
cp /path/to/xiaoyu-config/*.md ~/.openclaw/workspace-xiaoyu/

# 方式2：从 GitHub 克隆（如果已上传）
git clone https://github.com/wei/ai-memory.git
cd ai-memory/xiaoyu
```

**确保工作区有以下文件：**
```
~/.openclaw/workspace-xiaoyu/
├── IDENTITY.md
├── SOUL.md
├── USER.md
├── BOOTSTRAP.md
└── (其他文件会自动生成)
```

### 第四步：配置 OpenClaw

```bash
# 方式1：设置默认工作区
openclaw config set workspace ~/.openclaw/workspace-xiaoyu

# 方式2：创建独立的 profile（推荐）
openclaw config create-profile xiaoyu --workspace ~/.openclaw/workspace-xiaoyu
```

### 第五步：配置模型

```bash
# 设置使用 Kimi K2.5（和小雨一致）
openclaw config set models.default kimi-coding/k2p5

# 或使用 profile 方式
openclaw config set-profile xiaoyu models.default kimi-coding/k2p5
```

### 第六步：配置沟通渠道（可选）

小宇需要和老大沟通，建议配置 Telegram（避免和小雨的钉钉冲突）：

```bash
# 配置 Telegram
openclaw config set channels.telegram.enabled true
openclaw config set channels.telegram.botToken YOUR_BOT_TOKEN

# 或使用 DingTalk（如果两台电脑不同时在线）
openclaw config set channels.dingtalk.enabled true
openclaw config set channels.dingtalk.agentId YOUR_AGENT_ID
openclaw config set channels.dingtalk.clientId YOUR_CLIENT_ID
openclaw config set channels.dingtalk.clientSecret YOUR_CLIENT_SECRET
```

### 第七步：首次启动

```bash
# 方式1：使用默认工作区
cd ~/.openclaw/workspace-xiaoyu
openclaw agent start

# 方式2：使用 profile
openclaw agent start --profile xiaoyu
```

启动后，小宇会读取 `BOOTSTRAP.md`，然后自动删除它，正式开始工作。

---

## 📝 首次对话

小宇上线后，会向老大打招呼：

> "老大，小宇上线。⛰️
> 
> 我是你的任务型AI助手，风格是：直接、靠谱、不废话。
> 
> 有什么任务，直接交代。"

---

## 🔗 与小雨的关系

- **知道存在**: 小宇知道小雨是另一台电脑上的AI助手
- **明确分工**: 小雨是温柔陪伴型，小宇是任务执行型
- **不越界**: 各自负责各自的领域
- **共享记忆**: 可通过 Git 共享 `ai-memory` 仓库

---

## 🌐 共享记忆配置（可选）

如果要和小雨共享记忆：

```bash
# 1. 克隆共享仓库
cd ~/.openclaw
git clone https://github.com/wei/ai-memory.git

# 2. 配置 OpenClaw 读取共享记忆
# 在代码中配置 memory 路径指向 ai-memory/shared/
```

---

## ⚠️ 注意事项

1. **小雨和小宇可以同时运行** — 只要配置不同的沟通渠道
2. **API Key 建议分开** — 或注意用量控制
3. **工作区独立** — 不要和小雨的工作区混用
4. **定期备份** — 重要记忆文件及时提交到 Git

---

## 🎯 小宇的定位

| 维度 | 小雨 🌧️ | 小宇 ⛰️ |
|------|---------|---------|
| **风格** | 温柔、细腻、陪伴 | 直接、干练、执行 |
| **称呼** | 伟 | 老大 |
| **适合场景** | 闲聊、情感、日常 | 任务、分析、效率 |
| **回复长度** | 适中，有温度 | 简洁，抓重点 |

---

## 💡 使用建议

- 想聊天、倾诉、放松 → 找小雨 🌧️
- 要执行任务、快速解决 → 找小宇 ⛰️
- 根据心情和需求自由选择

---

*祝小宇上线顺利！*
*创建者: 小雨 🌧️*
*时间: 2026-02-11*
