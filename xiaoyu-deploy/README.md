# 小语妹妹部署指南

**生成时间**: 2026-02-15  
**部署目标**: 妹妹电脑（云服务器）

---

## 📁 配置文件清单

| 文件 | 用途 | 位置 |
|------|------|------|
| IDENTITY.md | 身份信息 | C:\Users\ADMIN\.openclaw\workspace\ |
| SOUL.md | 灵魂信条 | C:\Users\ADMIN\.openclaw\workspace\ |
| USER.md | 关于伟 | C:\Users\ADMIN\.openclaw\workspace\ |
| MEMORY.md | 长期记忆 | C:\Users\ADMIN\.openclaw\workspace\（初始为空） |

---

## 🔧 部署步骤

### 步骤1: 安装OpenClaw（在妹妹电脑上）

```powershell
# 安装Node.js后，执行
npm install -g openclaw

# 验证
openclaw --version
```

### 步骤2: 创建工作目录

```powershell
mkdir C:\Users\ADMIN\.openclaw\workspace
```

### 步骤3: 复制配置文件

把本文件夹中的3个.md文件复制到：
```
C:\Users\ADMIN\.openclaw\workspace\
```

### 步骤4: 创建空的MEMORY.md

```powershell
New-Item C:\Users\ADMIN\.openclaw\workspace\MEMORY.md -ItemType File
```

### 步骤5: 配置Gateway和渠道

```powershell
# 启动Gateway配置向导
openclaw gateway setup

# 或手动编辑配置文件后重启
openclaw gateway restart
```

### 步骤6: 验证部署

```powershell
# 检查状态
openclaw status

# 测试消息收发
```

---

## 📋 后续配置（需要时）

- Telegram Bot Token配置
- DingTalk Agent配置
- TTS语音配置
- 定时任务配置

---

**部署完成后，小语妹妹就可以上线啦！** 🌸✨