# 云原生与Kubernetes进阶技术深度报告

> 报告日期：2026年2月16日  
> 版本：v1.0  
> 主题：Kubernetes高级调度、Service Mesh、GitOps、可观测性、多集群管理

---

## 目录

1. [Kubernetes高级调度与自动扩缩容](#1-kubernetes高级调度与自动扩缩容)
2. [Service Mesh深入 - Istio实践](#2-service-mesh深入---istio实践)
3. [GitOps实践 - ArgoCD与Flux](#3-gitops实践---argocd与flux)
4. [云原生可观测性 - OpenTelemetry](#4-云原生可观测性---opentelemetry)
5. [多集群管理架构](#5-多集群管理架构)

---

## 1. Kubernetes高级调度与自动扩缩容

### 1.1 高级调度机制

#### 1.1.1 亲和性与反亲和性 (Affinity & Anti-Affinity)

**节点亲和性 (Node Affinity)**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-node-affinity
spec:
  affinity:
    nodeAffinity:
      # 必须满足的条件（硬约束）
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/os
            operator: In
            values:
            - linux
          - key: node-type
            operator: In
            values:
            - compute-optimized
      # 偏好满足的条件（软约束）
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - zone-a
      - weight: 50
        preference:
          matchExpressions:
          - key: disk-type
            operator: In
            values:
            - ssd
  containers:
  - name: nginx
    image: nginx:1.25
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "1Gi"
        cpu: "1000m"
```

**Pod亲和性与反亲和性 (Pod Affinity & Anti-Affinity)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        # Pod亲和性：与redis在同一可用区
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - redis
              topologyKey: topology.kubernetes.io/zone
        
        # Pod反亲和性：相同应用不在同一节点
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web-app
            topologyKey: kubernetes.io/hostname
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: topology.kubernetes.io/zone
      containers:
      - name: web
        image: nginx:alpine
        ports:
        - containerPort: 80
```

#### 1.1.2 污点与容忍 (Taints & Tolerations)

```yaml
# 为节点添加污点
# kubectl taint nodes node1 dedicated=production:NoSchedule
# kubectl taint nodes gpu-node nvidia.com/gpu=true:NoSchedule

apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-workload
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-training
  template:
    metadata:
      labels:
        app: ml-training
    spec:
      tolerations:
      # 容忍GPU节点污点
      - key: "nvidia.com/gpu"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      # 容忍所有污点（不推荐生产使用）
      # - operator: "Exists"
      
      # 节点选择器
      nodeSelector:
        accelerator: nvidia-tesla-v100
      
      containers:
      - name: pytorch
        image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: dshm
          mountPath: /dev/shm
      volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```

#### 1.1.3 自定义调度器与调度框架

**调度框架插件配置 (Scheduler Configuration)**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
  namespace: kube-system
data:
  scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    profiles:
    - schedulerName: custom-scheduler
      plugins:
        queueSort:
          enabled:
          - name: PrioritySort
        preFilter:
          enabled:
          - name: NodeResourcesFit
          - name: NodePorts
        filter:
          enabled:
          - name: NodeUnschedulable
          - name: NodeResourcesFit
          - name: NodeName
          - name: NodePorts
          - name: NodeAffinity
          - name: PodTopologySpread
          - name: InterPodAffinity
        postFilter:
          enabled:
          - name: DefaultPreemption
        preScore:
          enabled:
          - name: InterPodAffinity
          - name: PodTopologySpread
          - name: TaintToleration
          - name: NodeAffinity
        score:
          enabled:
          - name: NodeResourcesBalancedAllocation
            weight: 1
          - name: ImageLocality
            weight: 1
          - name: InterPodAffinity
            weight: 1
          - name: NodeResourcesFit
            weight: 1
          - name: PodTopologySpread
            weight: 2
      pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
            - name: cpu
              weight: 1
            - name: memory
              weight: 1
      - name: PodTopologySpread
        args:
          defaultConstraints:
          - maxSkew: 1
            topologyKey: topology.kubernetes.io/zone
            whenUnsatisfiable: ScheduleAnyway
---
# 使用自定义调度器
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-scheduled-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    spec:
      schedulerName: custom-scheduler  # 指定使用自定义调度器
      containers:
      - name: app
        image: myapp:latest
```

#### 1.1.4 Pod拓扑分布约束 (Pod Topology Spread Constraints)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: distributed-web
spec:
  replicas: 6
  selector:
    matchLabels:
      app: distributed-web
  template:
    metadata:
      labels:
        app: distributed-web
    spec:
      topologySpreadConstraints:
      # 跨可用区均匀分布
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: distributed-web
        minDomains: 2
      
      # 跨节点均匀分布
      - maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: distributed-web
      
      # 跨机架分布（自定义标签）
      - maxSkew: 1
        topologyKey: rack
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: distributed-web
      
      containers:
      - name: web
        image: nginx:alpine
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
```

### 1.2 自动扩缩容体系

#### 1.2.1 HPA (Horizontal Pod Autoscaler) 高级配置

```yaml
# HPA v2 API - 多指标自动扩缩
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: advanced-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-application
  minReplicas: 3
  maxReplicas: 100
  metrics:
  # CPU使用率指标
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # 内存使用率指标
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  # 自定义指标：每秒请求数 (需要Metrics Server或Prometheus Adapter)
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  
  # 自定义指标：队列长度
  - type: External
    external:
      metric:
        name: kafka_consumer_lag
        selector:
          matchLabels:
            topic: orders
      target:
        type: AverageValue
        averageValue: "100"
  
  # 自定义指标：对象指标（如Ingress）
  - type: Object
    object:
      describedObject:
        apiVersion: networking.k8s.io/v1
        kind: Ingress
        name: web-ingress
      metric:
        name: requests-per-second
      target:
        type: AverageValue
        averageValue: "10000"
  
  behavior:
    # 扩容行为
    scaleUp:
      stabilizationWindowSeconds: 60  # 扩容前观察窗口
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15  # 15秒内最多扩容100%
      - type: Pods
        value: 4
        periodSeconds: 15  # 或最多增加4个Pod
      selectPolicy: Max  # 选择最激进的策略
    
    # 缩容行为
    scaleDown:
      stabilizationWindowSeconds: 300  # 缩容前观察5分钟
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60  # 每分钟最多缩容10%
      - type: Pods
        value: 2
        periodSeconds: 60  # 或最多减少2个Pod
      selectPolicy: Min  # 选择最保守的策略
---
# 预测性HPA (Predictive HPA - 需要KEDA)
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: predictive-hpa
  namespace: production
spec:
  scaleTargetRef:
    name: web-application
    kind: Deployment
  minReplicaCount: 3
  maxReplicaCount: 100
  cooldownPeriod: 300
  pollingInterval: 15
  triggers:
  # CPU指标
  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"
  
  # Prometheus指标：基于历史数据的预测
  - type: prometheus
    metadata:
      serverAddress: http://prometheus.monitoring.svc:9090
      metricName: http_requests_total
      threshold: "1000"
      query: |
        sum(rate(http_requests_total{service="web-app"}[2m]))
  
  # Cron定时扩缩容（应对已知流量高峰）
  - type: cron
    metadata:
      timezone: Asia/Shanghai
      start: 0 8 * * 1-5    # 工作日上午8点
      end: 0 20 * * 1-5     # 工作日晚8点
      desiredReplicas: "20"
```

#### 1.2.2 VPA (Vertical Pod Autoscaler) 配置

```yaml
# VPA CRD配置
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-application
  updatePolicy:
    # 更新模式：
    # - Auto: 自动更新Pod资源
    # - Recreate: 删除重建Pod
    # - Initial: 仅对新Pod生效
    # - Off: 仅推荐不执行
    updateMode: "Auto"
    minReplicas: 2  # 最少保留的Pod数
  resourcePolicy:
    containerPolicies:
    - containerName: '*'
      minAllowed:
        cpu: 50m
        memory: 100Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits
---
# 安装VPA (使用官方YAML)
# kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.14.0/vpa-v1-crd-gen.yaml
# kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.14.0/vpa-rbac.yaml
# kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-0.14.0/vpa-deployment.yaml
```

#### 1.2.3 Cluster Autoscaler 配置

```yaml
# Cluster Autoscaler部署配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8085"
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: registry.k8s.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi
        command:
        - ./cluster-autoscaler
        - --cloud-provider=aws  # 或azure, gcp, alicloud
        - --namespace=kube-system
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/my-cluster
        - --balance-similar-node-groups=true
        - --skip-nodes-with-system-pods=false
        - --skip-nodes-with-local-storage=false
        - --scale-down-enabled=true
        - --scale-down-delay-after-add=10m
        - --scale-down-delay-after-delete=10s
        - --scale-down-delay-after-failure=3m
        - --scale-down-unneeded-time=10m
        - --scale-down-utilization-threshold=0.5
        - --max-empty-bulk-delete=10
        - --max-graceful-termination-sec=600
        - --v=4
        env:
        - name: AWS_REGION
          value: us-west-2
        volumeMounts:
        - name: ssl-certs
          mountPath: /etc/ssl/certs/ca-certificates.crt
          readOnly: true
      volumes:
      - name: ssl-certs
        hostPath:
          path: /etc/ssl/certs/ca-bundle.crt
---
# 节点组配置示例 (AWS Auto Scaling Group标签)
# k8s.io/cluster-autoscaler/enabled: true
# k8s.io/cluster-autoscaler/my-cluster: owned
# k8s.io/cluster-autoscaler/node-template/label/node-type: spot
# k8s.io/cluster-autoscaler/node-template/taint/dedicated: spot:NoSchedule
```

#### 1.2.4 KEDA (Kubernetes Event-driven Autoscaling)

```yaml
# KEDA安装
# helm repo add kedacore https://kedacore.github.io/charts
# helm repo update
# helm install keda kedacore/keda --namespace keda --create-namespace

# ScaledObject示例
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: queue-consumer-scaler
  namespace: production
spec:
  scaleTargetRef:
    name: order-processor
    kind: Deployment
  pollingInterval: 10
  cooldownPeriod: 300
  minReplicaCount: 0      # 可以缩容到0
  maxReplicaCount: 100
  advanced:
    restoreToOriginalReplicaCount: false
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
          policies:
          - type: Percent
            value: 10
            periodSeconds: 60
  triggers:
  # Kafka触发器
  - type: kafka
    metadata:
      bootstrapServers: kafka-cluster.kafka.svc:9092
      consumerGroup: order-processors
      topic: orders
      lagThreshold: "100"
      activationLagThreshold: "10"
      offsetResetPolicy: latest
  
  # 补充：RabbitMQ触发器
  ---
  apiVersion: keda.sh/v1alpha1
  kind: ScaledObject
  metadata:
    name: rabbitmq-scaler
  spec:
    scaleTargetRef:
      name: email-worker
    triggers:
    - type: rabbitmq
      metadata:
        protocol: amqp
        queueName: email-queue
        mode: QueueLength
        value: "50"
      authenticationRef:
        name: rabbitmq-trigger-auth
  ---
  apiVersion: keda.sh/v1alpha1
  kind: TriggerAuthentication
  metadata:
    name: rabbitmq-trigger-auth
  spec:
    secretTargetRef:
    - parameter: host
      name: rabbitmq-secret
      key: host

  # 补充：Azure Service Bus触发器
  ---
  apiVersion: keda.sh/v1alpha1
  kind: ScaledObject
  metadata:
    name: servicebus-scaler
  spec:
    scaleTargetRef:
      name: notification-handler
    triggers:
    - type: azure-servicebus
      metadata:
        namespace: my-namespace
        queueName: notifications
        messageCount: "100"
      authenticationRef:
        name: azure-servicebus-auth
```

### 1.3 调度优化策略总结

| 场景 | 解决方案 | 关键配置 |
|------|----------|----------|
| 高可用部署 | Pod Anti-Affinity + Topology Spread | topologyKey: hostname/zone |
| 数据局部性 | Pod Affinity + Node Affinity | 同区域/同机架调度 |
| 专用节点 | Taints + Tolerations | NoSchedule/NoExecute |
| GPU/专用硬件 | Extended Resources + Node Selector | nvidia.com/gpu |
| 成本优化 | Cluster Autoscaler + Spot实例 | 混合实例策略 |
| 流量突发 | HPA + KEDA + Cluster Autoscaler | 多层弹性伸缩 |

---

## 2. Service Mesh深入 - Istio实践

### 2.1 Istio架构核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                         Istio Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   istiod    │  │  Ingress    │  │   Egress    │              │
│  │  (Control)  │  │   Gateway   │  │   Gateway   │              │
│  │             │  │             │  │             │              │
│  │ • Pilot     │  │ • 流量入口  │  │ • 流量出口  │              │
│  │ • Citadel   │  │ • TLS终止   │  │ • 外部访问  │              │
│  │ • Galley    │  │ • 路由分发  │  │ • 安全策略  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                    Data Plane (Envoy Sidecar)                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │App +     │    │App +     │    │App +     │                   │
│  │Envoy     │    │Envoy     │    │Envoy     │                   │
│  │Sidecar   │    │Sidecar   │    │Sidecar   │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Istio安装配置

```yaml
# Istio Operator配置 - 生产环境优化
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: production-istio
spec:
  profile: default
  hub: docker.io/istio
  tag: 1.20.0
  
  # 组件配置
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 5
          metrics:
          - type: Resource
            resource:
              name: cpu
              targetAverageUtilization: 80
        affinity:
          podAntiAffinity:
            requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: istiod
              topologyKey: kubernetes.io/hostname
    
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
            ephemeral-storage: 1Gi
        service:
          type: LoadBalancer
          ports:
          - name: status-port
            port: 15021
            targetPort: 15021
          - name: http2
            port: 80
            targetPort: 8080
          - name: https
            port: 443
            targetPort: 8443
        overlays:
        - apiVersion: apps/v1
          kind: Deployment
          name: istio-ingressgateway
          patches:
          - path: spec.template.spec.containers.[name:istio-proxy].securityContext.capabilities.add
            value: ["NET_ADMIN"]
    
    egressGateways:
    - name: istio-egressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
  
  # Mesh配置
  meshConfig:
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
      tracing:
        sampling: 100.0
        customTags:
          environment:
            literal:
              value: production
      proxyStatsMatcher:
        inclusionRegexps:
        - ".*outlier_detection.*"
        - ".*circuit_breakers.*"
    enableAutoMtls: true
    enableAutoSni: true
    trustDomain: cluster.local
    trustDomainAliases:
    - cluster.local
    
    # 访问日志
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON
    accessLogFormat: |
      {
        "access_log": "%ACCESS_LOG%",
        "authority": "%REQ(:AUTHORITY)%",
        "bytes_received": "%BYTES_RECEIVED%",
        "bytes_sent": "%BYTES_SENT%",
        "downstream_local_address": "%DOWNSTREAM_LOCAL_ADDRESS%",
        "duration": "%DURATION%",
        "istio_policy_status": "%DYNAMIC_METADATA(istio.mixer:status)%",
        "method": "%REQ(:METHOD)%",
        "path": "%REQ(X-ENVOY-ORIGINAL-PATH?:PATH)%",
        "protocol": "%PROTOCOL%",
        "request_id": "%REQ(X-REQUEST-ID)%",
        "response_code": "%RESPONSE_CODE%",
        "response_flags": "%RESPONSE_FLAGS%",
        "start_time": "%START_TIME%",
        "trace_id": "%REQ(X-B3-TRACEID)%",
        "upstream_cluster": "%UPSTREAM_CLUSTER%",
        "upstream_host": "%UPSTREAM_HOST%"
      }
    
    # 默认重试策略
    defaultHttpRetryPolicy:
      attempts: 3
      perTryTimeout: 2s
      retryOn: gateway-error,connect-failure,refused-stream
  
  # 附加组件
  addonComponents:
    kiali:
      enabled: true
    grafana:
      enabled: true
    prometheus:
      enabled: true
    tracing:
      enabled: true
```

### 2.3 流量管理

#### 2.3.1 智能路由与流量分割

```yaml
# VirtualService - 高级路由配置
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: product-service-routes
  namespace: production
spec:
  hosts:
  - product-service
  - product.api.example.com
  gateways:
  - istio-ingressgateway
  - mesh
  http:
  # 金丝雀发布 - 按Header路由
  - match:
    - headers:
        x-canary:
          exact: "true"
      uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: product-service
        subset: v2
        port:
          number: 8080
      weight: 100
    timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: gateway-error,connect-failure,refused-stream
  
  # A/B测试 - 按Cookie路由
  - match:
    - cookies:
        experiment:
          exact: "variant-b"
    route:
    - destination:
        host: product-service
        subset: v2
      weight: 100
  
  # 基于权重的金丝雀
  - match:
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: product-service
        subset: v1
        port:
          number: 8080
      weight: 90
    - destination:
        host: product-service
        subset: v2
        port:
          number: 8080
      weight: 10
    fault:
      delay:
        percentage:
          value: 0.1  # 0.1%请求注入延迟
        fixedDelay: 5s
  
  # 直接路由
  - route:
    - destination:
        host: product-service
        subset: v1
      weight: 100
    
    # 流量镜像（复制流量到v2进行测试，不返回响应）
    mirror:
      host: product-service
      subset: v2
    mirrorPercentage:
      value: 10.0
---
# DestinationRule - 服务子集定义
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: product-service-policy
  namespace: production
spec:
  host: product-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 30ms
        tcpKeepalive:
          time: 300s
          interval: 75s
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
        maxRetries: 3
    
    loadBalancer:
      simple: LEAST_REQUEST
      localityLbSetting:
        enabled: true
        failover:
        - from: us-east
          to: us-west
        - from: us-west
          to: us-east
    
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 40
    
    # 连接池设置
    portLevelSettings:
    - port:
        number: 8080
      connectionPool:
        http:
          h2UpgradePolicy: UPGRADE
  
  subsets:
  - name: v1
    labels:
      version: v1
    trafficPolicy:
      loadBalancer:
        simple: ROUND_ROBIN
  - name: v2
    labels:
      version: v2
    trafficPolicy:
      loadBalancer:
        simple: LEAST_CONN
---
# Gateway - 入口网关配置
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: public-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*.example.com"
    tls:
      httpsRedirect: true  # HTTP重定向到HTTPS
  
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: example-wildcard-tls  # 引用TLS证书Secret
      minProtocolVersion: TLSV1_2
      cipherSuites:
      - ECDHE-RSA-AES256-GCM-SHA384
      - ECDHE-RSA-AES128-GCM-SHA256
    hosts:
    - "*.example.com"
  
  # TCP流量入口
  - port:
      number: 5432
      name: tcp-postgres
      protocol: TCP
    hosts:
    - "db.internal.example.com"
---
# ServiceEntry - 外部服务定义
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-services
spec:
  hosts:
  - api.stripe.com
  - api.twilio.com
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
  location: MESH_EXTERNAL
  exportTo:
  - "."
---
# Sidecar - 命名空间隔离配置
apiVersion: networking.istio.io/v1beta1
kind: Sidecar
metadata:
  name: default
  namespace: production
spec:
  egress:
  - hosts:
    - "./*"                    # 本命名空间所有服务
    - "istio-system/*"         # istio系统服务
    - "kube-system/kube-dns"   # DNS服务
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY  # 只允许访问注册的服务
```

#### 2.3.2 流量控制高级特性

```yaml
# 超时与重试配置
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: timeout-retry-config
spec:
  hosts:
  - payment-service
  http:
  - match:
    - uri:
        prefix: /api/payments
    route:
    - destination:
        host: payment-service
    
    # 请求超时
    timeout: 10s
    
    # 重试策略
    retries:
      attempts: 3                    # 最多重试3次
      perTryTimeout: 3s              # 每次重试超时
      retryOn: gateway-error,connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes
      retriableStatusCodes: [503, 504]
    
    # 故障注入（测试用）
    fault:
      # 延迟注入
      delay:
        percentage:
          value: 5.0                 # 5%请求注入延迟
        fixedDelay: 2s
      # 错误注入
      abort:
        percentage:
          value: 1.0                 # 1%请求返回错误
        httpStatus: 503
  
  # 速率限制（与EnvoyFilter配合）
  - match:
    - uri:
        prefix: /api/public
    route:
    - destination:
        host: public-api
---
# EnvoyFilter - 本地速率限制
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit-filter
  namespace: production
spec:
  workloadSelector:
    labels:
      app: public-api
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
            subFilter:
              name: envoy.filters.http.router
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          value:
            stat_prefix: http_local_rate_limiter
            token_bucket:
              max_tokens: 100
              tokens_per_fill: 10
              fill_interval: 1s
            filter_enabled:
              runtime_key: local_rate_limit_enabled
              default_value:
                numerator: 100
                denominator: HUNDRED
            filter_enforced:
              runtime_key: local_rate_limit_enforced
              default_value:
                numerator: 100
                denominator: HUNDRED
            response_headers_to_add:
            - append_action: OVERWRITE_IF_EXISTS_OR_ADD
              header:
                key: x-local-rate-limit
                value: 'true'
```

### 2.4 安全通信

#### 2.4.1 mTLS配置

```yaml
# PeerAuthentication - 服务间mTLS策略
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # 强制mTLS
---
# 特定工作负载的mTLS策略
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: api-service-mtls
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-service
  mtls:
    mode: STRICT
  portLevelMtls:
    8080:
      mode: PERMISSIVE  # 该端口允许明文
---
# RequestAuthentication - JWT认证
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  jwtRules:
  # OIDC提供商
  - issuer: "https://accounts.google.com"
    audiences: ["my-client-id.apps.googleusercontent.com"]
    jwksUri: "https://www.googleapis.com/oauth2/v3/certs"
    forwardOriginalToken: true
    outputPayloadToHeader: x-jwt-payload
  
  # 自定义JWT
  - issuer: "https://auth.internal.example.com"
    jwksUri: "https://auth.internal.example.com/.well-known/jwks.json"
    audiences: ["api-service"]
    fromHeaders:
    - name: authorization
      prefix: "Bearer "
    outputPayloadToHeader: x-jwt-claims
---
# AuthorizationPolicy - 授权策略
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-service
  action: ALLOW
  rules:
  # 允许健康检查
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/health", "/ready"]
    from:
    - source:
        namespaces: ["istio-system"]
  
  # 管理员访问所有资源
  - from:
    - source:
        requestPrincipals: ["*"]
    when:
    - key: request.auth.claims[role]
      values: ["admin"]
  
  # 普通用户访问
  - from:
    - source:
        requestPrincipals: ["*"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/products/*", "/api/v1/orders/*"]
    when:
    - key: request.auth.claims[scope]
      values: ["read", "write"]
  
  # 服务间调用
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/order-service"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/inventory/reserve"]
---
# 拒绝策略示例
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: block-external
  namespace: production
spec:
  selector:
    matchLabels:
      app: internal-api
  action: DENY
  rules:
  - from:
    - source:
        notNamespaces: ["production", "istio-system"]
---
# 认证失败策略
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: protected-api
  action: ALLOW
  rules:
  - from:
    - source:
        requestPrincipals: ["*"]
```

### 2.5 可观测性集成

```yaml
# Telemetry配置 - 指标和日志
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: default-metrics
  namespace: production
spec:
  metrics:
  - providers:
    - name: prometheus
    overrides:
    # 自定义标签
    - tagOverrides:
        destination_service:
          operation: UPSERT
          value: "%DESTINATION_SERVICE%"
      match:
        metric: REQUEST_COUNT
  
  accessLogging:
  - providers:
    - name: envoy
    filter:
      expression: |
        response.code >= 500 || 
        request.url_path.contains('/api/') ||
        request.headers['x-log-request'] == 'true'
  
  tracing:
  - providers:
    - name: jaeger
    randomSamplingPercentage: 10.0
    customTags:
      environment:
        literal:
          value: production
      user_agent:
        header:
          name: user-agent
          defaultValue: unknown
---
# WasmPlugin - 自定义指标
apiVersion: extensions.istio.io/v1alpha1
kind: WasmPlugin
metadata:
  name: custom-metrics
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-service
  url: oci://registry.example.com/custom-metrics-filter:v1.0.0
  pluginConfig:
    metric_name: custom_request_duration
    dimensions:
      - api_version
      - endpoint_category
```

---

## 3. GitOps实践 - ArgoCD与Flux

### 3.1 GitOps核心原则

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitOps 工作流                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    Git Push    ┌─────────────┐    Pull/Poll      │
│  │  Git     │ ──────────────▶ │  ArgoCD/   │ ◀──────────────── │
│  │  Repo    │    (Desired    │  Flux       │    Reconcile      │
│  │          │     State)     │  Controller │                   │
│  └──────────┘                └──────┬──────┘                   │
│         │                           │                          │
│         │   ┌───────────────────────┘                          │
│         │   │   Apply                                            │
│         │   ▼                                                    │
│  ┌──────────┐    Current     ┌─────────────┐                   │
│  │  Image   │    State       │  Kubernetes  │                   │
│  │  Registry│ ──────────────▶ │  Cluster     │                   │
│  └──────────┘                └─────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 ArgoCD深度实践

#### 3.2.1 ArgoCD高可用安装

```yaml
# ArgoCD HA安装配置
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
# 使用Kustomize的kustomization.yaml
# 或通过Helm安装高可用版本
# helm repo add argo https://argoproj.github.io/argo-helm
# helm install argocd argo/argo-cd --namespace argocd -f values-ha.yaml

# values-ha.yaml 配置
---
# 高可用配置
redis-ha:
  enabled: true

controller:
  replicas: 1  # Application Controller必须是单例
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 4000m
      memory: 8Gi
  args:
    statusProcessors: "50"
    operationProcessors: "25"
    appResyncPeriod: "180"
    repoServerTimeoutSeconds: "300"

dex:
  enabled: true
  replicas: 2

server:
  replicas: 3
  service:
    type: LoadBalancer
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 5
    targetCPUUtilizationPercentage: 75
    targetMemoryUtilizationPercentage: 75
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  
  # SSO集成
  configEnabled: true
  config:
    url: https://argocd.example.com
    admin.enabled: "false"
    oidc.config: |
      name: OIDC
      issuer: https://auth.example.com
      clientID: $oidc.clientID
      clientSecret: $oidc.clientSecret
      requestedScopes: ["openid", "profile", "email", "groups"]
      requestedIDTokenClaims: {"groups": {"essential": true}}

repoServer:
  replicas: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 6
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  # 启用多个Helm/KSOPS插件
  volumes:
  - name: custom-tools
    emptyDir: {}
  volumeMounts:
  - name: custom-tools
    mountPath: /usr/local/bin/ksops
  initContainers:
  - name: download-tools
    image: alpine:3.8
    command: [sh, -c]
    args:
    - wget -O /custom-tools/ksops https://github.com/viaduct-ai/kustomize-sops/releases/download/v4.2.0/ksops_4.2.0_Linux_x86_64.tar.gz &&
      tar -xzf /custom-tools/ksops -C /custom-tools &&
      chmod +x /custom-tools/ksops
    volumeMounts:
    - name: custom-tools
      mountPath: /custom-tools

applicationSet:
  enabled: true
  replicaCount: 2

notifications:
  enabled: true

# 指标和监控
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    namespace: monitoring
```

#### 3.2.2 Application与AppProject配置

```yaml
# AppProject - 多租户隔离
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production-apps
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-1"
spec:
  description: Production Applications
  
  # 允许的源Git仓库
  sourceRepos:
  - "https://github.com/example/gitops-repo.git"
  - "https://github.com/example/helm-charts.git"
  
  # 允许部署的目标集群和命名空间
  destinations:
  - namespace: production
    server: https://kubernetes.default.svc
  - namespace: production-data
    server: https://production-cluster.example.com
  
  # 允许的资源类型白名单
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  - group: storage.k8s.io
    kind: StorageClass
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
  - kind: ClusterRoleBinding
  - group: admissionregistration.k8s.io
    kind: MutatingWebhookConfiguration
  - kind: ValidatingWebhookConfiguration
  
  namespaceResourceWhitelist:
  - group: apps
    kind: Deployment
  - group: apps
    kind: StatefulSet
  - group: ''
    kind: Service
  - group: ''
    kind: ConfigMap
  - group: ''
    kind: Secret
  - group: networking.k8s.io
    kind: Ingress
  - group: networking.istio.io
    kind: VirtualService
  - group: autoscaling
    kind: HorizontalPodAutoscaler
  
  # 黑名单（禁止的资源）
  namespaceResourceBlacklist:
  - group: ''
    kind: ResourceQuota
  
  # 角色权限
  roles:
  - name: developer
    description: Developer access
    policies:
    - p, proj:production-apps:developer, applications, get, production-apps/*, allow
    - p, proj:production-apps:developer, applications, sync, production-apps/*, allow
    groups:
    - example:developers
  
  - name: admin
    description: Admin access
    policies:
    - p, proj:production-apps:admin, *, *, production-apps/*, allow
    groups:
    - example:sre
  
  # 同步窗口限制
  syncWindows:
  - kind: allow
    schedule: "0 2 * * *"      # 每天凌晨2点
    duration: 4h                # 持续4小时
    applications:
    - "*-database*"
    namespaces:
    - "production-data"
    clusters:
    - "https://production-cluster.example.com"
  
  - kind: deny
    schedule: "0 9-18 * * 1-5"  # 工作时间禁止同步
    duration: 9h
    manualSync: true            # 但允许手动同步
  
  # 签名验证
  signatureKeys:
  - keyID: ABCD1234
  
  # 资源配额
  sourceNamespaces:
  - "argocd"
---
# Application - 单应用定义
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
  namespace: argocd
  labels:
    environment: production
    team: payments
    tier: backend
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: production-apps
  
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: apps/payment-service/overlays/production
    
    # Helm特定配置
    # helm:
    #   valueFiles:
    #   - values-production.yaml
    #   parameters:
    #   - name: replicaCount
    #     value: "5"
    #   version: v3
    
    # Kustomize特定配置
    kustomize:
      namePrefix: prod-
      nameSuffix: -v2
      images:
      - gcr.io/example/payment-service:v2.3.1
      commonLabels:
        environment: production
      commonAnnotations:
        deployed-by: argocd
        commit-sha: $ARGOCD_APP_REVISION
    
    # 目录配置
    directory:
      recurse: true
      jsonnet: {}
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    automated:
      prune: true              # 自动删除不在Git中的资源
      selfHeal: true           # 自动修复偏离状态
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    - ApplyOutOfSyncOnly=true
    - ServerSideApply=true
    - Validate=false
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  revisionHistoryLimit: 10
  
  # 健康检查忽略
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas
  - group: ""
    kind: Secret
    jsonPointers:
    - /data
---
# ApplicationSet - 多应用批量管理
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices-appset
  namespace: argocd
spec:
  generators:
  # Git目录生成器
  - git:
      repoURL: https://github.com/example/gitops-repo.git
      revision: main
      directories:
      - path: apps/*
        exclude: true
      - path: apps/payment-service
      - path: apps/order-service
      - path: apps/inventory-service
  
  # 列表生成器（环境矩阵）
  - list:
      elements:
      - env: development
        cluster: https://kubernetes.default.svc
        namespace: dev
        revision: HEAD
      - env: staging
        cluster: https://staging-cluster.example.com
        namespace: staging
        revision: HEAD
      - env: production
        cluster: https://production-cluster.example.com
        namespace: production
        revision: main
  
  # 集群生成器
  - clusters:
      selector:
        matchLabels:
          environment: production
      values:
        revision: main
  
  # SCM Provider生成器（自动发现仓库）
  - scmProvider:
      github:
        organization: example
        tokenRef:
          secretName: github-token
          key: token
      filters:
      - repositoryMatch: microservice-.*
        pathsExist: [kubernetes/]
  
  # 模板定义
  template:
    metadata:
      name: '{{path.basename}}-{{env}}'
      labels:
        app: '{{path.basename}}'
        environment: '{{env}}'
    spec:
      project: '{{env}}-apps'
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: '{{revision}}'
        path: '{{path}}'
      destination:
        server: '{{cluster}}'
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
  
  # 同步策略
  syncPolicy:
    preserveResourcesOnDeletion: false
```

#### 3.2.3 高级同步策略

```yaml
# 渐进式交付 - Argo Rollouts集成
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payment-service
  namespace: production
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: payment-service-canary
      stableService: payment-service-stable
      trafficRouting:
        istio:
          virtualService:
            name: payment-service-vs
            routes:
            - primary
          destinationRule:
            name: payment-service-dr
            canarySubsetName: canary
            stableSubsetName: stable
      steps:
      # 步骤1: 部署1个Pod，等待5分钟
      - setWeight: 20
      - pause: {duration: 5m}
      
      # 步骤2: 自动分析（基于Prometheus指标）
      - setWeight: 40
      - analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: payment-service
      
      # 步骤3: 扩展到60%，暂停等待手动批准
      - setWeight: 60
      - pause: {}
      
      # 步骤4: 扩展到80%，等待30分钟或手动继续
      - setWeight: 80
      - pause: {duration: 30m}
      
      # 步骤5: 100%流量切换
      - setWeight: 100
      
      # 回滚配置
      abortScaleDownDelaySeconds: 600
      scaleDownDelayRevisionLimit: 2
  
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: payment-service:v2.0.0
        ports:
        - containerPort: 8080
---
# 自动分析模板
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.99
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status=~"2.."}[1m]))
          /
          sum(rate(http_requests_total{service="{{args.service-name}}"}[1m]))
  - name: latency
    interval: 1m
    count: 5
    successCondition: result[0] <= 0.5
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc:9090
        query: |
          histogram_quantile(0.99, 
            sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[1m])) by (le)
          )
```

### 3.3 Flux CD实践

#### 3.3.1 Flux安装与配置

```bash
# Flux CLI安装
# curl -s https://fluxcd.io/install.sh | sudo bash

# Flux引导安装（GitHub）
flux bootstrap github \
  --owner=example \
  --repository=gitops-flux \
  --branch=main \
  --path=clusters/production \
  --personal \
  --components-extra=image-reflector-controller,image-automation-controller
```

```yaml
# GitRepository - 源配置
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: production-apps
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/example/gitops-flux
  ref:
    branch: main
  secretRef:
    name: github-token
  ignore:
    /*
    !/apps/
    !/infrastructure/
---
# OCIRepository - Helm Chart存储
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: podinfo
  namespace: flux-system
spec:
  interval: 5m
  url: oci://ghcr.io/stefanprodan/charts/podinfo
  ref:
    semver: ">=6.0.0"
---
# HelmRepository - 传统Helm仓库
apiVersion: source.toolkit.flux.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.bitnami.com/bitnami
```

#### 3.3.2 Kustomization与HelmRelease

```yaml
# Kustomization - 声明式应用
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: infrastructure
  namespace: flux-system
spec:
  interval: 10m
  path: ./infrastructure/overlays/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: production-apps
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: cert-manager
    namespace: cert-manager
  - apiVersion: apps/v1
    kind: Deployment
    name: ingress-nginx
    namespace: ingress-nginx
  timeout: 5m
  retryInterval: 1m
  wait: true
  dependsOn:
  - name: crds
---
# 应用层Kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  interval: 5m
  path: ./apps/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: production-apps
  dependsOn:
  - name: infrastructure
  postBuild:
    substitute:
      cluster_name: production
      cluster_region: us-west-2
      domain: example.com
    substituteFrom:
    - kind: ConfigMap
      name: cluster-vars
---
# HelmRelease - Helm部署
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: postgresql
  namespace: database
spec:
  interval: 5m
  chart:
    spec:
      chart: postgresql
      version: "12.x"
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
      interval: 1m
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
      remediateLastFailure: true
    cleanupOnFail: true
  rollback:
    timeout: 5m
    disableWait: false
    cleanupOnFail: false
  values:
    auth:
      existingSecret: postgres-credentials
    primary:
      persistence:
        enabled: true
        size: 100Gi
        storageClass: fast-ssd
      resources:
        requests:
          memory: 4Gi
          cpu: 2000m
      podDisruptionBudget:
        enabled: true
        minAvailable: 1
    metrics:
      enabled: true
      serviceMonitor:
        enabled: true
---
# 依赖管理
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: api-service
  namespace: production
spec:
  interval: 5m
  chart:
    spec:
      chart: ./charts/api-service
      sourceRef:
        kind: GitRepository
        name: production-apps
  dependsOn:
  - name: postgresql
    namespace: database
  - name: redis
    namespace: cache
  values:
    replicaCount: 5
    image:
      repository: api-service
      tag: v2.0.0
```

#### 3.3.3 镜像自动化

```yaml
# ImageRepository - 镜像仓库扫描
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: api-service
  namespace: flux-system
spec:
  image: ghcr.io/example/api-service
  interval: 1m
  provider: generic
  secretRef:
    name: ghcr-auth
  exclusionList:
  - ".*\\-arm64"
  - ".*\\-rc\\..*"
---
# ImagePolicy - 镜像策略
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: api-service
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: api-service
  policy:
    semver:
      range: ">=2.0.0 <3.0.0"
    # 或按时间戳
    # alphabetical:
    #   order: asc
  filterTags:
    pattern: '^v(?P<version>.*)$'
    extract: '$version'
---
# ImageUpdateAutomation - 自动更新Git
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: production-apps
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        name: Flux Bot
        email: flux@example.com
      messageTemplate: |
        Automated image update
        
        Images:
        {{ range .Updated.Images -}}
        - {{.}}
        {{ end }}
        
        Automation: {{ .AutomationObject }}
    signingKey:
      secretRef:
        name: flux-gpg-signing-key
  policy:
    alphabetical:
      order: asc
```

#### 3.3.4 通知与告警

```yaml
# Provider - 通知渠道
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack
  namespace: flux-system
spec:
  type: slack
  channel: deployments
  secretRef:
    name: slack-webhook
---
# Alert - 告警规则
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-alerts
  namespace: flux-system
spec:
  summary: "Production Deployments"
  providerRef:
    name: slack
  eventSeverity: info
  eventSources:
  - kind: Kustomization
    name: apps
    namespace: flux-system
  - kind: HelmRelease
    name: "*"
    namespace: production
  inclusionList:
  - "Succeeded"
  - "Failed"
  - "Progressing"
  exclusionList:
  - ".*upgrade.*has started"
---
# 事件过滤
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: critical-errors
  namespace: flux-system
spec:
  providerRef:
    name: pagerduty
  eventSeverity: error
  eventSources:
  - kind: HelmRelease
    name: database
    namespace: production
  - kind: Kustomization
    name: infrastructure
```

### 3.4 ArgoCD vs Flux对比

| 特性 | ArgoCD | Flux |
|------|--------|------|
| UI界面 | ✅ 功能丰富 | ❌ CLI/Grafana |
| 多集群管理 | ✅ 内置支持 | ✅ GitOps方式 |
| 应用依赖 | ✅ 支持 | ✅ dependsOn |
| 镜像自动化 | ⚠️ Argo Image Updater | ✅ 原生支持 |
| Helm支持 | ✅ 原生 | ✅ 原生 |
| Kustomize | ✅ 原生 | ✅ 原生 |
| 渐进式交付 | ✅ Argo Rollouts | ⚠️ Flagger |
| Secrets管理 | ✅ Sealed Secrets/External Secrets | ✅ SOPS/Mozilla SOPS |
| 多租户 | ✅ AppProject | ⚠️ RBAC |
| 资源清理 | ✅ 自动Prune | ✅ 自动Prune |

---

## 4. 云原生可观测性 - OpenTelemetry

### 4.1 OpenTelemetry架构

```
┌─────────────────────────────────────────────────────────────────┐
│                   OpenTelemetry Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Application │  │   Sidecar   │  │   Agent     │             │
│  │  (Auto      │  │  (Envoy/    │  │  (DaemonSet)│             │
│  │  Instrument)│  │  OTel SDK)  │  │             │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┴────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │              OpenTelemetry Collector                   │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │      │
│  │  │ Receivers│→ │ Processors│→ │ Exporters│            │      │
│  │  │ (OTLP/   │  │ (Batch/  │  │(Prometheus│            │      │
│  │  │ Prometheus│  │ Filter/  │  │ /Jaeger/  │            │      │
│  │  │ Zipkin)  │  │ Resource)│  │ Cloud)    │            │      │
│  │  └──────────┘  └──────────┘  └──────────┘            │      │
│  └───────────────────────────────────────────────────────┘      │
│                          │                                      │
│          ┌───────────────┼───────────────┐                     │
│          ▼               ▼               ▼                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Prometheus  │ │   Jaeger    │ │   Grafana   │               │
│  │  (Metrics)  │ │  (Traces)   │ │  (Unified)  │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 OpenTelemetry Collector配置

```yaml
# OpenTelemetry Collector配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
data:
  collector.yaml: |
    receivers:
      # OTLP接收器（gRPC/HTTP）
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
            max_recv_msg_size_mib: 16
            keepalive:
              server_parameters:
                timeout: 20s
          http:
            endpoint: 0.0.0.0:4318
            cors:
              allowed_origins: ["*"]
              allowed_headers: ["*"]
      
      # Prometheus抓取
      prometheus:
        config:
          scrape_configs:
          - job_name: 'kubernetes-pods'
            kubernetes_sd_configs:
            - role: pod
              namespaces:
                names:
                - production
                - staging
            relabel_configs:
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
              action: keep
              regex: true
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
              action: replace
              target_label: __metrics_path__
              regex: (.+)
            - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
              action: replace
              regex: ([^:]+)(?::\d+)?;(\d+)
              replacement: $1:$2
              target_label: __address__
            - action: labelmap
              regex: __meta_kubernetes_pod_label_(.+)
            - source_labels: [__meta_kubernetes_namespace]
              action: replace
              target_label: kubernetes_namespace
            - source_labels: [__meta_kubernetes_pod_name]
              action: replace
              target_label: kubernetes_pod_name
      
      # 主机指标
      hostmetrics:
        collection_interval: 10s
        scrapers:
          cpu:
          memory:
          disk:
          filesystem:
          network:
          load:
          processes:
      
      # Kubernetes事件
      k8s_events:
        auth_type: serviceAccount
        namespaces: [production, staging]
      
      # 文件日志
      filelog:
        include:
          - /var/log/pods/*/*/*.log
        exclude:
          - /var/log/pods/*/otel-collector/*.log
        start_at: beginning
        multiline:
          line_start_pattern: ^\d{4}-\d{2}-\d{2}
        operators:
          - type: kubernetes_parser
            id: parser-k8s-logs
      
      # Jaeger兼容
      jaeger:
        protocols:
          grpc:
            endpoint: 0.0.0.0:14250
          thrift_http:
            endpoint: 0.0.0.0:14268
          thrift_compact:
            endpoint: 0.0.0.0:6831
      
      # Zipkin兼容
      zipkin:
        endpoint: 0.0.0.0:9411
    
    processors:
      # 批处理
      batch:
        timeout: 1s
        send_batch_size: 1024
        send_batch_max_size: 2048
      
      # 内存限制
      memory_limiter:
        limit_mib: 1500
        spike_limit_mib: 512
        check_interval: 5s
      
      # 资源属性
      resource:
        attributes:
        - key: cluster.name
          value: production
          action: upsert
        - key: environment
          value: production
          action: upsert
        - key: k8s.cluster.name
          from_attribute: k8s.cluster.name
          action: upsert
      
      # K8s属性
      k8sattributes:
        auth_type: serviceAccount
        passthrough: false
        filter:
          node_from_env_var: K8S_NODE_NAME
        extract:
          metadata:
            - k8s.pod.name
            - k8s.pod.uid
            - k8s.deployment.name
            - k8s.namespace.name
            - k8s.node.name
            - k8s.pod.start_time
          labels:
            - tag_name: app.label.component
              key: app.kubernetes.io/component
              from: pod
            - tag_name: app.label.part-of
              key: app.kubernetes.io/part-of
              from: pod
        pod_association:
          - sources:
              - from: resource_attribute
                name: k8s.pod.ip
          - sources:
              - from: resource_attribute
                name: k8s.pod.uid
          - sources:
              - from: connection
      
      # 指标转换
      metricstransform:
        transforms:
          - include: kubernetes.
            match_type: regexp
            action: update
            operations:
              - action: add_label
                new_label: cluster
                new_value: production
      
      # 采样
      probabilistic_sampler:
        sampling_percentage: 10.0
        hash_seed: 22
      
      # 尾部采样
      tail_sampling:
        decision_wait: 10s
        num_traces: 100
        expected_new_traces_per_sec: 10
        policies:
          - name: errors
            type: status_code
            status_code: {status_codes: [ERROR]}
          - name: slow
            type: latency
            latency: {threshold_ms: 1000}
          - name: probabilistic
            type: probabilistic
            probabilistic: {sampling_percentage: 10}
      
      # 过滤器
      filter:
        error_mode: ignore
        metrics:
          metric:
            - 'type == METRIC_DATA_TYPE_SUMMARY'
      
      # 跨度处理器
      span:
        include:
          match_type: strict
          services: [payment-service, order-service]
        name:
          from_attributes: [http.method, http.route]
          separator: " "
    
    exporters:
      # Prometheus Remote Write
      prometheusremotewrite:
        endpoint: http://prometheus.monitoring.svc:9090/api/v1/write
        target_info:
          enabled: true
      
      # OTLP到Jaeger
      otlp/jaeger:
        endpoint: jaeger-collector.monitoring.svc:4317
        tls:
          insecure: true
      
      # OTLP到Tempo
      otlp/tempo:
        endpoint: tempo.monitoring.svc:4317
        tls:
          insecure: true
      
      # Loki日志
      loki:
        endpoint: http://loki.monitoring.svc:3100/loki/api/v1/push
        labels:
          attributes:
            k8s.container.name: "pod"
            k8s.namespace.name: "namespace"
            k8s.pod.name: "instance"
      
      # Elasticsearch
      elasticsearch:
        endpoints: [http://elasticsearch.logging.svc:9200]
        index: otel-logs
      
      # 云厂商
      otlp/aws:
        endpoint: otlp.ingest.us-east-1.aws.com:4317
        headers:
          x-api-key: ${AWS_API_KEY}
      
      # 调试
      debug:
        verbosity: detailed
      
      # 文件导出（备份）
      file:
        path: /var/log/otel/export.json
      
      # 队列重试
      otlp/backup:
        endpoint: backup-collector.monitoring.svc:4317
        retry_on_failure:
          enabled: true
          initial_interval: 5s
          max_interval: 30s
          max_elapsed_time: 300s
        sending_queue:
          enabled: true
          num_consumers: 10
          queue_size: 1000
    
    extensions:
      health_check:
        endpoint: 0.0.0.0:13133
      pprof:
        endpoint: 0.0.0.0:1777
      zpages:
        endpoint: 0.0.0.0:55679
      memory_ballast:
        size_mib: 512
    
    service:
      extensions: [health_check, pprof, zpages, memory_ballast]
      pipelines:
        # 指标管道
        metrics:
          receivers: [otlp, prometheus, hostmetrics]
          processors: [memory_limiter, resource, k8sattributes, batch]
          exporters: [prometheusremotewrite, debug]
        
        # 链路管道
        traces:
          receivers: [otlp, jaeger, zipkin]
          processors: [memory_limiter, resource, k8sattributes, tail_sampling, batch]
          exporters: [otlp/jaeger, otlp/tempo]
        
        # 日志管道
        logs:
          receivers: [otlp, filelog, k8s_events]
          processors: [memory_limiter, resource, k8sattributes, batch]
          exporters: [loki, elasticsearch]
      
      telemetry:
        logs:
          level: info
        metrics:
          level: detailed
          address: 0.0.0.0:8888
---
# OpenTelemetry Collector部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: observability
spec:
  replicas: 3
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      serviceAccountName: otel-collector
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.91.0
        command:
        - /otelcol-contrib
        - --config=/conf/collector.yaml
        resources:
          limits:
            cpu: 2000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 4317    # OTLP gRPC
          name: otlp-grpc
        - containerPort: 4318    # OTLP HTTP
          name: otlp-http
        - containerPort: 8888    # Metrics
          name: metrics
        - containerPort: 13133   # Health
          name: health
        volumeMounts:
        - name: config
          mountPath: /conf
        - name: varlog
          mountPath: /var/log
          readOnly: true
        livenessProbe:
          httpGet:
            path: /
            port: 13133
        readinessProbe:
          httpGet:
            path: /
            port: 13133
      volumes:
      - name: config
        configMap:
          name: otel-collector-config
      - name: varlog
        hostPath:
          path: /var/log
---
# DaemonSet - 节点级收集
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-agent
  namespace: observability
spec:
  selector:
    matchLabels:
      app: otel-agent
  template:
    metadata:
      labels:
        app: otel-agent
    spec:
      serviceAccountName: otel-collector
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: otel-agent
        image: otel/opentelemetry-collector-contrib:0.91.0
        command:
        - /otelcol-contrib
        - --config=/conf/agent.yaml
        env:
        - name: K8S_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: config
          mountPath: /conf
        - name: varlog
          mountPath: /var/log
        - name: dockerlogs
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: otel-agent-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: dockerlogs
        hostPath:
          path: /var/lib/docker/containers
```

### 4.3 应用程序插桩

```yaml
# Java应用 - OpenTelemetry自动插桩
apiVersion: apps/v1
kind: Deployment
metadata:
  name: java-service
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: java-service
  template:
    metadata:
      labels:
        app: java-service
      annotations:
        instrumentation.opentelemetry.io/inject-java: "true"
    spec:
      containers:
      - name: app
        image: java-service:1.0.0
        env:
        - name: OTEL_SERVICE_NAME
          value: java-service
        - name: OTEL_RESOURCE_ATTRIBUTES
          value: "deployment.environment=production,service.version=1.0.0"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: http://otel-collector.observability.svc:4317
        - name: OTEL_EXPORTER_OTLP_PROTOCOL
          value: grpc
        - name: OTEL_TRACES_EXPORTER
          value: otlp
        - name: OTEL_METRICS_EXPORTER
          value: otlp,prometheus
        - name: OTEL_LOGS_EXPORTER
          value: otlp
        - name: OTEL_JAVAAGENT_DEBUG
          value: "false"
        - name: OTEL_INSTRUMENTATION_COMMON_EXPERIMENTAL_CONTROLLER_TELEMETRY_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
---
# OpenTelemetry Instrumentation CRD
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: java-instrumentation
  namespace: production
spec:
  exporter:
    endpoint: http://otel-collector.observability.svc:4317
  propagators:
    - tracecontext
    - baggage
    - b3
  sampler:
    type: parentbased_traceidratio
    argument: "0.1"
  java:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:1.32.0
    env:
    - name: OTEL_INSTRUMENTATION_MICROMETER_ENABLED
      value: "true"
    - name: OTEL_INSTRUMENTATION_REDISCALA_ENABLED
      value: "true"
---
# Node.js应用
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-service
  namespace: production
spec:
  replicas: 3
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-nodejs: "true"
    spec:
      containers:
      - name: app
        image: nodejs-service:1.0.0
        env:
        - name: NODE_OPTIONS
          value: "--require /otel-auto-instrumentation/autoinstrumentation.js"
---
# Python应用
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-service
  namespace: production
spec:
  replicas: 3
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-python: "true"
    spec:
      containers:
      - name: app
        image: python-service:1.0.0
        env:
        - name: OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
          value: "urllib3"
```

### 4.4 Grafana统一观测

```yaml
# Grafana Tempo配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-config
  namespace: monitoring
data:
  tempo.yaml: |
    server:
      http_listen_port: 3200
    
    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317
            http:
              endpoint: 0.0.0.0:4318
    
    ingester:
      max_block_duration: 5m
    
    compactor:
      compaction:
        compaction_window: 1h
        max_block_bytes: 100_000_000
        block_retention: 168h  # 7天
        compacted_block_retention: 1h
    
    storage:
      trace:
        backend: s3
        s3:
          bucket: tempo-traces
          endpoint: s3.us-west-2.amazonaws.com
          region: us-west-2
        wal:
          path: /var/tempo/wal
        local:
          path: /var/tempo/blocks
    
    overrides:
      defaults:
        global:
          ingestion:
            rate_strategy: local
            rate_limit_bytes: 15000000
            burst_size_bytes: 20000000
            max_traces_per_user: 10000
---
# Grafana数据源配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus.monitoring.svc:9090
      access: proxy
      isDefault: true
      jsonData:
        timeInterval: "5s"
        httpMethod: POST
        manageAlerts: true
        prometheusType: Prometheus
        prometheusVersion: "2.40.0"
        cacheLevel: 'High'
        incrementalQuerying: true
    
    - name: Tempo
      type: tempo
      url: http://tempo.monitoring.svc:3200
      access: proxy
      jsonData:
        httpMethod: GET
        tracesToLogs:
          datasourceUid: 'loki'
          tags: ['pod', 'namespace']
          spanStartTimeShift: '-1h'
          spanEndTimeShift: '1h'
          filterByTraceID: false
          filterBySpanID: false
        tracesToMetrics:
          datasourceUid: 'prometheus'
          tags: [{ key: 'service.name', value: 'service' }]
        serviceMap:
          datasourceUid: 'prometheus'
        nodeGraph:
          enabled: true
    
    - name: Loki
      type: loki
      url: http://loki.monitoring.svc:3100
      access: proxy
      jsonData:
        maxLines: 1000
        derivedFields:
        - name: 'TraceID'
          matcherRegex: '"trace_id":"(\w+)"'
          url: '$${__value.raw}'
          datasourceUid: 'tempo'
    
    - name: Pyroscope
      type: grafana-pyroscope-datasource
      url: http://pyroscope.monitoring.svc:4040
---
# Grafana Dashboard配置示例
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  service-overview.json: |
    {
      "dashboard": {
        "title": "Service Overview - OpenTelemetry",
        "panels": [
          {
            "title": "Request Rate",
            "targets": [{
              "expr": "sum(rate(http_server_duration_count{service=\"$service\"}[5m]))"
            }]
          },
          {
            "title": "Error Rate",
            "targets": [{
              "expr": "sum(rate(http_server_duration_count{service=\"$service\",status_code=~\"5..\"}[5m])) / sum(rate(http_server_duration_count{service=\"$service\"}[5m]))"
            }]
          },
          {
            "title": "P99 Latency",
            "targets": [{
              "expr": "histogram_quantile(0.99, sum(rate(http_server_duration_bucket{service=\"$service\"}[5m])) by (le))"
            }]
          }
        ]
      }
    }
```

### 4.5 告警规则

```yaml
# PrometheusRule - OpenTelemetry指标告警
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: opentelemetry-alerts
  namespace: monitoring
spec:
  groups:
  - name: opentelemetry
    rules:
    # 高错误率
    - alert: HighErrorRate
      expr: |
        sum(rate(http_server_duration_count{status_code=~"5.."}[5m])) by (service)
        / sum(rate(http_server_duration_count[5m])) by (service) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Service {{ $labels.service }} has error rate above 5%"
    
    # 高延迟
    - alert: HighLatency
      expr: |
        histogram_quantile(0.99, 
          sum(rate(http_server_duration_bucket[5m])) by (le, service)
        ) > 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected"
        description: "Service {{ $labels.service }} P99 latency > 1s"
    
    # 收集器队列积压
    - alert: OTelCollectorQueueFull
      expr: otelcol_exporter_queue_size / otelcol_exporter_queue_capacity > 0.8
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "OTel Collector queue near capacity"
    
    # 链路采样率下降
    - alert: LowTraceSampling
      expr: |
        rate(otelcol_processor_tail_sampling_decision{decision="sampled"}[5m])
        / rate(otelcol_processor_tail_sampling_decision[5m]) < 0.05
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "Low trace sampling rate"
```

---

## 5. 多集群管理架构

### 5.1 多集群架构模式

```
┌─────────────────────────────────────────────────────────────────┐
│                  多集群管理架构模式                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  模式1: 联邦式 (KubeFed/Karmada)                                │
│  ┌─────────────┐                                               │
│  │   Control   │                                               │
│  │   Plane     │                                               │
│  │  (Karmada)  │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│    ┌────┼────┬────────┐                                        │
│    ▼    ▼    ▼        ▼                                        │
│  ┌────┐┌────┐┌────┐┌────┐                                      │
│  │ C1 ││ C2 ││ C3 ││ C4 │  # 成员集群                          │
│  └────┘└────┘└────┘└────┘                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  模式2: 控制平面集群                                            │
│  ┌─────────────────────────────┐                               │
│  │     Management Cluster      │                               │
│  │  ┌─────────┐ ┌─────────┐   │                               │
│  │  │ ArgoCD  │ │  Rancher│   │                               │
│  │  │ Istio   │ │ Fleet   │   │                               │
│  │  └─────────┘ └─────────┘   │                               │
│  └──────┬────────────────────┘                               │
│         │ 推送配置                                             │
│    ┌────┴────────────────────────┐                            │
│    ▼                             ▼                            │
│  ┌──────────┐              ┌──────────┐                       │
│  │ Prod     │              │ DR       │                       │
│  │ Cluster  │              │ Cluster  │                       │
│  └──────────┘              └──────────┘                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  模式3: 服务网格多集群                                          │
│  ┌─────────────┐       ┌─────────────┐                        │
│  │  Cluster A  │◄─────►│  Cluster B  │                        │
│  │ (Primary)   │  mTLS │ (Remote)    │                        │
│  │  ┌───────┐  │       │  ┌───────┐  │                        │
│  │  │Istiod │  │       │  │Istiod │  │                        │
│  │  │(Shared│◄─┘       │  │(Proxy)│  │                        │
│  │  └───────┘          │  └───────┘  │                        │
│  └─────────────┘       └─────────────┘                        │
│         │                    │                                  │
│         └────────────────────┘                                  │
│              跨集群服务发现                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Karmada多集群管理

```yaml
# Karmada安装
# kubectl apply -f https://raw.githubusercontent.com/karmada-io/karmada/master/hack/deploy-karmada.sh

# Karmada PropagationPolicy - 资源分发策略
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-propagation
  namespace: production
spec:
  resourceSelectors:
  - apiVersion: apps/v1
    kind: Deployment
    name: nginx
  - apiVersion: v1
    kind: Service
    name: nginx
  
  placement:
    clusterAffinity:
      clusterNames:
      - cluster-beijing
      - cluster-shanghai
      - cluster-shenzhen
      # 或标签选择
      # labelSelector:
      #   matchLabels:
      #     region: east-china
    
    clusterTolerations:
    - key: cluster.karmada.io/not-ready
      operator: Exists
      effect: NoExecute
      tolerationSeconds: 300
    - key: cluster.karmada.io/unreachable
      operator: Exists
      effect: NoExecute
      tolerationSeconds: 300
    
    spreadConstraints:
    - spreadByField: cluster
      maxGroups: 3
      minGroups: 2
    - spreadByField: region
      maxGroups: 2
      minGroups: 1
    
    replicaScheduling:
      replicaSchedulingType: Divided
      replicaDivisionPreference: Weighted
      weightPreference:
        staticWeightList:
        - targetCluster:
            clusterNames: [cluster-beijing]
          weight: 40
        - targetCluster:
            clusterNames: [cluster-shanghai]
          weight: 35
        - targetCluster:
            clusterNames: [cluster-shenzhen]
          weight: 25
---
# OverridePolicy - 集群特定覆盖
apiVersion: policy.karmada.io/v1alpha1
kind: OverridePolicy
metadata:
  name: nginx-override
  namespace: production
spec:
  resourceSelectors:
  - apiVersion: apps/v1
    kind: Deployment
    name: nginx
  
  overrideRules:
  # 北京集群特定配置
  - targetCluster:
      clusterNames: [cluster-beijing]
    overriders:
      plaintext:
      - path: "/spec/template/spec/containers/0/image"
        operator: replace
        value: "nginx:beijing-mirror"
      - path: "/spec/replicas"
        operator: replace
        value: 5
      - path: "/metadata/annotations"
        operator: add
        value:
          region: beijing
  
  # 上海集群特定配置
  - targetCluster:
      clusterNames: [cluster-shanghai]
    overriders:
      plaintext:
      - path: "/spec/replicas"
        operator: replace
        value: 4
      - path: "/spec/template/spec/nodeSelector"
        operator: add
        value:
          zone: shanghai-az1
  
  # 字段解析器覆盖
  - targetCluster:
      labelSelector:
        matchLabels:
          zone: south
    overriders:
      fieldoverride:
        fieldPath: "/spec/template/spec/containers/0/resources/limits/cpu"
        value: "2000m"
---
# MultiClusterIngress - 跨集群Ingress
apiVersion: networking.karmada.io/v1alpha1
kind: MultiClusterIngress
metadata:
  name: web-ingress
  namespace: production
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx
            port:
              number: 80
  tls:
  - hosts:
    - app.example.com
    secretName: tls-secret
---
# MultiClusterService - 跨集群Service
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: mcs-policy
  namespace: production
spec:
  resourceSelectors:
  - apiVersion: multicluster.x-k8s.io/v1alpha1
    kind: ServiceExport
    name: backend-service
  placement:
    clusterAffinity:
      clusterNames:
      - cluster-beijing
      - cluster-shanghai
---
# ServiceExport
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: backend-service
  namespace: production
---
# ServiceImport
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceImport
metadata:
  name: backend-service
  namespace: production
spec:
  type: ClusterSetIP
  ports:
  - name: http
    protocol: TCP
    port: 80
```

### 5.3 Rancher Fleet多集群GitOps

```yaml
# GitRepo - Fleet配置
apiVersion: fleet.cattle.io/v1alpha1
kind: GitRepo
metadata:
  name: production-apps
  namespace: fleet-default
spec:
  repo: https://github.com/example/gitops-fleet
  branch: main
  
  # 路径配置
  paths:
  - /apps/common
  - /apps/production
  
  # 目标集群选择
  targets:
  # 所有生产集群
  - name: all-production
    clusterSelector:
      matchLabels:
        environment: production
    clusterGroup: production-clusters
  
  # 特定区域
  - name: asia-pacific
    clusterSelector:
      matchExpressions:
      - key: region
        operator: In
        values: [ap-northeast, ap-southeast]
    
    # 覆盖值
    helm:
      values:
        replicaCount: 5
        resources:
          requests:
            memory: 2Gi
  
  # 金丝雀部署
  - name: canary
    clusterSelector:
      matchLabels:
        canary: "true"
    helm:
      values:
        image:
          tag: canary
  
  # 暂停某些集群
  - name: maintenance
    clusterSelector:
      matchLabels:
        maintenance: "true"
    paused: true
  
  # 同步配置
  clientSecretName: git-creds
  helmSecretName: helm-creds
  
  # 轮询间隔
  pollingInterval: 15s
  
  # 强制同步
  forceSyncGeneration: 1
  
  # 回滚配置
  rollback:
    enabled: true
    historyLimit: 10
---
# ClusterGroup - 集群分组
apiVersion: fleet.cattle.io/v1alpha1
kind: ClusterGroup
metadata:
  name: production-clusters
  namespace: fleet-default
spec:
  selector:
    matchExpressions:
    - key: environment
      operator: In
      values: [production]
    - key: ready
      operator: In
      values: ["true"]
---
# Bundle - 资源包
apiVersion: fleet.cattle.io/v1alpha1
kind: Bundle
metadata:
  name: monitoring-stack
  namespace: fleet-default
spec:
  resources:
  - content: |
      apiVersion: v1
      kind: Namespace
      metadata:
        name: monitoring
  - secretName: prometheus-config
  
  targets:
  - clusterSelector:
      matchLabels:
        monitoring: enabled
    
    helm:
      chart: prometheus
      repo: https://prometheus-community.github.io/helm-charts
      version: 15.0.0
      values:
        retention: 30d
        resources:
          requests:
            memory: 4Gi
---
# BundleDeployment - 部署状态
apiVersion: fleet.cattle.io/v1alpha1
kind: BundleDeployment
metadata:
  name: monitoring-stack
  namespace: cluster-clusters-production-xyz
status:
  conditions:
  - type: Ready
    status: "True"
  display:
    readyClusters: 5/5
    state: Ready
```

### 5.4 Istio多集群服务网格

```yaml
# Primary-Remote模式配置

# 主集群 (istiod所在集群)
# ---
# 主集群IstioOperator
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: primary-istio
spec:
  profile: minimal
  meshConfig:
    trustDomain: example.com
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
        ISTIO_META_DNS_AUTO_ALLOCATE: "true"
  components:
    pilot:
      k8s:
        env:
        - name: PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY
          value: "true"
        - name: PILOT_ENABLE_K8S_SELECT_WORKLOAD_ENTRIES
          value: "false"
        - name: PILOT_ENABLE_REMOTE_JWKS
          value: "true"
  values:
    global:
      multiCluster:
        clusterName: primary
        network: network1
      meshID: mesh1
      istiod:
        enableAnalysis: true
---
# 远程集群IstioOperator
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: remote-istio
spec:
  profile: remote
  values:
    global:
      istiod:
        enableAnalysis: true
      multiCluster:
        clusterName: remote-beijing
        network: network1
      meshID: mesh1
      remotePilotAddress: istiod.istio-system.svc.cluster.local  # 主集群istiod
  meshConfig:
    trustDomain: example.com
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
        ISTIO_META_DNS_AUTO_ALLOCATE: "true"
---
# 多集群Secret（主集群创建）
apiVersion: v1
kind: Secret
metadata:
  name: remote-beijing-secret
  namespace: istio-system
  labels:
    istio/multiCluster: "true"
type: Opaque
data:
  # base64编码的远程集群kubeconfig
  config: <base64-encoded-kubeconfig>
---
# 跨集群ServiceEntry
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: cross-cluster-service
  namespace: production
spec:
  hosts:
  - backend.remote-beijing.global
  location: MESH_INTERNAL
  ports:
  - number: 8080
    name: http
    protocol: HTTP
  resolution: DNS
  endpoints:
  # 本地端点
  - address: backend.production.svc.cluster.local
    locality: region/primary/zone-1a
    labels:
      cluster: primary
  # 远程端点
  - address: backend.remote-beijing.global
    locality: region/beijing/zone-1
    labels:
      cluster: remote-beijing
---
# 本地性负载均衡配置
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: cross-cluster-lb
  namespace: production
spec:
  host: backend.remote-beijing.global
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
    loadBalancer:
      simple: LEAST_CONN
      localityLbSetting:
        enabled: true
        distribute:
        - from: region/primary/*
          to:
            "region/primary/*": 80
            "region/beijing/*": 20
        failover:
        - from: region/primary
          to: region/beijing
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
---
# 多集群Gateway
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: multi-cluster-gateway
  namespace: istio-system
spec:
  selector:
    istio: eastwestgateway
  servers:
  - port:
      number: 15443
      name: tls
      protocol: TLS
    tls:
      mode: ISTIO_MUTUAL
    hosts:
    - "*.local"
  # 跨集群发现端口
  - port:
      number: 15012
      name: tls-istiod
      protocol: TLS
    tls:
      mode: ISTIO_MUTUAL
    hosts:
    - "istiod.istio-system.svc.cluster.local"
```

### 5.5 跨集群可观测性

```yaml
# Thanos - 多集群Prometheus联邦
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: thanos-query
  template:
    metadata:
      labels:
        app: thanos-query
    spec:
      containers:
      - name: thanos-query
        image: quay.io/thanos/thanos:v0.32.0
        args:
        - query
        - --http-address=0.0.0.0:9090
        - --grpc-address=0.0.0.0:10901
        - --store=thanos-sidecar-prod-1.monitoring.svc:10901
        - --store=thanos-sidecar-prod-2.monitoring.svc:10901
        - --store=thanos-sidecar-dr.monitoring.svc:10901
        - --store=thanos-store-gateway:10901
        - --query.replica-label=replica
        - --query.auto-downsampling
        ports:
        - containerPort: 9090
          name: http
        - containerPort: 10901
          name: grpc
---
# Thanos Sidecar配置
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.48.0
        args:
        - --config.file=/etc/prometheus/prometheus.yml
        - --storage.tsdb.path=/prometheus
        - --storage.tsdb.retention.time=2h  # 本地只保留2小时
      - name: thanos-sidecar
        image: quay.io/thanos/thanos:v0.32.0
        args:
        - sidecar
        - --tsdb.path=/prometheus
        - --prometheus.url=http://localhost:9090
        - --grpc.address=0.0.0.0:10901
        - --http.address=0.0.0.0:10902
        - --objstore.config-file=/etc/thanos/bucket.yml
        volumeMounts:
        - name: thanos-config
          mountPath: /etc/thanos
---
# Thanos对象存储配置
apiVersion: v1
kind: Secret
metadata:
  name: thanos-objstore
  namespace: monitoring
type: Opaque
stringData:
  bucket.yml: |
    type: S3
    config:
      bucket: thanos-metrics
      endpoint: s3.us-west-2.amazonaws.com
      region: us-west-2
      access_key: ${AWS_ACCESS_KEY}
      secret_key: ${AWS_SECRET_KEY}
      insecure: false
      signature_version2: false
      put_user_metadata:
        X-Storage-Class: REDUCED_REDUNDANCY
---
# 跨集群日志聚合 - Fluent Bit
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            docker
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10
    
    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        Keep_Log            Off
        K8S-Logging.Parser  On
        K8S-Logging.Exclude On
        Labels              On
        Annotations         Off
        Kube_Meta_Cache_TTL 300s
    
    [FILTER]
        Name          modify
        Match         kube.*
        Add           cluster ${CLUSTER_NAME}
    
    [OUTPUT]
        Name            loki
        Match           *
        Host            loki-gateway.logging.svc
        Port            80
        Labels          job=fluentbit,cluster=${CLUSTER_NAME}
        Line_Format     json
        Drop_Records    On
        Drop_Records_Cond  $kubernetes['namespace_name'] =~ 'kube-system|istio-system'
---
# Grafana Tempo多集群链路聚合
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-distributed
  namespace: monitoring
data:
  tempo.yaml: |
    multitenancy_enabled: true
    
    compactor:
      compaction:
        block_retention: 168h
    
    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317
    
    ingester:
      lifecycler:
        ring:
          replication_factor: 3
    
    storage:
      trace:
        backend: s3
        s3:
          bucket: tempo-traces
          endpoint: s3.us-west-2.amazonaws.com
    
    overrides:
      per_tenant_override_config: /conf/overrides.yaml
---
# 租户覆盖配置（按集群分离）
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-overrides
  namespace: monitoring
data:
  overrides.yaml: |
    overrides:
      "cluster-primary":
        ingestion_rate_strategy: local
        ingestion_rate_limit: 15000000
        ingestion_burst_size: 20000000
        max_traces_per_user: 100000
      "cluster-dr":
        ingestion_rate_strategy: local
        ingestion_rate_limit: 10000000
        ingestion_burst_size: 15000000
        max_traces_per_user: 50000
```

### 5.6 灾备与故障转移

```yaml
# 应用层灾备配置
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: dr-apps
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - cluster: primary
        url: https://primary.example.com
        region: us-west-2
        replicas: 5
      - cluster: dr
        url: https://dr.example.com
        region: us-east-1
        replicas: 0  # DR站点初始0副本
  template:
    metadata:
      name: '{{cluster}}-app'
    spec:
      project: production
      source:
        repoURL: https://github.com/example/gitops
        targetRevision: HEAD
        path: apps/dr-enabled
        helm:
          values: |
            clusterName: {{cluster}}
            region: {{region}}
            replicaCount: {{replicas}}
            failover:
              enabled: {{cluster == 'dr'}}
              primaryCluster: primary
      destination:
        server: '{{url}}'
        namespace: production
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
---
# DNS故障转移 - ExternalDNS + Route53
apiVersion: externaldns.k8s.io/v1alpha1
kind: DNSEndpoint
metadata:
  name: app-failover
  namespace: production
  annotations:
    external-dns.alpha.kubernetes.io/ttl: "60"
spec:
  endpoints:
  - dnsName: app.example.com
    recordType: A
    recordTTL: 60
    providerSpecific:
    - name: routing-policy
      value: failover
    - name: failover-routing-policy
      value: PRIMARY
    targets:
    - 1.2.3.4  # Primary LB IP
    - 5.6.7.8  # Secondary LB IP
    setIdentifier: primary
    
  - dnsName: app.example.com
    recordType: A
    recordTTL: 60
    providerSpecific:
    - name: routing-policy
      value: failover
    - name: failover-routing-policy
      value: SECONDARY
    targets:
    - 5.6.7.8
    setIdentifier: secondary
    
  - dnsName: health-check.example.com
    recordType: CNAME
    targets:
    - primary-health-check.example.com
---
# 数据库跨集群复制 - MySQL Operator
apiVersion: mysql.oracle.com/v2
kind: InnoDBCluster
metadata:
  name: production-db
  namespace: database
spec:
  secretName: db-credentials
  instances: 3
  router:
    instances: 2
  
  # 跨集群复制
  replicationGroupSeeds: |
    primary-cluster-mysql-0.mysql.database.svc:3306,
    dr-cluster-mysql-0.mysql.database.svc:3306
  
  # 故障转移配置
  failover:
    automatic: true
    consistency: BEFORE_ON_PRIMARY_FAILOVER
  
  # 备份配置
  backupSchedules:
  - name: hourly-backup
    schedule: "0 * * * *"
    backupProfile:
      dumpInstance:
        storage:
          s3:
            bucket: mysql-backups
            region: us-west-2
            prefix: hourly/
    enabled: true
    deleteBackupAfter: 168h  # 7天后删除
  
  - name: cross-region-replication
    schedule: "*/5 * * * *"
    backupProfile:
      dumpInstance:
        storage:
          s3:
            bucket: mysql-backups-dr
            region: us-east-1  # 跨区域备份
            prefix: replica/
    enabled: true
```

### 5.7 多集群安全最佳实践

```yaml
# 跨集群RBAC配置
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cross-cluster-reader
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
---
# ServiceAccount绑定
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cross-cluster-agent
  namespace: system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cross-cluster-agent-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cross-cluster-reader
subjects:
- kind: ServiceAccount
  name: cross-cluster-agent
  namespace: system
---
# 跨集群Secret同步
apiVersion: external-secrets.io/v1beta1
kind: ClusterExternalSecret
metadata:
  name: shared-secrets
spec:
  externalSecretName: shared-secrets
  namespaceSelectors:
  - matchLabels:
      shared-secrets: "true"
  externalSecretSpec:
    secretStoreRef:
      kind: ClusterSecretStore
      name: aws-secrets-manager
    target:
      name: shared-credentials
      creationPolicy: Owner
    data:
    - secretKey: db-password
      remoteRef:
        key: production/db-password
    - secretKey: api-key
      remoteRef:
        key: production/api-key
---
# 集群间mTLS证书管理
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: cross-cluster-ca
spec:
  ca:
    secretName: cross-cluster-ca-secret
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: inter-cluster-cert
  namespace: istio-system
spec:
  secretName: inter-cluster-cert
  issuerRef:
    name: cross-cluster-ca
    kind: ClusterIssuer
  dnsNames:
  - "*.cluster.local"
  - "*.svc.cluster.local"
  - istiod.istio-system.svc.cluster.local
  ipAddresses:
  - 10.0.0.1
  - 10.0.0.2
  usages:
  - server auth
  - client auth
```

---

## 6. 总结与最佳实践

### 6.1 技术选型建议

| 场景 | 推荐方案 | 备选方案 |
|------|----------|----------|
| 调度优化 | Pod Topology Spread + Cluster Autoscaler | KEDA事件驱动 |
| 服务网格 | Istio | Linkerd, Cilium Service Mesh |
| GitOps | ArgoCD (UI需求) / Flux (自动化需求) | Jenkins X |
| 可观测性 | OpenTelemetry + Grafana Stack | Datadog, New Relic |
| 多集群管理 | Karmada (工作负载) + Rancher (管理) | Google Anthos, Azure Arc |

### 6.2 实施路线图

```
第一阶段（1-2月）: 基础能力
├── Kubernetes调度优化
├── HPA/VPA配置
└── 基础监控部署

第二阶段（2-3月）: 服务网格
├── Istio部署
├── mTLS配置
├── 金丝雀发布
└── 可观测性集成

第三阶段（3-4月）: GitOps
├── ArgoCD/Flux部署
├── 应用迁移
└── 自动化流水线

第四阶段（4-6月）: 多集群
├── 集群联邦
├── 跨集群网络
├── 灾备方案
└── 统一可观测性
```

### 6.3 关键检查清单

- [ ] **调度**: 节点亲和性、Pod反亲和性、拓扑分布配置
- [ ] **扩缩容**: HPA多指标、VPA资源优化、KEDA事件触发
- [ ] **网格**: mTLS强制、授权策略、流量镜像
- [ ] **GitOps**: 自动同步、资源清理、密钥管理
- [ ] **可观测性**: 三大支柱、统一关联、智能告警
- [ ] **多集群**: 网络互通、服务发现、故障转移

---

*报告完成 - 云原生与Kubernetes进阶技术深度报告*
