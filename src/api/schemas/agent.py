"""
에이전트 관련 API 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from src.core.schemas import AgentType


class AgentStatusResponse(BaseModel):
    """에이전트 상태 응답"""
    name: str = Field(..., description="에이전트 이름")
    type: AgentType = Field(..., description="에이전트 타입")
    status: str = Field(..., description="상태 (ready, busy, error)")
    version: str = Field(..., description="버전")
    capabilities: List[str] = Field(..., description="지원 기능 목록")
    
    class Config:
        use_enum_values = True


class AgentExecutionResponse(BaseModel):
    """에이전트 실행 응답"""
    id: UUID
    pipeline_id: UUID
    agent_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    
    class Config:
        orm_mode = True


class AgentMetricsResponse(BaseModel):
    """에이전트 메트릭 응답"""
    period: str = Field(..., description="조회 기간")
    start_time: str = Field(..., description="시작 시간")
    end_time: str = Field(..., description="종료 시간")
    metrics: Dict[str, Dict[str, Any]] = Field(..., description="에이전트별 메트릭")
    
    class Config:
        schema_extra = {
            "example": {
                "period": "24h",
                "start_time": "2025-01-01T00:00:00Z",
                "end_time": "2025-01-02T00:00:00Z",
                "metrics": {
                    "planning": {
                        "total_executions": 10,
                        "success_count": 9,
                        "failed_count": 1,
                        "success_rate": 90.0,
                        "avg_execution_time": 45.3,
                        "total_tokens_used": 50000
                    }
                }
            }
        }


class AgentTestRequest(BaseModel):
    """에이전트 테스트 요청"""
    test_type: str = Field(..., description="테스트 유형")
    input_data: Dict[str, Any] = Field(..., description="테스트 입력 데이터")
    options: Optional[Dict[str, Any]] = Field(None, description="테스트 옵션")


class AgentCapability(BaseModel):
    """에이전트 기능"""
    name: str = Field(..., description="기능 이름")
    description: str = Field(..., description="기능 설명")
    parameters: Dict[str, Any] = Field(..., description="필요 파라미터")
    examples: Optional[List[Dict[str, Any]]] = Field(None, description="사용 예시")