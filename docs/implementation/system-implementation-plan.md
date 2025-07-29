# 에이전틱 개발 파이프라인 시스템 구현 계획

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [구현 로드맵](#구현-로드맵)
3. [Phase 1: 기반 인프라 구축](#phase-1-기반-인프라-구축)
4. [Phase 2: 핵심 엔진 개발](#phase-2-핵심-엔진-개발)
5. [Phase 3: 에이전트 구현](#phase-3-에이전트-구현)
6. [Phase 4: 통합 및 최적화](#phase-4-통합-및-최적화)
7. [Phase 5: 프로덕션 준비](#phase-5-프로덕션-준비)
8. [리스크 관리](#리스크-관리)
9. [성공 지표](#성공-지표)

## 프로젝트 개요

### 목표
AI 에이전트를 활용하여 소프트웨어 개발 생명주기 전체를 자동화하는 시스템 구축

### 핵심 가치
- **개발 시간 단축**: 2-4주 → 2-4시간
- **품질 향상**: 테스트 커버리지 85%+ 자동 달성
- **비용 절감**: 개발 비용 30-50% 감소

### 기술 스택
- **Orchestration**: LangGraph
- **Runtime**: Python 3.11+
- **API**: FastAPI
- **Storage**: PostgreSQL, Redis, ChromaDB
- **AI**: Claude API (Opus 4)
- **Integration**: MCP (Model Context Protocol)

## 구현 로드맵

```mermaid
gantt
    title 에이전틱 개발 파이프라인 구현 일정
    dateFormat  YYYY-MM-DD
    section Phase 1
    기반 인프라           :p1, 2025-01-01, 2w
    section Phase 2
    핵심 엔진            :p2, after p1, 3w
    section Phase 3
    에이전트 구현         :p3, after p2, 3w
    section Phase 4
    통합 및 최적화        :p4, after p3, 2w
    section Phase 5
    프로덕션 준비         :p5, after p4, 2w
```

## Phase 1: 기반 인프라 구축

### 1.1 프로젝트 구조 설정 (3일)

#### 디렉토리 구조
```bash
agentic-dev-pipeline/
├── src/
│   ├── api/                    # FastAPI 애플리케이션
│   │   ├── __init__.py
│   │   ├── main.py            # 메인 엔트리포인트
│   │   ├── dependencies.py    # 의존성 주입
│   │   ├── routes/            # API 라우트
│   │   │   ├── pipeline.py
│   │   │   ├── agents.py
│   │   │   └── monitoring.py
│   │   └── middleware/        # 미들웨어
│   │       ├── auth.py
│   │       ├── logging.py
│   │       └── error.py
│   │
│   ├── core/                  # 핵심 비즈니스 로직
│   │   ├── config.py         # 설정 관리
│   │   ├── constants.py      # 상수 정의
│   │   ├── exceptions.py     # 커스텀 예외
│   │   └── schemas.py        # Pydantic 스키마
│   │
│   ├── orchestration/         # LangGraph 워크플로우
│   │   ├── __init__.py
│   │   ├── engine.py         # 워크플로우 엔진
│   │   ├── graphs/           # 그래프 정의
│   │   │   ├── main.py
│   │   │   ├── hotfix.py
│   │   │   └── feature.py
│   │   ├── nodes/            # 노드 구현
│   │   │   ├── base.py
│   │   │   ├── planning.py
│   │   │   └── development.py
│   │   └── state.py          # 상태 관리
│   │
│   ├── agents/               # AI 에이전트
│   │   ├── __init__.py
│   │   ├── base.py          # 베이스 에이전트
│   │   ├── planning/        # Planning Agent
│   │   ├── development/     # Development Agent
│   │   ├── testing/         # Testing Agent
│   │   ├── deployment/      # Deployment Agent
│   │   └── monitoring/      # Monitoring Agent
│   │
│   ├── integrations/        # 외부 서비스 통합
│   │   ├── __init__.py
│   │   ├── claude.py       # Claude API 클라이언트
│   │   ├── mcp/           # MCP 통합
│   │   │   ├── client.py
│   │   │   ├── servers.py
│   │   │   └── tools.py
│   │   └── tools/         # 도구 어댑터
│   │       ├── github.py
│   │       ├── docker.py
│   │       └── kubernetes.py
│   │
│   ├── storage/            # 데이터 저장소
│   │   ├── __init__.py
│   │   ├── database.py    # PostgreSQL
│   │   ├── cache.py       # Redis
│   │   ├── vector.py      # ChromaDB
│   │   └── models.py      # SQLAlchemy 모델
│   │
│   └── utils/             # 유틸리티
│       ├── __init__.py
│       ├── logger.py      # 로깅 설정
│       ├── metrics.py     # 메트릭 수집
│       └── helpers.py     # 헬퍼 함수
│
├── tests/                 # 테스트
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/              # 스크립트
│   ├── setup.sh
│   ├── migrate.py
│   └── seed.py
│
├── docker/              # Docker 설정
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── k8s/                # Kubernetes 매니페스트
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
├── docs/               # 문서
├── .env.example       # 환경 변수 템플릿
├── requirements.txt   # Python 의존성
├── pyproject.toml    # 프로젝트 설정
└── README.md         # 프로젝트 설명
```

#### 초기 설정 스크립트
```python
# scripts/init_project.py
import os
import subprocess
from pathlib import Path

def create_project_structure():
    """프로젝트 디렉토리 구조 생성"""
    base_dirs = [
        "src/api/routes",
        "src/api/middleware",
        "src/core",
        "src/orchestration/graphs",
        "src/orchestration/nodes",
        "src/agents/planning",
        "src/agents/development",
        "src/agents/testing",
        "src/agents/deployment",
        "src/agents/monitoring",
        "src/integrations/mcp",
        "src/integrations/tools",
        "src/storage",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "scripts",
        "docker",
        "k8s",
        "docs"
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # __init__.py 생성
        if dir_path.startswith("src/"):
            init_file = Path(dir_path) / "__init__.py"
            init_file.touch()

def setup_virtual_environment():
    """가상 환경 설정"""
    subprocess.run(["python", "-m", "venv", "venv"])
    print("Virtual environment created. Activate with: source venv/bin/activate")

def create_requirements_file():
    """requirements.txt 생성"""
    requirements = """
# Core
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Cache
redis==5.0.1
hiredis==2.3.2

# Vector Store
chromadb==0.4.22

# AI/ML
langchain==0.1.0
langchain-anthropic==0.1.1
langgraph==0.0.26
openai==1.9.0

# Monitoring
prometheus-client==0.19.0
sentry-sdk==1.39.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development
black==23.12.1
ruff==0.1.11
mypy==1.8.0
pre-commit==3.6.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements.strip())

if __name__ == "__main__":
    create_project_structure()
    setup_virtual_environment()
    create_requirements_file()
    print("Project structure initialized successfully!")
```

### 1.2 개발 환경 설정 (2일)

#### Docker Compose 설정
```yaml
# docker/docker-compose.yml
version: '3.9'

services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: agentic_pipeline
      POSTGRES_USER: agentic
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentic"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ChromaDB
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      IS_PERSISTENT: TRUE
      ANONYMIZED_TELEMETRY: FALSE

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning

  # Application
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://agentic:${POSTGRES_PASSWORD}@postgres:5432/agentic_pipeline
      REDIS_URL: redis://redis:6379
      CHROMA_URL: http://chromadb:8000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_started
    volumes:
      - ../src:/app/src
      - ../.claude:/app/.claude

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  prometheus_data:
  grafana_data:
```

#### 환경 변수 설정
```python
# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    app_name: str = "Agentic Development Pipeline"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API
    api_v1_str: str = "/api/v1"
    api_key: Optional[str] = None
    
    # Database
    postgres_server: str = "localhost"
    postgres_user: str = "agentic"
    postgres_password: str
    postgres_db: str = "agentic_pipeline"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}/{self.postgres_db}"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour
    
    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    
    # Claude API
    anthropic_api_key: str
    claude_model: str = "claude-3-opus-20240229"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.1
    
    # LangGraph
    langgraph_recursion_limit: int = 50
    langgraph_checkpoint_ttl: int = 86400  # 24 hours
    
    # MCP
    mcp_servers: Dict[str, Dict[str, Any]] = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "env": {}
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
        }
    }
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 8081
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """캐시된 설정 인스턴스 반환"""
    return Settings()

# 설정 검증
def validate_settings():
    """설정 값 검증"""
    settings = get_settings()
    
    # 필수 값 확인
    required = [
        "anthropic_api_key",
        "postgres_password",
        "secret_key"
    ]
    
    for field in required:
        if not getattr(settings, field):
            raise ValueError(f"Required setting '{field}' is not set")
    
    print("✅ All settings validated successfully")
```

### 1.3 데이터베이스 스키마 설계 (2일)

#### SQLAlchemy 모델
```python
# src/storage/models.py
from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class PipelineStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(enum.Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class Pipeline(Base):
    __tablename__ = "pipelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(PipelineStatus), default=PipelineStatus.PENDING)
    config = Column(JSON, default={})
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="pipeline")
    checkpoints = relationship("Checkpoint", back_populates="pipeline")

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"))
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(PipelineStatus), default=PipelineStatus.PENDING)
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    error_message = Column(Text)
    execution_time = Column(Integer)  # milliseconds
    token_usage = Column(JSON, default={})  # {"input": 0, "output": 0}
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="executions")
    artifacts = relationship("Artifact", back_populates="execution")

class Artifact(Base):
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_executions.id"))
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # code, document, test, config
    content = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    execution = relationship("AgentExecution", back_populates="artifacts")

class Checkpoint(Base):
    __tablename__ = "checkpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"))
    thread_id = Column(String(255), nullable=False)
    checkpoint_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="checkpoints")

class MCPServer(Base):
    __tablename__ = "mcp_servers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    command = Column(String(255), nullable=False)
    args = Column(JSON, default=[])
    env = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    health_check_url = Column(String(255))
    last_health_check = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 데이터베이스 마이그레이션
```python
# scripts/create_migration.py
import subprocess
import sys
from datetime import datetime

def create_migration(message: str):
    """Alembic 마이그레이션 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    revision_message = f"{timestamp}_{message.replace(' ', '_').lower()}"
    
    subprocess.run([
        "alembic", "revision",
        "--autogenerate",
        "-m", revision_message
    ])
    
    print(f"Migration created: {revision_message}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_migration.py 'migration message'")
        sys.exit(1)
    
    create_migration(sys.argv[1])
```

### 1.4 CI/CD 파이프라인 설정 (2일)

#### GitHub Actions 워크플로우
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install ruff black mypy
    
    - name: Run Ruff
      run: ruff check src tests
    
    - name: Run Black
      run: black --check src tests
    
    - name: Run MyPy
      run: mypy src

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/unit -v --cov=src --cov-report=xml
        pytest tests/integration -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./docker/Dockerfile
        push: false
        tags: agentic-pipeline:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

## Phase 2: 핵심 엔진 개발

### 2.1 LangGraph 워크플로우 엔진 (5일)

#### 베이스 워크플로우 엔진
```python
# src/orchestration/engine.py
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolExecutor
import asyncio
import logging

from src.core.config import get_settings
from src.orchestration.state import WorkflowState
from src.storage.database import get_async_session

logger = logging.getLogger(__name__)
settings = get_settings()

class WorkflowEngine:
    """LangGraph 기반 워크플로우 엔진"""
    
    def __init__(self):
        self.graphs: Dict[str, StateGraph] = {}
        self.checkpointer = None
        self._initialize_checkpointer()
    
    def _initialize_checkpointer(self):
        """체크포인터 초기화"""
        self.checkpointer = PostgresSaver.from_conn_string(
            settings.database_url.replace("+asyncpg", "")
        )
    
    def register_graph(self, name: str, graph: StateGraph):
        """그래프 등록"""
        compiled = graph.compile(checkpointer=self.checkpointer)
        self.graphs[name] = compiled
        logger.info(f"Graph '{name}' registered successfully")
    
    async def execute(
        self,
        graph_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """워크플로우 실행"""
        if graph_name not in self.graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.graphs[graph_name]
        
        # 기본 설정
        if config is None:
            config = {}
        
        # thread_id 생성
        if "configurable" not in config:
            config["configurable"] = {}
        if "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = f"{graph_name}-{asyncio.get_event_loop().time()}"
        
        try:
            # 비동기 실행
            result = await graph.ainvoke(input_data, config)
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            raise
    
    async def stream(
        self,
        graph_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """워크플로우 스트리밍 실행"""
        if graph_name not in self.graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.graphs[graph_name]
        
        async for chunk in graph.astream(input_data, config):
            yield chunk
    
    async def get_state(
        self,
        graph_name: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        if graph_name not in self.graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.graphs[graph_name]
        config = {"configurable": {"thread_id": thread_id}}
        
        state = await graph.aget_state(config)
        return state.values if state else None
    
    async def update_state(
        self,
        graph_name: str,
        thread_id: str,
        updates: Dict[str, Any]
    ):
        """워크플로우 상태 업데이트"""
        if graph_name not in self.graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.graphs[graph_name]
        config = {"configurable": {"thread_id": thread_id}}
        
        await graph.aupdate_state(config, updates)

# 싱글톤 인스턴스
workflow_engine = WorkflowEngine()
```

#### 메인 워크플로우 그래프
```python
# src/orchestration/graphs/main.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
import logging

from src.orchestration.state import WorkflowState
from src.orchestration.nodes import (
    analyze_task_node,
    planning_node,
    development_node,
    testing_node,
    deployment_node,
    monitoring_node,
    review_node
)

logger = logging.getLogger(__name__)

def create_main_workflow() -> StateGraph:
    """메인 개발 워크플로우 생성"""
    
    # 그래프 초기화
    graph = StateGraph(WorkflowState)
    
    # 노드 추가
    graph.add_node("analyze_task", analyze_task_node)
    graph.add_node("planning", planning_node)
    graph.add_node("development", development_node)
    graph.add_node("testing", testing_node)
    graph.add_node("deployment", deployment_node)
    graph.add_node("monitoring", monitoring_node)
    graph.add_node("review", review_node)
    
    # 엣지 정의
    graph.set_entry_point("analyze_task")
    
    # 조건부 라우팅
    graph.add_conditional_edges(
        "analyze_task",
        route_after_analysis,
        {
            "planning": "planning",
            "hotfix": "development",  # 핫픽스는 바로 개발로
            "review": "review"
        }
    )
    
    # 순차 실행
    graph.add_edge("planning", "development")
    graph.add_edge("development", "testing")
    graph.add_edge("testing", "review")
    
    # 리뷰 후 조건부 라우팅
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "deployment": "deployment",
            "rework": "development",
            "end": END
        }
    )
    
    graph.add_edge("deployment", "monitoring")
    graph.add_edge("monitoring", END)
    
    return graph

def route_after_analysis(state: WorkflowState) -> str:
    """태스크 분석 후 라우팅"""
    task_type = state.get("task_type", "")
    
    if task_type == "hotfix":
        logger.info("Routing to hotfix flow")
        return "hotfix"
    elif task_type == "review_only":
        logger.info("Routing to review only")
        return "review"
    else:
        logger.info("Routing to standard planning flow")
        return "planning"

def route_after_review(state: WorkflowState) -> str:
    """리뷰 후 라우팅"""
    review_result = state.get("review_result", {})
    
    if review_result.get("approved", False):
        logger.info("Review approved, proceeding to deployment")
        return "deployment"
    elif review_result.get("needs_rework", False):
        logger.info("Review requires rework")
        return "rework"
    else:
        logger.info("Review completed, ending workflow")
        return "end"

# 병렬 실행을 위한 서브그래프
def create_parallel_development_graph() -> StateGraph:
    """병렬 개발 워크플로우 (프론트엔드/백엔드/인프라)"""
    
    graph = StateGraph(WorkflowState)
    
    # 병렬 실행 노드
    graph.add_node("split_tasks", split_development_tasks)
    graph.add_node("frontend", frontend_development_node)
    graph.add_node("backend", backend_development_node)
    graph.add_node("infrastructure", infrastructure_development_node)
    graph.add_node("merge_results", merge_development_results)
    
    # 플로우 정의
    graph.set_entry_point("split_tasks")
    
    # 병렬 실행 (Send API 사용)
    graph.add_edge("split_tasks", "frontend")
    graph.add_edge("split_tasks", "backend")
    graph.add_edge("split_tasks", "infrastructure")
    
    # 결과 병합
    graph.add_edge("frontend", "merge_results")
    graph.add_edge("backend", "merge_results")
    graph.add_edge("infrastructure", "merge_results")
    
    graph.add_edge("merge_results", END)
    
    return graph
```

### 2.2 상태 관리 시스템 (3일)

#### 워크플로우 상태 정의
```python
# src/orchestration/state.py
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class TaskType(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"

class AgentMessage(BaseModel):
    """에이전트 메시지"""
    agent: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class WorkflowState(TypedDict):
    """워크플로우 전체 상태"""
    # 기본 정보
    pipeline_id: str
    thread_id: str
    task_type: TaskType
    status: str
    
    # 입력 데이터
    requirements: str
    context: Dict[str, Any]
    constraints: List[str]
    
    # 메시지 히스토리
    messages: List[AgentMessage]
    
    # 각 단계별 결과
    analysis_result: Dict[str, Any]
    planning_result: Dict[str, Any]
    development_result: Dict[str, Any]
    testing_result: Dict[str, Any]
    review_result: Dict[str, Any]
    deployment_result: Dict[str, Any]
    
    # 아티팩트
    artifacts: List[Dict[str, Any]]
    
    # 메타데이터
    created_at: datetime
    updated_at: datetime
    execution_time: int
    token_usage: Dict[str, int]
    
    # 에러 처리
    errors: List[Dict[str, Any]]
    retry_count: int

class StateManager:
    """상태 관리 유틸리티"""
    
    @staticmethod
    def create_initial_state(
        pipeline_id: str,
        requirements: str,
        task_type: TaskType = TaskType.FEATURE
    ) -> WorkflowState:
        """초기 상태 생성"""
        return WorkflowState(
            pipeline_id=pipeline_id,
            thread_id=f"{pipeline_id}-{datetime.utcnow().timestamp()}",
            task_type=task_type,
            status="initialized",
            requirements=requirements,
            context={},
            constraints=[],
            messages=[],
            analysis_result={},
            planning_result={},
            development_result={},
            testing_result={},
            review_result={},
            deployment_result={},
            artifacts=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            execution_time=0,
            token_usage={"input": 0, "output": 0},
            errors=[],
            retry_count=0
        )
    
    @staticmethod
    def add_message(
        state: WorkflowState,
        agent: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> WorkflowState:
        """메시지 추가"""
        message = AgentMessage(
            agent=agent,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        state["messages"].append(message)
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    @staticmethod
    def add_artifact(
        state: WorkflowState,
        name: str,
        type: str,
        content: Any,
        metadata: Dict[str, Any] = None
    ) -> WorkflowState:
        """아티팩트 추가"""
        artifact = {
            "name": name,
            "type": type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        state["artifacts"].append(artifact)
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    @staticmethod
    def update_token_usage(
        state: WorkflowState,
        input_tokens: int,
        output_tokens: int
    ) -> WorkflowState:
        """토큰 사용량 업데이트"""
        state["token_usage"]["input"] += input_tokens
        state["token_usage"]["output"] += output_tokens
        
        return state
```

### 2.3 노드 구현 (5일)

#### 베이스 노드
```python
# src/orchestration/nodes/base.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import time
from functools import wraps

from src.orchestration.state import WorkflowState, StateManager
from src.core.exceptions import NodeExecutionError

logger = logging.getLogger(__name__)

def node_error_handler(func):
    """노드 에러 처리 데코레이터"""
    @wraps(func)
    async def wrapper(state: WorkflowState, *args, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        node_name = func.__name__
        
        try:
            logger.info(f"Starting node: {node_name}")
            result = await func(state, *args, **kwargs)
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Node {node_name} completed in {execution_time}ms")
            
            # 실행 시간 업데이트
            state["execution_time"] += execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Node {node_name} failed: {str(e)}")
            
            # 에러 기록
            error = {
                "node": node_name,
                "error": str(e),
                "timestamp": time.time()
            }
            state["errors"].append(error)
            state["status"] = "error"
            
            # 재시도 카운트 증가
            state["retry_count"] += 1
            
            raise NodeExecutionError(f"Node {node_name} execution failed: {str(e)}")
    
    return wrapper

class BaseNode(ABC):
    """모든 노드의 베이스 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """노드 실행 로직"""
        pass
    
    async def __call__(self, state: WorkflowState) -> Dict[str, Any]:
        """노드 호출"""
        return await self.execute(state)
    
    def add_message(self, state: WorkflowState, content: str, metadata: Dict[str, Any] = None):
        """상태에 메시지 추가"""
        StateManager.add_message(state, self.name, content, metadata)
    
    def add_artifact(self, state: WorkflowState, name: str, type: str, content: Any, metadata: Dict[str, Any] = None):
        """상태에 아티팩트 추가"""
        StateManager.add_artifact(state, name, type, content, metadata)
```

#### 태스크 분석 노드
```python
# src/orchestration/nodes/analyze.py
from typing import Dict, Any
import json

from src.orchestration.nodes.base import BaseNode, node_error_handler
from src.orchestration.state import WorkflowState, TaskType
from src.integrations.claude import claude_client

class AnalyzeTaskNode(BaseNode):
    """태스크 분석 노드"""
    
    def __init__(self):
        super().__init__("AnalyzeTask")
        
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """태스크 분석 실행"""
        requirements = state["requirements"]
        
        # Claude API를 사용한 요구사항 분석
        prompt = f"""
        Analyze the following requirements and provide a structured analysis:
        
        Requirements: {requirements}
        
        Please provide:
        1. Task type classification (feature/bugfix/hotfix/refactor/documentation)
        2. Complexity assessment (simple/medium/complex)
        3. Key technical requirements
        4. Potential risks and challenges
        5. Estimated effort (in hours)
        6. Required expertise areas
        
        Format the response as JSON.
        """
        
        response = await claude_client.analyze(prompt)
        analysis = json.loads(response)
        
        # 상태 업데이트
        state["task_type"] = TaskType(analysis["task_type"])
        state["analysis_result"] = analysis
        
        # 메시지 추가
        self.add_message(
            state,
            f"Task analyzed: {analysis['task_type']} - {analysis['complexity']}",
            {"analysis": analysis}
        )
        
        return {
            "analysis_result": analysis,
            "task_type": analysis["task_type"],
            "status": "analyzed"
        }

# 노드 인스턴스
analyze_task_node = AnalyzeTaskNode()
```

## Phase 3: 에이전트 구현

### 3.1 베이스 에이전트 (3일)

#### 에이전트 베이스 클래스
```python
# src/agents/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool
from langgraph.prebuilt import create_react_agent

from src.core.config import get_settings
from src.integrations.mcp import MCPClient

settings = get_settings()
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """모든 AI 에이전트의 베이스 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agents.{name}")
        
        # LLM 초기화
        self.llm = ChatAnthropic(
            model=settings.claude_model,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=settings.claude_max_tokens,
            temperature=settings.claude_temperature
        )
        
        # MCP 클라이언트
        self.mcp_client = MCPClient(settings.mcp_servers)
        
        # 도구 초기화
        self.tools = self._initialize_tools()
        
        # ReAct 에이전트 생성
        self.agent = self._create_agent()
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        pass
    
    @abstractmethod
    def _get_tools(self) -> List[Tool]:
        """에이전트 전용 도구 정의"""
        pass
    
    def _initialize_tools(self) -> List[Tool]:
        """도구 초기화"""
        base_tools = [
            Tool(
                name="mcp_filesystem",
                description="Access filesystem through MCP",
                func=self._mcp_filesystem_tool
            ),
            Tool(
                name="mcp_github",
                description="Access GitHub through MCP",
                func=self._mcp_github_tool
            )
        ]
        
        # 에이전트별 도구 추가
        agent_tools = self._get_tools()
        
        return base_tools + agent_tools
    
    def _create_agent(self):
        """ReAct 에이전트 생성"""
        return create_react_agent(
            self.llm,
            self.tools,
            messages_modifier=self._get_system_prompt()
        )
    
    async def _mcp_filesystem_tool(self, operation: str, path: str, content: Optional[str] = None) -> str:
        """MCP 파일시스템 도구"""
        return await self.mcp_client.call_tool(
            "filesystem",
            operation,
            {"path": path, "content": content}
        )
    
    async def _mcp_github_tool(self, operation: str, repo: str, **kwargs) -> str:
        """MCP GitHub 도구"""
        return await self.mcp_client.call_tool(
            "github",
            operation,
            {"repo": repo, **kwargs}
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행 (재시도 로직 포함)"""
        self.logger.info(f"Executing task: {task.get('description', 'No description')}")
        
        try:
            # 에이전트 실행
            result = await self.agent.ainvoke(task)
            
            # 결과 처리
            processed_result = await self._process_result(result)
            
            self.logger.info("Task execution completed successfully")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            raise
    
    @abstractmethod
    async def _process_result(self, result: Any) -> Dict[str, Any]:
        """결과 후처리"""
        pass
    
    async def validate_output(self, output: Dict[str, Any]) -> bool:
        """출력 검증"""
        # 기본 검증 로직
        if not output:
            return False
        
        if "error" in output:
            return False
        
        # 에이전트별 추가 검증은 서브클래스에서 구현
        return await self._validate_specific_output(output)
    
    async def _validate_specific_output(self, output: Dict[str, Any]) -> bool:
        """에이전트별 출력 검증 (오버라이드 가능)"""
        return True
```

### 3.2 Planning Agent (3일)

```python
# src/agents/planning/agent.py
from typing import List, Dict, Any
import json

from src.agents.base import BaseAgent
from langchain.tools import Tool
from src.integrations.tools.architecture import ArchitectureTool
from src.integrations.tools.estimation import EstimationTool

class PlanningAgent(BaseAgent):
    """요구사항 분석 및 계획 수립 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            description="Analyzes requirements and creates development plans"
        )
        self.architecture_tool = ArchitectureTool()
        self.estimation_tool = EstimationTool()
    
    def _get_system_prompt(self) -> str:
        return """You are a Planning Agent responsible for analyzing requirements and creating comprehensive development plans.

Your responsibilities:
1. Analyze functional and non-functional requirements
2. Design system architecture
3. Create work breakdown structure (WBS)
4. Estimate timelines and resources
5. Identify risks and dependencies
6. Define success criteria

Always provide structured, actionable plans with clear milestones.
Consider scalability, maintainability, and security in your designs.
"""
    
    def _get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="create_architecture",
                description="Create system architecture diagram",
                func=self.architecture_tool.create_diagram
            ),
            Tool(
                name="estimate_effort",
                description="Estimate development effort",
                func=self.estimation_tool.estimate
            ),
            Tool(
                name="identify_risks",
                description="Identify project risks",
                func=self._identify_risks
            ),
            Tool(
                name="create_wbs",
                description="Create work breakdown structure",
                func=self._create_wbs
            )
        ]
    
    async def _identify_risks(self, requirements: str) -> str:
        """리스크 식별"""
        prompt = f"""
        Identify potential risks for the following requirements:
        {requirements}
        
        Categories to consider:
        - Technical risks
        - Resource risks
        - Timeline risks
        - Integration risks
        - Security risks
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def _create_wbs(self, requirements: str) -> str:
        """작업 분해 구조 생성"""
        prompt = f"""
        Create a detailed Work Breakdown Structure (WBS) for:
        {requirements}
        
        Format as hierarchical JSON with:
        - Task ID
        - Task name
        - Description
        - Estimated hours
        - Dependencies
        - Assignee type (frontend/backend/devops)
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def _process_result(self, result: Any) -> Dict[str, Any]:
        """계획 결과 처리"""
        return {
            "architecture": result.get("architecture", {}),
            "wbs": result.get("wbs", {}),
            "timeline": result.get("timeline", {}),
            "risks": result.get("risks", []),
            "resources": result.get("resources", {}),
            "success_criteria": result.get("success_criteria", [])
        }
    
    async def _validate_specific_output(self, output: Dict[str, Any]) -> bool:
        """계획 출력 검증"""
        required_fields = ["architecture", "wbs", "timeline", "risks"]
        
        for field in required_fields:
            if field not in output or not output[field]:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # WBS 검증
        if "tasks" not in output["wbs"] or len(output["wbs"]["tasks"]) == 0:
            self.logger.error("WBS must contain at least one task")
            return False
        
        return True
```

### 3.3 Development Agent (3일)

```python
# src/agents/development/agent.py
from typing import List, Dict, Any
import os
import json

from src.agents.base import BaseAgent
from langchain.tools import Tool
from src.integrations.tools.code_generator import CodeGenerator
from src.integrations.tools.dependency_manager import DependencyManager

class DevelopmentAgent(BaseAgent):
    """코드 생성 및 구현 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="DevelopmentAgent",
            description="Generates code and implements features"
        )
        self.code_generator = CodeGenerator()
        self.dependency_manager = DependencyManager()
    
    def _get_system_prompt(self) -> str:
        return """You are a Development Agent responsible for implementing code based on specifications.

Your responsibilities:
1. Generate clean, maintainable code
2. Follow best practices and design patterns
3. Implement proper error handling
4. Add appropriate logging and monitoring
5. Write self-documenting code
6. Ensure code is testable

Technologies you work with:
- Backend: Python (FastAPI), Node.js (Express)
- Frontend: React, TypeScript
- Database: PostgreSQL, Redis
- Infrastructure: Docker, Kubernetes

Always follow the project's coding standards and architecture decisions.
"""
    
    def _get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="generate_code",
                description="Generate code based on specifications",
                func=self.code_generator.generate
            ),
            Tool(
                name="create_api_endpoint",
                description="Create API endpoint with FastAPI",
                func=self._create_api_endpoint
            ),
            Tool(
                name="create_react_component",
                description="Create React component",
                func=self._create_react_component
            ),
            Tool(
                name="setup_database_schema",
                description="Setup database schema",
                func=self._setup_database_schema
            ),
            Tool(
                name="manage_dependencies",
                description="Manage project dependencies",
                func=self.dependency_manager.manage
            )
        ]
    
    async def _create_api_endpoint(self, spec: Dict[str, Any]) -> str:
        """API 엔드포인트 생성"""
        template = """
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.{schema_name} import {schema_name}Create, {schema_name}Update, {schema_name}Response
from src.services.{service_name} import {service_name}Service

router = APIRouter()

@router.post("/", response_model={schema_name}Response, status_code=status.HTTP_201_CREATED)
async def create_{resource_name}(
    data: {schema_name}Create,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Create a new {resource_name}\"\"\"
    service = {service_name}Service(db)
    return await service.create(data)

@router.get("/{{{resource_name}_id}}", response_model={schema_name}Response)
async def get_{resource_name}(
    {resource_name}_id: str,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Get a {resource_name} by ID\"\"\"
    service = {service_name}Service(db)
    result = await service.get({resource_name}_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{resource_name} not found"
        )
    return result
"""
        
        # 템플릿 채우기
        code = template.format(
            schema_name=spec["schema_name"],
            service_name=spec["service_name"],
            resource_name=spec["resource_name"]
        )
        
        # 파일 생성
        file_path = f"src/api/routes/{spec['resource_name']}.py"
        await self._mcp_filesystem_tool("write", file_path, code)
        
        return f"API endpoint created at {file_path}"
    
    async def _create_react_component(self, spec: Dict[str, Any]) -> str:
        """React 컴포넌트 생성"""
        template = """
import React, { useState, useEffect } from 'react';
import {{ {imports} }} from '@/components/ui';
import {{ use{hook_name} }} from '@/hooks';

interface {component_name}Props {{
  {props}
}}

export const {component_name}: React.FC<{component_name}Props> = ({{ {prop_names} }}) => {{
  const [state, setState] = useState({initial_state});
  const {{ data, loading, error }} = use{hook_name}();
  
  useEffect(() => {{
    // Component logic
  }}, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {{error.message}}</div>;
  
  return (
    <div className="{class_name}">
      {{/* Component JSX */}}
    </div>
  );
}};
"""
        
        code = template.format(
            component_name=spec["component_name"],
            imports=spec.get("imports", "Button, Card"),
            hook_name=spec.get("hook_name", "Query"),
            props=spec.get("props", ""),
            prop_names=spec.get("prop_names", ""),
            initial_state=spec.get("initial_state", "{}"),
            class_name=spec.get("class_name", "container")
        )
        
        file_path = f"frontend/src/components/{spec['component_name']}.tsx"
        await self._mcp_filesystem_tool("write", file_path, code)
        
        return f"React component created at {file_path}"
    
    async def _setup_database_schema(self, spec: Dict[str, Any]) -> str:
        """데이터베이스 스키마 설정"""
        # SQLAlchemy 모델 생성
        model_code = f"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from src.storage.database import Base

class {spec['model_name']}(Base):
    __tablename__ = "{spec['table_name']}"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    {self._generate_columns(spec['columns'])}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
"""
        
        file_path = f"src/storage/models/{spec['model_name'].lower()}.py"
        await self._mcp_filesystem_tool("write", file_path, model_code)
        
        # Alembic 마이그레이션 생성
        migration_command = f"alembic revision --autogenerate -m 'Add {spec['model_name']} model'"
        await self._mcp_filesystem_tool("execute", ".", migration_command)
        
        return f"Database schema created for {spec['model_name']}"
    
    def _generate_columns(self, columns: List[Dict[str, Any]]) -> str:
        """컬럼 정의 생성"""
        column_defs = []
        
        for col in columns:
            col_type = col['type']
            col_name = col['name']
            nullable = col.get('nullable', True)
            
            if col_type == 'string':
                col_def = f"{col_name} = Column(String({col.get('length', 255)}), nullable={nullable})"
            elif col_type == 'boolean':
                col_def = f"{col_name} = Column(Boolean, default={col.get('default', False)})"
            elif col_type == 'datetime':
                col_def = f"{col_name} = Column(DateTime, nullable={nullable})"
            elif col_type == 'uuid':
                col_def = f"{col_name} = Column(UUID(as_uuid=True), ForeignKey('{col.get('foreign_key')}'), nullable={nullable})"
            else:
                col_def = f"{col_name} = Column(String(255), nullable={nullable})"
            
            column_defs.append(col_def)
        
        return '\n    '.join(column_defs)
    
    async def _process_result(self, result: Any) -> Dict[str, Any]:
        """개발 결과 처리"""
        return {
            "generated_files": result.get("files", []),
            "dependencies": result.get("dependencies", {}),
            "api_endpoints": result.get("endpoints", []),
            "database_models": result.get("models", []),
            "documentation": result.get("documentation", "")
        }
```

## Phase 4: 통합 및 최적화

### 4.1 API 서버 구현 (3일)

```python
# src/api/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from src.api.routes import pipeline, agents, monitoring
from src.core.config import get_settings
from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.error import error_handler
from src.utils.logger import setup_logging

# 설정 및 로깅
settings = get_settings()
setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 미들웨어
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

# 에러 핸들러
app.add_exception_handler(Exception, error_handler)

# 라우터 등록
app.include_router(
    pipeline.router,
    prefix=f"{settings.api_v1_str}/pipelines",
    tags=["pipelines"]
)
app.include_router(
    agents.router,
    prefix=f"{settings.api_v1_str}/agents",
    tags=["agents"]
)
app.include_router(
    monitoring.router,
    prefix=f"{settings.api_v1_str}/monitoring",
    tags=["monitoring"]
)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 이벤트"""
    # 워크플로우 엔진 초기화
    from src.orchestration.engine import workflow_engine
    from src.orchestration.graphs.main import create_main_workflow
    
    # 그래프 등록
    workflow_engine.register_graph("main", create_main_workflow())
    
    # MCP 서버 시작
    from src.integrations.mcp import mcp_manager
    await mcp_manager.start_all_servers()

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 이벤트"""
    # MCP 서버 정리
    from src.integrations.mcp import mcp_manager
    await mcp_manager.stop_all_servers()

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
```

### 4.2 모니터링 시스템 (2일)

```python
# src/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

# 메트릭 정의
pipeline_counter = Counter(
    'pipeline_total',
    'Total number of pipeline executions',
    ['status', 'type']
)

pipeline_duration = Histogram(
    'pipeline_duration_seconds',
    'Pipeline execution duration',
    ['type']
)

active_pipelines = Gauge(
    'active_pipelines',
    'Number of currently active pipelines'
)

agent_execution_counter = Counter(
    'agent_execution_total',
    'Total number of agent executions',
    ['agent', 'status']
)

token_usage_counter = Counter(
    'token_usage_total',
    'Total token usage',
    ['model', 'type']
)

system_info = Info(
    'system',
    'System information'
)

def track_pipeline_execution(pipeline_type: str):
    """파이프라인 실행 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            active_pipelines.inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                pipeline_counter.labels(status='success', type=pipeline_type).inc()
                return result
            except Exception as e:
                pipeline_counter.labels(status='failure', type=pipeline_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                pipeline_duration.labels(type=pipeline_type).observe(duration)
                active_pipelines.dec()
        
        return wrapper
    return decorator

def track_agent_execution(agent_name: str):
    """에이전트 실행 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                agent_execution_counter.labels(agent=agent_name, status='success').inc()
                return result
            except Exception as e:
                agent_execution_counter.labels(agent=agent_name, status='failure').inc()
                raise
        
        return wrapper
    return decorator

# 시스템 정보 설정
system_info.info({
    'version': '1.0.0',
    'environment': 'production'
})
```

## Phase 5: 프로덕션 준비

### 5.1 테스트 스위트 (3일)

```python
# tests/unit/test_workflow_engine.py
import pytest
from unittest.mock import Mock, AsyncMock

from src.orchestration.engine import WorkflowEngine
from src.orchestration.state import StateManager, TaskType

@pytest.fixture
async def workflow_engine():
    """워크플로우 엔진 픽스처"""
    engine = WorkflowEngine()
    yield engine
    # 정리
    await engine.cleanup()

@pytest.mark.asyncio
async def test_workflow_execution(workflow_engine):
    """워크플로우 실행 테스트"""
    # 테스트 그래프 생성
    from langgraph.graph import StateGraph
    
    graph = StateGraph(dict)
    graph.add_node("test", lambda x: {"result": "success"})
    graph.set_entry_point("test")
    graph.add_edge("test", END)
    
    # 그래프 등록
    workflow_engine.register_graph("test", graph)
    
    # 실행
    result = await workflow_engine.execute(
        "test",
        {"input": "test_data"}
    )
    
    assert result["result"] == "success"

@pytest.mark.asyncio
async def test_state_management():
    """상태 관리 테스트"""
    state = StateManager.create_initial_state(
        "test-pipeline",
        "Test requirements",
        TaskType.FEATURE
    )
    
    assert state["pipeline_id"] == "test-pipeline"
    assert state["task_type"] == TaskType.FEATURE
    assert state["status"] == "initialized"
    
    # 메시지 추가
    StateManager.add_message(state, "TestAgent", "Test message")
    assert len(state["messages"]) == 1
    assert state["messages"][0].agent == "TestAgent"
```

### 5.2 배포 설정 (2일)

#### Kubernetes 매니페스트
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-pipeline
  labels:
    app: agentic-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic-pipeline
  template:
    metadata:
      labels:
        app: agentic-pipeline
    spec:
      containers:
      - name: app
        image: agentic-pipeline:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: database-url
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: anthropic-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 5.3 문서화 (2일)

```python
# scripts/generate_docs.py
import os
import subprocess
from pathlib import Path

def generate_api_docs():
    """API 문서 생성"""
    # OpenAPI 스펙 추출
    subprocess.run([
        "python", "-c",
        "from src.api.main import app; import json; "
        "print(json.dumps(app.openapi()))"
    ], stdout=open("docs/openapi.json", "w"))
    
    # Redoc 생성
    subprocess.run([
        "npx", "redoc-cli", "bundle",
        "docs/openapi.json",
        "-o", "docs/api.html"
    ])

def generate_code_docs():
    """코드 문서 생성"""
    subprocess.run([
        "sphinx-build", "-b", "html",
        "docs/source", "docs/build"
    ])

if __name__ == "__main__":
    generate_api_docs()
    generate_code_docs()
    print("Documentation generated successfully!")
```

## 리스크 관리

### 기술적 리스크
| 리스크 | 영향도 | 확률 | 대응 방안 |
|--------|--------|------|-----------|
| Claude API 제한 | 높음 | 중간 | 요청 제한 및 캐싱 구현 |
| LangGraph 성능 이슈 | 중간 | 낮음 | 노드 캐싱 및 병렬 처리 |
| MCP 서버 안정성 | 중간 | 중간 | 헬스체크 및 자동 재시작 |
| 대용량 상태 관리 | 높음 | 낮음 | 외부 스토리지 활용 |

### 운영적 리스크
| 리스크 | 영향도 | 확률 | 대응 방안 |
|--------|--------|------|-----------|
| 비용 초과 | 높음 | 중간 | 사용량 모니터링 및 예산 알림 |
| 보안 취약점 | 높음 | 낮음 | 정기적 보안 스캔 |
| 데이터 손실 | 높음 | 낮음 | 백업 및 복구 전략 |

## 성공 지표

### 기술적 KPI
- **응답 시간**: 95%ile < 5초
- **가용성**: 99.9% 이상
- **에러율**: < 0.1%
- **테스트 커버리지**: 85% 이상

### 비즈니스 KPI
- **개발 시간 단축**: 70% 이상
- **코드 품질**: SonarQube A등급
- **사용자 만족도**: NPS 50 이상
- **비용 절감**: 30% 이상

### 모니터링 대시보드
- Grafana 대시보드 구성
- 실시간 메트릭 추적
- 알림 설정 (Slack, Email)
- 월간 리포트 자동 생성

## 구현 일정 요약

| Phase | 기간 | 주요 결과물 |
|-------|------|-------------|
| Phase 1: 기반 인프라 | 2주 | 프로젝트 구조, 개발 환경, DB 스키마 |
| Phase 2: 핵심 엔진 | 3주 | LangGraph 엔진, 상태 관리, 기본 노드 |
| Phase 3: 에이전트 | 3주 | 5개 전문 에이전트 구현 |
| Phase 4: 통합 | 2주 | API 서버, 모니터링, 최적화 |
| Phase 5: 프로덕션 | 2주 | 테스트, 배포, 문서화 |

**총 소요 기간: 12주**

## 다음 단계

1. **PoC 구현** (2주)
   - 핵심 기능만 구현
   - 기술 검증 수행

2. **MVP 개발** (6주)
   - 기본 워크플로우 구현
   - 2개 에이전트 구현

3. **점진적 확장** (4주)
   - 나머지 에이전트 추가
   - 성능 최적화

4. **프로덕션 배포**
   - 단계적 롤아웃
   - 모니터링 강화