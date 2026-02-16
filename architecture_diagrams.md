# 数据架构图集

本文档使用 Mermaid 语法绘制各层架构图

---

## 1. Lakehouse 架构图

```mermaid
graph TB
    subgraph 计算引擎层
        F1[Apache Spark]
        F2[Apache Flink]
        F3[Trino/Presto]
        F4[Dremio]
        F5[Hive]
    end
    
    subgraph Catalog层
        C1[Hive Metastore]
        C2[Glue Data Catalog]
        C3[Project Nessie]
        C4[JDBC Catalog]
    end
    
    subgraph 元数据层
        M1[metadata.json<br/>表结构/分区信息]
        M2[manifest-list.avro<br/>快照列表]
        M3[manifest.avro<br/>数据文件列表]
    end
    
    subgraph 数据层
        D1[data-1.parquet]
        D2[data-2.parquet]
        D3[data-3.parquet]
        D4[...]
    end
    
    subgraph 对象存储
        S1[S3/OSS]
        S2[HDFS]
        S3[Azure Blob]
        S4[GCS]
    end
    
    F1 & F2 & F3 & F4 & F5 --> C1 & C2 & C3 & C4
    C1 & C2 & C3 & C4 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> D1 & D2 & D3 & D4
    D1 & D2 & D3 & D4 --> S1 & S2 & S3 & S4
```

---

## 2. 实时数仓架构 (Flink + StarRocks)

```mermaid
graph TB
    subgraph 数据源
        K[Kafka/Pulsar]
        DB[(MySQL/PostgreSQL<br/>CDC)]
        LOG[日志文件]
        API[业务API]
    end
    
    subgraph Flink实时计算层
        F_ETL[数据清洗ETL]
        F_JOIN[双流Join]
        F_AGG[窗口聚合]
        F_FE[特征计算]
    end
    
    subgraph 数据存储层
        K2[Kafka<br/>流数据缓存]
        ICE[Iceberg<br/>冷数据存储]
    end
    
    subgraph StarRocks数仓层
        subgraph ODS
            O1[订单明细表]
            O2[用户行为表]
            O3[商品信息表]
        end
        
        subgraph DWD
            D1[订单宽表]
            D2[用户行为宽表]
        end
        
        subgraph DWS
            W1[日汇总表]
            W2[周汇总表]
        end
        
        subgraph ADS
            A1[实时报表]
            A2[API服务]
        end
    end
    
    subgraph 数据消费
        BI[BI工具]
        DASH[数据大屏]
        REC[推荐系统]
    end
    
    K & DB & LOG & API --> F_ETL
    F_ETL --> F_JOIN & F_AGG
    F_JOIN --> F_FE
    F_AGG --> K2 & ICE
    F_FE --> O1 & O2 & O3
    O1 & O2 & O3 --> D1 & D2
    D1 & D2 --> W1 & W2
    W1 & W2 --> A1 & A2
    A1 --> BI & DASH
    A2 --> REC
```

---

## 3. 数据治理架构

```mermaid
graph TB
    subgraph 数据标准
        STD1[命名规范]
        STD2[数据字典]
        STD3[质量标准]
        STD4[安全策略]
    end
    
    subgraph 元数据管理
        META1[技术元数据<br/>- 表结构<br/>- 数据类型<br/>- 存储位置]
        META2[业务元数据<br/>- 业务定义<br/>- 数据来源<br/>- 责任人]
        META3[血缘关系<br/>- 上下游依赖<br/>- 影响分析]
    end
    
    subgraph 数据质量
        Q1[完整性检查]
        Q2[一致性检查]
        Q3[准确性检查]
        Q4[及时性检查]
        Q5[有效性检查]
        GE[Great Expectations]
    end
    
    subgraph 数据安全
        SEC1[权限控制RBAC]
        SEC2[数据脱敏]
        SEC3[加密传输]
        SEC4[审计日志]
    end
    
    subgraph 监控告警
        AL1[Slack通知]
        AL2[邮件告警]
        AL3[PagerDuty]
        AL4[Dashboard]
    end
    
    STD1 & STD2 & STD3 & STD4 --> META1 & META2
    META1 & META2 --> META3
    META3 --> Q1 & Q2 & Q3 & Q4 & Q5
    Q1 & Q2 & Q3 & Q4 & Q5 --> GE
    GE --> SEC1 & SEC2 & SEC3 & SEC4
    GE --> AL1 & AL2 & AL3 & AL4
```

---

## 4. 实时特征平台架构

```mermaid
graph TB
    subgraph 数据源
        EV[事件流<br/>Kafka]
        CDC2[数据库CDC]
        API2[外部API]
    end
    
    subgraph 特征计算
        FE1[流式计算<br/>Flink]
        FE2[批式计算<br/>Spark SQL]
    end
    
    subgraph 特征存储
        subgraph OnlineStore
            OS1[Redis<br/>低延迟<10ms]
            OS2[Tair<br/>热点数据]
        end
        
        subgraph OfflineStore
            OF1[Hive/Iceberg<br/>批量训练]
            OF2[ClickHouse<br/>分析查询]
        end
    end
    
    subgraph 特征服务
        SVC1[Feature Server<br/>REST/gRPC API]
        SVC2[Feature Registry<br/>元数据管理]
        SVC3[血缘追踪]
    end
    
    subgraph 消费场景
        C1[推荐系统]
        C2[风控模型]
        C3[广告投放]
        C4[搜索排序]
    end
    
    EV & CDC2 & API2 --> FE1 & FE2
    FE1 --> OS1 & OS2
    FE2 --> OF1 & OF2
    OS1 & OS2 --> SVC1
    OF1 & OF2 --> SVC1
    SVC1 --> SVC2 & SVC3
    SVC1 --> C1 & C2 & C3 & C4
```

