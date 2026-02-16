# 零信任安全架构实施手册

**版本**: v1.0  
**日期**: 2026-02-16  
**适用场景**: 云原生微服务架构 / Kubernetes 集群

---

## 目录

1. [零信任网络架构（ZTA）设计原则](#一零信任网络架构zta设计原则)
2. [身份感知代理（IAP）实现](#二身份感知代理iap实现)
3. [微服务间mTLS通信实践](#三微服务间mtls通信实践)
4. [密钥管理（HashiCorp Vault深入）](#四密钥管理hashicorp-vault深入)
5. [云原生安全（OPA策略即代码）](#五云原生安全opa策略即代码)
6. [附录：快速配置模板](#附录快速配置模板)

---

## 一、零信任网络架构（ZTA）设计原则

### 1.1 核心理念

零信任安全模型的核心信条：**"永不信任，始终验证" (Never Trust, Always Verify)**

| 传统安全模型 | 零信任模型 |
|------------|-----------|
| 内网=信任区域 | 无边界安全 |
| 边界防御为主 | 持续验证 |
| 静态访问控制 | 动态授权 |
| 网络位置决定信任 | 身份决定信任 |

### 1.2 NIST SP 800-207 零信任架构原则

```
┌─────────────────────────────────────────────────────────────────┐
│                    零信任架构核心原则                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. 所有数据源和计算服务都被视为资源                             │
│ 2. 无论网络位置如何，所有通信都必须安全                          │
│ 3. 对企业资源的访问是逐个会话授予的                              │
│ 4. 访问控制是动态的策略决定                                      │
│ 5. 企业监控并测量所有资产的完整性和安全态势                      │
│ 6. 所有资产的认证和授权是动态的，在访问前强制执行                │
│ 7. 企业尽可能收集信息以改进安全态势                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 实施框架

```
                    ┌─────────────────────┐
                    │    策略决策点 (PDP)  │
                    │  Policy Decision    │
                    │     Point           │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   策略引擎   │    │   信任算法   │    │  策略管理   │
    │Policy Engine │    │   Trust     │    │   Admin     │
    └─────────────┘    └─────────────┘    └─────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    策略执行点 (PEP)  │
                    │  Policy Enforcement │
                    │       Point         │
                    └─────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   ┌─────────┐          ┌──────────┐          ┌──────────┐
   │  用户   │          │  设备    │          │  工作负载 │
   │  User   │          │ Device   │          │ Workload │
   └─────────┘          └──────────┘          └──────────┘
```

### 1.4 关键组件

| 组件 | 功能描述 | 典型实现 |
|-----|---------|---------|
| **身份提供商 (IdP)** | 统一身份认证 | Keycloak, Azure AD, Okta |
| **设备清单** | 设备安全状态管理 | Microsoft Intune, Jamf |
| **策略引擎** | 访问决策 | OPA, Cedar |
| **策略执行点** | 访问控制执行 | Envoy, Istio, NGINX |
| **安全分析** | 行为分析与威胁检测 | SIEM, XDR |

---

## 二、身份感知代理（IAP）实现

### 2.1 IAP 架构设计

身份感知代理是零信任架构的关键入口组件，负责：
- 统一身份认证
- 细粒度访问控制
- 会话管理
- 审计日志

```
┌─────────────────────────────────────────────────────────────┐
│                        公网流量                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloudflare Access /                        │
│                  Google Cloud IAP /                         │
│                  AWS Verified Access /                      │
│                  自建 IAP (基于 Envoy)                       │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  认证模块    │───▶│  授权模块    │───▶│  代理模块    │     │
│  │  OAuth2/OIDC │    │  RBAC/ABAC   │    │  Reverse     │     │
│  │  SAML/LDAP   │    │  Policy      │    │  Proxy       │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │   内部应用服务     │
              │  (无需直接暴露)    │
              └───────────────────┘
```

### 2.2 自建 IAP：基于 Envoy + OAuth2 Filter

**配置模板：Envoy OAuth2 过滤器**

```yaml
# envoy-iap.yaml
static_resources:
  listeners:
  - name: ingress_listener
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 8080
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          codec_type: AUTO
          route_config:
            name: local_route
            virtual_hosts:
            - name: backend
              domains: ["*"]
              routes:
              - match:
                  prefix: "/"
                route:
                  cluster: internal_service
                  timeout: 30s
          http_filters:
          # OAuth2 认证过滤器
          - name: envoy.filters.http.oauth2
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.oauth2.v3.OAuth2
              token_endpoint:
                cluster: oauth2_cluster
                uri: "https://auth.example.com/oauth2/token"
                timeout: 5s
              authorization_endpoint: "https://auth.example.com/oauth2/authorize"
              credentials:
                client_id: "${OAUTH_CLIENT_ID}"
                token_secret:
                  name: oauth2_client_secret
                  sds_config:
                    path: /etc/envoy/secrets/oauth2_client_secret.yaml
                hmac_secret:
                  name: hmac_secret
                  sds_config:
                    path: /etc/envoy/secrets/hmac_secret.yaml
              redirect_uri: "https://app.example.com/oauth2/callback"
              redirect_path_matcher:
                path:
                  exact: /oauth2/callback
              signout_path:
                path:
                  exact: /oauth2/signout
              forward_bearer_token: true
              # 认证通过后添加的头信息
              auth_scopes:
              - openid
              - profile
              - email
          # JWT 验证过滤器（可选，用于细粒度授权）
          - name: envoy.filters.http.jwt_authn
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.jwt_authn.v3.JwtAuthentication
              providers:
                keycloak:
                  issuer: "https://auth.example.com/realms/production"
                  audiences: ["app-client-id"]
                  remote_jwks:
                    http_uri:
                      uri: "https://auth.example.com/realms/production/protocol/openid-connect/certs"
                      cluster: keycloak_cluster
                      timeout: 5s
                  forward: true
                  payload_in_metadata: jwt_payload
              rules:
              - match:
                  prefix: /admin
                requires:
                  provider_name: keycloak
              - match:
                  prefix: /
                requires:
                  provider_name: keycloak
          # RBAC 授权过滤器
          - name: envoy.filters.http.rbac
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.rbac.v3.RBAC
              rules:
                action: ALLOW
                policies:
                  admin_policy:
                    permissions:
                    - url_path:
                        path:
                          prefix: /admin
                    principals:
                    - metadata:
                        filter: envoy.filters.http.jwt_authn
                        path:
                        - key: jwt_payload
                        - key: realm_access
                        - key: roles
                        value:
                          list_match:
                            one_of:
                              string_match:
                                exact: admin
                  user_policy:
                    permissions:
                    - any: true
                    principals:
                    - metadata:
                        filter: envoy.filters.http.jwt_authn
                        path:
                        - key: jwt_payload
                        - key: sub
                        value:
                          string_match:
                            safe_regex:
                              regex: ".+"
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
  - name: internal_service
    connect_timeout: 5s
    type: STRICT_DNS
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: internal_service
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: internal-app
                port_value: 8081
  
  - name: oauth2_cluster
    connect_timeout: 5s
    type: LOGICAL_DNS
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: oauth2_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: auth.example.com
                port_value: 443
    transport_socket:
      name: envoy.transport_sockets.tls
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
        sni: auth.example.com

  - name: keycloak_cluster
    connect_timeout: 5s
    type: LOGICAL_DNS
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: keycloak_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: auth.example.com
                port_value: 443
    transport_socket:
      name: envoy.transport_sockets.tls
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
        sni: auth.example.com
```

### 2.3 Kubernetes Ingress 集成 IAP

```yaml
# iap-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iap-protected-ingress
  namespace: production
  annotations:
    # 使用 NGINX Ingress Controller + oauth2-proxy
    nginx.ingress.kubernetes.io/auth-url: "https://$host/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://$host/oauth2/start?rd=$escaped_request_uri"
    nginx.ingress.kubernetes.io/auth-response-headers: "Authorization,X-Auth-Request-User,X-Auth-Request-Email,X-Auth-Request-Groups"
    # 配置连接限制
    nginx.ingress.kubernetes.io/limit-connections: "10"
    nginx.ingress.kubernetes.io/limit-rps: "5"
    # 启用 CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Authorization, Content-Type, X-Request-ID"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: protected-app
            port:
              number: 80
---
# OAuth2-Proxy Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:v7.5.1
        args:
        - --provider=oidc
        - --oidc-issuer-url=https://auth.example.com/realms/production
        - --client-id=$(CLIENT_ID)
        - --client-secret=$(CLIENT_SECRET)
        - --cookie-secret=$(COOKIE_SECRET)
        - --cookie-secure=true
        - --cookie-httponly=true
        - --cookie-samesite=lax
        - --cookie-domain=.example.com
        - --cookie-expire=24h
        - --cookie-refresh=1h
        - --email-domain=*
        - --upstream=static://202
        - --http-address=0.0.0.0:4180
        - --redirect-url=https://app.example.com/oauth2/callback
        - --pass-access-token=true
        - --pass-authorization-header=true
        - --set-authorization-header=true
        - --set-xauthrequest=true
        - --scope=openid email profile groups
        env:
        - name: CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: client-id
        - name: CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: client-secret
        - name: COOKIE_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: cookie-secret
        ports:
        - containerPort: 4180
          name: http
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /ping
            port: 4180
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 4180
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: oauth2-proxy
  namespace: production
spec:
  selector:
    app: oauth2-proxy
  ports:
  - port: 4180
    targetPort: 4180
```

---

## 三、微服务间mTLS通信实践

### 3.1 mTLS 核心概念

双向 TLS（Mutual TLS）要求通信双方互相验证身份：

```
┌─────────────────────────────────────────────────────────────┐
│                      mTLS 握手流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Client                              Server                │
│     │                                   │                   │
│     │── ClientHello ───────────────────▶│  协商加密套件     │
│     │                                   │                   │
│     │◀── ServerHello ───────────────────│                   │
│     │◀── Server Certificate ────────────│  服务端证书       │
│     │◀── CertificateRequest ────────────│  请求客户端证书   │
│     │                                   │                   │
│     │── Client Certificate ────────────▶│  客户端证书       │
│     │── ClientKeyExchange ─────────────▶│                   │
│     │── CertificateVerify ─────────────▶│  验证客户端       │
│     │── [ChangeCipherSpec] ────────────▶│                   │
│     │── Finished ──────────────────────▶│                   │
│     │                                   │                   │
│     │◀── [ChangeCipherSpec] ────────────│                   │
│     │◀── Finished ──────────────────────│                   │
│     │                                   │                   │
│     │◀═══ 加密通信通道建立 ═════════════▶│                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Istio Service Mesh mTLS 配置

#### 3.2.1 启用集群级严格 mTLS

```yaml
# peerauthentication-strict.yaml
# 全局严格 mTLS 策略
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
---
# 按命名空间覆盖（如有需要）
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: permissive-workload
  namespace: legacy-system
spec:
  mtls:
    mode: PERMISSIVE  # 兼容非 mTLS 客户端
  selector:
    matchLabels:
      app: legacy-app
```

#### 3.2.2 自动 TLS 证书管理

```yaml
# istio-operator-mtls.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-mtls-config
spec:
  profile: default
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
  meshConfig:
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
    enableAutoMtls: true  # 自动 mTLS
    trustDomain: cluster.local
    trustDomainAliases:
    - "*.cluster.local"
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 2000m
            memory: 1Gi
      # 使用自定义 CA
      caAddress: cert-manager-istio-csr.cert-manager.svc:443
    pilot:
      env:
        PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY: "true"
        PILOT_ENABLE_K8S_SELECT_WORKLOAD_ENTRIES: "false"
```

#### 3.2.3 工作负载身份与授权

```yaml
# authorization-policy.yaml
# 服务级访问控制
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-service-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  action: ALLOW
  rules:
  # 规则1：只允许 order-service 调用支付接口
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/order-service"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/payments/*"]
    when:
    - key: request.auth.claims[groups]
      values: ["payment-operators"]
  
  # 规则2：只允许特定命名空间访问健康检查
  - from:
    - source:
        namespaces: ["istio-system", "monitoring"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/health", "/ready"]
  
  # 规则3：拒绝所有其他访问
  - from:
    - source:
        notNamespaces: ["production", "istio-system"]
    to:
    - operation:
        methods: ["*"]
    action: DENY
---
# 请求认证（JWT验证）
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: api-jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  jwtRules:
  - issuer: "https://auth.example.com/realms/production"
    jwksUri: "https://auth.example.com/realms/production/protocol/openid-connect/certs"
    audiences: ["api-gateway"]
    forwardOriginalToken: true
    outputPayloadToHeader: x-jwt-payload
```

### 3.3 自定义 mTLS：Go 语言实现

```go
// mtls-server.go - mTLS 服务端示例
package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
)

func main() {
	// 加载 CA 证书池
	caCert, err := ioutil.ReadFile("/certs/ca.crt")
	if err != nil {
		log.Fatalf("Failed to read CA cert: %v", err)
	}
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)

	// 加载服务端证书
	cert, err := tls.LoadX509KeyPair("/certs/server.crt", "/certs/server.key")
	if err != nil {
		log.Fatalf("Failed to load server cert: %v", err)
	}

	// 配置 TLS
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		ClientCAs:    caCertPool,
		ClientAuth:   tls.RequireAndVerifyClientCert,
		MinVersion:   tls.VersionTLS13,
		CipherSuites: []uint16{
			tls.TLS_AES_256_GCM_SHA384,
			tls.TLS_CHACHA20_POLY1305_SHA256,
			tls.TLS_AES_128_GCM_SHA256,
		},
		PreferServerCipherSuites: true,
	}

	// 创建 HTTP 服务
	server := &http.Server{
		Addr:      ":8443",
		TLSConfig: tlsConfig,
		Handler:   http.HandlerFunc(handler),
	}

	log.Println("Starting mTLS server on :8443")
	if err := server.ListenAndServeTLS("", ""); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func handler(w http.ResponseWriter, r *http.Request) {
	// 获取客户端证书信息
	if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
		clientCert := r.TLS.PeerCertificates[0]
		log.Printf("Client: %s, Serial: %s", 
			clientCert.Subject.CommonName, 
			clientCert.SerialNumber)
	}
	
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "Authenticated as: %s\n", r.TLS.PeerCertificates[0].Subject.CommonName)
}
```

```go
// mtls-client.go - mTLS 客户端示例
package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

func main() {
	// 加载 CA 证书
	caCert, err := ioutil.ReadFile("/certs/ca.crt")
	if err != nil {
		log.Fatalf("Failed to read CA cert: %v", err)
	}
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)

	// 加载客户端证书
	cert, err := tls.LoadX509KeyPair("/certs/client.crt", "/certs/client.key")
	if err != nil {
		log.Fatalf("Failed to load client cert: %v", err)
	}

	// 配置 TLS
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caCertPool,
		MinVersion:   tls.VersionTLS13,
		ServerName:   "payment-service.production.svc.cluster.local",
	}

	// 创建 HTTP 客户端
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
		},
		Timeout: 30 * time.Second,
	}

	// 发送请求
	resp, err := client.Get("https://payment-service.production.svc:8443/api/payments")
	if err != nil {
		log.Fatalf("Request failed: %v", err)
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Printf("Status: %s\nBody: %s\n", resp.Status, string(body))
}
```

### 3.4 cert-manager 证书自动轮转

```yaml
# cert-manager-ca.yaml
# 创建自签名 CA
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
---
# CA 证书
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: service-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: Service Mesh CA
  secretName: service-ca-secret
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer
    group: cert-manager.io
---
# 基于 CA 的 Issuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: service-ca-issuer
spec:
  ca:
    secretName: service-ca-secret
---
# 为服务自动颁发证书
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: payment-service-tls
  namespace: production
spec:
  secretName: payment-service-tls-secret
  duration: 2160h  # 90天
  renewBefore: 360h  # 15天前自动续期
  subject:
    organizations:
    - production
  commonName: payment-service
  dnsNames:
  - payment-service
  - payment-service.production
  - payment-service.production.svc.cluster.local
  issuerRef:
    name: service-ca-issuer
    kind: ClusterIssuer
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
  - server auth
  - client auth
```

---

## 四、密钥管理（HashiCorp Vault深入）

### 4.1 Vault 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vault 高可用架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐          ┌─────────────┐                     │
│   │  Vault Node │◄────────►│  Vault Node │                     │
│   │   (Active)  │   Raft   │  (Standby)  │                     │
│   └──────┬──────┘          └─────────────┘                     │
│          │                                                      │
│          │  Storage Backend                                     │
│          ▼                                                      │
│   ┌─────────────┐                                              │
│   │ Integrated  │                                              │
│   │   Storage   │                                              │
│   │   (Raft)    │                                              │
│   └─────────────┘                                              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                     Secret Engines                       │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│   │  │   KV    │  │  PKI    │  │ Database│  │ Transit │    │   │
│   │  │  V1/V2  │  │  (TLS)  │  │  Dynamic│  │Encrypt/ │    │   │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│   │  │  AWS    │  │  Azure  │  │  GCP    │  │  SSH    │    │   │
│   │  │Dynamic │  │Dynamic │  │Dynamic │  │  OTP    │    │   │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                     Auth Methods                         │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │  Kubernetes │ LDAP │ OIDC │ AppRole │ AWS-IAM │ Token  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Vault 在 Kubernetes 中的部署

```yaml
# vault-values.yaml - Helm 安装配置
global:
  enabled: true
  tlsDisable: false

server:
  image:
    repository: hashicorp/vault
    tag: "1.15.2"
  
  # 高可用配置
  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true
        listener "tcp" {
          tls_disable = 0
          tls_cert_file = "/vault/userconfig/vault-server-tls/tls.crt"
          tls_key_file  = "/vault/userconfig/vault-server-tls/tls.key"
          tls_client_ca_file = "/vault/userconfig/vault-server-tls/ca.crt"
          address = "[::]:8200"
          cluster_address = "[::]:8201"
          telemetry {
            prometheus_retention_time = "30s"
            disable_hostname = true
          }
        }
        storage "raft" {
          path = "/vault/data"
          retry_leader_election = true
          autopilot {
            cleanup_dead_servers = "true"
            last_contact_threshold = "10s"
            max_trailing_logs = 1000
            min_quorum = 3
            server_stabilization_time = "10s"
          }
        }
        service_registration "kubernetes" {}
        seal "awskms" {
          region     = "us-east-1"
          kms_key_id = "arn:aws:kms:us-east-1:xxxx:key/xxxx"
        }
        telemetry {
          prometheus_retention_time = "30s"
          disable_hostname = true
        }
  
  # 资源限制
  resources:
    requests:
      memory: 512Mi
      cpu: 500m
    limits:
      memory: 2Gi
      cpu: 2000m
  
  # 数据持久化
  dataStorage:
    enabled: true
    size: 10Gi
    storageClass: fast-ssd
  
  # TLS 证书
  volumes:
  - name: userconfig-vault-server-tls
    secret:
      defaultMode: 420
      secretName: vault-server-tls
  volumeMounts:
  - mountPath: /vault/userconfig/vault-server-tls
    name: userconfig-vault-server-tls
    readOnly: true

  # 自动解封配置（使用 AWS KMS）
  extraEnvironmentVars:
    VAULT_SEAL_TYPE: awskms
    AWS_REGION: us-east-1

  # 审计日志
  auditStorage:
    enabled: true
    size: 5Gi

# Vault Agent Injector 配置
injector:
  enabled: true
  replicas: 2
  metrics:
    enabled: true
  
# CSI Provider 配置
csi:
  enabled: true
  daemonSet:
    updateStrategy:
      type: RollingUpdate
      maxUnavailable: ""
```

### 4.3 Vault 初始化与配置

```bash
#!/bin/bash
# vault-init.sh - Vault 初始化脚本

set -e

NAMESPACE="vault"
VAULT_POD="vault-0"

# 1. 等待 Vault Pod 就绪
echo "Waiting for Vault pod..."
kubectl wait --for=condition=Ready pod/${VAULT_POD} -n ${NAMESPACE} --timeout=300s

# 2. 初始化 Vault (仅在首次安装时执行)
echo "Initializing Vault..."
kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -format=json > vault-init.json

# 3. 保存恢复密钥（生产环境应使用安全存储）
echo "Unseal keys saved to vault-init.json (SECURE THIS FILE!)"

# 4. 解封 Vault
export VAULT_ADDR="https://vault.${NAMESPACE}.svc.cluster.local:8200"

for i in 0 1 2; do
  UNSEAL_KEY=$(jq -r ".unseal_keys_b64[$i]" vault-init.json)
  kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault operator unseal ${UNSEAL_KEY}
done

# 5. 登录并配置
ROOT_TOKEN=$(jq -r ".root_token" vault-init.json)
kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault login ${ROOT_TOKEN}

echo "Vault initialized and unsealed successfully!"
```

```bash
#!/bin/bash
# vault-config.sh - Vault 详细配置脚本

VAULT_ADDR="https://vault.vault.svc.cluster.local:8200"
ROOT_TOKEN="${VAULT_ROOT_TOKEN}"

vault login ${ROOT_TOKEN}

# ==================== 1. 启用 Secret Engines ====================

# 启用 KV v2 (版本化密钥存储)
vault secrets enable -version=2 -path=secret kv-v2

# 启用 PKI Engine（用于自动签发 TLS 证书）
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

# 配置根 CA
vault write -field=certificate pki/root/generate/internal \
  common_name="Service Mesh Root CA" \
  ttl=87600h \
  key_type=ec \
  key_bits=384 > ca.crt

# 配置 CRL 和证书分发点
vault write pki/config/urls \
  issuing_certificates="${VAULT_ADDR}/v1/pki/ca" \
  crl_distribution_points="${VAULT_ADDR}/v1/pki/crl"

# 创建中间 CA 角色
vault write pki/roles/service-mesh \
  allowed_domains="cluster.local,svc.cluster.local" \
  allow_subdomains=true \
  max_ttl=720h \
  key_type=ec \
  key_bits=256 \
  require_cn=false \
  allowed_uri_sans="spiffe://cluster.local/*"

# 启用 Database Engine（动态数据库凭证）
vault secrets enable -path=database database

# 配置 PostgreSQL 连接
vault write database/config/postgresql-prod \
  plugin_name=postgresql-database-plugin \
  allowed_roles="app-readonly,app-readwrite" \
  connection_url="postgresql://{{username}}:{{password}}@postgres.prod.svc:5432/appdb?sslmode=require" \
  username="vaultadmin" \
  password="${PG_ADMIN_PASSWORD}"

# 创建动态角色
vault write database/roles/app-readonly \
  db_name=postgresql-prod \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl=1h \
  max_ttl=24h

vault write database/roles/app-readwrite \
  db_name=postgresql-prod \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl=1h \
  max_ttl=4h

# 启用 Transit Engine（加密即服务）
vault secrets enable transit

# 创建加密密钥
vault write -f transit/keys/app-data-encryption \
  type=aes-256-gcm

vault write -f transit/keys/pii-encryption \
  type=rsa-4096

# ==================== 2. 启用 Auth Methods ====================

# 启用 Kubernetes Auth
vault auth enable kubernetes

# 配置 Kubernetes 认证
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  issuer="https://kubernetes.default.svc.cluster.local"

# 创建 Kubernetes 认证策略
vault policy write app-read - <<EOF
path "secret/data/app/{{identity.entity.aliases.auth_kubernetes_xxxx.metadata.service_account_namespace}}/{{identity.entity.aliases.auth_kubernetes_xxxx.metadata.service_account_name}}/*" {
  capabilities = ["read", "list"]
}

path "database/creds/app-readonly" {
  capabilities = ["read"]
}
EOF

vault policy write app-write - <<EOF
path "secret/data/app/{{identity.entity.aliases.auth_kubernetes_xxxx.metadata.service_account_namespace}}/{{identity.entity.aliases.auth_kubernetes_xxxx.metadata.service_account_name}}/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "database/creds/app-readwrite" {
  capabilities = ["read"]
}

path "transit/encrypt/app-data-encryption" {
  capabilities = ["update"]
}

path "transit/decrypt/app-data-encryption" {
  capabilities = ["update"]
}
EOF

# 创建 Kubernetes 角色
vault write auth/kubernetes/role/app-service \
  bound_service_account_names=app-service \
  bound_service_account_namespaces=production \
  policies=app-read,app-write \
  ttl=1h

# 启用 AppRole（用于 CI/CD）
vault auth enable approle

vault write auth/approle/role/cicd-deployer \
  secret_id_ttl=24h \
  token_num_uses=10 \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_num_uses=5 \
  token_policies=cicd-policy

# ==================== 3. 启用审计日志 ====================

vault audit enable file file_path=/vault/audit/audit.log

# 可选：启用 Syslog 审计
vault audit enable syslog tag="vault-audit" facility="AUTH"

echo "Vault configuration completed!"
```

### 4.4 Vault Agent Sidecar 注入

```yaml
# deployment-with-vault.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: production
  annotations:
    # 启用 Vault Agent 注入
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "app-service"
    vault.hashicorp.com/agent-pre-populate: "true"
    vault.hashicorp.com/agent-pre-populate-only: "false"
    vault.hashicorp.com/agent-run-as-user: "65534"
    
    # 注入数据库凭证模板
    vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/app-readwrite"
    vault.hashicorp.com/agent-inject-template-db-creds: |
      {{ with secret "database/creds/app-readwrite" -}}
      export DB_USER="{{ .Data.username }}"
      export DB_PASS="{{ .Data.password }}"
      export DB_HOST="postgres.prod.svc"
      export DB_NAME="paymentdb"
      {{- end }}
    
    # 注入 API 密钥
    vault.hashicorp.com/agent-inject-secret-api-keys: "secret/data/app/production/payment-service/api-keys"
    vault.hashicorp.com/agent-inject-template-api-keys: |
      {{ with secret "secret/data/app/production/payment-service/api-keys" -}}
      STRIPE_KEY="{{ .Data.data.stripe_key }}"
      PAYPAL_CLIENT="{{ .Data.data.paypal_client }}"
      {{- end }}
    
    # 注入 TLS 证书
    vault.hashicorp.com/agent-inject-secret-tls: "pki/issue/service-mesh"
    vault.hashicorp.com/agent-inject-template-tls: |
      {{ with secret "pki/issue/service-mesh" \
         "common_name=payment-service.production.svc.cluster.local" \
         "ttl=24h" \
         "alt_names=payment-service,payment-service.production" \
         "uri_sans=spiffe://cluster.local/ns/production/sa/payment-service" -}}
      {{ .Data.certificate }}
      {{ .Data.ca_chain }}
      {{ .Data.private_key }}
      {{- end }}
    
    # 容器配置
    vault.hashicorp.com/agent-inject-container: "payment-service"
    vault.hashicorp.com/agent-run-as-same-user: "true"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      serviceAccountName: app-service
      containers:
      - name: payment-service
        image: registry.example.com/payment-service:v1.2.3
        command: ["/bin/sh"]
        args: ["-c", "source /vault/secrets/db-creds && /app/payment-service"]
        env:
        - name: VAULT_ADDR
          value: "https://vault.vault.svc.cluster.local:8200"
        volumeMounts:
        - name: vault-tls
          mountPath: /vault/tls
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
      volumes:
      - name: vault-tls
        secret:
          secretName: vault-ca
          items:
          - key: ca.crt
            path: ca.crt
---
# ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service
  namespace: production
```

### 4.5 External Secrets Operator 集成

```yaml
# external-secrets-vault.yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.vault.svc.cluster.local:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
---
# 从 Vault 同步到 Kubernetes Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: payment-service-secrets
  namespace: production
spec:
  refreshInterval: "1h"
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: payment-service-credentials
    creationPolicy: Owner
    template:
      type: Opaque
      data:
        database-url: "postgresql://{{ .db_user }}:{{ .db_pass }}@postgres:5432/payments"
        stripe-key: "{{ .stripe_key }}"
  data:
  - secretKey: db_user
    remoteRef:
      key: app/production/payment-service/database
      property: username
  - secretKey: db_pass
    remoteRef:
      key: app/production/payment-service/database
      property: password
  - secretKey: stripe_key
    remoteRef:
      key: app/production/payment-service/api-keys
      property: stripe_key
```

---

## 五、云原生安全（OPA策略即代码）

### 5.1 OPA 架构与原理

```
┌─────────────────────────────────────────────────────────────────┐
│                     OPA 决策流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    API Server /          OPA /                                  │
│    Service Mesh ──────▶  Gatekeeper  ──────▶  决策结果         │
│    Application           (Policy Engine)                        │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                         │
│                    │  Rego Policy    │                         │
│                    │  策略即代码      │                         │
│                    │                 │                         │
│                    │  • 准入控制      │                         │
│                    │  • 授权决策      │                         │
│                    │  • 数据脱敏      │                         │
│                    └─────────────────┘                         │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                         │
│                    │   Data Sources  │                         │
│                    │  (Kubernetes/   │                         │
│                    │   External APIs)│                         │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 OPA Gatekeeper 安装与配置

```yaml
# gatekeeper-values.yaml
disabledBuiltins: []
psp:
  enabled: false
auditInterval: 60
constraintViolationsLimit: 20
auditFromCache: false
disableMutation: false
logLevel: INFO
emitAdmissionEvents: true
emitAuditEvents: true

# 资源限制
resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi

# 启用变异功能
enableMutation: true

# 自定义标签
nodeSelector: {}
tolerations: []
affinity: {}
```

```bash
# 安装 Gatekeeper
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system \
  --create-namespace \
  --values gatekeeper-values.yaml
```

### 5.3 安全策略模板库

```yaml
# constraint-templates.yaml
# ==================== 1. 禁止特权容器 ====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspprivilegedcontainer
spec:
  crd:
    spec:
      names:
        kind: K8sPSPPrivilegedContainer
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8spspprivilegedcontainer
      violation[{"msg": msg}] {
        c := input_containers[_]
        c.securityContext.privileged
        msg := sprintf("Privileged container is not allowed: %v", [c.name])
      }
      input_containers[c] {
        c := input.review.object.spec.containers[_]
      }
      input_containers[c] {
        c := input.review.object.spec.initContainers[_]
      }
      input_containers[c] {
        c := input.review.object.spec.ephemeralContainers[_]
      }
---
# ==================== 2. 要求资源限制 ====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredresources
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredResources
      validation:
        openAPIV3Schema:
          type: object
          properties:
            limits:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredresources
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        required := input.parameters.limits[_]
        not container.resources.limits[required]
        msg := sprintf("Container %s must specify %s limit", [container.name, required])
      }
---
# ==================== 3. 禁止最新标签 ====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblocklatesttag
spec:
  crd:
    spec:
      names:
        kind: K8sBlockLatestTag
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sblocklatesttag
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        endswith(container.image, ":latest")
        msg := sprintf("Image with 'latest' tag is not allowed: %s", [container.image])
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not contains(container.image, ":")
        msg := sprintf("Image must have explicit tag (not 'latest'): %s", [container.image])
      }
---
# ==================== 4. 要求只读根文件系统 ====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspreadonlyrootfilesystem
spec:
  crd:
    spec:
      names:
        kind: K8sPSPReadOnlyRootFilesystem
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8spspreadonlyrootfilesystem
      violation[{"msg": msg}] {
        container := input_containers[_]
        not container.securityContext.readOnlyRootFilesystem
        msg := sprintf("Container %s must use readOnlyRootFilesystem", [container.name])
      }
      input_containers[c] {
        c := input.review.object.spec.containers[_]
      }
      input_containers[c] {
        c := input.review.object.spec.initContainers[_]
      }
---
# ==================== 5. 网络策略要求 ====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirednetworkpolicy
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredNetworkPolicy
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequirednetworkpolicy
      violation[{"msg": msg}] {
        input.review.kind.kind == "Namespace"
        namespace := input.review.object.metadata.name
        not data.inventory.namespace[namespace]["networking.k8s.io/v1"]["NetworkPolicy"]
        msg := sprintf("Namespace %s must have a NetworkPolicy", [namespace])
      }
---
# ==================== 6. Pod 安全标准（PSS）====================
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spsprestricted
spec:
  crd:
    spec:
      names:
        kind: K8sPSPRestricted
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8spsprestricted
      violation[{"msg": msg}] {
        input.review.object.spec.securityContext.runAsRoot
        msg := "Running as root is not allowed"
      }
      violation[{"msg": msg}] {
        input.review.object.spec.securityContext.runAsUser == 0
        msg := "Running with UID 0 is not allowed"
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        container.securityContext.allowPrivilegeEscalation
        msg := sprintf("Container %s must not allow privilege escalation", [container.name])
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        capabilities := {cap | cap := container.securityContext.capabilities.add[_]}
        count(capabilities) > 0
        msg := sprintf("Container %s must not add capabilities", [container.name])
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.securityContext.seccompProfile
        msg := sprintf("Container %s must specify seccompProfile", [container.name])
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.securityContext.seccompProfile.type
        msg := sprintf("Container %s must specify seccompProfile type", [container.name])
      }
```

### 5.4 策略约束应用

```yaml
# constraints.yaml
# ==================== 1. 禁止特权容器 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: privileged-container
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces:
    - kube-system
    - gatekeeper-system
    - istio-system
---
# ==================== 2. 要求资源限制 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: required-resources
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces:
    - kube-system
  parameters:
    limits:
    - cpu
    - memory
---
# ==================== 3. 禁止最新标签 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockLatestTag
metadata:
  name: block-latest-tag
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces:
    - kube-system
---
# ==================== 4. 生产环境只读根文件系统 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPReadOnlyRootFilesystem
metadata:
  name: readonly-root-fs
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - production
---
# ==================== 5. 要求网络策略 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredNetworkPolicy
metadata:
  name: required-network-policy
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Namespace"]
    excludedNamespaces:
    - kube-system
    - default
    - kube-public
    - kube-node-lease
---
# ==================== 6. 生产环境 Pod 安全标准 ====================
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPRestricted
metadata:
  name: restricted-pods
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - production
    - payment
    - user-data
```

### 5.5 OPA 与 Istio 集成（授权策略）

```yaml
# opa-istio.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: opa-istio-config
data:
  policy.rego: |
    package istio.authz
    
    import input.attributes.request.http as http_request
    import input.parsed_path
    import input.parsed_query
    import data.kubernetes.users
    import data.kubernetes.roles
    
    default allow = false
    
    # 允许健康检查
    allow {
        http_request.path == "/health"
    }
    
    # 允许已认证用户访问自己的资源
    allow {
        some user_id
        jwt_payload.sub == user_id
        parsed_path[0] == "api"
        parsed_path[1] == "users"
        parsed_path[2] == user_id
    }
    
    # 管理员可以访问所有资源
    allow {
        jwt_payload.realm_access.roles[_] == "admin"
    }
    
    # 支付服务需要特殊权限
    allow {
        parsed_path[0] == "api"
        parsed_path[1] == "payments"
        jwt_payload.realm_access.roles[_] == "payment-operator"
        http_request.method == "POST"
    }
    
    # 提取 JWT payload
    jwt_payload = payload {
        [_, payload, _] := io.jwt.decode(bearer_token)
    }
    
    bearer_token = t {
        v := http_request.headers.authorization
        startswith(v, "Bearer ")
        t := substring(v, count("Bearer "), -1)
    }
    
    # 审计日志
    decision_log[{
        "decision_id": sprintf("%v", [input.attributes.request.id]),
        "timestamp": time.now_ns(),
        "user": jwt_payload.sub,
        "path": http_request.path,
        "method": http_request.method,
        "allowed": allow,
        "source_ip": input.attributes.source.address
    }]
---
# OPA Sidecar 注入
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      annotations:
        # Istio 与 OPA 集成
        inject.istio.io/templates: "sidecar,opa"
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: registry.example.com/api-gateway:v1.0
        ports:
        - containerPort: 8080
      - name: opa-istio
        image: openpolicyagent/opa:0.60.0-istio
        args:
        - "run"
        - "--server"
        - "--config-file=/config/config.yaml"
        - "--addr=localhost:8181"
        volumeMounts:
        - name: opa-config
          mountPath: /config
        - name: opa-policy
          mountPath: /policy
      volumes:
      - name: opa-config
        configMap:
          name: opa-istio-config
      - name: opa-policy
        configMap:
          name: opa-istio-policy
---
# EnvoyFilter 配置 OPA 扩展
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: opa-authz
  namespace: production
spec:
  workloadSelector:
    labels:
      app: api-gateway
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.ext_authz
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
          grpc_service:
            google_grpc:
              target_uri: localhost:9191
              stat_prefix: opa
            timeout: 5s
          transport_api_version: V3
          include_peer_certificate: true
```

### 5.6 OPA 运行时策略测试

```rego
# policy_test.rego - OPA 策略单元测试
package istio.authz

test_allow_health_check {
    allow with input as {
        "attributes": {
            "request": {
                "http": {
                    "path": "/health",
                    "method": "GET"
                }
            }
        }
    }
}

test_deny_anonymous_admin_access {
    not allow with input as {
        "attributes": {
            "request": {
                "http": {
                    "path": "/api/admin/users",
                    "method": "GET",
                    "headers": {}
                }
            }
        }
    }
}

test_allow_admin_with_token {
    allow with input as {
        "attributes": {
            "request": {
                "http": {
                    "path": "/api/admin/users",
                    "method": "GET",
                    "headers": {
                        "authorization": "Bearer eyJhbGciOiJSUzI1NiIs..."
                    }
                }
            }
        }
    } with jwt_payload as {
        "sub": "admin-user",
        "realm_access": {
            "roles": ["admin"]
        }
    }
}

# 运行测试: opa test -v .
```

---

## 附录：快速配置模板

### A. 完整 Istio mTLS 安装

```bash
#!/bin/bash
# install-istio-mtls.sh

istioctl install -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  profile: default
  meshConfig:
    enableAutoMtls: true
    accessLogFile: /dev/stdout
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
EOF

# 应用严格 mTLS
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
EOF
```

### B. Vault Kubernetes 快速启动

```bash
#!/bin/bash
# quickstart-vault-k8s.sh

# 1. 安装 Vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm upgrade --install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --set "csi.enabled=true" \
  --namespace vault --create-namespace

# 2. 等待就绪
kubectl wait --for=condition=Ready pod/vault-0 -n vault --timeout=120s

# 3. 初始化并解封
kubectl exec -it vault-0 -n vault -- vault operator init -key-shares=1 -key-threshold=1 -format=json > vault-init.json
UNSEAL_KEY=$(jq -r ".unseal_keys_b64[0]" vault-init.json)
ROOT_TOKEN=$(jq -r ".root_token" vault-init.json)
kubectl exec -it vault-0 -n vault -- vault operator unseal $UNSEAL_KEY

# 4. 启用 Kubernetes 认证
kubectl exec -it vault-0 -n vault -- vault login $ROOT_TOKEN
kubectl exec -it vault-0 -n vault -- vault auth enable kubernetes
kubectl exec -it vault-0 -n vault -- vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

echo "Vault ready! Root token: $ROOT_TOKEN"
```

### C. Gatekeeper 策略包

```bash
#!/bin/bash
# apply-security-policies.sh

NAMESPACE="gatekeeper-system"

# 安装 Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml

# 等待就绪
kubectl wait --for=condition=Ready -l control-plane=controller-manager -n $NAMESPACE pod --timeout=120s

# 应用策略模板
kubectl apply -f constraint-templates.yaml

# 等待模板就绪
sleep 5

# 应用约束
kubectl apply -f constraints.yaml

echo "Security policies applied!"
```

### D. 安全加固检查清单

```yaml
# security-checklist.md

## 集群安全基线检查清单

### 网络层面
- [ ] 启用集群级严格 mTLS
- [ ] 配置网络策略（NetworkPolicy）
- [ ] 启用 Ingress TLS
- [ ] 禁用不必要的端口暴露
- [ ] 配置 WAF 规则

### 访问控制
- [ ] 启用 RBAC
- [ ] 配置 Pod 安全标准（PSS）
- [ ] 禁用默认 ServiceAccount 自动挂载
- [ ] 启用审计日志
- [ ] 配置准入控制器

### 密钥管理
- [ ] 部署 Vault 并启用自动解封
- [ ] 配置动态数据库凭证
- [ ] 启用 PKI 自动证书签发
- [ ] 配置密钥自动轮转
- [ ] 禁止 Secret 明文存储

### 运行时安全
- [ ] 启用只读根文件系统
- [ ] 禁止特权容器
- [ ] 配置资源限制
- [ ] 启用 Seccomp/AppArmor
- [ ] 配置运行时安全监控（Falco）

### 镜像安全
- [ ] 启用镜像签名验证（Cosign）
- [ ] 配置镜像漏洞扫描
- [ ] 禁止 latest 标签
- [ ] 使用私有镜像仓库
- [ ] 配置镜像拉取策略

### 合规审计
- [ ] 部署 OPA Gatekeeper
- [ ] 配置策略违规告警
- [ ] 启用审计日志聚合
- [ ] 配置合规报告
- [ ] 定期安全评估
```

### E. 紧急响应脚本

```bash
#!/bin/bash
# incident-response.sh

INCIDENT_TYPE=$1

case $INCIDENT_TYPE in
  "compromised-pod")
    POD_NAME=$2
    NAMESPACE=$3
    echo "隔离受感染 Pod: $POD_NAME"
    kubectl label pod $POD_NAME -n $NAMESPACE incident/isolated=true --overwrite
    kubectl annotate pod $POD_NAME -n $NAMESPACE incident/isolated-at="$(date -Iseconds)"
    kubectl cordon $(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.nodeName}')
    ;;
    
  "revoke-access")
    SERVICE_ACCOUNT=$2
    NAMESPACE=$3
    echo "撤销服务账户访问权限: $SERVICE_ACCOUNT"
    kubectl delete serviceaccount $SERVICE_ACCOUNT -n $NAMESPACE
    vault token revoke -mode=path auth/kubernetes/role/$SERVICE_ACCOUNT
    ;;
    
  "rotate-secrets")
    echo "触发所有密钥轮转"
    vault write -f transit/keys/app-data-encryption/rotate
    kubectl delete secrets --all --all-namespaces --field-selector type=Opaque
    ;;
    
  "lockdown")
    echo "进入安全锁定模式"
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
    ;;
    
  *)
    echo "用法: $0 {compromised-pod|revoke-access|rotate-secrets|lockdown}"
    exit 1
    ;;
esac
```

---

## 总结

本手册涵盖了零信任安全架构的五个核心领域：

1. **ZTA 设计原则** - 建立"永不信任，始终验证"的安全理念
2. **IAP 实现** - 统一身份认证与细粒度访问控制
3. **mTLS 通信** - 服务间双向认证保障通信安全
4. **Vault 密钥管理** - 动态凭证与自动化密钥生命周期
5. **OPA 策略即代码** - 声明式安全策略与合规自动化

通过这些技术的组合应用，可以构建出面向云原生环境的全栈零信任安全体系。

---

**文档维护**: Security Team  
**审核周期**: 季度  
**联系方式**: security@example.com
