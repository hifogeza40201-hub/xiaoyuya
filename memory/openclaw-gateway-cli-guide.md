# OpenClaw Gateway 命令行操作指南

> 研究日期: 2025-02-13
> 目标: 总结常用管理命令和故障排查技巧

---

## 一、Gateway 服务管理命令

### 1. 服务状态查看
```bash
# 查看 Gateway 运行状态
openclaw gateway status

# 查看详细健康状态（包含各子系统）
openclaw status
```

### 2. 服务启停控制
```bash
# 启动 Gateway 服务
openclaw gateway start

# 停止 Gateway 服务
openclaw gateway stop

# 重启 Gateway 服务
openclaw gateway restart
```

### 3. 服务安装/卸载（守护进程模式）
```bash
# 安装 Gateway 为系统服务（systemd/launchd）
openclaw gateway install

# 强制重新安装
openclaw gateway install --force

# 指定端口安装
openclaw gateway install --port 8080

# 指定运行时（node 或 bun）
openclaw gateway install --runtime node

# 卸载 Gateway 服务
openclaw gateway uninstall
```

---

## 二、配置管理命令

### 1. 配置查看与修改
```bash
# 查看配置项
openclaw config get <key>

# 示例：查看 Gateway 是否启用
openclaw config get gateway.enabled

# 查看 Gateway 端口
openclaw config get gateway.port

# 查看 Gateway 认证令牌
openclaw config get gateway.auth.token

# 设置配置项
openclaw config set <key> <value>

# 查看完整配置
openclaw config show

# 验证配置有效性
openclaw config validate
```

### 2. 配置路径相关
- **配置文件路径**: `~/.openclaw/config.json5`
- **状态目录**: `~/.openclaw/state/`
- **日志目录**: 可通过 `openclaw config get` 查看

---

## 三、节点（Node）管理命令

### 1. 节点配对与管理
```bash
# 列出已配对节点
openclaw nodes list

# 查看节点详细信息
openclaw nodes describe <node-id>

# 重命名节点
openclaw nodes rename <node-id> <new-name>

# 删除节点配对
openclaw nodes remove <node-id>

# 查看待处理的配对请求
openclaw nodes pending

# 批准配对请求
openclaw nodes approve <device-id>

# 拒绝配对请求
openclaw nodes reject <device-id>
```

### 2. 设备令牌管理
```bash
# 轮转设备令牌（安全更新）
openclaw nodes token rotate <node-id>

# 吊销设备令牌
openclaw nodes token revoke <node-id>
```

---

## 四、代理（Agent）管理命令

### 1. 代理生命周期
```bash
# 列出所有代理
openclaw agents list

# 查看代理状态
openclaw agents status <agent-id>

# 启动代理会话
openclaw agent --agent <agent-id>

# 查看代理文件
openclaw agents files list <agent-id>

# 读取代理文件
openclaw agents files get <agent-id> <filename>

# 设置代理文件
openclaw agents files set <agent-id> <filename> <content>
```

---

## 五、频道（Channel）管理命令

### 1. 频道配置
```bash
# 列出已配置频道
openclaw channels list

# 查看频道状态
openclaw channels status

# 退出指定频道
openclaw channels logout <channel-id>

# 登录指定频道
openclaw channels login <channel-id>
```

---

## 六、技能（Skills）管理命令

### 1. 技能操作
```bash
# 列出可用技能
openclaw skills list

# 查看技能状态
openclaw skills status

# 安装技能
openclaw skills install <skill-name>

# 更新技能
openclaw skills update <skill-name>

# 移除技能
openclaw skills remove <skill-name>
```

---

## 七、计划任务（Cron）管理

```bash
# 列出所有计划任务
openclaw cron list

# 添加计划任务
openclaw cron add --schedule "0 9 * * *" --command "openclaw heartbeat"

# 查看任务运行历史
openclaw cron runs <job-id>

# 查看任务状态
openclaw cron status <job-id>

# 更新任务
openclaw cron update <job-id> --schedule "0 10 * * *"

# 移除任务
openclaw cron remove <job-id>

# 立即运行任务
openclaw cron run <job-id>
```

---

## 八、会话（Session）管理

```bash
# 列出会话
openclaw sessions list

# 查看会话详情
openclaw sessions preview <session-id>

# 删除会话
openclaw sessions delete <session-id>

# 重置会话
openclaw sessions reset <session-id>

# 查看会话用量
openclaw sessions usage
```

---

## 九、日志与诊断

### 1. 日志查看
```bash
# 查看 Gateway 日志
openclaw logs

# 实时跟踪日志
openclaw logs --follow

# 查看指定行数
openclaw logs --lines 100
```