---

## 5. Dagster 编排架构

```mermaid
graph TB
    subgraph DagsterWebserver
        UI1[资产血缘图]
        UI2[执行监控]
        UI3[配置管理]
    end
    
    subgraph DagsterDaemon
        DM1[调度器<br/>Scheduler]
        DM2[传感器<br/>Sensors]
        DM3[队列管理]
    end
    
    subgraph CodeLocation
        subgraph Assets
            A1[raw_events<br/>原始数据]
            A2[stg_events<br/>清洗数据]
            A3[fct_metrics<br/>汇总数据]
        end
        
        subgraph Jobs
            J1[daily_etl]
            J2[hourly_sync]
            J3[data_quality]
        end
        
        subgraph Resources
            R1[Postgres]
            R2[S3]
            R3[Spark]
        end
    end
    
    subgraph 存储
        ST1[DagsterDB<br/>运行记录]
        ST2[对象存储<br/>中间结果]
    end
    
    UI1 & UI2 & UI3 --> DM1 & DM2 & DM3
    DM1 & DM2 & DM3 --> A1 & A2 & A3
    A1 --> A2 --> A3
    A1 & A2 & A3 --> J1 & J2 & J3
    J1 & J2 & J3 --> R1 & R2 & R3
    R1 & R2 & R3 --> ST1 & ST2
```

---

## 6. 整体 Lakehouse 架构

```mermaid
graph TB
    subgraph 数据采集层
        IN1[Kafka Connect]
        IN2[Debezium CDC]
        IN3[API Gateway]
        IN4[文件上传]
    end
    
    subgraph 实时计算层
        RT1[Flink<br/>Stream Processing]
        RT2[实时特征计算]
    end
    
    subgraph Lakehouse存储层
        subgraph DataLake
            L1[Iceberg<br/>ODS层]
            L2[Iceberg<br/>DWD层]
        end
        
        subgraph OLAP
            O1[StarRocks<br/>DWS层]
            O2[StarRocks<br/>ADS层]
        end
        
        subgraph FeatureStore
            FS1[Redis<br/>Online]
            FS2[Iceberg<br/>Offline]
        end
    end
    
    subgraph 治理层
        G1[DataHub<br/>元数据]
        G2[Great Expectations<br/>数据质量]
        G3[Ranger<br/>数据安全]
    end
    
    subgraph 编排层
        OR1[Dagster<br/>Asset编排]
        OR2[Airflow<br/>任务调度]
    end
    
    subgraph 应用层
        APP1[BI报表<br/>Superset]
        APP2[数据大屏]
        APP3[推荐系统]
        APP4[风控模型]
    end
    
    IN1 & IN2 & IN3 & IN4 --> RT1 & RT2
    RT1 --> L1 & L2
    RT2 --> FS1 & FS2
    L1 --> L2 --> O1 --> O2
    L1 & L2 & O1 & O2 --> G1 & G2 & G3
    G1 & G2 & G3 --> OR1 & OR2
    OR1 & OR2 --> APP1 & APP2 & APP3 & APP4
    FS1 --> APP3 & APP4
```

---

## 7. Iceberg vs Delta Lake 对比

```mermaid
graph LR
    subgraph Iceberg
        I1[Apache Iceberg]
        I2[多引擎支持<br/>Spark/Flink/Trino]
        I3[分区演进<br/>无需重写]
        I4[隐藏分区]
        I5[Time Travel]
    end
    
    subgraph DeltaLake
        D1[Delta Lake]
        D2[Spark原生<br/>最佳支持]
        D3[Databricks集成<br/>深度优化]
        D4[MLflow集成]
        D5[Time Travel]
    end
    
    I1 --> I2 & I3 & I4 & I5
    D1 --> D2 & D3 & D4 & D5
    
    I3 -.->|Iceberg独有| I1
    D3 -.->|Delta独有| D1
```

---

## 8. 数据流水线编排演进

```mermaid
graph LR
    subgraph 传统ETL
        T1[Airflow<br/>Task-centric]
        T2[定时调度<br/>Cron-based]
        T3[弱类型<br/>XCom传递]
    end
    
    subgraph 现代数据平台
        M1[Dagster<br/>Asset-centric]
        M2[数据感知<br/>Data-aware]
        M3[强类型<br/>Python类型]
        M4[测试友好<br/>可调试]
    end
    
    T1 --> M1
    T2 --> M2
    T3 --> M3
    
    style M1 fill:#90EE90
    style M2 fill:#90EE90
    style M3 fill:#90EE90
```

---

*生成时间: 2026-02-16*
