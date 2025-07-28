# 데이터 파이프라인 개발 워크플로우

## 📊 End-to-End 데이터 파이프라인 자동 구축

이 워크플로우는 데이터 수집부터 분석 및 시각화까지 완전한 데이터 파이프라인을 자동으로 구축합니다.

**목표 완료 시간: 2-3시간**

## 실행 방법
```bash
export REQUIREMENTS="e-commerce 사용자 행동 데이터 파이프라인 (실시간 분석 + 대시보드)"
export DATA_SOURCES="web_analytics,user_events,transaction_data"
export PROCESSING_TYPE="batch,streaming" # 또는 "batch" 또는 "streaming"
claude -f workflows/data-pipeline-development.md
```

## 워크플로우 단계

### 🎯 1단계: 데이터 아키텍처 설계 (30분)

다음을 수행해줘:

#### 데이터 플로우 설계 및 요구사항 분석
- 파이프라인 요구사항: ${REQUIREMENTS}
- 데이터 소스: ${DATA_SOURCES}
- 처리 방식: ${PROCESSING_TYPE}

```
데이터 소스 분석:
1. 데이터 소스 종류 및 특성 파악
   - 구조화 데이터: 데이터베이스, CSV, JSON
   - 반구조화 데이터: 로그 파일, XML, YAML
   - 비구조화 데이터: 텍스트, 이미지, 비디오

2. 데이터 볼륨 및 속도 추정
   - 일일 데이터 볼륨 (GB/TB)
   - 실시간 처리 요구사항 (이벤트/초)
   - 피크 시간대 트래픽 패턴

3. 데이터 품질 및 거버넌스
   - 데이터 스키마 정의
   - 데이터 무결성 규칙
   - 개인정보 보호 요구사항 (GDPR, CCPA)
   - 데이터 보존 정책

데이터 처리 전략:
배치 처리 (Batch Processing):
- 대용량 데이터 일괄 처리
- 복잡한 집계 및 분석 작업
- 정확성이 속도보다 중요한 경우
- 도구: Apache Spark, Apache Airflow

스트림 처리 (Stream Processing):
- 실시간 데이터 처리
- 즉시 응답이 필요한 경우
- 이벤트 기반 아키텍처
- 도구: Apache Kafka, Apache Flink

하이브리드 처리 (Lambda Architecture):
- 배치와 스트림의 장점 결합
- 실시간 + 일괄 처리 병행
- 정확성과 속도 모두 확보
```

#### 기술 스택 선택 및 아키텍처 설계
```
Modern Data Stack 구성:

데이터 수집 (Ingestion):
- Apache Kafka: 실시간 스트리밍 데이터
- Apache NiFi: 데이터 플로우 관리
- Airbyte: ELT 도구
- Fivetran: SaaS 데이터 커넥터

데이터 저장 (Storage):
- Data Lake: Amazon S3, Google Cloud Storage
- Data Warehouse: Snowflake, BigQuery, Redshift
- NoSQL: MongoDB, Cassandra
- 시계열 DB: InfluxDB, TimescaleDB

데이터 처리 (Processing):
- Apache Spark: 대규모 데이터 처리
- Apache Flink: 실시간 스트림 처리
- dbt: 데이터 변환 및 모델링
- Great Expectations: 데이터 품질 검증

오케스트레이션 (Orchestration):
- Apache Airflow: 워크플로우 관리
- Prefect: 최신 워크플로우 엔진
- Dagster: 데이터 오케스트레이션

모니터링 & 관찰성:
- DataDog: 인프라 및 애플리케이션 모니터링
- Monte Carlo: 데이터 품질 모니터링
- Grafana: 메트릭 시각화

클라우드 기반 아키텍처:
AWS 스택:
- 수집: Kinesis, MSK (Kafka)
- 저장: S3, Redshift, RDS
- 처리: EMR (Spark), Lambda
- 분석: QuickSight, SageMaker

GCP 스택:
- 수집: Pub/Sub, Dataflow
- 저장: Cloud Storage, BigQuery
- 처리: Dataproc, Cloud Functions
- 분석: Looker, Vertex AI

Azure 스택:
- 수집: Event Hubs, Stream Analytics
- 저장: Data Lake Storage, Synapse
- 처리: HDInsight, Functions
- 분석: Power BI, Machine Learning
```

**결과물**: 
- `docs/data-architecture.md`
- `docs/data-flow-diagram.md`
- `architecture/data-pipeline-design.yaml`

---

### 🔧 2단계: 데이터 수집 시스템 구축 (45분)

다음 데이터 수집 시스템을 구현해줘:

