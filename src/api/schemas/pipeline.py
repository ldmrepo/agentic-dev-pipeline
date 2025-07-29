"""
파이프라인 관련 API 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from src.core.schemas import TaskType, PipelineStatus


class PipelineBase(BaseModel):
    """파이프라인 기본 모델"""
    name: str = Field(..., description="파이프라인 이름")
    description: Optional[str] = Field(None, description="파이프라인 설명")
    task_type: TaskType = Field(..., description="작업 유형")
    requirements: Optional[str] = Field(None, description="요구사항")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")


class PipelineCreate(PipelineBase):
    """파이프라인 생성 요청"""
    auto_execute: bool = Field(True, description="생성 후 자동 실행 여부")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="실행 컨텍스트")


class PipelineUpdate(BaseModel):
    """파이프라인 업데이트 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PipelineStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class PipelineResponse(PipelineBase):
    """파이프라인 응답"""
    id: UUID
    status: PipelineStatus
    created_at: datetime
    updated_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[int] = Field(None, description="실행 시간 (밀리초)")
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True


class PipelineListResponse(BaseModel):
    """파이프라인 목록 응답"""
    pipelines: List[PipelineResponse]
    total: int = Field(..., description="전체 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="조회 개수")


class PipelineExecuteRequest(BaseModel):
    """파이프라인 실행 요청"""
    requirements: Optional[str] = Field(None, description="요구사항 (기존 값 사용 시 생략)")
    context: Optional[Dict[str, Any]] = Field(None, description="실행 컨텍스트")
    force: bool = Field(False, description="강제 실행 여부")


class PipelineArtifact(BaseModel):
    """파이프라인 아티팩트"""
    id: UUID
    name: str
    type: str
    path: str
    size: int
    created_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


class PipelineLog(BaseModel):
    """파이프라인 로그"""
    timestamp: datetime
    level: str
    agent: str
    message: str
    context: Optional[Dict[str, Any]] = None