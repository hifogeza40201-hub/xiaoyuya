# 系统安全与DevSecOps实践指南

> 研究日期：2026-02-16  
> 涵盖范围：应用安全、身份认证、容器云安全、安全扫描、DevSecOps集成

---

## 目录

1. [应用安全常见漏洞与防护](#一应用安全常见漏洞与防护)
2. [身份认证与授权](#二身份认证与授权oauthjwt)
3. [容器与云安全](#三容器与云安全)
4. [安全扫描与代码审计](#四安全扫描与代码审计)
5. [DevSecOps流程集成](#五devsecops流程集成)
6. [安全检查清单](#六安全检查清单)
7. [安全工具推荐](#七安全工具推荐)
8. [安全最佳实践指南](#八安全最佳实践指南)

---

## 一、应用安全常见漏洞与防护

### 1.1 OWASP Top 10 (2021 - 2024)

| 排名 | 漏洞类型 | 描述 | 防护措施 |
|------|----------|------|----------|
| 1 | **注入攻击** | SQL/NoSQL/OS/Command注入 | 参数化查询、ORM框架、输入验证 |
| 2 | **失效的访问控制** | 权限绕过、目录遍历、IDOR | 最小权限原则、RBAC/ABAC、访问控制检查 |
| 3 | **敏感数据暴露** | 明文存储、传输未加密 | TLS 1.3、数据加密、密钥管理 |
| 4 | **XML外部实体攻击(XXE)** | XML解析器漏洞 | 禁用DTD/外部实体、使用JSON |
| 5 | **失效的身份认证** | 暴力破解、会话劫持、弱密码 | MFA、强密码策略、JWT安全 |
| 6 | **安全配置错误** | 默认配置、功能暴露 | 安全配置基线、自动化扫描 |
| 7 | **跨站脚本(XSS)** | 存储型/反射型/DOM型XSS | CSP、HTML编码、XSS过滤器 |
| 8 | **不安全的反序列化** | 远程代码执行、权限提升 | 白名单、签名验证、避免原生反序列化 |
| 9 | **使用含有已知漏洞的组件** | 依赖库漏洞 | SCA工具、定期更新、漏洞扫描 |
| 10 | **日志记录和监控不足** | 无法检测和响应攻击 | 集中日志、SIEM、安全监控 |

### 1.2 其他常见漏洞

#### 1.2.1 CSRF (跨站请求伪造)
**防护措施：**
- 使用CSRF Token
- SameSite Cookie属性
- 验证Referer/Origin头
- 敏感操作二次确认

#### 1.2.2 SSRF (服务器端请求伪造)
**防护措施：**
- URL白名单
- 禁用不必要协议(file://, gopher://)
- 内网IP黑名单
- 响应内容验证

#### 1.2.3 点击劫持 (Clickjacking)
**防护措施：**
- X-Frame-Options: DENY/SAMEORIGIN
- Content-Security-Policy: frame-ancestors
- Framekiller脚本

#### 1.2.4 不安全的直接对象引用(IDOR)
**防护措施：**
- 间接引用映射(使用UUID替代自增ID)
- 严格的权限检查
- 资源访问日志

### 1.3 安全编码原则

```
1. 输入验证 - 白名单 > 黑名单
2. 输出编码 - 根据上下文编码
3. 参数化查询 - 永远不要拼接SQL
4. 最小权限 - 只授予必要的权限
5. 深度防御 - 多层安全控制
6. 失败安全 - 默认拒绝
7. 会话安全 - 安全的会话管理
8. 加密存储 - 敏感数据加密
```

---

## 二、身份认证与授权(OAuth/JWT)

### 2.1 OAuth 2.0 / OIDC 安全

#### 2.1.1 OAuth 2.0 授权流程

```
┌─────────┐                                    ┌─────────┐
│  Client │                                    │  Auth   │
│         │──────(1) Authorization Request────▶│ Server  │
│         │◀─────(2) Authorization Grant──────│         │
│         │                                    │         │
│         │──────(3) Access Token Request─────▶│         │
│         │◀─────(4) Access Token─────────────│         │
└─────────┘                                    └─────────┘
```

#### 2.1.2 安全最佳实践

| 安全项 | 推荐做法 |
|--------|----------|
| **PKCE (Proof Key)** | 所有客户端必须实现PKCE |
| **State参数** | 必须验证state防止CSRF |
| **Redirect URI** | 严格白名单验证，禁止通配符 |
| **Scope最小化** | 只请求必要权限 |
| **Token存储** | 使用httpOnly/secure Cookie |
| **Token刷新** | 实现Refresh Token轮换 |

#### 2.1.3 常见OAuth攻击及防护

| 攻击类型 | 描述 | 防护措施 |
|----------|------|----------|
| Authorization Code拦截 | 恶意应用拦截授权码 | PKCE、严格Redirect URI验证 |
| Token泄露 | Token被窃取或日志泄露 | 短有效期、Token绑定、日志脱敏 |
| CSRF | 伪造授权请求 | State参数验证 |
| Scope升级 | 客户端请求额外权限 | 服务端严格验证scope |

### 2.2 JWT (JSON Web Token) 安全

#### 2.2.1 JWT 结构

```
Header.Payload.Signature

Header:    { "alg": "RS256", "typ": "JWT" }
Payload:   { "sub": "user123", "exp": 1234567890, "scope": "read" }
Signature: HMACSHA256(base64(header) + "." + base64(payload), secret)
```

#### 2.2.2 JWT 安全最佳实践

```yaml
算法安全:
  - 禁止: "none" 算法
  - 禁止: HS256 (对称加密用于服务端)
  - 推荐: RS256/ES256 (非对称加密)
  - 必须: 服务端验证算法白名单

Token结构:
  - iss (发行者): 验证Token来源
  - aud (受众): 验证Token用途
  - exp (过期时间): 设置合理过期时间(15-60分钟)
  - iat (签发时间): 防止重放攻击
  - jti (唯一标识): 支持Token吊销

存储安全:
  - 浏览器: httpOnly + Secure + SameSite Cookie
  - 移动端: Keychain/Keystore
  - 服务端: 加密存储

传输安全:
  - 始终使用HTTPS
  - Authorization: Bearer <token>
  - 避免URL传递Token
```

#### 2.2.3 JWT 攻击及防护

| 攻击类型 | 描述 | 防护措施 |
|----------|------|----------|
| 算法混淆攻击 | 修改alg为none/HS256 | 服务端强制指定算法 |
| 密钥泄露 | 密钥被破解或泄露 | 使用足够长度的密钥、定期轮换 |
| Token伪造 | 使用泄露密钥伪造Token | 密钥安全存储、监控异常Token |
| 重放攻击 | 捕获并重用Token | 短有效期、jti黑名单 |

### 2.3 现代身份认证架构

#### 2.3.1 推荐架构

```
┌─────────────────────────────────────────────────────────┐
│                       Client                            │
│  (Browser/Mobile/SPA)                                   │
└─────────────┬───────────────────────────────────────────┘
              │ HTTPS
              ▼
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│  - Rate Limiting                                        │
│  - JWT Validation                                       │
│  - Request/Response Filtering                           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                 Identity Provider                       │
│  (Auth0/Okta/Cognito/Azure AD/Keycloak)                 │
│  - Authentication                                       │
│  - MFA                                                  │
│  - Token Issuance                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 三、容器与云安全

### 3.1 容器安全 (Docker/Kubernetes)

#### 3.1.1 Docker 安全

**镜像安全:**
```dockerfile
# ❌ 不安全
FROM ubuntu:latest
RUN apt-get update && apt-get install -y curl

# ✅ 安全
FROM alpine:3.19 AS builder
# 多阶段构建，最小化攻击面
FROM scratch
COPY --from=builder /app /app
USER nonroot
```

**Dockerfile 安全检查清单:**
- [ ] 使用官方基础镜像
- [ ] 固定镜像版本标签(非latest)
- [ ] 多阶段构建减少镜像大小
- [ ] 使用非root用户运行
- [ ] 最小化镜像层数
- [ ] 扫描镜像漏洞
- [ ] 不存储敏感信息在镜像中
- [ ] 启用Docker Content Trust

**Docker 运行时安全:**
```bash
# 安全运行参数
docker run -d \
  --read-only \\
  --security-opt=no-new-privileges:true \\
  --cap-drop=ALL \\
  --cap-add=NET_BIND_SERVICE \\
  --user=1000:1000 \\
  --memory=512m \\
  --cpus=1.0 \\
  --pids-limit=100 \\
  myapp:latest
```

#### 3.1.2 Kubernetes 安全

**Pod 安全标准:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "256Mi"
        cpu: "500m"
      requests:
        memory: "128Mi"
        cpu: "250m"
```

**Kubernetes 安全组件:**

| 组件 | 用途 | 推荐工具 |
|------|------|----------|
| **Pod Security Admission** | 强制Pod安全策略 | 内置(PSP替代) |
| **Network Policies** | 网络隔离 | Calico/Cilium |
| **RBAC** | 权限控制 | 内置 |
| **Admission Controllers** | 准入控制 | OPA/Gatekeeper/Kyverno |
| **Secrets管理** | 敏感数据 | Vault/External Secrets |
| **Runtime Security** | 运行时监控 | Falco/Tetragon |

### 3.2 云安全 (AWS/Azure/GCP)

#### 3.2.1 云安全责任共担模型

```
┌─────────────────────────────────────────────────────┐
│              云服务提供商责任                        │
│  (物理设施、网络、虚拟化层、托管服务)                │
├─────────────────────────────────────────────────────┤
│                客户责任                              │
│  (操作系统、应用、数据、访问控制、加密)              │
└─────────────────────────────────────────────────────┘
```

#### 3.2.2 云安全最佳实践

**身份与访问管理:**
- 使用IAM角色而非长期凭证
- 实施最小权限原则
- 启用MFA
- 定期轮换凭证
- 使用临时凭证

**数据安全:**
- 启用服务端加密(SSE)
- 使用KMS管理密钥
- 敏感数据分类分级
- 启用访问日志

**网络安全:**
- VPC隔离
- 安全组最小开放
- 使用WAF防护
- DDoS防护

---

## 四、安全扫描与代码审计

### 4.1 静态应用安全测试 (SAST)

**工作原理:**
```
源代码 ──▶ 分析引擎 ──▶ 漏洞检测 ──▶ 报告
              │
              ├── 数据流分析
              ├── 控制流分析
              ├── 语义分析
              └── 配置分析
```

**SAST 工具特性:**
| 特性 | 说明 |
|------|------|
| 误报率 | 高，需要人工确认 |
| 检测时机 | 开发/构建阶段 |
| 检测范围 | 源代码、配置文件 |
| 覆盖漏洞 | 注入、XSS、硬编码密钥等 |

### 4.2 动态应用安全测试 (DAST)

**工作原理:**
```
           ┌──────────────┐
           │   DAST工具   │
           └──────┬───────┘
                  │ 发送攻击Payload
                  ▼
            ┌───────────┐
   响应分析 │ 运行中的   │ 行为分析
   ◀───────│   应用    │───────▶
            └───────────┘
```

**DAST vs SAST:**

| 特性 | SAST | DAST |
|------|------|------|
| 检测阶段 | 编码/构建 | 运行时 |
| 代码访问 | 需要 | 不需要 |
| 误报率 | 较高 | 较低 |
| 检测能力 | 已知模式 | 实际漏洞 |
| 覆盖范围 | 全代码 | 暴露面 |

### 4.3 软件成分分析 (SCA)

**SCA 检测内容:**
- 开源组件漏洞(CVE)
- 许可证合规性
- 过期依赖
- 恶意包检测

### 4.4 交互式应用安全测试 (IAST)

**优势:**
- 结合SAST和DAST优点
- 低误报率
- 精确定位漏洞
- 运行时上下文分析

### 4.5 代码审计检查清单

```markdown
## 代码审计检查清单

### 输入验证
- [ ] 所有用户输入都经过验证
- [ ] 使用白名单而非黑名单
- [ ] 验证输入长度和类型
- [ ] 验证文件上传类型和大小

### 输出编码
- [ ] HTML上下文输出编码
- [ ] JavaScript上下文编码
- [ ] URL参数编码
- [ ] SQL查询参数化

### 认证授权
- [ ] 密码强度策略
- [ ] 会话管理安全
- [ ] 权限检查在所有敏感操作
- [ ] 防止IDOR攻击

### 敏感数据
- [ ] 敏感数据加密存储
- [ ] 日志中不包含敏感信息
- [ ] 配置文件无硬编码密钥
- [ ] 使用密钥管理服务

### 错误处理
- [ ] 不向用户暴露详细错误
- [ ] 统一错误处理机制
- [ ] 错误日志记录

### 依赖安全
- [ ] 依赖包无已知漏洞
- [ ] 使用私有仓库
- [ ] 定期更新依赖
```

---

## 五、DevSecOps流程集成

### 5.1 DevSecOps 流水线

```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│   Plan   │   Code   │  Build   │   Test   │  Deploy  │  Operate │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 威胁建模 │   SAST   │   SCA    │   DAST   │ 配置检查 │ 运行监控 │
│ 安全需求 │ 预提交   │ 镜像扫描 │ 模糊测试 │ 密钥扫描 │ 漏洞管理 │
│          │ 代码审查 │ 依赖检查 │ IAST     │ 合规检查 │ 事件响应 │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 5.2 安全左移 (Shift Left)

**传统模式 vs DevSecOps:**
```
传统: 开发 ──▶ 测试 ──▶ 部署 ──▶ 安全审计 ──▶ 漏洞修复(高成本)

DevSecOps:
规划 ──▶ 编码(SAST) ──▶ 构建(SCA/镜像扫描) ──▶ 测试(DAST) ──▶ 部署(配置扫描)
         早期发现问题 ──▶ 低成本修复
```

### 5.3 CI/CD 安全集成示例

**GitLab CI 安全配置:**

```yaml
stages:
  - build
  - test
  - security
  - deploy

# SAST - 静态分析
sast:
  stage: security
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --error --json-output=semgrep.json
  artifacts:
    reports:
      sast: semgrep.json
  allow_failure: false

# SCA - 依赖检查
sca:
  stage: security
  image: node:18-alpine
  script:
    - npm audit --audit-level=high
    - npx audit-ci --high
  allow_failure: false

# Secret Detection - 密钥扫描
detect-secrets:
  stage: security
  image: python:3.11-alpine
  script:
    - pip install detect-secrets
    - detect-secrets scan --all-files --force-use-all-plugins
  allow_failure: false

# Container Scanning - 镜像扫描
container_scan:
  stage: security
  image: aquasec/trivy
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  allow_failure: false

# IaC Scanning - 基础设施扫描
iac_scan:
  stage: security
  image: bridgecrew/checkov
  script:
    - checkov -d . --compact
  allow_failure: false
```

**GitHub Actions 安全配置:**

```yaml
name: Security Pipeline

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # SAST - Semgrep
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/cwe-top-25

      # SCA - Dependabot/Node Audit
      - name: Run npm audit
        run: npm audit --audit-level=high

      # Secret Scanning - TruffleHog
      - name: Secret Detection
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: main
          head: HEAD

      # CodeQL Analysis
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript,typescript

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

### 5.4 安全门禁策略

```yaml
# 安全门禁示例
security_gates:
  block_on:
    - critical_vulnerabilities: > 0
    - high_vulnerabilities: > 5
    - secrets_detected: true
    - compliance_violations: > 0
    - code_coverage: < 80%
  
  warn_on:
    - medium_vulnerabilities: > 10
    - dependencies_outdated: > 5
  
  exceptions:
    - path: "test/**"
      reason: "Test files are not deployed"
      approved_by: "security-team"
```

---

## 六、安全检查清单

### 6.1 应用安全检查清单

```markdown
## Web应用安全基线检查

### 基础安全
- [ ] HTTPS全站启用，HSTS配置
- [ ] 安全响应头配置完整
  - [ ] Content-Security-Policy
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY/SAMEORIGIN
  - [ ] Strict-Transport-Security
  - [ ] Referrer-Policy
  - [ ] Permissions-Policy
- [ ] Cookie安全属性
  - [ ] Secure
  - [ ] HttpOnly
  - [ ] SameSite
- [ ] 敏感操作CSRF防护
- [ ] 文件上传安全
  - [ ] 类型白名单
  - [ ] 大小限制
  - [ ] 存储隔离
  - [ ] 病毒扫描

### 认证授权
- [ ] 强密码策略
- [ ] 账户锁定机制
- [ ] MFA支持
- [ ] 会话管理
  - [ ] 超时退出
  - [ ] 并发登录限制
  - [ ] 安全登出
- [ ] 密码重置安全
- [ ] JWT安全配置

### 输入输出
- [ ] SQL注入防护
- [ ] XSS防护
- [ ] 命令注入防护
- [ ] 路径遍历防护
- [ ] XML外部实体防护
- [ ] SSRF防护

### 数据安全
- [ ] 敏感数据加密存储
- [ ] 传输加密(TLS 1.3)
- [ ] 密钥安全管理
- [ ] 数据脱敏
- [ ] 备份加密

### 日志监控
- [ ] 安全事件记录
- [ ] 审计日志完整
- [ ] 日志防篡改
- [ ] 异常告警
- [ ] 日志保留策略
```

### 6.2 API 安全检查清单

```markdown
## API 安全基线检查

### 认证授权
- [ ] OAuth 2.0 / OIDC 实现
- [ ] PKCE 支持
- [ ] Scope 限制
- [ ] Token 过期策略
- [ ] API 密钥管理

### 请求安全
- [ ] 请求签名验证
- [ ] 重放攻击防护
- [ ] 请求大小限制
- [ ] 参数验证
- [ ] Content-Type 验证

### 限流防护
- [ ] 速率限制
- [ ] 并发限制
- [ ] 配额管理
- [ ] DDoS 防护

### 数据安全
- [ ] 响应数据最小化
- [ ] 错误信息脱敏
- [ ] 批量操作限制
- [ ] 敏感操作二次确认
```

### 6.3 容器云安全检查清单

```markdown
## Kubernetes 安全基线检查

### 集群配置
- [ ] API Server 安全配置
  - [ ] 禁用匿名访问
  - [ ] 启用审计日志
  - [ ] TLS 双向认证
- [ ] etcd 加密
- [ ] 网络策略启用

### 工作负载安全
- [ ] Pod 安全标准
- [ ] 非root运行
- [ ] 只读文件系统
- [ ] 资源限制
- [ ] 安全上下文配置

### 访问控制
- [ ] RBAC 配置
- [ ] ServiceAccount 最小权限
- [ ] 定期审查权限

### 镜像安全
- [ ] 镜像扫描
- [ ] 镜像签名验证
- [ ] 私有镜像仓库
- [ ] 镜像拉取策略

### 运行时安全
- [ ] Falco 部署
- [ ] 异常行为监控
- [ ] 网络流量监控
```

---

## 七、安全工具推荐

### 7.1 SAST 工具

| 工具 | 语言支持 | 特点 | 许可 |
|------|----------|------|------|
| **Semgrep** | 多语言 | 快速、可定制规则、CI友好 | 开源/商业 |
| **SonarQube** | 多语言 | 代码质量+安全、企业级 | 开源/商业 |
| **Checkmarx** | 多语言 | 企业级、深度分析 | 商业 |
| **CodeQL** | 多语言 | GitHub集成、语义分析 | 开源 |
| **Bandit** | Python | Python专用 | 开源 |
| **Brakeman** | Ruby | Rails专用 | 开源 |
| **ESLint Security** | JS/TS | 前端安全规则 | 开源 |

### 7.2 DAST 工具

| 工具 | 特点 | 许可 |
|------|------|------|
| **OWASP ZAP** | 功能全面、自动化、社区活跃 | 开源 |
| **Burp Suite** | 专业渗透测试、功能强大 | 商业/免费社区版 |
| **Nuclei** | 快速、模板化、DevOps友好 | 开源 |
| **Arachni** | 高性能、分布式 | 开源 |

### 7.3 SCA 工具

| 工具 | 特点 | 许可 |
|------|------|------|
| **Snyk** | 开发者友好、修复建议、多语言 | 开源/商业 |
| **OWASP Dependency-Check** | 免费、支持多种语言 | 开源 |
| **WhiteSource/Mend** | 企业级、合规支持 | 商业 |
| **FOSSA** | 许可证合规、CI集成 | 开源/商业 |
| **npm audit** | Node.js内置 | 免费 |
| **pip-audit** | Python | 开源 |

### 7.4 容器安全工具

| 工具 | 功能 | 许可 |
|------|------|------|
| **Trivy** | 镜像扫描、SCA、配置检查 | 开源 |
| **Grype** | 快速镜像扫描 | 开源 |
| **Clair** | 静态分析镜像漏洞 | 开源 |
| **Falco** | 运行时安全监控 | 开源 |
| **Tetragon** | eBPF运行时安全 | 开源 |
| **Kube-bench** | CIS Kubernetes基准测试 | 开源 |
| **Kube-hunter** | Kubernetes渗透测试 | 开源 |

### 7.5 密钥扫描工具

| 工具 | 特点 | 许可 |
|------|------|------|
| **TruffleHog** | 深度扫描、熵检测、验证 | 开源 |
| **GitLeaks** | 快速、可定制 | 开源 |
| **GitGuardian** | 企业级、实时监控 | 商业 |
| **detect-secrets** | Yelp出品、可扩展 | 开源 |

### 7.6 IaC 安全工具

| 工具 | 支持平台 | 许可 |
|------|----------|------|
| **Checkov** | Terraform/CloudFormation/K8s | 开源 |
| **Tfsec** | Terraform | 开源 |
| **Terrascan** | Terraform/K8s/Docker | 开源 |
| **Kics** | 多平台 | 开源 |
| **OPA/Gatekeeper** | K8s策略 | 开源 |
| **Kyverno** | K8s原生策略 | 开源 |

### 7.7 综合安全平台

| 平台 | 功能覆盖 | 目标用户 |
|------|----------|----------|
| **Snyk** | SAST/SCA/容器/IaC | 开发者 |
| **SonarQube** | SAST/代码质量 | 企业 |
| **Veracode** | SAST/DAST/SCA | 企业 |
| **Checkmarx One** | 全生命周期 | 企业 |
| **DefectDojo** | 漏洞管理 | 安全团队 |

### 7.8 开源安全工具组合推荐

```yaml
# 小型团队/个人项目 (免费)
stack:
  sast: Semgrep
  sca: npm audit / pip-audit + OWASP Dependency-Check
  dast: OWASP ZAP
  container: Trivy
  secrets: TruffleHog
  iac: Checkov

# 中型团队 (混合)
stack:
  sast: SonarQube Community + Semgrep
  sca: Snyk Open Source
  dast: OWASP ZAP + Nuclei
  container: Trivy + Falco
  secrets: GitLeaks
  iac: Checkov + OPA

# 企业级 (商业)
stack:
  sast: Checkmarx / Veracode
  sca: Snyk / WhiteSource
  dast: Burp Suite Enterprise
  container: Aqua / Sysdig
  secrets: GitGuardian
  iac: Bridgecrew / Snyk IaC
```

---

## 八、安全最佳实践指南

### 8.1 安全开发生命周期 (SDLC)

```
┌─────────────────────────────────────────────────────────────┐
│                      安全SDLC                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  需求阶段 ──▶ 威胁建模 ──▶ 识别攻击面 ──▶ 定义安全需求      │
│      │                                                      │
│      ▼                                                      │
│  设计阶段 ──▶ 安全设计评审 ──▶ 安全架构设计                 │
│      │                                                      │
│      ▼                                                      │
│  编码阶段 ──▶ 安全编码规范 ──▶ 静态分析 ──▶ 代码审查       │
│      │                                                      │
│      ▼                                                      │
│  测试阶段 ──▶ 动态扫描 ──▶ 渗透测试 ──▶ 模糊测试           │
│      │                                                      │
│      ▼                                                      │
│  部署阶段 ──▶ 配置检查 ──▶ 镜像扫描 ──▶ 上线审批           │
│      │                                                      │
│      ▼                                                      │
│  运营阶段 ──▶ 监控告警 ──▶ 应急响应 ──▶ 漏洞管理           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 威胁建模方法

**STRIDE 威胁分类:**
| 威胁 | 描述 | 防护 |
|------|------|------|
| **S**poofing | 身份伪造 | 认证、数字签名 |
| **T**ampering | 数据篡改 | 完整性校验、签名 |
| **R**epudiation | 抵赖 | 审计日志、不可抵赖 |
| **I**nformation Disclosure | 信息泄露 | 加密、访问控制 |
| **D**enial of Service | 拒绝服务 | 限流、容灾 |
| **E**levation of Privilege | 权限提升 | 授权检查、沙箱 |

**威胁建模流程:**
1. 识别资产
2. 创建架构图
3. 识别威胁(STRIDE)
4. 评估风险(DREAD)
5. 制定缓解措施
6. 验证和迭代

### 8.3 安全编码规范

**输入处理原则:**
```
1. 信任边界明确
2. 输入在边界处验证
3. 使用白名单验证
4. 验证失败即拒绝
5. 规范化后再验证
```

**输出编码原则:**
```
1. 根据上下文编码
2. HTML: HTML实体编码
3. JavaScript: JS编码
4. URL: URL编码
5. CSS: CSS编码
6. SQL: 参数化查询
```

**错误处理原则:**
```
1. 不要向用户暴露系统信息
2. 统一错误处理
3. 记录详细错误日志
4. 安全的默认值
5. 优雅降级
```

### 8.4 安全配置基线

**Web服务器安全:**
```nginx
# Nginx 安全配置示例
server {
    # SSL配置
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # 安全响应头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 隐藏版本信息
    server_tokens off;
    
    # 限制请求方法
    if ($request_method !~ ^(GET|HEAD|POST)$) {
        return 405;
    }
}
```

**数据库安全:**
```sql
-- MySQL 安全配置
-- 删除匿名用户
DELETE FROM mysql.user WHERE User='';

-- 删除远程root访问
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1');

-- 删除测试数据库
DROP DATABASE IF EXISTS test;

-- 启用SSL
REQUIRE SSL;

-- 启用查询日志
SET GLOBAL general_log = 'ON';
```

### 8.5 安全监控与响应

**安全监控覆盖:**
| 层级 | 监控内容 | 工具 |
|------|----------|------|
| 应用层 | 异常请求、业务逻辑异常 | APM工具 |
| 主机层 | 文件完整性、进程监控 | OSSEC/AIDE |
| 容器层 | 容器逃逸、异常网络 | Falco |
| 网络层 | 流量异常、DDoS | IDS/IPS |
| 日志层 | 登录异常、权限变更 | ELK/Splunk |

**应急响应流程:**
```
检测 ──▶ 响应 ──▶ 遏制 ──▶ 根除 ──▶ 恢复 ──▶ 总结
  │        │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼        ▼
告警    初步分析  隔离系统  清除恶意  恢复服务  复盘改进
日志    确定范围  阻断通信  修补漏洞  加强监控  更新预案
```

### 8.6 合规性框架

**主要安全标准:**
| 标准 | 适用范围 | 重点 |
|------|----------|------|
| **OWASP ASVS** | 应用安全 | 安全需求、验证 |
| **CIS Controls** | 企业安全 | 安全控制措施 |
| **NIST CSF** | 网络安全 | 风险管理框架 |
| **ISO 27001** | 信息安全管理 | 管理体系 |
| **SOC 2** | 服务组织 | 信任服务标准 |
| **PCI DSS** | 支付卡行业 | 数据安全 |
| **GDPR** | 欧盟数据保护 | 隐私保护 |

**ASVS 级别选择:**
- **Level 1** - 最低安全标准，适用于所有应用
- **Level 2** - 敏感数据保护，适用于大多数应用
- **Level 3** - 最高安全要求，适用于关键系统

---

## 附录

### A. 快速参考卡片

```yaml
# 安全响应头速查
Security Headers:
  Content-Security-Policy: "default-src 'self'"
  X-Content-Type-Options: "nosniff"
  X-Frame-Options: "DENY"
  X-XSS-Protection: "1; mode=block"
  Strict-Transport-Security: "max-age=31536000; includeSubDomains"
  Referrer-Policy: "strict-origin-when-cross-origin"
  Permissions-Policy: "geolocation=(), microphone=()"

# Cookie安全速查
Secure Cookies:
  Secure: true
  HttpOnly: true
  SameSite: "Strict"
  Max-Age: 3600

# JWT安全速查
JWT Security:
  Algorithm: RS256/ES256
  Expiration: 15-60 minutes
  Issuer: 验证iss
  Audience: 验证aud
  Storage: httpOnly cookie
```

### B. 资源链接

- [OWASP](https://owasp.org/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [CNCF Security TAG](https://github.com/cncf/tag-security)

---

*文档版本: v1.0*  
*最后更新: 2026-02-16*  
*作者: Agent 4 - 安全与DevSecOps研究*