#### 실시간 데이터 수집 (Kafka + Kafka Connect)
```
Kafka 클러스터 설정:
# docker-compose.yml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  kafka-connect:
    image: confluentinc/cp-kafka-connect:latest
    depends_on:
      - kafka
    ports:
      - "8083:8083"
    environment:
      CONNECT_BOOTSTRAP_SERVERS: kafka:9092
      CONNECT_REST_ADVERTISED_HOST_NAME: kafka-connect
      CONNECT_GROUP_ID: "connect-cluster"
      CONNECT_CONFIG_STORAGE_TOPIC: "connect-configs"
      CONNECT_OFFSET_STORAGE_TOPIC: "connect-offsets"
      CONNECT_STATUS_STORAGE_TOPIC: "connect-status"

토픽 생성 및 구성:
# 토픽 생성 스크립트
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --partitions 3 \
  --replication-factor 1

kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic transaction-data \
  --partitions 6 \
  --replication-factor 1

Kafka Connect 커넥터 설정:
# 데이터베이스 소스 커넥터
{
  "name": "mysql-source-connector",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "connection.url": "jdbc:mysql://mysql:3306/ecommerce",
    "connection.user": "kafka_user",
    "connection.password": "kafka_password",
    "table.whitelist": "users,orders,products",
    "mode": "incrementing",
    "incrementing.column.name": "id",
    "topic.prefix": "mysql-"
  }
}

# 웹 로그 커넥터
{
  "name": "file-source-connector",
  "config": {
    "connector.class": "FileStreamSource",
    "file": "/var/log/web/access.log",
    "topic": "web-logs"
  }
}
```

#### Python 데이터 수집기 구현
```python
# data_collectors/event_collector.py
import json
import asyncio
from kafka import KafkaProducer
from typing import Dict, Any
import logging

class EventCollector:
    def __init__(self, kafka_config: Dict[str, Any]):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        self.logger = logging.getLogger(__name__)
    
    async def collect_user_events(self, event_data: Dict[str, Any]):
        """사용자 이벤트 수집"""
        try:
            # 이벤트 데이터 검증
            validated_event = self._validate_event(event_data)
            
            # 개인정보 마스킹
            masked_event = self._mask_pii(validated_event)
            
            # Kafka로 전송
            self.producer.send(
                topic='user-events',
                key=event_data.get('user_id'),
                value=masked_event
            )
            
            self.logger.info(f"Event collected: {event_data.get('event_type')}")
            
        except Exception as e:
            self.logger.error(f"Failed to collect event: {e}")
    
    def _validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 데이터 검증"""
        required_fields = ['event_type', 'timestamp', 'user_id']
        
        for field in required_fields:
            if field not in event:
                raise ValueError(f"Missing required field: {field}")
        
        return event
    
    def _mask_pii(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """개인정보 마스킹"""
        pii_fields = ['email', 'phone', 'ip_address']
        
        for field in pii_fields:
            if field in event:
                event[field] = self._hash_field(event[field])
        
        return event

# API 서버 통합
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()
collector = EventCollector({'bootstrap_servers': ['localhost:9092']})

class UserEvent(BaseModel):
    event_type: str
    user_id: str
    timestamp: int
    properties: Dict[str, Any]

@app.post("/events")
async def collect_event(event: UserEvent, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        collector.collect_user_events, 
        event.dict()
    )
    return {"status": "accepted"}
```

#### 배치 데이터 수집 (Airbyte)
```yaml
# airbyte-config.yaml
version: "0.40.0"
definitions:
  sources:
    postgres-source:
      type: postgres
      config:
        host: postgres-db
        port: 5432
        database: ecommerce_prod
        username: readonly_user
        password: ${POSTGRES_PASSWORD}
        schemas: ["public"]
        ssl: true
    
    api-source:
      type: http-api
      config:
        base_url: "https://api.example.com"
        headers:
          Authorization: "Bearer ${API_TOKEN}"
        endpoints:
          - path: "/users"
            method: "GET"
            pagination:
              type: "offset"
              limit: 1000
          - path: "/orders"
            method: "GET"
            pagination:
              type: "cursor"
              cursor_field: "created_at"

  destinations:
    data-warehouse:
      type: snowflake
      config:
        host: ${SNOWFLAKE_HOST}
        database: ANALYTICS
        schema: RAW_DATA
        username: ${SNOWFLAKE_USER}
        password: ${SNOWFLAKE_PASSWORD}
        warehouse: COMPUTE_WH

connections:
  - source: postgres-source
    destination: data-warehouse
    schedule: "0 2 * * *"  # 매일 새벽 2시
    
  - source: api-source
    destination: data-warehouse
    schedule: "0 */6 * * *"  # 6시간마다
```

---

### ⚙️ 3단계: 데이터 처리 및 변환 (1시간)

다음 데이터 처리 시스템을 구현해줘:

