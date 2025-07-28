# 데이터 파이프라인 개발 워크플로우

## 📊 End-to-End 데이터 파이프라인 자동 구축
**목표 완료 시간: 2-3시간**

다음의 데이터 파이프라인을 구축해주세요: $ARGUMENTS

## 워크플로우 단계

### 1단계: 데이터 요구사항 분석 (15분)

다음을 수행해줘:

#### 데이터 소스 분석
- 데이터 소스 유형 파악 (DB, API, 파일, 스트림)
- 데이터 볼륨 및 속도 추정
- 데이터 형식 및 스키마 분석
- 데이터 품질 요구사항 정의

#### 데이터 처리 요구사항
- 변환 규칙 정의
- 집계 및 분석 요구사항
- 실시간 vs 배치 처리 결정
- 데이터 보존 정책

#### 아키텍처 설계
- 파이프라인 아키텍처 다이어그램
- 기술 스택 선정
- 확장성 고려사항
- 모니터링 전략

docs/data-pipeline/ 디렉토리에 다음 문서 생성:
- data-requirements.md
- pipeline-architecture.md
- data-flow-diagram.md

### 2단계: 데이터 수집 계층 구현 (30분)

다음을 수행해줘:

#### Kafka 설정 (스트리밍 데이터)
```yaml
# docker-compose.kafka.yml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

#### 데이터 수집기 구현
- Kafka Producer 구현
- API 데이터 수집기
- 파일 시스템 모니터링
- 데이터베이스 CDC (Change Data Capture)

src/collectors/ 디렉토리에 구현:
- kafka_producer.py
- api_collector.py
- file_watcher.py
- database_cdc.py

### 3단계: 데이터 처리 계층 구현 (45분)

다음을 수행해줘:

#### Apache Spark 처리
```python
# src/processing/spark_processor.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

class DataProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("DataPipeline") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
    
    def process_stream(self):
        # 스트림 처리 로직
        pass
    
    def process_batch(self):
        # 배치 처리 로직
        pass
```

#### Apache Flink 처리 (실시간)
```java
// src/processing/flink/StreamProcessor.java
public class StreamProcessor {
    public static void main(String[] args) {
        StreamExecutionEnvironment env = 
            StreamExecutionEnvironment.getExecutionEnvironment();
        
        // 실시간 처리 로직
    }
}
```

#### 데이터 변환 규칙
- 데이터 정제 및 검증
- 스키마 변환
- 집계 및 윈도우 함수
- 데이터 보강 (Enrichment)

### 4단계: 데이터 저장 계층 구현 (30분)

다음을 수행해줘:

#### 데이터 레이크 (S3/MinIO)
```python
# src/storage/data_lake.py
class DataLakeStorage:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def save_raw_data(self, data, partition):
        # Parquet 형식으로 저장
        pass
    
    def save_processed_data(self, data, partition):
        # 처리된 데이터 저장
        pass
```

#### 데이터 웨어하우스 (Snowflake/BigQuery)
```sql
-- schemas/data_warehouse.sql
CREATE SCHEMA IF NOT EXISTS raw_data;
CREATE SCHEMA IF NOT EXISTS processed_data;
CREATE SCHEMA IF NOT EXISTS analytics;

-- 테이블 생성
CREATE TABLE analytics.fact_events (
    event_id UUID PRIMARY KEY,
    event_time TIMESTAMP,
    user_id VARCHAR,
    event_type VARCHAR,
    properties VARIANT
);
```

#### 시계열 데이터베이스 (InfluxDB)
```python
# src/storage/timeseries_db.py
from influxdb_client import InfluxDBClient

class TimeSeriesStorage:
    def __init__(self):
        self.client = InfluxDBClient(
            url="http://localhost:8086",
            token="your-token"
        )
    
    def write_metrics(self, metrics):
        # 메트릭 저장
        pass
```

### 5단계: 데이터 품질 관리 (30분)

다음을 수행해줘:

#### Great Expectations 설정
```python
# src/quality/data_quality.py
import great_expectations as ge

class DataQualityChecker:
    def __init__(self):
        self.context = ge.get_context()
    
    def create_expectations(self):
        # 데이터 품질 규칙 정의
        suite = self.context.create_expectation_suite(
            "data_quality_suite"
        )
        
        # 컬럼 존재 여부
        # 데이터 타입 검증
        # 값 범위 검증
        # 중복 검사
