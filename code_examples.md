# 数据架构代码示例集

## 1. Iceberg 操作示例

### 1.1 Spark + Iceberg 基础操作
```python
from pyspark.sql import SparkSession

# 创建 SparkSession
spark = SparkSession.builder \
    .appName("IcebergDemo") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.hive_prod", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.hive_prod.type", "hive") \
    .config("spark.sql.catalog.hive_prod.uri", "thrift://localhost:9083") \
    .getOrCreate()

# 创建 Iceberg 表
spark.sql("""
    CREATE TABLE hive_prod.db.orders (
        order_id BIGINT,
        user_id BIGINT,
        amount DECIMAL(10,2),
        order_time TIMESTAMP,
        dt DATE
    ) USING iceberg
    PARTITIONED BY (days(order_time))
""")

# 写入数据
spark.sql("""
    INSERT INTO hive_prod.db.orders
    VALUES 
        (1, 100, 99.99, CAST('2024-01-15 10:00:00' AS TIMESTAMP), DATE '2024-01-15'),
        (2, 101, 149.50, CAST('2024-01-15 11:00:00' AS TIMESTAMP), DATE '2024-01-15')
""")

# Time Travel 查询
spark.sql("SELECT * FROM hive_prod.db.orders TIMESTAMP AS OF '2024-01-15 00:00:00'")
spark.sql("SELECT * FROM hive_prod.db.orders VERSION AS OF 1234567890")

# 查看历史版本
spark.sql("SELECT * FROM hive_prod.db.orders.history").show()

# 回滚到历史版本
spark.sql("CALL hive_prod.system.rollback_to_snapshot('db.orders', 1234567890)")

# 隐藏分区查询
spark.sql("SELECT * FROM hive_prod.db.orders WHERE order_time >= '2024-01-15'")
```

### 1.2 Flink + Iceberg 流式写入
```sql
-- 创建 Kafka 源表
CREATE TABLE kafka_orders (
    order_id BIGINT,
    user_id BIGINT,
    amount DECIMAL(10,2),
    order_time TIMESTAMP(3),
    WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

-- 创建 Iceberg 目标表
CREATE TABLE iceberg_orders (
    order_id BIGINT,
    user_id BIGINT,
    amount DECIMAL(10,2),
    order_time TIMESTAMP(3),
    dt STRING
) WITH (
    'connector' = 'iceberg',
    'catalog-name' = 'hive_prod',
    'catalog-type' = 'hive',
    'uri' = 'thrift://localhost:9083',
    'warehouse' = 's3://bucket/warehouse'
);

-- 流式写入
INSERT INTO iceberg_orders
SELECT 
    order_id,
    user_id,
    amount,
    order_time,
    DATE_FORMAT(order_time, 'yyyy-MM-dd') as dt
FROM kafka_orders;
```

---

## 2. Delta Lake 操作示例

### 2.1 Spark + Delta Lake
```python
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

builder = SparkSession.builder \
    .appName("DeltaDemo") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

spark = configure_spark_with_delta_pip(builder).getOrCreate()

# 创建 Delta 表
data = spark.range(0, 5)
data.write.format("delta").save("/tmp/delta-table")

# 读取 Delta 表
df = spark.read.format("delta").load("/tmp/delta-table")

# 条件更新
deltaTable = DeltaTable.forPath(spark, "/tmp/delta-table")
deltaTable.update(
    condition="id % 2 == 0",
    set={"id": "id + 100"}
)

# Merge 操作 (Upsert)
source_df = spark.range(3, 8)
deltaTable.alias("target").merge(
    source_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdate(set={"id": "source.id"}) \
 .whenNotMatchedInsert(values={"id": "source.id"}) \
 .execute()

# Time Travel
spark.read.format("delta") \
    .option("versionAsOf", 0) \
    .load("/tmp/delta-table").show()

# 查看历史
spark.sql("DESCRIBE HISTORY delta.`/tmp/delta-table`").show()

# Vacuum (清理旧版本)
deltaTable.vacuum(168)  # 保留7天
```

---

## 3. StarRocks 建表示例