#### Apache Spark 배치 처리
```python
# spark_jobs/user_behavior_analysis.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging

class UserBehaviorAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("UserBehaviorAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.logger = logging.getLogger(__name__)
    
    def analyze_daily_user_behavior(self, date: str):
        """일일 사용자 행동 분석"""
        
        # 원시 이벤트 데이터 로드
        events_df = self.spark.read \
            .option("multiline", "true") \
            .json(f"s3a://data-lake/events/date={date}/*")
        
        # 데이터 품질 검증
        events_df = self._validate_data_quality(events_df)
        
        # 사용자 세션 분석
        user_sessions = self._analyze_user_sessions(events_df)
        
        # 제품 상호작용 분석
        product_interactions = self._analyze_product_interactions(events_df)
        
        # 전환 깔때기 분석
        conversion_funnel = self._analyze_conversion_funnel(events_df)
        
        # 결과 저장
        self._save_analysis_results(date, {
            'user_sessions': user_sessions,
            'product_interactions': product_interactions,
            'conversion_funnel': conversion_funnel
        })
    
    def _analyze_user_sessions(self, events_df):
        """사용자 세션 분석"""
        
        # 세션 정의: 30분 이상 비활성 시 새 세션
        window_spec = Window.partitionBy("user_id").orderBy("timestamp")
        
        sessions_df = events_df \
            .withColumn("prev_timestamp", lag("timestamp").over(window_spec)) \
            .withColumn("time_diff", 
                       col("timestamp") - col("prev_timestamp")) \
            .withColumn("session_break", 
                       when(col("time_diff") > 1800, 1).otherwise(0)) \
            .withColumn("session_id", 
                       sum("session_break").over(window_spec))
        
        # 세션별 메트릭 계산
        session_metrics = sessions_df \
            .groupBy("user_id", "session_id") \
            .agg(
                min("timestamp").alias("session_start"),
                max("timestamp").alias("session_end"),
                count("*").alias("event_count"),
                countDistinct("page_url").alias("unique_pages"),
                sum(when(col("event_type") == "purchase", 1).otherwise(0)).alias("purchases")
            ) \
            .withColumn("session_duration", 
                       col("session_end") - col("session_start"))
        
        return session_metrics
    
    def _validate_data_quality(self, df):
        """데이터 품질 검증"""
        # 필수 필드 확인
        required_fields = ["user_id", "timestamp", "event_type"]
        for field in required_fields:
            if field not in df.columns:
                raise ValueError(f"Missing required field: {field}")
        
        # NULL 값 제거
        df_cleaned = df.dropna(subset=required_fields)
        
        # 이상치 제거 (타임스탬프 범위 확인)
        current_time = unix_timestamp()
        df_cleaned = df_cleaned.filter(
            (col("timestamp") > current_time - 86400 * 30) &  # 30일 이내
            (col("timestamp") <= current_time)
        )
        
        # 로그 기록
        original_count = df.count()
        cleaned_count = df_cleaned.count()
        self.logger.info(f"Data quality check: {original_count} → {cleaned_count} records")
        
        return df_cleaned

# dbt 데이터 변환 모델
# models/marts/user_behavior/daily_user_metrics.sql
{{ config(materialized='table') }}

WITH user_daily_events AS (
    SELECT 
        user_id,
        DATE(timestamp) as event_date,
        COUNT(*) as total_events,
        COUNT(DISTINCT session_id) as sessions,
        SUM(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as page_views,
        SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as add_to_carts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchases,
        SUM(CASE WHEN event_type = 'purchase' THEN revenue ELSE 0 END) as total_revenue
    FROM {{ ref('stg_user_events') }}
    WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY user_id, DATE(timestamp)
),

user_metrics AS (
    SELECT 
        *,
        CASE 
            WHEN purchases > 0 THEN total_revenue / purchases 
            ELSE 0 
        END as avg_order_value,
        CASE 
            WHEN add_to_carts > 0 THEN purchases::FLOAT / add_to_carts 
            ELSE 0 
        END as cart_conversion_rate
    FROM user_daily_events
)

SELECT * FROM user_metrics
```

#### 실시간 스트림 처리 (Apache Flink)
```python
# flink_jobs/real_time_analytics.py
import json
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema

class RealTimeAnalytics:
    def __init__(self):
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.env.set_parallelism(4)
        
        self.table_env = StreamTableEnvironment.create(self.env)
        
        # Kafka 커넥터 설정
        self._setup_kafka_connectors()
    
    def _setup_kafka_connectors(self):
        """Kafka 소스 및 싱크 설정"""
        
        # 사용자 이벤트 소스 테이블
        self.table_env.execute_sql("""
            CREATE TABLE user_events (
                user_id STRING,
                event_type STRING,
                timestamp BIGINT,
                page_url STRING,
                product_id STRING,
                revenue DECIMAL(10,2),
                event_time AS TO_TIMESTAMP(FROM_UNIXTIME(timestamp)),
                WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'user-events',
                'properties.bootstrap.servers' = 'kafka:9092',
                'properties.group.id' = 'flink-analytics',
                'format' = 'json',
                'scan.startup.mode' = 'latest-offset'
            )
        """)
        
        # 실시간 메트릭 싱크 테이블
        self.table_env.execute_sql("""
            CREATE TABLE real_time_metrics (
                window_start TIMESTAMP(3),
                window_end TIMESTAMP(3),
                total_events BIGINT,
                unique_users BIGINT,
                total_revenue DECIMAL(10,2),
                avg_session_duration DOUBLE
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'real-time-metrics',
                'properties.bootstrap.servers' = 'kafka:9092',
                'format' = 'json'
            )
        """)
    
    def run_real_time_analytics(self):
        """실시간 분석 실행"""
        
        # 5분 단위 윈도우 집계
        self.table_env.execute_sql("""
            INSERT INTO real_time_metrics
            SELECT 
                TUMBLE_START(event_time, INTERVAL '5' MINUTE) as window_start,
                TUMBLE_END(event_time, INTERVAL '5' MINUTE) as window_end,
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN event_type = 'purchase' THEN revenue ELSE 0 END) as total_revenue,
                AVG(CASE WHEN event_type = 'session_end' THEN timestamp ELSE NULL END) as avg_session_duration
            FROM user_events
            WHERE event_time BETWEEN 
                TUMBLE_START(event_time, INTERVAL '5' MINUTE) AND 
                TUMBLE_END(event_time, INTERVAL '5' MINUTE)
            GROUP BY TUMBLE(event_time, INTERVAL '5' MINUTE)
        """)
        
        # 이상 탐지 - 급격한 트래픽 증가
        self.table_env.execute_sql("""
            CREATE VIEW traffic_anomalies AS
            SELECT *
            FROM (
                SELECT 
                    window_start,
                    total_events,
                    LAG(total_events, 1) OVER (ORDER BY window_start) as prev_events,
                    (total_events - LAG(total_events, 1) OVER (ORDER BY window_start)) / 
                    LAG(total_events, 1) OVER (ORDER BY window_start) * 100 as growth_rate
                FROM real_time_metrics
            ) 
            WHERE growth_rate > 200  -- 200% 이상 증가 시 이상으로 판단
        """)

    def setup_alerting(self):
        """실시간 알림 설정"""
        
        # 수익 급감 알림
        self.table_env.execute_sql("""
            CREATE TABLE revenue_alerts (
                alert_time TIMESTAMP(3),
                message STRING,
                severity STRING,
                current_revenue DECIMAL(10,2),
                expected_revenue DECIMAL(10,2)
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'alerts',
                'properties.bootstrap.servers' = 'kafka:9092',
                'format' = 'json'
            )
        """)
        
        self.table_env.execute_sql("""
            INSERT INTO revenue_alerts
            SELECT 
                CURRENT_TIMESTAMP as alert_time,
                CONCAT('Revenue drop detected: ', CAST(total_revenue AS STRING)) as message,
                'HIGH' as severity,
                total_revenue as current_revenue,
                LAG(total_revenue, 1) OVER (ORDER BY window_start) as expected_revenue
            FROM real_time_metrics
            WHERE total_revenue < LAG(total_revenue, 1) OVER (ORDER BY window_start) * 0.5
        """)
```