### 2. 诊断工具
```bash
# 运行诊断检查
openclaw doctor

# 诊断特定子系统
openclaw doctor --target gateway

# 查看端口使用情况
openclaw gateway audit
```

---

## 十、执行审批（Exec Approvals）

```bash
# 列出待审批的执行请求
openclaw exec-approvals list

# 批准执行请求
openclaw exec-approvals approve <request-id>

# 拒绝执行请求
openclaw exec-approvals reject <request-id>

# 查看节点执行审批状态
openclaw exec-approvals node get <node-id>

# 设置节点审批策略
openclaw exec-approvals node set <node-id> --policy <policy>
```

---

## 十一、插件（Plugins）管理

```bash
# 列出已安装插件
openclaw plugins list

# 查看插件详情
openclaw plugins show <plugin-id>

# 启用/禁用插件
openclaw plugins enable <plugin-id>
openclaw plugins disable <plugin-id>
```

---

## 十二、常用故障排查技巧

### 1. Gateway 无法启动

**排查步骤：**
```bash
# 1. 检查端口占用
openclaw gateway audit

# 2. 查看最后错误日志
openclaw logs --lines 50

# 3. 验证配置
openclaw config validate

# 4. 检查端口可用性
openclaw config get gateway.port
# 然后使用系统命令检查端口占用（如 netstat / lsof）
```

**常见原因：**
- 端口被其他程序占用
- 配置文件格式错误
- 认证令牌未设置
- 权限不足（Linux/macOS）

### 2. 节点连接问题

**排查步骤：**
```bash
# 1. 检查 Gateway 是否运行
openclaw gateway status

# 2. 查看节点列表状态
openclaw nodes list

# 3. 检查配对请求
openclaw nodes pending

# 4. 验证节点令牌
openclaw nodes describe <node-id>
```

### 3. 频道连接失败

**排查步骤：**
```bash
# 1. 检查频道状态
openclaw channels status

# 2. 重新登录频道
openclaw channels logout <channel-id>
openclaw channels login <channel-id>

# 3. 检查凭证配置
openclaw config get --section <channel-id>
```

### 4. 技能加载失败

**排查步骤：**
```bash
# 1. 检查技能状态
openclaw skills status

# 2. 重新安装技能
openclaw skills remove <skill-name>
openclaw skills install <skill-name>

# 3. 查看详细日志
openclaw logs --follow | grep -i skill
```

### 5. 配置问题诊断

```bash
# 查看配置快照
openclaw config snapshot

# 对比默认配置
openclaw config schema

# 重置配置项为默认值
openclaw config unset <key>
```

---

## 十三、环境变量参考

| 变量名 | 说明 |
|--------|------|
| `OPENCLAW_GATEWAY_TOKEN` | Gateway 认证令牌 |
| `OPENCLAW_GATEWAY_PORT` | Gateway 服务端口 |
| `OPENCLAW_CONFIG_PATH` | 自定义配置文件路径 |
| `OPENCLAW_STATE_DIR` | 自定义状态目录 |
| `OPENCLAW_VERBOSE` | 详细日志模式 |
| `OPENCLAW_NIX_MODE` | Nix 模式（禁用服务安装） |

---

## 十四、实用快捷命令

```bash
# 快速检查系统健康
openclaw status

# 查看版本信息
openclaw --version

# 获取帮助
openclaw --help
openclaw gateway --help
openclaw <command> --help

# 以 JSON 格式输出（适合脚本）
openclaw gateway status --json

# 非交互式模式（自动化脚本）
openclaw --non-interactive <command>
```

---

## 十五、更新与维护

```bash
# 检查更新
openclaw update check

# 执行更新
openclaw update run

# 查看更新状态
openclaw update status

# 更新到特定版本
openclaw update run --version <version>
```

---

## 附录：命令速查表

| 操作 | 命令 |
|------|------|
| 查看状态 | `openclaw gateway status` |
| 启动服务 | `openclaw gateway start` |
| 停止服务 | `openclaw gateway stop` |
| 重启服务 | `openclaw gateway restart` |
| 安装服务 | `openclaw gateway install` |
| 卸载服务 | `openclaw gateway uninstall` |
| 查看日志 | `openclaw logs` |
| 运行诊断 | `openclaw doctor` |
| 查看配置 | `openclaw config show` |
| 列出节点 | `openclaw nodes list` |
| 列出代理 | `openclaw agents list` |
| 列出频道 | `openclaw channels list` |
| 列出技能 | `openclaw skills list` |
| 列出任务 | `openclaw cron list` |
| 列出会话 | `openclaw sessions list` |

---

*文档生成时间: 2025-02-13*