```

#### 데이터 프로파일링
- 통계 정보 수집
- 이상치 탐지
- 데이터 분포 분석
- 품질 메트릭 계산

#### 알림 시스템
- 품질 임계치 설정
- Slack/이메일 알림
- 대시보드 통합
- 자동 복구 로직

### 6단계: 오케스트레이션 설정 (30분)

다음을 수행해줘:

#### Apache Airflow DAG
```python
# dags/data_pipeline_dag.py
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'data_pipeline',
    default_args=default_args,
    description='End-to-end data pipeline',
    schedule_interval='@hourly',
    catchup=False
)

# 태스크 정의
collect_data = PythonOperator(
    task_id='collect_data',
    python_callable=collect_data_func,
    dag=dag
)

process_data = PythonOperator(
    task_id='process_data',
    python_callable=process_data_func,
    dag=dag
)

quality_check = PythonOperator(
    task_id='quality_check',
    python_callable=quality_check_func,
    dag=dag
)

# 의존성 설정
collect_data >> process_data >> quality_check
```

#### 스케줄링 및 의존성
- 작업 의존성 관리
- 실패 처리 로직
- 재시도 정책
- SLA 모니터링

### 7단계: 모니터링 및 관측성 (30분)

다음을 수행해줘:

#### Prometheus 메트릭
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
records_processed = Counter(
    'pipeline_records_processed_total',
    'Total records processed'
)

processing_time = Histogram(
    'pipeline_processing_duration_seconds',
    'Processing time in seconds'
)

pipeline_health = Gauge(
    'pipeline_health_status',
    'Pipeline health status'
)
```

#### Grafana 대시보드
```json
{
  "dashboard": {
    "title": "Data Pipeline Monitor",
    "panels": [
      {
        "title": "처리량",
        "targets": [
          {
            "expr": "rate(pipeline_records_processed_total[5m])"
          }
        ]
      },
      {
        "title": "레이턴시",
        "targets": [
          {
            "expr": "pipeline_processing_duration_seconds"
          }
        ]
      }
    ]
  }
}
```

#### 로그 집계
- ELK 스택 설정
- 구조화된 로깅
- 로그 파싱 규칙
- 검색 가능한 로그

### 8단계: 성능 최적화 (30분)

다음을 수행해줘:

#### 처리 최적화
- 파티셔닝 전략
- 병렬 처리 튜닝
- 메모리 최적화
- 캐싱 구현

#### 저장소 최적화
- 압축 알고리즘 선택
- 파티션 프루닝
- 인덱싱 전략
- 콜드 스토리지 계층화

#### 네트워크 최적화
- 배치 크기 조정
- 압축 전송
- 연결 풀링
- 대역폭 관리

성능 테스트 결과:
- 처리량: X records/sec
- 레이턴시: Y ms
- 리소스 사용률: Z%

### 9단계: 보안 및 거버넌스 (20분)

다음을 수행해줘:

#### 데이터 보안
- 전송 중 암호화 (TLS)
- 저장 시 암호화
- 접근 제어 (RBAC)
- 감사 로깅

#### 데이터 거버넌스
- 데이터 계보 추적
- 메타데이터 관리
- 데이터 카탈로그
- 규정 준수 (GDPR, CCPA)

#### 개인정보 보호
- PII 마스킹
- 익명화 처리
- 데이터 보존 정책
- 삭제 권한 구현

### 10단계: 문서화 및 배포 (20분)

다음을 수행해줘:

#### 문서화
- 파이프라인 아키텍처 문서
- API 문서
- 운영 가이드
- 트러블슈팅 가이드

#### 배포
- Docker 이미지 빌드
- Kubernetes 매니페스트
- Helm 차트
- CI/CD 파이프라인

#### 인수인계
- 운영팀 교육 자료
- 모니터링 가이드
- 알림 설정 가이드
- 비상 대응 매뉴얼

최종 산출물:
- 완전히 자동화된 데이터 파이프라인
- 실시간 모니터링 대시보드
- 데이터 품질 보고서
- 운영 문서

각 단계별로 진행 상황을 보고하고, 모든 코드와 설정 파일을 생성해줘.