---

### 🗄️ 4단계: 데이터 웨어하우스 및 레이크 구축 (30분)

다음 데이터 저장 시스템을 구현해줘:

#### 데이터 레이크 구조 (S3 기반)
```
데이터 레이크 계층 구조:
s3://company-data-lake/
├── raw/                    # 원시 데이터 (Bronze Layer)
│   ├── events/
│   │   └── year=2024/month=03/day=15/hour=14/
│   ├── transactions/
│   └── user_profiles/
├── processed/              # 정제된 데이터 (Silver Layer)
│   ├── user_sessions/
│   ├── product_interactions/
│   └── daily_aggregates/
├── curated/               # 분석용 데이터 (Gold Layer)
│   ├── user_behavior_metrics/
│   ├── sales_analytics/
│   └── ml_features/
└── archive/               # 아카이브 데이터
    └── year=2023/

파티셔닝 전략:
- 시간 기반: year/month/day/hour
- 지역 기반: region/country
- 사용자 기반: user_segment

데이터 포맷:
- Raw: JSON, CSV, Avro
- Processed: Parquet (컬럼형 저장)
- Curated: Delta Lake (버전 관리)
```

#### Snowflake 데이터 웨어하우스 설계
```sql
-- 데이터베이스 구조
CREATE DATABASE ANALYTICS;
USE DATABASE ANALYTICS;

-- 스키마 생성
CREATE SCHEMA RAW_DATA;      -- 원시 데이터
CREATE SCHEMA STAGING;       -- 중간 처리 데이터
CREATE SCHEMA MARTS;         -- 분석용 데이터 마트
CREATE SCHEMA SANDBOX;       -- 실험용 공간

-- 팩트 테이블: 사용자 이벤트
CREATE OR REPLACE TABLE MARTS.FACT_USER_EVENTS (
    event_id STRING PRIMARY KEY,
    user_id STRING NOT NULL,
    session_id STRING,
    event_type STRING NOT NULL,
    event_timestamp TIMESTAMP_NTZ NOT NULL,
    page_url STRING,
    product_id STRING,
    revenue DECIMAL(10,2),
    properties VARIANT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) 
CLUSTER BY (event_timestamp, user_id)
COMMENT = '사용자 이벤트 팩트 테이블';

-- 디멘젼 테이블: 사용자
CREATE OR REPLACE TABLE MARTS.DIM_USERS (
    user_id STRING PRIMARY KEY,
    email STRING,
    first_name STRING,
    last_name STRING,
    registration_date DATE,
    user_segment STRING,
    lifetime_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = '사용자 디멘젼 테이블';

-- 집계 테이블: 일일 사용자 메트릭
CREATE OR REPLACE TABLE MARTS.AGG_DAILY_USER_METRICS (
    metric_date DATE,
    user_id STRING,
    total_events INTEGER,
    session_count INTEGER,
    page_views INTEGER,
    add_to_carts INTEGER,
    purchases INTEGER,
    total_revenue DECIMAL(10,2),
    avg_session_duration DECIMAL(10,2),
    PRIMARY KEY (metric_date, user_id)
)
CLUSTER BY (metric_date)
COMMENT = '일일 사용자 행동 메트릭';

-- 스트림 생성 (CDC)
CREATE OR REPLACE STREAM USER_EVENTS_STREAM 
ON TABLE RAW_DATA.USER_EVENTS
COMMENT = '사용자 이벤트 변경 스트림';

-- 태스크 생성 (자동 처리)
CREATE OR REPLACE TASK PROCESS_USER_EVENTS
    WAREHOUSE = ANALYTICS_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('USER_EVENTS_STREAM')
AS
    INSERT INTO MARTS.FACT_USER_EVENTS
    SELECT 
        event_id,
        user_id,
        session_id,
        event_type,
        event_timestamp,
        page_url,
        product_id,
        revenue,
        properties,
        CURRENT_TIMESTAMP()
    FROM RAW_DATA.USER_EVENTS_STREAM
    WHERE METADATA$ACTION = 'INSERT';

-- 데이터 보존 정책
ALTER TABLE MARTS.FACT_USER_EVENTS 
SET DATA_RETENTION_TIME_IN_DAYS = 90;

-- 보안 설정
CREATE ROW ACCESS POLICY user_data_policy AS (user_id) RETURNS BOOLEAN ->
    CASE 
        WHEN CURRENT_ROLE() IN ('ADMIN', 'DATA_ENGINEER') THEN TRUE
        WHEN CURRENT_ROLE() = 'ANALYST' AND user_id NOT LIKE '%@internal.com' THEN TRUE
        ELSE FALSE
    END;

ALTER TABLE MARTS.DIM_USERS ADD ROW ACCESS POLICY user_data_policy ON (user_id);
```