### 3.1 明细模型 (Duplicate Key)
```sql
-- 订单明细表 (ODS层)
CREATE TABLE ods_orders (
    order_id BIGINT COMMENT '订单ID',
    user_id BIGINT COMMENT '用户ID',
    product_id BIGINT COMMENT '商品ID',
    amount DECIMAL(18,2) COMMENT '订单金额',
    order_status INT COMMENT '订单状态 0-未支付 1-已支付',
    create_time DATETIME COMMENT '创建时间',
    dt DATE COMMENT '分区日期'
) ENGINE = OLAP
DUPLICATE KEY(order_id)
COMMENT '订单明细表'
PARTITION BY RANGE(dt) (
    START ("2024-01-01") END ("2025-01-01") EVERY (INTERVAL 1 MONTH)
)
DISTRIBUTED BY HASH(order_id) BUCKETS 16
PROPERTIES (
    "replication_num" = "3",
    "storage_format" = "DEFAULT"
);
```

### 3.2 聚合模型 (Aggregate Key)
```sql
-- 日统计表 (DWS层)
CREATE TABLE dws_order_daily (
    dt DATE COMMENT '日期',
    category_id INT COMMENT '品类ID',
    total_orders BIGINT SUM COMMENT '订单总数',
    total_amount DECIMAL(18,2) SUM COMMENT '订单总金额',
    unique_users BIGINT DISTINCT_COUNT COMMENT '独立用户数',
    avg_order_amount DECIMAL(18,2) REPLACE COMMENT '平均订单金额'
) ENGINE = OLAP
AGGREGATE KEY(dt, category_id)
COMMENT '订单日统计'
PARTITION BY RANGE(dt) (
    START ("2024-01-01") END ("2025-01-01") EVERY (INTERVAL 1 MONTH)
)
DISTRIBUTED BY HASH(category_id) BUCKETS 8
PROPERTIES (
    "replication_num" = "3"
);
```

### 3.3 主键模型 (Primary Key)
```sql
-- 用户实时画像 (ADS层)
CREATE TABLE ads_user_profile (
    user_id BIGINT PRIMARY KEY COMMENT '用户ID',
    user_name VARCHAR(64) COMMENT '用户名',
    total_orders BIGINT COMMENT '累计订单数',
    total_amount DECIMAL(18,2) COMMENT '累计消费金额',
    last_order_time DATETIME COMMENT '最后下单时间',
    user_level INT COMMENT '用户等级 1-5',
    update_time DATETIME COMMENT '更新时间'
) ENGINE = OLAP
PRIMARY KEY(user_id)
COMMENT '用户实时画像'
DISTRIBUTED BY HASH(user_id) BUCKETS 16
PROPERTIES (
    "replication_num" = "3",
    "enable_persistent_index" = "true"
);
```

### 3.4 物化视图
```sql
-- 创建物化视图自动聚合
CREATE MATERIALIZED VIEW mv_order_stats AS
SELECT 
    dt,
    category_id,
    COUNT(*) as order_count,
    SUM(amount) as total_amount,
    COUNT(DISTINCT user_id) as unique_users
FROM dwd_order_detail
GROUP BY dt, category_id;
```

### 3.5 Routine Load (Kafka导入)
```sql
-- 创建 Routine Load 任务
CREATE ROUTINE LOAD db1.orders_load ON ods_orders
COLUMNS TERMINATED BY ',',
COLUMNS(order_id, user_id, product_id, amount, order_status, create_time, dt)
PROPERTIES (
    "desired_concurrent_number" = "3",
    "max_batch_interval" = "20",
    "max_batch_rows" = "300000",
    "max_batch_size" = "209715200"
)
FROM KAFKA (
    "kafka_broker_list" = "kafka1:9092,kafka2:9092",
    "kafka_topic" = "orders",
    "kafka_partitions" = "0,1,2,3",
    "kafka_offsets" = "OFFSET_BEGINNING"
);

-- 查看任务状态
SHOW ROUTINE LOAD;

-- 暂停任务
PAUSE ROUTINE LOAD FOR orders_load;

-- 恢复任务
RESUME ROUTINE LOAD FOR orders_load;
```

---

## 4. Flink SQL 实时计算

### 4.1 CDC 数据同步
```sql
-- MySQL CDC 源表
CREATE TABLE mysql_users (
    id BIGINT PRIMARY KEY NOT ENFORCED,
    name STRING,
    email STRING,
    updated_at TIMESTAMP(3)
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql-host',
    'port' = '3306',
    'username' = 'flink',
    'password' = 'password',
    'database-name' = 'ecommerce',
    'table-name' = 'users',
    'server-id' = '5400-5404'
);

-- StarRocks 目标表
CREATE TABLE starrocks_users (
    id BIGINT,
    name STRING,
    email STRING,
    updated_at TIMESTAMP(3),
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
    'connector' = 'starrocks',
    'jdbc-url' = 'jdbc:mysql://starrocks:9030',
    'load-url' = 'starrocks:8030',
    'database-name' = 'ecommerce',
    'table-name' = 'users',
    'username' = 'root',
    'password' = 'password'
);

-- 实时同步
INSERT INTO starrocks_users
SELECT * FROM mysql_users;
```

