"""
Pydantic 스키마 정의
API 요청/응답 모델
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import re

from src.core.constants import (
    PipelineStatus, AgentType, TaskType, TaskComplexity,
    ArtifactType, DeploymentEnvironment, DeploymentStrategy,
    ErrorCode
)

# 기본 스키마
class BaseSchema(BaseModel):
    """기본 스키마"""
    model_config = ConfigDict(from_attributes=True)

class TimestampSchema(BaseSchema):
    """타임스탬프 포함 스키마"""
    created_at: datetime
    updated_at: datetime

# 파이프라인 관련 스키마
class PipelineCreate(BaseSchema):
    """파이프라인 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255, description="Pipeline name")
    description: Optional[str] = Field(None, max_length=1000, description="Pipeline description")
    requirements: str = Field(..., min_length=1, description="Project requirements")
    task_type: TaskType = Field(TaskType.FEATURE, description="Task type")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pipeline configuration")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, and underscores')
        return v

class PipelineUpdate(BaseSchema):
    """파이프라인 업데이트 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[PipelineStatus] = None
    config: Optional[Dict[str, Any]] = None

class PipelineResponse(TimestampSchema):
    """파이프라인 응답"""
    id: UUID
    name: str
    description: Optional[str]
    status: PipelineStatus
    requirements: str
    task_type: TaskType
    config: Dict[str, Any]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[int] = Field(None, description="Execution time in milliseconds")

class PipelineListResponse(BaseSchema):
    """파이프라인 목록 응답"""
    items: List[PipelineResponse]
    total: int
    page: int = 1
    size: int = 20
    pages: int

# 에이전트 관련 스키마
class AgentExecutionCreate(BaseSchema):
    """에이전트 실행 요청"""
    agent_type: AgentType
    input_data: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentExecutionResponse(TimestampSchema):
    """에이전트 실행 응답"""
    id: UUID
    pipeline_id: UUID
    agent_type: AgentType
    status: PipelineStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[int]
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0})
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

# 아티팩트 관련 스키마
class ArtifactCreate(BaseSchema):
    """아티팩트 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255)
    type: ArtifactType
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ArtifactResponse(BaseSchema):
    """아티팩트 응답"""
    id: UUID
    execution_id: UUID
    name: str
    type: ArtifactType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

# 워크플로우 관련 스키마
class WorkflowStateResponse(BaseSchema):
    """워크플로우 상태 응답"""
    pipeline_id: str
    thread_id: str
    task_type: TaskType
    status: str
    requirements: str
    context: Dict[str, Any]
    messages: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]
    planning_result: Dict[str, Any]
    development_result: Dict[str, Any]
    testing_result: Dict[str, Any]
    deployment_result: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    execution_time: int
    token_usage: Dict[str, int]
    errors: List[Dict[str, Any]]

# 태스크 분석 관련 스키마
class TaskAnalysis(BaseSchema):
    """태스크 분석 결과"""
    task_type: TaskType
    complexity: TaskComplexity
    technical_requirements: List[str]
    risks: List[str]
    challenges: List[str]
    estimated_hours: int
    required_expertise: List[str]
    dependencies: List[str]

# 계획 관련 스키마
class WorkBreakdownItem(BaseSchema):
    """작업 분해 항목"""
    task_id: str
    task_name: str
    description: str
    estimated_hours: int
    dependencies: List[str]
    assignee_type: str

class ProjectPlan(BaseSchema):
    """프로젝트 계획"""
    architecture: Dict[str, Any]
    wbs: List[WorkBreakdownItem]
    timeline: Dict[str, Any]
    risks: List[Dict[str, Any]]
    resources: Dict[str, Any]
    success_criteria: List[str]

# 개발 관련 스키마
class CodeFile(BaseSchema):
    """코드 파일"""
    path: str
    content: str
    language: str
    description: Optional[str]

class DevelopmentResult(BaseSchema):
    """개발 결과"""
    generated_files: List[CodeFile]
    dependencies: Dict[str, List[str]]
    api_endpoints: List[Dict[str, Any]]
    database_models: List[Dict[str, Any]]
    documentation: str

# 테스트 관련 스키마
class TestCase(BaseSchema):
    """테스트 케이스"""
    name: str
    description: str
    type: str  # unit, integration, e2e
    code: str
    expected_result: Any

class TestResult(BaseSchema):
    """테스트 결과"""
    test_cases: List[TestCase]
    coverage: float
    passed: int
    failed: int
    skipped: int
    report: str

# 배포 관련 스키마
class DeploymentConfig(BaseSchema):
    """배포 설정"""
    environment: DeploymentEnvironment
    strategy: DeploymentStrategy
    rollback_enabled: bool = True
    health_check_url: Optional[str]
    monitoring_enabled: bool = True

class DeploymentResult(BaseSchema):
    """배포 결과"""
    environment: DeploymentEnvironment
    version: str
    url: Optional[str]
    status: str
    health_check_passed: bool
    deployment_time: int
    rollback_available: bool

# 모니터링 관련 스키마
class Metric(BaseSchema):
    """메트릭"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = Field(default_factory=dict)

class MonitoringData(BaseSchema):
    """모니터링 데이터"""
    metrics: List[Metric]
    alerts: List[Dict[str, Any]]
    health_status: str
    uptime: float
    error_rate: float
    response_time_p95: float

# 에러 응답 스키마
class ErrorDetail(BaseSchema):
    """에러 상세"""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None

class ErrorResponse(BaseSchema):
    """에러 응답"""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    @classmethod
    def from_exception(cls, exc: Exception) -> "ErrorResponse":
        """예외로부터 에러 응답 생성"""
        if hasattr(exc, 'to_dict'):
            return cls(error=exc.to_dict()['error'])
        
        return cls(error={
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": str(exc),
            "details": {}
        })

# 헬스체크 스키마
class HealthCheck(BaseSchema):
    """헬스체크 응답"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    environment: str
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")

# 페이지네이션 스키마
class PaginationParams(BaseSchema):
    """페이지네이션 파라미터"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        """오프셋 계산"""
        return (self.page - 1) * self.size

# 토큰 관련 스키마
class TokenUsage(BaseSchema):
    """토큰 사용량"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str
    cost_estimate: Optional[float] = None

# MCP 서버 관련 스키마
class MCPServerConfig(BaseSchema):
    """MCP 서버 설정"""
    name: str
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True

class MCPServerStatus(BaseSchema):
    """MCP 서버 상태"""
    name: str
    is_running: bool
    pid: Optional[int]
    last_health_check: Optional[datetime]
    error: Optional[str]

# WebSocket 메시지 스키마
class WSMessage(BaseSchema):
    """WebSocket 메시지"""
    type: str = Field(..., description="Message type")
    data: Any = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class WSPipelineUpdate(WSMessage):
    """파이프라인 업데이트 메시지"""
    type: str = "pipeline_update"
    data: Dict[str, Any]

class WSAgentUpdate(WSMessage):
    """에이전트 업데이트 메시지"""
    type: str = "agent_update"
    data: Dict[str, Any]

class WSError(WSMessage):
    """에러 메시지"""
    type: str = "error"
    data: ErrorResponse