#### 데이터 거버넌스 및 품질 관리
```python
# data_quality/great_expectations_config.py
import great_expectations as ge
from great_expectations.checkpoint import SimpleCheckpoint

class DataQualityValidator:
    def __init__(self, data_context_config):
        self.context = ge.DataContext(data_context_config)
    
    def create_expectation_suite(self, suite_name: str):
        """데이터 품질 규칙 정의"""
        
        suite = self.context.create_expectation_suite(
            expectation_suite_name=suite_name
        )
        
        # 사용자 이벤트 데이터 품질 규칙
        if suite_name == "user_events_quality":
            expectations = [
                {
                    "expectation_type": "expect_column_to_exist",
                    "kwargs": {"column": "user_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "user_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {
                        "column": "event_type",
                        "regex": "^(page_view|add_to_cart|purchase|login|logout)$"
                    }
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {
                        "column": "timestamp",
                        "min_value": 1640995200,  # 2022-01-01
                        "max_value": None  # 현재 시간까지
                    }
                },
                {
                    "expectation_type": "expect_column_values_to_be_of_type",
                    "kwargs": {
                        "column": "revenue",
                        "type_": "float"
                    }
                }
            ]
            
            for expectation in expectations:
                suite.add_expectation(**expectation)
        
        return suite
    
    def run_validation(self, batch_request, suite_name: str):
        """데이터 품질 검증 실행"""
        
        checkpoint_config = {
            "name": f"{suite_name}_checkpoint",
            "config_version": 1.0,
            "template_name": None,
            "run_name_template": "%Y%m%d-%H%M%S-my-run-name-template",
            "expectation_suite_name": suite_name,
            "batch_request": batch_request,
            "action_list": [
                {
                    "name": "store_validation_result",
                    "action": {"class_name": "StoreValidationResultAction"},
                },
                {
                    "name": "update_data_docs",
                    "action": {"class_name": "UpdateDataDocsAction"},
                },
                {
                    "name": "send_slack_notification",
                    "action": {
                        "class_name": "SlackNotificationAction",
                        "slack_webhook": "https://hooks.slack.com/...",
                        "notify_on": "failure"
                    }
                }
            ],
        }
        
        checkpoint = SimpleCheckpoint(
            f"{suite_name}_checkpoint",
            self.context,
            **checkpoint_config
        )
        
        return checkpoint.run()

# 데이터 카탈로그 (Apache Atlas)
from atlas_client.client import Atlas

class DataCatalog:
    def __init__(self, atlas_config):
        self.atlas = Atlas(
            host=atlas_config['host'],
            port=atlas_config['port'],
            username=atlas_config['username'],
            password=atlas_config['password']
        )
    
    def register_dataset(self, dataset_info):
        """데이터셋 메타데이터 등록"""
        
        entity = {
            "typeName": "DataSet",
            "attributes": {
                "name": dataset_info['name'],
                "description": dataset_info['description'],
                "owner": dataset_info['owner'],
                "location": dataset_info['location'],
                "schema": dataset_info['schema'],
                "tags": dataset_info['tags'],
                "qualifiedName": f"{dataset_info['name']}@data-lake"
            }
        }
        
        return self.atlas.entity_post.create(entity)
```

---

### 📊 5단계: 분석 및 시각화 (30분)

다음 분석 및 시각화 시스템을 구현해줘:

#### 비즈니스 인텔리전스 대시보드 (Tableau/PowerBI)
```python
# dashboards/bi_dashboard_config.py
from tableau_api_lib import TableauServerConnection
import json

class BIDashboardBuilder:
    def __init__(self, tableau_config):
        self.tableau = TableauServerConnection(tableau_config)
        self.tableau.sign_in()
    
    def create_user_behavior_dashboard(self):
        """사용자 행동 분석 대시보드 생성"""
        
        dashboard_config = {
            "name": "User Behavior Analytics",
            "sheets": [
                {
                    "name": "Daily Active Users",
                    "data_source": "MARTS.AGG_DAILY_USER_METRICS",
                    "chart_type": "line",
                    "dimensions": ["metric_date"],
                    "measures": ["unique_users"],
                    "filters": ["metric_date >= DATEADD('day', -30, CURRENT_DATE())"]
                },
                {
                    "name": "Conversion Funnel",
                    "data_source": "MARTS.CONVERSION_FUNNEL",
                    "chart_type": "funnel",
                    "dimensions": ["funnel_step"],
                    "measures": ["user_count", "conversion_rate"]
                },
                {
                    "name": "Revenue Trends",
                    "data_source": "MARTS.REVENUE_ANALYTICS",
                    "chart_type": "combo",
                    "dimensions": ["date"],
                    "measures": ["total_revenue", "avg_order_value"]
                },
                {
                    "name": "User Segments",
                    "data_source": "MARTS.USER_SEGMENTS",
                    "chart_type": "treemap",
                    "dimensions": ["segment_name"],
                    "measures": ["user_count", "revenue_contribution"]
                }
            ]
        }
        
        return self._create_dashboard(dashboard_config)
    
    def create_real_time_monitoring_dashboard(self):
        """실시간 모니터링 대시보드"""
        
        dashboard_config = {
            "name": "Real-Time Monitoring",
            "refresh_interval": 60,  # 60초마다 새로고침
            "sheets": [
                {
                    "name": "Live Traffic",
                    "data_source": "real_time_metrics",
                    "chart_type": "area",
                    "streaming": True
                },
                {
                    "name": "Current Active Users",
                    "data_source": "active_sessions",
                    "chart_type": "metric",
                    "kpi_threshold": {
                        "good": "> 1000",
                        "warning": "500-1000",
                        "critical": "< 500"
                    }
                }
            ]
        }
        
        return self._create_dashboard(dashboard_config)

# Grafana 실시간 대시보드
# dashboards/grafana_dashboard.json
{
  "dashboard": {
    "title": "Data Pipeline Monitoring",
    "panels": [
      {
        "id": 1,
        "title": "Kafka Topic Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(kafka_server_brokertopicmetrics_messagesin_total[5m])) by (topic)",
            "legendFormat": "{{topic}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Spark Job Performance",
        "type": "table",
        "targets": [
          {
            "expr": "spark_job_duration_seconds",
            "format": "table"
          }
        ]
      },
      {
        "id": 3,
        "title": "Data Quality Metrics",
        "type": "stat",
        "targets": [
          {
            "expr": "data_quality_validation_success_rate"
          }
        ]
      },
      {
        "id": 4,
        "title": "Pipeline Latency",
        "type": "gauge",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, pipeline_processing_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

#### ML 기반 분석 (Python)
```python
# analytics/ml_analytics.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from prophet import Prophet
import mlflow

class MLAnalytics:
    def __init__(self, warehouse_connection):
        self.warehouse = warehouse_connection
        mlflow.set_tracking_uri("http://mlflow:5000")
    
    def anomaly_detection(self, date_range):
        """이상 탐지 모델"""
        
        # 데이터 로드
        query = f"""
        SELECT 
            user_id,
            DATE(event_timestamp) as date,
            COUNT(*) as event_count,
            SUM(CASE WHEN event_type = 'purchase' THEN revenue ELSE 0 END) as daily_revenue
        FROM MARTS.FACT_USER_EVENTS
        WHERE event_timestamp BETWEEN '{date_range[0]}' AND '{date_range[1]}'
        GROUP BY user_id, DATE(event_timestamp)
        """
        
        df = pd.read_sql(query, self.warehouse)
        
        # Isolation Forest 모델 학습
        features = ['event_count', 'daily_revenue']
        model = IsolationForest(contamination=0.05, random_state=42)
        
        # 이상치 탐지
        df['anomaly'] = model.fit_predict(df[features])
        df['anomaly_score'] = model.score_samples(df[features])
        
        # 결과 저장
        anomalies = df[df['anomaly'] == -1]
        
        with mlflow.start_run():
            mlflow.log_metric("total_anomalies", len(anomalies))
            mlflow.sklearn.log_model(model, "anomaly_detector")
        
        return anomalies
    
    def revenue_forecasting(self, historical_days=365):
        """수익 예측 모델"""
        
        # 과거 데이터 로드
        query = f"""
        SELECT 
            DATE(event_timestamp) as ds,
            SUM(revenue) as y
        FROM MARTS.FACT_USER_EVENTS
        WHERE event_type = 'purchase'
            AND event_timestamp >= CURRENT_DATE - {historical_days}
        GROUP BY DATE(event_timestamp)
        ORDER BY ds
        """
        
        df = pd.read_sql(query, self.warehouse)
        
        # Prophet 모델 학습
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        model.fit(df)
        
        # 30일 예측
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        
        # 모델 저장
        with mlflow.start_run():
            mlflow.prophet.log_model(model, "revenue_forecast")
            mlflow.log_metric("mape", self._calculate_mape(df, forecast))
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def user_segmentation(self):
        """사용자 세분화"""
        
        query = """
        SELECT 
            user_id,
            COUNT(DISTINCT DATE(event_timestamp)) as active_days,
            COUNT(DISTINCT session_id) as total_sessions,
            SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_count,
            SUM(CASE WHEN event_type = 'purchase' THEN revenue ELSE 0 END) as total_revenue,
            DATEDIFF('day', MIN(event_timestamp), MAX(event_timestamp)) as customer_lifetime
        FROM MARTS.FACT_USER_EVENTS
        GROUP BY user_id
        """
        
        df = pd.read_sql(query, self.warehouse)
        
        # RFM 분석
        df['recency'] = df['customer_lifetime']
        df['frequency'] = df['purchase_count'] 
        df['monetary'] = df['total_revenue']
        
        # 세그먼트 생성
        df['segment'] = pd.cut(
            df['total_revenue'],
            bins=[0, 100, 500, 1000, float('inf')],
            labels=['Bronze', 'Silver', 'Gold', 'Platinum']
        )
        
        return df