### 4.2 窗口聚合
```sql
-- 事件流
CREATE TABLE user_events (
    user_id STRING,
    event_type STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'user_events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

-- 滚动窗口统计
CREATE TABLE window_stats (
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    event_type STRING,
    event_count BIGINT,
    PRIMARY KEY (window_start, window_end, event_type) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://starrocks:9030/analytics',
    'table-name' = 'window_stats',
    'username' = 'root',
    'password' = 'password'
);

-- 窗口聚合
INSERT INTO window_stats
SELECT
    TUMBLE_START(event_time, INTERVAL '5' MINUTE) as window_start,
    TUMBLE_END(event_time, INTERVAL '5' MINUTE) as window_end,
    event_type,
    COUNT(*) as event_count
FROM user_events
GROUP BY
    TUMBLE(event_time, INTERVAL '5' MINUTE),
    event_type;
```

### 4.3 双流 Join
```sql
-- 订单流
CREATE TABLE orders (
    order_id STRING,
    user_id STRING,
    amount DECIMAL(10,2),
    proctime AS PROCTIME()
) WITH ('connector' = 'kafka', ...);

-- 用户维表 (Lookup Join)
CREATE TABLE users (
    user_id STRING,
    user_name STRING,
    age INT
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://mysql:3306/ecommerce',
    'table-name' = 'users',
    'username' = 'root',
    'password' = 'password',
    'lookup.cache.max-rows' = '5000',
    'lookup.cache.ttl' = '10min'
);

-- 关联查询
SELECT 
    o.order_id,
    o.user_id,
    u.user_name,
    o.amount
FROM orders o
LEFT JOIN users FOR SYSTEM_TIME AS OF o.proctime u
ON o.user_id = u.user_id;
```

---

## 5. Great Expectations 数据质量

### 5.1 基础配置
```python
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations import (
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnDistinctValuesToContainSet
)

# 初始化上下文
context = gx.get_context()

# 创建 Expectation Suite
suite = ExpectationSuite(name="orders_suite")

# 添加期望规则
suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
suite.add_expectation(ExpectColumnValuesToBeBetween(column="amount", min_value=0, max_value=100000))
suite.add_expectation(ExpectColumnValuesToMatchRegex(column="email", regex=r"^\S+@\S+\.\S+$"))
suite.add_expectation(ExpectColumnDistinctValuesToContainSet(
    column="status", 
    value_set=["pending", "paid", "shipped", "delivered"]
))

# 保存
context.save_expectation_suite(suite)
```

### 5.2 Checkpoint 配置
```python
from great_expectations.checkpoint import Checkpoint

# 创建 Checkpoint
checkpoint = Checkpoint(
    name="orders_checkpoint",
    data_context=context,
    config_version=1,
    run_name_template="%Y%m%d-%H%M%S",
    expectation_suite_name="orders_suite",
    batch_request={
        "datasource_name": "my_datasource",
        "data_asset_name": "orders_table",
    },
    action_list=[
        {
            "name": "store_validation_result",
            "action": {"class_name": "StoreValidationResultAction"}
        },
        {
            "name": "update_data_docs",
            "action": {"class_name": "UpdateDataDocsAction"}
        },
        {
            "name": "send_slack_notification",
            "action": {
                "class_name": "SlackNotificationAction",
                "slack_webhook": "${SLACK_WEBHOOK}",
                "notify_on": "failure",
                "renderer": {
                    "module_name": "great_expectations.render.renderer.slack_renderer",
                    "class_name": "SlackRenderer"
                }
            }
        }
    ]
)

context.add_checkpoint(checkpoint=checkpoint)

# 运行
result = checkpoint.run()
```

### 5.3 Airflow 集成
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'data_quality_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    validate_orders = GreatExpectationsOperator(
        task_id='validate_orders',
        data_context_root_dir='/opt/airflow/gx',
        checkpoint_name='orders_checkpoint',
        fail_task_on_validation_failure=True,
    )
```

---

## 6. Dagster 数据流水线

### 6.1 基础 Asset 定义
```python
from dagster import asset, Definitions
import pandas as pd

