# 高性能系统设计 - 性能优化实战指南

> **文档版本**: v1.0  
> **编写日期**: 2026-02-16  
> **适用场景**: 高并发互联网系统架构设计与优化

---

## 目录

1. [分布式缓存策略](#一分布式缓存策略)
2. [消息队列选型与优化](#二消息队列选型与优化)
3. [数据库分库分表与读写分离](#三数据库分库分表与读写分离)
4. [限流熔断与降级策略](#四限流熔断与降级策略)
5. [全链路压测与性能调优](#五全链路压测与性能调优)
6. [压测方案与执行计划](#六压测方案与执行计划)

---

## 一、分布式缓存策略

### 1.1 Redis Cluster 架构详解

#### 架构特点
- **去中心化设计**: 无中心节点，节点间通过Gossip协议通信
- **数据分片**: 采用Hash Slot（16384个槽位）进行数据分片
- **主从复制**: 每个主节点可配置多个从节点，自动故障转移
- **水平扩展**: 支持在线扩缩容，数据自动迁移

#### 核心配置
```yaml
# redis-cluster.conf
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
cluster-require-full-coverage no
cluster-slave-validity-factor 10
cluster-migration-barrier 1

# 性能优化参数
tcp-keepalive 300
timeout 0
tcp-backlog 511
maxclients 10000
```

#### 智能客户端路由
```java
@Configuration
public class RedisClusterConfig {
    
    @Bean
    public LettuceConnectionFactory redisConnectionFactory() {
        RedisClusterConfiguration clusterConfig = new RedisClusterConfiguration(
            Arrays.asList(
                "node1:6379", "node2:6379", "node3:6379",
                "node4:6379", "node5:6379", "node6:6379"
            )
        );
        
        // 拓扑刷新配置
        ClientOptions clientOptions = ClientOptions.builder()
            .topologyRefreshOptions(
                ClusterTopologyRefreshOptions.builder()
                    .enableAllAdaptiveRefreshTriggers()
                    .enablePeriodicRefresh(Duration.ofSeconds(30))
                    .build()
            )
            .build();
        
        LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
            .clientOptions(clientOptions)
            .readFrom(ReadFrom.REPLICA_PREFERRED)
            .build();
        
        return new LettuceConnectionFactory(clusterConfig, clientConfig);
    }
}
```

### 1.2 Codis 架构详解

#### 架构组件
| 组件 | 功能 | 高可用方案 |
|------|------|-----------|
| codis-proxy | 请求转发、路由 | 多实例+HAProxy |
| codis-group | Redis实例组（主从） | 主从+Sentinel |
| codis-dashboard | 集群管理、数据迁移 | 单点（可部署多实例） |
| codis-fe | 管理界面 | 单点 |
| Zookeeper/Etcd | 配置存储、服务发现 | 集群部署 |

#### 适用场景对比

| 特性 | Redis Cluster | Codis |
|------|---------------|-------|
| **开发维护** | 官方维护 | 社区维护（已停更） |
| **数据迁移** | 自动迁移（较慢） | 支持异步迁移 |
| **扩缩容** | 支持在线扩容 | 更平滑的扩容体验 |
| **客户端** | 需要智能客户端 | 对客户端透明 |
| **跨机房** | 原生不支持 | 支持多机房部署 |
| **性能** | 更高（无代理层） | 略低（有代理层） |
| **推荐版本** | Redis 7.0+ | 不建议新项目使用 |

### 1.3 缓存设计最佳实践

#### 多级缓存架构
```
┌─────────────────────────────────────────────────────────┐
│                     用户请求                             │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  L1: 本地缓存 (Caffeine/Guava)                          │
│  - 命中率: 60-80%                                       │
│  - 延迟: <1ms                                           │
│  - 容量: 热点数据（千级）                                │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  L2: 分布式缓存 (Redis Cluster)                          │
│  - 命中率: 90-95%                                       │
│  - 延迟: 1-5ms                                          │
│  - 容量: 百万级                                         │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  L3: 数据库/源头                                         │
│  - 最终一致性保障                                       │
└─────────────────────────────────────────────────────────┘
```

#### 缓存一致性策略
```java
/**
 * Cache-Aside 模式 + 延迟双删
 */
@Service
public class CacheService {
    
    @Resource
    private StringRedisTemplate redisTemplate;
    
    @Resource
    private ThreadPoolExecutor executor;
    
    /**
     * 读操作：先读缓存，再读数据库
     */
    public <T> T getWithCache(String key, Class<T> clazz, Supplier<T> dbLoader) {
        String cached = redisTemplate.opsForValue().get(key);
        if (cached != null) {
            return JSON.parseObject(cached, clazz);
        }
        
        // 缓存未命中，查询数据库
        T value = dbLoader.get();
        if (value != null) {
            redisTemplate.opsForValue().set(key, JSON.toJSONString(value), 
                Duration.ofMinutes(30));
        }
        return value;
    }
    
    /**
     * 写操作：延迟双删策略
     */
    public void updateWithCache(String key, Runnable dbUpdater) {
        // 1. 先删除缓存
        redisTemplate.delete(key);
        
        // 2. 更新数据库
        dbUpdater.run();
        
        // 3. 延迟删除缓存（处理并发读写）
        executor.execute(() -> {
            try {
                Thread.sleep(500); // 延迟500ms
                redisTemplate.delete(key);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }
}
```

#### 缓存穿透、击穿、雪崩防护
```java
@Component
public class CacheProtection {
    
    @Resource
    private RedissonClient redisson;
    
    @Resource
    private StringRedisTemplate redisTemplate;
    
    /**
     * 布隆过滤器防穿透
     */
    public <T> T getWithBloomFilter(String key, Class<T> clazz, 
            RBloomFilter<String> bloomFilter, Supplier<T> dbLoader) {
        // 布隆过滤器检查
        if (!bloomFilter.contains(key)) {
            return null; // 数据肯定不存在
        }
        return getWithCache(key, clazz, dbLoader);
    }
    
    /**
     * 互斥锁防击穿
     */
    public <T> T getWithMutex(String key, Class<T> clazz, Supplier<T> dbLoader) {
        String cached = redisTemplate.opsForValue().get(key);
        if (cached != null) {
            return JSON.parseObject(cached, clazz);
        }
        
        // 获取分布式锁
        RLock lock = redisson.getLock("lock:" + key);
        try {
            if (lock.tryLock(3, 10, TimeUnit.SECONDS)) {
                // 双重检查
                cached = redisTemplate.opsForValue().get(key);
                if (cached != null) {
                    return JSON.parseObject(cached, clazz);
                }
                
                T value = dbLoader.get();
                if (value != null) {
                    redisTemplate.opsForValue().set(key, JSON.toJSONString(value),
                        Duration.ofMinutes(30));
                }
                return value;
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            lock.unlock();
        }
        return null;
    }
    
    /**
     * 随机过期时间防雪崩
     */
    public void setWithRandomExpire(String key, Object value, int baseMinutes) {
        int randomSeconds = ThreadLocalRandom.current().nextInt(60);
        Duration expireTime = Duration.ofMinutes(baseMinutes).plusSeconds(randomSeconds);
        redisTemplate.opsForValue().set(key, JSON.toJSONString(value), expireTime);
    }
}
```

---

## 二、消息队列选型与优化

### 2.1 三大消息队列对比

| 特性 | Apache Kafka | Apache RocketMQ | Apache Pulsar |
|------|-------------|-----------------|---------------|
| **开发语言** | Scala/Java | Java | Java/C++ |
| **存储模型** | 磁盘顺序写 | 磁盘顺序写 | 分层存储（BookKeeper） |
| **吞吐量** | 百万级TPS | 十万级TPS | 百万级TPS |
| **延迟** | ms级 | ms级 | ms级（可亚ms） |
| **消息回溯** | 支持（按offset） | 支持（按时间/offset） | 支持（无限回溯） |
| **延迟消息** | 不支持原生 | 原生支持18级 | 原生支持 |
| **事务消息** | 支持 | 支持 | 支持 |
| **消息过滤** | 客户端过滤 | Tag/SQL过滤 | 客户端过滤 |
| **多租户** | 不支持 | 不支持 | 原生支持 |
| **地理复制** | MirrorMaker | 支持 | 原生支持 |
| **运维复杂度** | 中等 | 低 | 中等 |
| **社区活跃度** | 高 | 高（阿里云托管） | 高 |

### 2.2 选型决策树

```
                    ┌─────────────────┐
                    │   业务场景需求   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │日志采集  │         │金融业务  │         │ 云原生   │
   │大数据处理│         │电商交易  │         │多租户   │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │  Kafka  │         │RocketMQ │         │ Pulsar  │
   │- 高吞吐  │         │- 低延迟  │         │- 计算存储│
   │- 高积压  │         │- 事务消息│         │  分离   │
   │- 生态丰富│         │- 延迟消息│         │- 无限回溯│
   └─────────┘         │- 运维简单│         │- 地理复制│
                       └─────────┘         └─────────┘
```

### 2.3 Kafka 生产级配置

#### Broker 配置
```properties
# server.properties - 生产环境推荐配置

# ==================== 网络与IO ====================
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# ==================== 日志与存储 ====================
log.dirs=/data/kafka-logs
num.partitions=12
default.replication.factor=3
min.insync.replicas=2
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

# ==================== 性能优化 ====================
num.replica.fetchers=4
replica.socket.timeout.ms=30000
replica.socket.receive.buffer.bytes=65536
replica.fetch.max.bytes=52428800

# ==================== 高可用配置 ====================
unclean.leader.election.enable=false
auto.create.topics.enable=false
controlled.shutdown.enable=true
```

#### Producer 优化配置
```java
@Configuration
public class KafkaProducerConfig {
    
    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092,kafka2:9092,kafka3:9092");
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        
        // 性能优化
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);          // 32KB批量
        props.put(ProducerConfig.LINGER_MS_CONFIG, 10);              // 10ms等待
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 67108864);    // 64MB缓冲
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");    // 压缩算法
        props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);
        
        // 可靠性配置
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);   // 幂等性
        props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "prod-" + UUID.randomUUID());
        
        return new DefaultKafkaProducerFactory<>(props);
    }
    
    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
```

#### Consumer 优化配置
```java
@Configuration
public class KafkaConsumerConfig {
    
    @Bean
    public ConsumerFactory<String, Object> consumerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092,kafka2:9092,kafka3:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "order-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
        
        // 性能优化
        props.put(ConsumerConfig.FETCH_MIN_BYTES_CONFIG, 1048576);   // 1MB最小拉取
        props.put(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG, 500);     // 最大等待500ms
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);      // 单次最大500条
        
        // 提交策略
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);  // 手动提交
        props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300000);
        
        return new DefaultKafkaConsumerFactory<>(props);
    }
    
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, Object> factory = 
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());
        factory.setConcurrency(10);                                  // 并发消费者数
        factory.setBatchListener(true);                              // 批量消费
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        return factory;
    }
}
```

### 2.4 RocketMQ 金融级配置

```java
@Configuration
public class RocketMQConfig {
    
    /**
     * 事务消息生产者
     */
    @Bean
    public TransactionMQProducer transactionProducer() throws MQClientException {
        TransactionMQProducer producer = new TransactionMQProducer("transaction_producer_group");
        producer.setNamesrvAddr("rocketmq-nameserver:9876");
        
        // 线程池配置
        producer.setExecutorService(new ThreadPoolExecutor(
            4, 8, 60, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(100),
            new ThreadFactoryBuilder().setNameFormat("rocketmq-transaction-%d").build()
        ));
        
        // 事务监听器
        producer.setTransactionListener(new TransactionListener() {
            @Override
            public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
                // 执行本地事务
                try {
                    // 执行订单创建等业务逻辑
                    return LocalTransactionState.COMMIT_MESSAGE;
                } catch (Exception e) {
                    return LocalTransactionState.ROLLBACK_MESSAGE;
                }
            }
            
            @Override
            public LocalTransactionState checkLocalTransaction(MessageExt msg) {
                // 回查本地事务状态
                if (checkTransactionStatus(msg)) {
                    return LocalTransactionState.COMMIT_MESSAGE;
                }
                return LocalTransactionState.ROLLBACK_MESSAGE;
            }
        });
        
        producer.start();
        return producer;
    }
    
    /**
     * 延迟消息发送
     */
    public SendResult sendDelayMessage(DefaultMQProducer producer, String topic, 
            String content, int delayLevel) throws MQClientException, RemotingException, 
            MQBrokerException, InterruptedException {
        Message msg = new Message(topic, "TagA", content.getBytes(StandardCharsets.UTF_8));
        // RocketMQ 支持18个延迟级别
        // 1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h
        msg.setDelayTimeLevel(delayLevel);
        return producer.send(msg);
    }
}
```

### 2.5 消息队列监控指标

| 指标类别 | 关键指标 | 告警阈值 | 说明 |
|---------|---------|---------|------|
| **吞吐量** | Messages In/Out Per Sec | 低于预期的50% | 业务是否正常 |
| **延迟** | Consumer Lag | >10000 | 消费是否跟得上 |
| **存储** | Log Size / Retention | >磁盘80% | 磁盘空间 |
| **可用性** | Under Replicated Partitions | >0 | 副本同步问题 |
| **性能** | Request Latency (p99) | >100ms | 响应延迟 |
| **错误率** | Failed Produce Requests | >0.1% | 发送失败率 |

---

## 三、数据库分库分表与读写分离

### 3.1 分库分表策略

#### 分片策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **Hash取模** | 用户ID、订单ID | 数据分布均匀 | 扩缩容需要迁移数据 |
| **范围分片** | 时间序列数据 | 支持范围查询 | 可能产生热点 |
| **枚举分片** | 地区、类型 | 可控的数据分布 | 需要维护映射关系 |
| **复合分片** | 复杂业务 | 灵活性高 | 实现复杂 |

#### ShardingSphere 配置
```yaml
# application-sharding.yml
spring:
  shardingsphere:
    datasource:
      names: ds0, ds1, ds2, ds3
      ds0:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://db-host1:3306/order_db_0?useUnicode=true&characterEncoding=utf8
        username: ${DB_USER}
        password: ${DB_PASSWORD}
        maximum-pool-size: 20
      ds1:
        jdbc-url: jdbc:mysql://db-host2:3306/order_db_1?useUnicode=true&characterEncoding=utf8
        # ... 其他配置
      ds2:
        jdbc-url: jdbc:mysql://db-host3:3306/order_db_2?useUnicode=true&characterEncoding=utf8
      ds3:
        jdbc-url: jdbc:mysql://db-host4:3306/order_db_3?useUnicode=true&characterEncoding=utf8
    
    rules:
      sharding:
        tables:
          t_order:
            actual-data-nodes: ds${0..3}.t_order_${0..15}
            table-strategy:
              standard:
                sharding-column: order_id
                sharding-algorithm-name: order-table-hash
            database-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: order-db-hash
            key-generate-strategy:
              column: order_id
              key-generator-name: snowflake
          
          t_order_item:
            actual-data-nodes: ds${0..3}.t_order_item_${0..15}
            table-strategy:
              standard:
                sharding-column: order_id
                sharding-algorithm-name: order-table-hash
        
        sharding-algorithms:
          order-db-hash:
            type: INLINE
            props:
              algorithm-expression: ds${user_id % 4}
          order-table-hash:
            type: INLINE
            props:
              algorithm-expression: t_order_${order_id % 16}
        
        key-generators:
          snowflake:
            type: SNOWFLAKE
            props:
              worker-id: ${WORKER_ID:0}
              max-vibration-offset: 1
      
      readwrite-splitting:
        data-sources:
          ds0:
            type: Static
            props:
              write-data-source-name: ds0
              read-data-source-names: ds0-slave1, ds0-slave2
            load-balancer-name: round-robin
        load-balancers:
          round-robin:
            type: ROUND_ROBIN
    
    props:
      sql-show: false
      sql-simple: true
```

### 3.2 分布式主键生成

#### 雪花算法改进版
```java
@Component
public class IdGenerator {
    
    private final SnowflakeShardingKeyGenerator keyGenerator;
    
    public IdGenerator(@Value("${worker.id:0}") long workerId,
                       @Value("${datacenter.id:0}") long datacenterId) {
        this.keyGenerator = new SnowflakeShardingKeyGenerator(workerId, datacenterId);
    }
    
    public long nextId() {
        return keyGenerator.generateKey();
    }
    
    /**
     * 生成订单ID（包含时间信息，便于排序）
     * 格式：1位符号 + 41位时间戳 + 10位工作节点 + 12位序列号
     */
    public long generateOrderId() {
        return keyGenerator.generateKey();
    }
    
    /**
     * 解析ID获取时间
     */
    public LocalDateTime extractTime(long id) {
        long timestamp = (id >> 22) + 1609459200000L; // 2021-01-01起始
        return LocalDateTime.ofInstant(
            Instant.ofEpochMilli(timestamp), 
            ZoneId.systemDefault()
        );
    }
}

/**
 * 改进版雪花算法（解决时钟回拨）
 */
public class SafeSnowflakeIdWorker {
    
    private final long workerId;
    private final long datacenterId;
    private long sequence = 0L;
    private long lastTimestamp = -1L;
    
    // 使用序列号最大值的1/10作为时钟回拨容忍范围
    private static final long CLOCK_BACKWARD_TOLERANCE = 10;
    
    public synchronized long nextId() {
        long timestamp = timeGen();
        
        if (timestamp < lastTimestamp) {
            long offset = lastTimestamp - timestamp;
            if (offset <= CLOCK_BACKWARD_TOLERANCE) {
                // 小幅度回拨，等待追赶
                try {
                    wait(offset << 1);
                    timestamp = timeGen();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            } else {
                throw new RuntimeException("Clock moved backwards too far");
            }
        }
        
        if (lastTimestamp == timestamp) {
            sequence = (sequence + 1) & 4095;
            if (sequence == 0) {
                timestamp = tilNextMillis(lastTimestamp);
            }
        } else {
            sequence = 0L;
        }
        
        lastTimestamp = timestamp;
        return ((timestamp - 1609459200000L) << 22) |
               (datacenterId << 17) |
               (workerId << 12) |
               sequence;
    }
    
    private long tilNextMillis(long lastTimestamp) {
        long timestamp = timeGen();
        while (timestamp <= lastTimestamp) {
            timestamp = timeGen();
        }
        return timestamp;
    }
    
    private long timeGen() {
        return System.currentTimeMillis();
    }
}
```

### 3.3 读写分离最佳实践

```java
@Configuration
public class ReadWriteSplittingConfig {
    
    /**
     * 强制走主库注解
     */
    @Target({ElementType.METHOD, ElementType.TYPE})
    @Retention(RetentionPolicy.RUNTIME)
    public @interface MasterRoute {
    }
    
    /**
     * 数据源路由切面
     */
    @Aspect
    @Component
    public class DataSourceRouteAspect {
        
        @Around("@annotation(MasterRoute)")
        public Object around(ProceedingJoinPoint point) throws Throwable {
            HintManager hintManager = HintManager.getInstance();
            hintManager.setWriteRouteOnly();
            try {
                return point.proceed();
            } finally {
                hintManager.close();
            }
        }
    }
    
    /**
     * 服务层使用示例
     */
    @Service
    public class OrderService {
        
        @Autowired
        private OrderRepository orderRepository;
        
        /**
         * 读操作 - 自动路由到从库
         */
        public Order getOrder(Long orderId) {
            return orderRepository.findById(orderId).orElse(null);
        }
        
        /**
         * 写操作 - 路由到主库
         */
        @Transactional
        public Order createOrder(Order order) {
            return orderRepository.save(order);
        }
        
        /**
         * 需要强一致性读 - 强制走主库
         */
        @MasterRoute
        public Order getOrderWithConsistency(Long orderId) {
            return orderRepository.findById(orderId).orElse(null);
        }
    }
}
```

### 3.4 分库分表运维工具

```java
@Component
public class ShardingDataMigration {
    
    @Autowired
    private DataSource dataSource;
    
    /**
     * 在线扩容 - 双写迁移方案
     */
    public void expandShardingCapacity(String tableName, int oldShardCount, int newShardCount) {
        // 1. 配置双写
        enableDualWrite(tableName);
        
        // 2. 历史数据迁移
        migrateHistoricalData(tableName, oldShardCount, newShardCount);
        
        // 3. 数据校验
        validateDataConsistency(tableName);
        
        // 4. 切换路由
        switchToNewShardingRule(tableName, newShardCount);
        
        // 5. 停止双写
        disableDualWrite(tableName);
    }
    
    /**
     * 数据校验
     */
    public boolean validateDataConsistency(String tableName) {
        // 校验逻辑：对比源表和目标表的记录数、checksum
        String checksumSql = "SELECT COUNT(*), SUM(CRC32(CONCAT_WS(',', col1, col2, col3))) " +
                            "FROM " + tableName;
        // 执行校验...
        return true;
    }
}
```

---

## 四、限流熔断与降级策略

### 4.1 Sentinel 架构与原理

```
┌─────────────────────────────────────────────────────────────┐
│                        应用服务                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Entry      │  │  Slot Chain │  │  Statistic Slot     │  │
│  │  (入口)      │──│  (责任链)   │──│  (统计)              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                                    │               │
│         ▼                                    ▼               │
│  ┌─────────────┐                    ┌─────────────────────┐  │
│  │  Rule       │                    │  Metrics            │  │
│  │  Manager    │                    │  Repository         │  │
│  └─────────────┘                    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Slot Chain 执行顺序：                                        │
│  NodeSelectorSlot → ClusterBuilderSlot → LogSlot            │
│  → StatisticSlot → AuthoritySlot → SystemSlot               │
│  → ParamFlowSlot → FlowSlot → DegradeSlot                   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 限流策略配置

#### 流控规则
```java
@Configuration
public class SentinelFlowConfig {
    
    @PostConstruct
    public void initFlowRules() {
        List<FlowRule> rules = new ArrayList<>();
        
        // QPS 限流 - 下单接口
        FlowRule orderRule = new FlowRule();
        orderRule.setResource("createOrder");
        orderRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        orderRule.setCount(1000);           // QPS 限制
        orderRule.setStrategy(RuleConstant.STRATEGY_DIRECT);
        orderRule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_WARM_UP);
        orderRule.setWarmUpPeriodSec(10);   // 预热10秒
        orderRule.setMaxQueueingTimeMs(500);
        rules.add(orderRule);
        
        // 线程数限流 - 查询接口
        FlowRule queryRule = new FlowRule();
        queryRule.setResource("queryOrder");
        queryRule.setGrade(RuleConstant.FLOW_GRADE_THREAD);
        queryRule.setCount(50);             // 最大并发线程数
        rules.add(queryRule);
        
        // 关联限流 - 查询和修改不能同时高负载
        FlowRule relateRule = new FlowRule();
        relateRule.setResource("queryOrder");
        relateRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        relateRule.setCount(100);
        relateRule.setStrategy(RuleConstant.STRATEGY_RELATE);
        relateRule.setRefResource("updateOrder");
        rules.add(relateRule);
        
        // 链路限流
        FlowRule chainRule = new FlowRule();
        chainRule.setResource("getUserInfo");
        chainRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        chainRule.setCount(200);
        chainRule.setStrategy(RuleConstant.STRATEGY_CHAIN);
        rules.add(chainRule);
        
        FlowRuleManager.loadRules(rules);
    }
}
```

#### 代码集成方式
```java
@Service
public class OrderService {
    
    /**
     * 注解方式限流
     */
    @SentinelResource(
        value = "createOrder",
        blockHandler = "createOrderBlockHandler",
        fallback = "createOrderFallback"
    )
    public Order createOrder(OrderRequest request) {
        // 业务逻辑
        return orderRepository.save(request.toOrder());
    }
    
    /**
     * 限流处理（参数和返回值必须与原方法一致）
     */
    public Order createOrderBlockHandler(OrderRequest request, BlockException ex) {
        log.warn("Order creation rate limited: {}", request.getUserId());
        throw new RateLimitException("系统繁忙，请稍后重试");
    }
    
    /**
     * 异常降级处理
     */
    public Order createOrderFallback(OrderRequest request, Throwable ex) {
        log.error("Order creation failed: {}", ex.getMessage());
        // 返回降级数据或抛出异常
        throw new ServiceException("下单失败，请重试");
    }
    
    /**
     * 代码方式限流（更灵活）
     */
    public Order queryOrder(Long orderId) {
        Entry entry = null;
        try {
            entry = SphU.entry("queryOrder");
            // 被保护的业务逻辑
            return orderRepository.findById(orderId).orElse(null);
        } catch (BlockException e) {
            // 限流处理
            return queryOrderFromCache(orderId);
        } finally {
            if (entry != null) {
                entry.exit();
            }
        }
    }
}
```

### 4.3 熔断降级策略

```java
@Configuration
public class SentinelDegradeConfig {
    
    @PostConstruct
    public void initDegradeRules() {
        List<DegradeRule> rules = new ArrayList<>();
        
        // 慢调用比例熔断
        DegradeRule slowCallRule = new DegradeRule();
        slowCallRule.setResource("queryInventory");
        slowCallRule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
        slowCallRule.setCount(0.5);           // 慢调用比例阈值 50%
        slowCallRule.setTimeWindow(30);       // 熔断时长30秒
        slowCallRule.setSlowRatioThreshold(0.2); // 慢调用比例阈值
        slowCallRule.setStatIntervalMs(1000); // 统计时长1秒
        slowCallRule.setMinRequestAmount(10); // 最小请求数
        rules.add(slowCallRule);
        
        // 异常比例熔断
        DegradeRule errorRateRule = new DegradeRule();
        errorRateRule.setResource("paymentService");
        errorRateRule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType());
        errorRateRule.setCount(0.5);          // 异常比例50%
        errorRateRule.setTimeWindow(60);      // 熔断60秒
        errorRateRule.setStatIntervalMs(1000);
        errorRateRule.setMinRequestAmount(10);
        rules.add(errorRateRule);
        
        // 异常数熔断
        DegradeRule errorCountRule = new DegradeRule();
        errorCountRule.setResource("thirdPartyApi");
        errorCountRule.setGrade(CircuitBreakerStrategy.ERROR_COUNT.getType());
        errorCountRule.setCount(10);          // 异常数10个
        errorCountRule.setTimeWindow(60);
        errorCountRule.setStatIntervalMs(60 * 1000);
        errorCountRule.setMinRequestAmount(10);
        rules.add(errorCountRule);
        
        DegradeRuleManager.loadRules(rules);
    }
}
```

### 4.4 热点参数限流

```java
@Configuration
public class SentinelParamFlowConfig {
    
    @PostConstruct
    public void initParamFlowRules() {
        List<ParamFlowRule> rules = new ArrayList<>();
        
        // 用户ID维度限流
        ParamFlowRule userRule = new ParamFlowRule();
        userRule.setResource("getUserOrders");
        userRule.setParamIdx(0);              // 第0个参数（userId）
        userRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        userRule.setCount(10);                // 每个用户每秒最多10次
        userRule.setDurationInSec(1);
        
        // 特定用户特殊限制
        List<ParamFlowItem> items = new ArrayList<>();
        ParamFlowItem hotUser = new ParamFlowItem();
        hotUser.setObject("VIP_USER_001");
        hotUser.setCount(100);                // VIP用户100 QPS
        items.add(hotUser);
        userRule.setParamFlowItemList(items);
        
        rules.add(userRule);
        ParamFlowRuleManager.loadRules(rules);
    }
}
```

### 4.5 系统自适应保护

```java
@Configuration
public class SentinelSystemConfig {
    
    @PostConstruct
    public void initSystemRules() {
        List<SystemRule> rules = new ArrayList<>();
        
        SystemRule rule = new SystemRule();
        rule.setHighestSystemLoad(80);        // 最大负载
        rule.setHighestCpuUsage(0.8);         // 最大CPU使用率
        rule.setQps(10000);                   // 最大QPS
        rule.setAvgRt(100);                   // 平均响应时间
        rule.setMaxThread(500);               // 最大线程数
        
        rules.add(rule);
        SystemRuleManager.loadRules(rules);
    }
}
```

### 4.6 规则持久化（Nacos）

```yaml
# application-sentinel.yml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
        port: 8719
      datasource:
        flow:
          nacos:
            server-addr: ${NACOS_SERVER:localhost:8848}
            data-id: ${spring.application.name}-flow-rules
            group-id: SENTINEL_GROUP
            rule-type: flow
        degrade:
          nacos:
            server-addr: ${NACOS_SERVER:localhost:8848}
            data-id: ${spring.application.name}-degrade-rules
            group-id: SENTINEL_GROUP
            rule-type: degrade
        param-flow:
          nacos:
            server-addr: ${NACOS_SERVER:localhost:8848}
            data-id: ${spring.application.name}-param-flow-rules
            group-id: SENTINEL_GROUP
            rule-type: param-flow
```

---

## 五、全链路压测与性能调优

### 5.1 压测环境设计

#### 压测环境架构
```
┌────────────────────────────────────────────────────────────────┐
│                         压测流量入口                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   JMeter     │  │   Locust     │  │   Gatling    │         │
│  │  (协议压测)   │  │  (Python)    │  │  (Scala)     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼─────────────────┼─────────────────┼─────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌─────────────────────┐           ┌─────────────────────┐
│   压测集群 (云端)    │           │   生产集群（影子库）  │
│  - 流量录制回放       │           │  - 影子表隔离        │
│  - 多地域并发        │           │  - 影子消息队列      │
│  - 全链路监控        │           │  - 影子缓存          │
└─────────────────────┘           └─────────────────────┘
```

#### 影子库配置
```yaml
# 压测影子库配置
spring:
  profiles:
    active: stress-test
  
  shardingsphere:
    rules:
      shadow:
        data-sources:
          shadow-data-source:
            source-data-source-name: ds
            shadow-data-source-name: ds-shadow
        tables:
          t_order:
            data-source-names: shadow-data-source
            shadow-algorithm-names:
              - user-id-insert-match-algorithm
        shadow-algorithms:
          user-id-insert-match-algorithm:
            type: VALUE_MATCH
            props:
              operation: insert
              column: user_id
              value: PT_               # 压测用户前缀
```

### 5.2 压测指标体系

| 指标类别 | 指标名称 | 目标值 | 监控工具 |
|---------|---------|--------|---------|
| **吞吐量** | QPS/TPS | 根据业务设定 | Prometheus + Grafana |
| **响应时间** | P50/P95/P99 | <50ms/<100ms/<200ms | SkyWalking / APM |
| **错误率** | Error Rate | <0.1% | ELK / Sentry |
| **资源使用** | CPU/Memory | <70%/<80% | Node Exporter |
| **数据库** | 连接数/慢查询 | <80%连接池/<10次/秒 | MySQL Exporter |
| **缓存** | 命中率/响应时间 | >95%/<5ms | Redis Exporter |
| **队列** | 积压量/消费速率 | <10000 msg | Kafka Exporter |

### 5.3 压测执行方案

#### 压测阶段规划

| 阶段 | 目标 | 并发数 | 持续时间 | 关注重点 |
|------|------|--------|---------|---------|
| **基准测试** | 单机性能基线 | 10 | 5min | 服务本身性能 |
| **容量测试** | 找到性能拐点 | 逐步增加 | 每阶梯10min | 吞吐量vs延迟 |
| **稳定性测试** | 长时间稳定性 | 目标并发 | 8h+ | 内存泄漏、GC |
| **峰值测试** | 峰值承载能力 | 2-3倍日常峰值 | 30min | 降级策略有效性 |
| **恢复测试** | 故障恢复能力 | 峰值并发 | 随机降级 | 系统恢复时间 |

#### JMeter 压测脚本
```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testname="全链路压测计划">
      <elementProp name="UserDefinedVariables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="BASE_URL" elementType="Argument">
            <stringProp name="Argument.value">${__P(baseUrl,http://api.example.com)}</stringProp>
          </elementProp>
          <elementProp name="THREAD_COUNT" elementType="Argument">
            <stringProp name="Argument.value">${__P(threads,100)}</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    
    <hashTree>
      <!-- 线程组配置 -->
      <ThreadGroup guiclass="ThreadGroupGui" testname="订单压测线程组">
        <stringProp name="ThreadGroup.num_threads">${THREAD_COUNT}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">60</stringProp>
        <stringProp name="ThreadGroup.duration">3600</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        
        <!-- 压力模型 - 阶梯加压 -->
        <elementProp name="ThreadGroup.arguments" elementType="Arguments">
          <collectionProp name="Arguments.arguments"/>
        </elementProp>
      </ThreadGroup>
      
      <hashTree>
        <!-- HTTP请求默认值 -->
        <ConfigTestElement guiclass="HttpDefaultsGui" testname="HTTP默认配置">
          <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
          <stringProp name="HTTPSampler.port">8080</stringProp>
          <stringProp name="HTTPSampler.connect_timeout">5000</stringProp>
          <stringProp name="HTTPSampler.response_timeout">30000</stringProp>
        </ConfigTestElement>
        
        <!-- 创建订单请求 -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testname="创建订单">
          <stringProp name="HTTPSampler.path">/api/v1/orders</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">{
                  "userId": "PT_${__Random(100000,999999)}",
                  "productId": "${__RandomFromMultipleVars(prod1|prod2|prod3)}",
                  "quantity": ${__Random(1,10)},
                  "amount": ${__Random(1000,100000)}
                }</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        
        <!-- 响应断言 -->
        <ResponseAssertion guiclass="AssertionGui" testname="响应断言">
          <collectionProp name="Asserion.test_strings">
            <stringProp name="49586">200</stringProp>
            <stringProp name="49587">success</stringProp>
          </collectionProp>
          <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
        </ResponseAssertion>
        
        <!-- 监听器配置 -->
        <BackendListener guiclass="BackendListenerGui" testname="InfluxDB监听器">
          <stringProp name="classname">org.apache.jmeter.visualizers.backend.influxdb.InfluxdbBackendListenerClient</stringProp>
          <stringProp name="influxdbUrl">http://influxdb:8086/write?db=jmeter</stringProp>
          <stringProp name="application">order-service</stringProp>
        </BackendListener>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### 5.4 性能调优 checklist

#### JVM 调优
```bash
# 生产环境推荐 JVM 参数
JAVA_OPTS="
  -server
  -Xms4g -Xmx4g
  -XX:MetaspaceSize=256m
  -XX:MaxMetaspaceSize=512m
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:InitiatingHeapOccupancyPercent=35
  -XX:+ParallelRefProcEnabled
  -XX:+AlwaysPreTouch
  -XX:+DisableExplicitGC
  -XX:+HeapDumpOnOutOfMemoryError
  -XX:HeapDumpPath=/logs/heapdump.hprof
  -Xlog:gc*:file=/logs/gc.log:time,uptime,level,tags:filecount=10,filesize=100m
"
```

#### MySQL 调优
```ini
# my.cnf 生产环境推荐配置
[mysqld]
# 基础配置
innodb_buffer_pool_size = 8G          # 内存的50-75%
innodb_buffer_pool_instances = 8
innodb_log_file_size = 1G
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 2    # 平衡性能和持久化
innodb_flush_method = O_DIRECT

# 连接配置
max_connections = 1000
max_user_connections = 900
thread_cache_size = 100
thread_pool_size = 16

# 查询缓存（MySQL 8.0已移除）
query_cache_type = 0
query_cache_size = 0

# 临时表
tmp_table_size = 128M
max_heap_table_size = 128M

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = 1
```

#### Redis 调优
```conf
# redis.conf 高性能配置
maxmemory 8gb
maxmemory-policy allkeys-lru

tcp-keepalive 60
tcp-backlog 511
timeout 0

# 关闭持久化（纯缓存场景）
save ""
appendonly no

# 启用持久化（需要可靠性）
# appendonly yes
# appendfsync everysec
# auto-aof-rewrite-percentage 100
# auto-aof-rewrite-min-size 64mb

# 客户端输出缓冲
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# 慢日志
slowlog-log-slower-than 10000
slowlog-max-len 128
```

### 5.5 全链路监控方案

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  # Prometheus - 指标收集
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"

  # Grafana - 可视化
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  # SkyWalking - APM
  skywalking-oap:
    image: apache/skywalking-oap-server:latest
    environment:
      - SW_STORAGE=elasticsearch
      - SW_STORAGE_ES_CLUSTER_NODES=elasticsearch:9200
    ports:
      - "11800:11800"
      - "12800:12800"

  skywalking-ui:
    image: apache/skywalking-ui:latest
    environment:
      - SW_OAP_ADDRESS=http://skywalking-oap:12800
    ports:
      - "8080:8080"

  # ELK Stack - 日志分析
  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es-data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  prometheus-data:
  grafana-data:
  es-data:
```

---

## 六、压测方案与执行计划

### 6.1 压测准备清单

| 检查项 | 负责人 | 完成标准 | 状态 |
|--------|--------|---------|------|
| 压测环境搭建 | 运维 | 1:1复制生产环境 | ⬜ |
| 影子库配置 | DBA | 数据隔离完成 | ⬜ |
| 监控部署 | SRE | 全链路监控就绪 | ⬜ |
| 脚本准备 | 测试 | 覆盖核心场景 | ⬜ |
| 降级开关 | 开发 | 紧急降级方案就绪 | ⬜ |
| 数据准备 | DBA | 生产数据脱敏导入 | ⬜ |
| 备份方案 | 运维 | 数据可快速恢复 | ⬜ |

### 6.2 压测执行计划

```
压测执行计划 (假设目标: 10万QPS)
═══════════════════════════════════════════════════════════════

Day 1: 基准测试
├── 09:00 环境检查 & 基线数据收集
├── 10:00 单机单接口基准测试 (100并发)
├── 11:00 数据库基准测试 (sysbench)
├── 14:00 缓存基准测试 (redis-benchmark)
├── 15:00 消息队列基准测试
└── 16:00 基线数据整理 & 报告

Day 2-3: 容量测试
├── 09:00 逐步加压 (每30分钟增加20%负载)
├── 12:00 性能拐点分析
├── 14:00 瓶颈定位 (CPU/内存/IO/网络)
├── 15:00 第一轮优化
└── 17:00 复测验证

Day 4: 稳定性测试
├── 09:00 目标负载持续压测 (8小时)
├── 每小时 数据收集 & 健康检查
├── 17:00 数据分析 & 泄漏检测
└── 18:00 稳定性报告

Day 5: 峰值测试
├── 09:00 2倍峰值负载 (30分钟)
├── 10:00 3倍峰值负载 (15分钟)
├── 11:00 降级策略验证
├── 14:00 故障恢复测试
└── 16:00 压测总结报告
```

### 6.3 压测报告模板

```markdown
# 全链路压测报告

## 1. 压测概览
- 压测时间: 202X年XX月XX日
- 压测目标: 验证系统是否能承载XX万QPS
- 压测范围: 订单服务、支付服务、库存服务

## 2. 压测场景
| 场景 | 并发数 | QPS目标 | 实际QPS | P99延迟 | 错误率 |
|------|--------|---------|---------|---------|--------|
| 下单流程 | 5000 | 10000 | 9800 | 120ms | 0.05% |
| 查询订单 | 10000 | 50000 | 52000 | 50ms | 0.01% |
| 支付回调 | 2000 | 5000 | 5100 | 80ms | 0.02% |

## 3. 资源使用
| 资源 | 峰值使用率 | 瓶颈点 |
|------|-----------|--------|
| CPU | 75% | 订单服务实例 |
| 内存 | 60% | 无 |
| 数据库连接 | 85% | 需扩容 |
| Redis带宽 | 70% | 无 |

## 4. 发现的问题
1. 数据库连接池在高峰期出现等待
2. 订单查询接口P99延迟超标
3. 缓存命中率在压力下有下降

## 5. 优化建议
1. 数据库连接池从100调整到150
2. 订单查询增加二级缓存
3. 优化慢查询SQL (索引优化)

## 6. 结论
系统基本满足目标QPS要求，建议按优化建议调整后再次压测确认。
```

### 6.4 应急响应预案

```yaml
# 压测熔断条件
emergency_triggers:
  database:
    - connection_usage > 95%
    - slow_queries_per_minute > 100
    - replication_lag > 10s
  
  redis:
    - memory_usage > 90%
    - hit_rate < 80%
    - max_clients_reached: true
  
  application:
    - error_rate > 5%
    - p99_latency > 5s
    - gc_pause > 1s
  
  infrastructure:
    - cpu_usage > 90%
    - disk_usage > 85%
    - network_errors_increasing: true

# 自动响应动作
auto_actions:
  - trigger: database.connection_usage > 95%
    action: pause_stress_test
    notify: [dba, oncall]
  
  - trigger: error_rate > 10%
    action: emergency_degrade
    action_params:
      enable_circuit_breaker: true
      reduce_traffic_to: 50%
```

---

## 附录：关键配置速查表

### Redis Cluster 常用命令
```bash
# 创建集群
redis-cli --cluster create \
  192.168.1.10:6379 192.168.1.11:6379 192.168.1.12:6379 \
  192.168.1.13:6379 192.168.1.14:6379 192.168.1.15:6379 \
  --cluster-replicas 1

# 查看集群信息
redis-cli -c cluster nodes
redis-cli -c cluster info

# 重新分片
redis-cli --cluster reshard 192.168.1.10:6379
```

### Kafka 常用命令
```bash
# 创建Topic
kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 3 \
  --partitions 12 \
  --topic order-events

# 查看Consumer Group
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group order-consumers

# 性能测试
kafka-producer-perf-test.sh \
  --topic test-topic \
  --num-records 1000000 \
  --record-size 1024 \
  --throughput -1 \
  --producer-props bootstrap.servers=localhost:9092
```

### MySQL 分库分表检查
```sql
-- 查看各分片数据分布
SELECT 
    'shard_0' as shard, COUNT(*) as count FROM order_db_0.t_order
UNION ALL
SELECT 
    'shard_1' as shard, COUNT(*) as count FROM order_db_1.t_order
UNION ALL
SELECT 
    'shard_2' as shard, COUNT(*) as count FROM order_db_2.t_order
UNION ALL
SELECT 
    'shard_3' as shard, COUNT(*) as count FROM order_db_3.t_order;

-- 检查热点Key
SELECT user_id, COUNT(*) as order_count 
FROM t_order 
GROUP BY user_id 
ORDER BY order_count DESC 
LIMIT 100;
```

---

> **文档结束**  
> 如有问题，请参考各组件官方文档或联系架构团队。