```

---

### 🚀 6단계: 파이프라인 오케스트레이션 및 모니터링 (45분)

다음 오케스트레이션 시스템을 구현해줘:

#### Apache Airflow DAG 구성
```python
# airflow/dags/data_pipeline_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'sla': timedelta(hours=2)
}

# 메인 파이프라인 DAG
dag = DAG(
    'data_pipeline',
    default_args=default_args,
    description='End-to-end data pipeline',
    schedule_interval='0 2 * * *',  # 매일 새벽 2시
    start_date=days_ago(1),
    catchup=False,
    tags=['production', 'data-pipeline']
)

# 1. 데이터 수집
collect_kafka_data = BashOperator(
    task_id='collect_kafka_data',
    bash_command='python /opt/data_collectors/kafka_collector.py --date {{ ds }}',
    dag=dag
)

collect_database_data = BashOperator(
    task_id='collect_database_data', 
    bash_command='airbyte sync --connection-id {{ var.value.db_connection_id }}',
    dag=dag
)

# 2. 데이터 품질 검증
validate_data_quality = PythonOperator(
    task_id='validate_data_quality',
    python_callable=run_data_quality_checks,
    op_kwargs={'date': '{{ ds }}'},
    dag=dag
)

# 3. Spark 처리
spark_batch_processing = SparkSubmitOperator(
    task_id='spark_batch_processing',
    application='/opt/spark_jobs/user_behavior_analysis.py',
    conf={
        'spark.executor.memory': '4g',
        'spark.executor.cores': '4',
        'spark.sql.adaptive.enabled': 'true'
    },
    application_args=['--date', '{{ ds }}'],
    dag=dag
)

# 4. dbt 변환
dbt_transformation = BashOperator(
    task_id='dbt_transformation',
    bash_command='cd /opt/dbt && dbt run --models +daily_user_metrics',
    dag=dag
)

# 5. Snowflake 적재
load_to_warehouse = SnowflakeOperator(
    task_id='load_to_warehouse',
    snowflake_conn_id='snowflake_default',
    sql="""
        COPY INTO MARTS.FACT_USER_EVENTS
        FROM @S3_STAGE/processed/{{ ds }}/
        FILE_FORMAT = (TYPE = PARQUET)
        ON_ERROR = CONTINUE;
    """,
    dag=dag
)

# 6. ML 모델 실행
run_ml_models = PythonOperator(
    task_id='run_ml_models',
    python_callable=execute_ml_analytics,
    op_kwargs={'date': '{{ ds }}'},
    dag=dag
)

# 7. 대시보드 업데이트
refresh_dashboards = BashOperator(
    task_id='refresh_dashboards',
    bash_command='python /opt/dashboards/refresh_all.py',
    dag=dag
)

# 8. 알림 전송
send_completion_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_slack_notification,
    op_kwargs={
        'message': 'Data pipeline completed successfully for {{ ds }}',
        'channel': '#data-alerts'
    },
    trigger_rule='all_done',
    dag=dag
)

# 태스크 의존성 설정
[collect_kafka_data, collect_database_data] >> validate_data_quality
validate_data_quality >> spark_batch_processing
spark_batch_processing >> dbt_transformation
dbt_transformation >> load_to_warehouse
load_to_warehouse >> [run_ml_models, refresh_dashboards]
[run_ml_models, refresh_dashboards] >> send_completion_notification

# 실시간 스트리밍 DAG
streaming_dag = DAG(
    'streaming_pipeline',
    default_args=default_args,
    description='Real-time streaming pipeline',
    schedule_interval=None,  # 항상 실행
    start_date=days_ago(1),
    catchup=False,
    tags=['production', 'streaming']
)

start_flink_job = BashOperator(
    task_id='start_flink_job',
    bash_command="""
        flink run \
            -c com.example.RealTimeAnalytics \
            /opt/flink_jobs/real-time-analytics.jar
    """,
    dag=streaming_dag
)
```

#### 모니터링 및 알림 시스템
```python
# monitoring/pipeline_monitor.py
import requests
from prometheus_client import Counter, Histogram, Gauge
import logging
from typing import Dict, Any

# Prometheus 메트릭 정의
pipeline_success_counter = Counter('pipeline_success_total', 'Total successful pipeline runs')
pipeline_failure_counter = Counter('pipeline_failure_total', 'Total failed pipeline runs')
pipeline_duration_histogram = Histogram('pipeline_duration_seconds', 'Pipeline execution duration')
data_quality_score_gauge = Gauge('data_quality_score', 'Current data quality score')

class PipelineMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.slack_webhook = config['slack_webhook']
        self.pagerduty_key = config['pagerduty_key']
    
    def monitor_pipeline_health(self):
        """파이프라인 상태 모니터링"""
        
        health_checks = {
            'kafka_health': self._check_kafka_health(),
            'spark_health': self._check_spark_health(),
            'warehouse_health': self._check_warehouse_health(),
            'data_freshness': self._check_data_freshness()
        }
        
        # 건강 상태 평가
        overall_health = all(health_checks.values())
        
        if not overall_health:
            self._send_alert({
                'severity': 'critical',
                'message': 'Pipeline health check failed',
                'details': health_checks
            })
        
        return health_checks
    
    def _check_data_freshness(self):
        """데이터 최신성 확인"""
        
        query = """
        SELECT MAX(event_timestamp) as latest_timestamp
        FROM MARTS.FACT_USER_EVENTS
        """
        
        result = self.warehouse.execute(query)
        latest_timestamp = result[0]['latest_timestamp']
        
        # 1시간 이상 지연되면 문제로 판단
        delay_minutes = (datetime.now() - latest_timestamp).total_seconds() / 60
        
        if delay_minutes > 60:
            self._send_alert({
                'severity': 'warning',
                'message': f'Data freshness issue: {delay_minutes:.0f} minutes delay',
                'metric': 'data_freshness_delay_minutes',
                'value': delay_minutes
            })
            return False
        
        return True
    
    def _send_alert(self, alert: Dict[str, Any]):
        """알림 전송"""
        
        # Slack 알림
        if alert['severity'] in ['critical', 'warning']:
            slack_message = {
                'text': f"🚨 {alert['severity'].upper()}: {alert['message']}",
                'attachments': [{
                    'color': 'danger' if alert['severity'] == 'critical' else 'warning',
                    'fields': [
                        {'title': k, 'value': str(v), 'short': True}
                        for k, v in alert.get('details', {}).items()
                    ]
                }]
            }
            
            requests.post(self.slack_webhook, json=slack_message)
        
        # PagerDuty 알림 (Critical only)
        if alert['severity'] == 'critical':
            pagerduty_event = {
                'routing_key': self.pagerduty_key,
                'event_action': 'trigger',
                'payload': {
                    'summary': alert['message'],
                    'severity': 'critical',
                    'source': 'data-pipeline',
                    'custom_details': alert.get('details', {})
                }
            }
            
            requests.post(
                'https://events.pagerduty.com/v2/enqueue',
                json=pagerduty_event
            )

# 성능 모니터링
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def track_processing_metrics(self, job_name: str, metrics: Dict[str, Any]):
        """처리 성능 메트릭 추적"""
        
        # 처리 시간
        if 'duration_seconds' in metrics:
            pipeline_duration_histogram.observe(metrics['duration_seconds'])
        
        # 처리된 레코드 수
        if 'records_processed' in metrics:
            records_gauge = Gauge(
                f'pipeline_{job_name}_records_processed',
                f'Records processed by {job_name}'
            )
            records_gauge.set(metrics['records_processed'])
        
        # 에러율
        if 'error_rate' in metrics:
            error_gauge = Gauge(
                f'pipeline_{job_name}_error_rate',
                f'Error rate for {job_name}'
            )
            error_gauge.set(metrics['error_rate'])
        
        # 처리 속도 (records/second)
        if 'throughput' in metrics:
            throughput_gauge = Gauge(
                f'pipeline_{job_name}_throughput',
                f'Processing throughput for {job_name}'
            )
            throughput_gauge.set(metrics['throughput'])
```

---

### 📋 7단계: 문서화 및 배포 (15분)

다음 문서와 배포 설정을 생성해줘:

#### 파이프라인 문서
```markdown
# 데이터 파이프라인 운영 가이드

## 아키텍처 개요
- **데이터 수집**: Kafka, Airbyte
- **데이터 처리**: Apache Spark, Apache Flink
- **데이터 저장**: S3 (Data Lake), Snowflake (Data Warehouse)
- **오케스트레이션**: Apache Airflow
- **모니터링**: Prometheus, Grafana, DataDog

## 일일 운영 체크리스트
- [ ] Airflow DAG 상태 확인
- [ ] 데이터 품질 리포트 검토
- [ ] 처리 지연 모니터링
- [ ] 스토리지 사용량 확인
- [ ] 비용 모니터링

## 문제 해결 가이드

### 데이터 지연 문제
1. Kafka lag 확인: `kafka-consumer-groups --describe`
2. Spark job 상태 확인: Spark UI (http://spark-master:8080)
3. Airflow 태스크 로그 확인

### 데이터 품질 문제
1. Great Expectations 리포트 확인
2. 데이터 소스 검증
3. 변환 로직 검토

### 성능 문제
1. 리소스 사용률 확인 (CPU, Memory, I/O)
2. 파티션 전략 검토
3. 쿼리 최적화

## 연락처
- 데이터 엔지니어링 팀: data-eng@company.com
- 온콜 엔지니어: #data-oncall (Slack)
```

#### 배포 설정
```yaml
# kubernetes/data-pipeline-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-pipeline
  namespace: data-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-pipeline
  template:
    metadata:
      labels:
        app: data-pipeline
    spec:
      containers:
      - name: airflow-scheduler
        image: apache/airflow:2.5.0
        command: ["airflow", "scheduler"]
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        
      - name: spark-worker
        image: bitnami/spark:3.3
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
```

**결과물**:
- 완전한 데이터 파이프라인 아키텍처
- 실시간 및 배치 처리 시스템
- 데이터 품질 관리 체계
- ML 기반 분석 기능
- 종합 모니터링 대시보드
- 자동화된 오케스트레이션

---

이 워크플로우를 실행하면 완전한 엔드투엔드 데이터 파이프라인이 자동으로 구축됩니다!