@asset(group_name="raw_data")
def raw_orders() -> pd.DataFrame:
    """从 S3 加载原始订单数据"""
    return pd.read_csv("s3://bucket/raw/orders.csv")

@asset(group_name="staging", deps=[raw_orders])
def stg_orders(raw_orders: pd.DataFrame) -> pd.DataFrame:
    """清洗订单数据"""
    df = raw_orders.copy()
    df = df.dropna(subset=['order_id'])
    df = df[df['amount'] > 0]
    return df

@asset(group_name="analytics", deps=[stg_orders])
def daily_metrics(stg_orders: pd.DataFrame) -> pd.DataFrame:
    """计算每日统计"""
    return stg_orders.groupby('date').agg({
        'order_id': 'count',
        'amount': 'sum'
    }).reset_index()

defs = Definitions(assets=[raw_orders, stg_orders, daily_metrics])
```

### 6.2 Job 和 Schedule
```python
from dagster import job, schedule, ScheduleDefinition

@job
def daily_etl_job():
    """每日 ETL 作业"""
    daily_metrics(stg_orders(raw_orders()))

# 定义调度
@schedule(
    job=daily_etl_job,
    cron_schedule="0 2 * * *",
    execution_timezone="Asia/Shanghai"
)
def daily_schedule():
    return {}

# 或使用 ScheduleDefinition
daily_schedule = ScheduleDefinition(
    job=daily_etl_job,
    cron_schedule="0 2 * * *",
)
```

### 6.3 资源定义
```python
from dagster import resource, EnvVar
import psycopg2

@resource(config_schema={"connection_string": str})
def postgres_resource(init_context):
    return psycopg2.connect(init_context.resource_config["connection_string"])

@resource
def s3_resource():
    import boto3
    return boto3.client('s3')

# 使用资源
@asset(required_resource_keys={"postgres", "s3"})
def processed_data(context) -> pd.DataFrame:
    s3 = context.resources.s3
    pg_conn = context.resources.postgres
    # 使用资源进行操作
    ...

# 资源配置
defs = Definitions(
    assets=[processed_data],
    resources={
        "postgres": postgres_resource.configured({
            "connection_string": EnvVar("POSTGRES_URL")
        }),
        "s3": s3_resource
    }
)
```

---

## 7. Airflow DAG 示例

### 7.1 基础 ETL DAG
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'etl_pipeline',
    default_args=default_args,
    description='数据ETL流水线',
    schedule_interval='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl'],
) as dag:
    
    extract = PostgresOperator(
        task_id='extract',
        postgres_conn_id='source_db',
        sql='SELECT * FROM orders WHERE dt = {{ ds }}',
    )
    
    transform = PostgresOperator(
        task_id='transform',
        postgres_conn_id='transform_db',
        sql='''
            INSERT INTO staging.orders 
            SELECT * FROM raw.orders 
            WHERE dt = '{{ ds }}' AND amount > 0
        ''',
    )
    
    load = PostgresOperator(
        task_id='load',
        postgres_conn_id='warehouse',
        sql='''
            INSERT INTO dw.fact_orders
            SELECT * FROM staging.orders WHERE dt = '{{ ds }}'
        ''',
    )
    
    extract >> transform >> load
```

### 7.2 动态任务生成
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

def process_table(table_name, **context):
    print(f"Processing table: {table_name}")
    # 处理逻辑

tables = ['users', 'orders', 'products', 'payments']

with DAG('dynamic_etl', schedule_interval='@daily', start_date=datetime(2024, 1, 1)) as dag:
    
    for table in tables:
        PythonOperator(
            task_id=f'process_{table}',
            python_callable=process_table,
            op_kwargs={'table_name': table},
        )
```

---

## 8. Docker Compose 开发环境

```yaml
version: '3.8'

services:
  # Zookeeper
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  # MySQL (CDC 源)
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: ecommerce
    command: --default-authentication-plugin=mysql_native_password --binlog-format=ROW

  # StarRocks FE
  starrocks-fe:
    image: starrocks/fe-ubuntu:latest
    ports:
      - "8030:8030"
      - "9020:9020"
      - "9030:9030"
    environment:
      - STARROCKS_HOME=/opt/starrocks/fe

  # StarRocks BE
  starrocks-be:
    image: starrocks/be-ubuntu:latest
    ports:
      - "8040:8040"
      - "9050:9050"
      - "9060:9060"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # MinIO (S3 兼容存储)
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
```

---

*代码示例更新于: 2026-02-16*
