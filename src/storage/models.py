"""
SQLAlchemy 모델 정의
데이터베이스 테이블 스키마
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Enum as SQLEnum, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from src.core.constants import (
    PipelineStatus, AgentType, TaskType, TaskComplexity,
    ArtifactType, DeploymentEnvironment, DeploymentStrategy
)

Base = declarative_base()

# Association tables
pipeline_tags = Table(
    'pipeline_tags',
    Base.metadata,
    Column('pipeline_id', UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE')),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE')),
    UniqueConstraint('pipeline_id', 'tag_id')
)

class Pipeline(Base):
    """파이프라인 모델"""
    __tablename__ = 'pipelines'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(PipelineStatus), nullable=False, default=PipelineStatus.CREATED)
    requirements = Column(Text, nullable=False)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    
    # 실행 데이터
    input_data = Column(JSON, nullable=False, default=dict)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    
    # 토큰 사용량
    total_tokens_used = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=True)
    
    # 사용자 정보
    created_by = Column(String(255), nullable=True)
    
    # 관계
    executions = relationship("AgentExecution", back_populates="pipeline", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="pipeline", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=pipeline_tags, back_populates="pipelines")
    
    # 인덱스
    __table_args__ = (
        Index('idx_pipeline_status', 'status'),
        Index('idx_pipeline_created_at', 'created_at'),
        Index('idx_pipeline_task_type', 'task_type'),
    )

class AgentExecution(Base):
    """에이전트 실행 모델"""
    __tablename__ = 'agent_executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id'), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    status = Column(SQLEnum(PipelineStatus), nullable=False, default=PipelineStatus.CREATED)
    
    # 실행 데이터
    input_data = Column(JSON, nullable=False, default=dict)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    
    # 토큰 사용량
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    
    # 메타데이터
    metadata = Column(JSON, nullable=False, default=dict)
    
    # 관계
    pipeline = relationship("Pipeline", back_populates="executions")
    artifacts = relationship("Artifact", back_populates="execution", cascade="all, delete-orphan")
    
    # 인덱스
    __table_args__ = (
        Index('idx_execution_pipeline_id', 'pipeline_id'),
        Index('idx_execution_agent_type', 'agent_type'),
        Index('idx_execution_status', 'status'),
        Index('idx_execution_created_at', 'created_at'),
    )

class Artifact(Base):
    """아티팩트 모델"""
    __tablename__ = 'artifacts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id'), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey('agent_executions.id'), nullable=True)
    
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(ArtifactType), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA256 hash
    size = Column(Integer, nullable=False, default=0)  # bytes
    
    # 메타데이터
    metadata = Column(JSON, nullable=False, default=dict)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # 관계
    pipeline = relationship("Pipeline", back_populates="artifacts")
    execution = relationship("AgentExecution", back_populates="artifacts")
    
    # 인덱스
    __table_args__ = (
        Index('idx_artifact_pipeline_id', 'pipeline_id'),
        Index('idx_artifact_execution_id', 'execution_id'),
        Index('idx_artifact_type', 'type'),
        Index('idx_artifact_created_at', 'created_at'),
        UniqueConstraint('pipeline_id', 'name', 'type', name='uq_artifact_name_type_per_pipeline'),
    )

class WorkflowState(Base):
    """워크플로우 상태 모델 (LangGraph 체크포인트)"""
    __tablename__ = 'workflow_states'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(255), nullable=False)
    checkpoint_id = Column(String(255), nullable=False)
    parent_id = Column(String(255), nullable=True)
    
    # 상태 데이터
    state = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # 인덱스
    __table_args__ = (
        Index('idx_workflow_thread_id', 'thread_id'),
        Index('idx_workflow_checkpoint_id', 'checkpoint_id'),
        UniqueConstraint('thread_id', 'checkpoint_id', name='uq_thread_checkpoint'),
    )

class Tag(Base):
    """태그 모델"""
    __tablename__ = 'tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # HEX color
    
    # 관계
    pipelines = relationship("Pipeline", secondary=pipeline_tags, back_populates="tags")
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class APIKey(Base):
    """API 키 모델"""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(255), nullable=False, unique=True)  # bcrypt hash
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 권한
    scopes = Column(JSON, nullable=False, default=list)  # ["pipelines:read", "pipelines:write"]
    rate_limit = Column(Integer, nullable=False, default=1000)  # requests per hour
    
    # 상태
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 인덱스
    __table_args__ = (
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_is_active', 'is_active'),
    )

class AuditLog(Base):
    """감사 로그 모델"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # 액션 정보
    action = Column(String(50), nullable=False)  # "pipeline.created", "agent.executed"
    entity_type = Column(String(50), nullable=False)  # "pipeline", "agent_execution"
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 사용자 정보
    user_id = Column(String(255), nullable=True)
    api_key_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # 변경 내용
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # 결과
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # 인덱스
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_user_id', 'user_id'),
    )

class Metric(Base):
    """메트릭 모델"""
    __tablename__ = 'metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # 메트릭 정보
    name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    
    # 차원
    labels = Column(JSON, nullable=False, default=dict)
    
    # 집계 정보
    aggregation_type = Column(String(20), nullable=True)  # "sum", "avg", "min", "max"
    aggregation_period = Column(Integer, nullable=True)  # seconds
    
    # 인덱스
    __table_args__ = (
        Index('idx_metric_timestamp', 'timestamp'),
        Index('idx_metric_name', 'name'),
        Index('idx_metric_name_timestamp', 'name', 'timestamp'),
    )

class DeploymentHistory(Base):
    """배포 이력 모델"""
    __tablename__ = 'deployment_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id'), nullable=False)
    
    # 배포 정보
    version = Column(String(50), nullable=False)
    environment = Column(SQLEnum(DeploymentEnvironment), nullable=False)
    strategy = Column(SQLEnum(DeploymentStrategy), nullable=False)
    
    # 상태
    status = Column(String(20), nullable=False)  # "pending", "in_progress", "success", "failed", "rolled_back"
    url = Column(String(500), nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    deployment_time = Column(Integer, nullable=True)  # seconds
    
    # 결과
    health_check_passed = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    rollback_version = Column(String(50), nullable=True)
    
    # 메타데이터
    metadata = Column(JSON, nullable=False, default=dict)
    
    # 인덱스
    __table_args__ = (
        Index('idx_deployment_pipeline_id', 'pipeline_id'),
        Index('idx_deployment_environment', 'environment'),
        Index('idx_deployment_created_at', 'created_at'),
    )