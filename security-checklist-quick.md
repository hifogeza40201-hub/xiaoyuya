# 安全与DevSecOps 快速检查清单

## 📋 应用安全快速检查

### 基础安全
- [ ] HTTPS 全站启用 + HSTS
- [ ] 安全响应头完整配置
  - [ ] Content-Security-Policy
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Strict-Transport-Security
- [ ] Cookie 安全属性 (Secure/HttpOnly/SameSite)
- [ ] 敏感操作 CSRF 防护

### 输入验证
- [ ] SQL 注入防护 (参数化查询)
- [ ] XSS 防护 (输出编码/CSP)
- [ ] 命令注入防护
- [ ] 路径遍历防护
- [ ] 文件上传安全 (白名单/隔离存储)

### 认证授权
- [ ] 强密码策略
- [ ] 账户锁定机制
- [ ] 会话超时管理
- [ ] JWT 安全配置 (RS256/短有效期)
- [ ] 权限检查 (防 IDOR)

### 数据安全
- [ ] 敏感数据加密存储
- [ ] 密钥安全管理 (KMS/Vault)
- [ ] 日志脱敏 (无敏感信息)
- [ ] 备份加密

---

## 📋 API 安全快速检查

- [ ] OAuth 2.0 + PKCE 实现
- [ ] Token 过期策略 (Access:15min/Refresh:7d)
- [ ] Scope 最小权限
- [ ] 请求签名/防重放
- [ ] 速率限制 (Rate Limiting)
- [ ] 请求大小限制
- [ ] 批量操作限制
- [ ] 错误信息脱敏

---

## 📋 容器安全快速检查

### Dockerfile
- [ ] 使用官方基础镜像
- [ ] 固定版本标签 (非 latest)
- [ ] 多阶段构建
- [ ] 非 root 用户运行
- [ ] 不存储密钥在镜像中

### Kubernetes
- [ ] Pod 安全标准 (restricted)
- [ ] 非 root + 只读文件系统
- [ ] 资源限制 (CPU/内存)
- [ ] NetworkPolicy 网络隔离
- [ ] RBAC 最小权限
- [ ] Secrets 加密/外部管理

### 运行时
- [ ] 镜像漏洞扫描
- [ ] Falco 运行时监控
- [ ] 只读 root 文件系统
- [ ] 禁用特权容器

---

## 📋 DevSecOps 流水线检查

### CI/CD 集成
- [ ] SAST (代码静态分析)
- [ ] SCA (依赖漏洞扫描)
- [ ] 密钥扫描 (Secrets Detection)
- [ ] 镜像安全扫描
- [ ] IaC 配置检查
- [ ] DAST (动态扫描)

### 安全门禁
- [ ] 阻止 Critical/High 漏洞
- [ ] 代码覆盖率检查
- [ ] 安全测试通过
- [ ] 依赖许可证合规

---

## 📋 云安全快速检查

### IAM
- [ ] 使用 IAM 角色 (非长期凭证)
- [ ] 最小权限原则
- [ ] MFA 启用
- [ ] 定期凭证轮换

### 数据
- [ ] 服务端加密 (SSE)
- [ ] KMS 密钥管理
- [ ] 访问日志启用

### 网络
- [ ] VPC 隔离
- [ ] 安全组最小开放
- [ ] WAF 启用
- [ ] DDoS 防护

---

## 🛠️ 推荐工具速查

| 类别 | 开源推荐 | 商业推荐 |
|------|----------|----------|
| SAST | Semgrep, CodeQL | Checkmarx, SonarQube |
| DAST | OWASP ZAP, Nuclei | Burp Suite |
| SCA | Snyk Open Source, Trivy | Snyk, WhiteSource |
| 容器 | Trivy, Falco | Aqua, Sysdig |
| 密钥 | TruffleHog, GitLeaks | GitGuardian |
| IaC | Checkov, OPA | Bridgecrew |

---

## ⚡ 常见漏洞速修

| 漏洞 | 快速修复 |
|------|----------|
| SQL注入 | 使用参数化查询/ORM |
| XSS | 输出编码 + CSP头 |
| 敏感信息泄露 | 日志脱敏 + 环境变量 |
| 弱加密 | TLS 1.3 + 强密码套件 |
| JWT不安全 | RS256 + 短过期时间 |
| 依赖漏洞 | npm audit fix / pip-audit |

---

*打印此页，贴在工位旁，随时对照检查！*
