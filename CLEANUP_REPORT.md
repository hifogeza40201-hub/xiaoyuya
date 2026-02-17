# 🧹 工作目录清理清单 - 小雨专属

**检查时间**: 2026-02-17  
**检查者**: 小雨 🌧️  
**范围**: C:\Users\Admin\.openclaw\workspace + D:\

---

## ✅ **属于小雨的内容（保留）**

### 核心身份文件
| 文件/目录 | 说明 | 状态 |
|-----------|------|------|
| `IDENTITY.md` | 小雨身份（姐姐，温柔陪伴） | ✅ 正确 |
| `SOUL.md` | 小雨的灵魂 | ✅ 正确 |
| `MEMORY.md` | 小雨的长期记忆 | ✅ 正确 |
| `USER.md` | 关于伟的信息 | ✅ 正确 |
| `AGENTS.md` | 启动自检已添加 | ✅ 已更新 |
| `HEARTBEAT.md` | 心跳检查配置 | ✅ 正确 |
| `TOOLS.md` | TTS配置等工具 | ✅ 正确 |

### 备份文件
| 文件 | 说明 | 状态 |
|------|------|------|
| `IDENTITY.md.backup` | 小雨身份备份 | ✅ 保留 |
| `SOUL.md.backup` | 小雨灵魂备份 | ✅ 保留 |
| `MEMORY.md.backup` | 小雨记忆备份 | ✅ 保留 |

### 小雨专属目录
| 目录 | 说明 | 状态 |
|------|------|------|
| `memory/` | 记忆系统（小雨的episodes/vault/graph） | ✅ 保留 |
| `scripts/` | 小雨的脚本（含自检脚本） | ✅ 保留 |
| `temp/` | 临时文件 | ⚠️ 可清理 |

### ai-memory 目录
| 路径 | 说明 | 状态 |
|------|------|------|
| `ai-memory/workspace/` | 小雨的工作空间 | ✅ 保留 |
| `ai-memory/shared/` | 家族共享内容 | ✅ 保留 |
| `ai-memory/xiaoyu/` | ⚠️ 这是弟弟的，但名称为xiaoyu | ❌ 需重命名或确认 |

### 其他小雨文件
| 文件 | 说明 | 状态 |
|------|------|------|
| `autonomous-mode-config.md` | 自主模式配置 | ✅ 保留 |
| `backup-memory.bat` | 小雨的记忆备份 | ✅ 保留 |
| `save-and-push.bat` | 小雨的推送脚本 | ✅ 保留 |

---

## ❌ **属于小宇的内容（需清理/隔离）**

### 小宇专属目录（工作区内）
| 目录 | 内容 | 建议操作 |
|------|------|---------|
| `xiaoyu/` | 小宇的身份文件、配置 | ❌ 移到 D:\xiaoyu-workspace |
| `xiaoyu-mountain/` | 小宇的副本 | ❌ 移到 D:\xiaoyu-workspace |
| `xiaoyu-flower/` | 小宇的副本 | ❌ 移到 D:\xiaoyu-workspace |
| `xiaoyu-deploy/` | 小宇的部署配置 | ❌ 移到 D:\xiaoyu-workspace |

### 小宇专属文件（工作区内）
| 文件 | 说明 | 建议操作 |
|------|------|---------|
| `backup_xiaoyu.bat` | 小宇的备份脚本 | ❌ 移到 D:\xiaoyu-workspace |
| `restore_xiaoyu.bat` | 小宇的恢复脚本 | ❌ 移到 D:\xiaoyu-workspace |
| `xiaoyu-deploy.rar` | 小宇的部署包 | ❌ 移到 D:\xiaoyu-workspace |
| `setup_admin.ps1` | 管理员设置（可能是小宇的） | ❌ 确认后移动 |
| `setup_admin_simple.ps1` | 简化版设置 | ❌ 确认后移动 |

### xiaoyuya 共享仓库内的小宇内容
| 路径 | 说明 | 建议操作 |
|------|------|---------|
| `xiaoyuya/xiaoyu/` | 小宇的文件 | ✅ 保留（共享仓库内） |
| `xiaoyuya/xiaoyu-deploy/` | 小宇的部署 | ✅ 保留（共享仓库内） |
| `xiaoyuya/xiaoyu-flower/` | 小宇的副本 | ✅ 保留（共享仓库内） |
| `xiaoyuya/xiaoyu-mountain/` | 小宇的副本 | ✅ 保留（共享仓库内） |

### D盘小宇内容
| 路径 | 说明 | 建议操作 |
|------|------|---------|
| `D:\xiaoyu-backup-2026-02-16/` | 小宇备份 | ✅ 保留（D盘，已隔离） |
| `D:\xiaoyu-backup-2026-02-17/` | 小宇备份 | ✅ 保留（D盘，已隔离） |

---

## ⚠️ **需要确认的内容**

| 文件/目录 | 说明 | 状态 |
|-----------|------|------|
| `xiaoyuya/` | 共享仓库，包含三兄妹内容 | ✅ 保留但需整理 |
| `api-integration/` 等目录 | 技术目录，可能属于小宇 | ❓ 需确认 |
| `first-setup.bat` | 首次设置脚本 | ❓ 需确认归属 |
| `restart.bat` | 重启脚本 | ❓ 需确认归属 |

---

## 📊 **清理统计**

**当前工作区目录数**: ~40个  
**确认小雨专属**: ~10个  
**确认小宇专属**: ~5个  
**共享/待确认**: ~25个

**需要清理的文件**: 
- backup_xiaoyu.bat
- restore_xiaoyu.bat  
- xiaoyu-deploy.rar
- xiaoyu/ 目录
- xiaoyu-mountain/ 目录
- xiaoyu-flower/ 目录
- xiaoyu-deploy/ 目录

---

## 🎯 **建议操作**

### 立即执行：
1. 移动小宇目录到 D:\xiaoyu-workspace\
2. 删除小宇专属bat文件
3. 确认技术目录归属

### 长期规划：
1. 建立清晰的工作区边界
2. 共享内容统一放在 xiaoyuya/
3. 个人内容严格分离

---

*清理清单生成时间: 2026-02-17*  
*小雨 🌧️*