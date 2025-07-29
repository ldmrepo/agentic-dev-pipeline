"""
워크플로우 상태 관리
LangGraph 워크플로우의 상태 정의 및 관리
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import operator

from langchain_core.messages import BaseMessage


class TaskType(str, Enum):
    """태스크 타입"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


class PipelineStatus(str, Enum):
    """파이프라인 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    status: PipelineStatus
    
    # 입력 데이터
    requirements: str
    context: Dict[str, Any]
    constraints: List[str]
    
    # 메시지 히스토리 (LangChain 메시지 리듀서 사용)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 각 단계별 결과
    analysis_result: Dict[str, Any]
    planning_result: Dict[str, Any]
    development_result: Dict[str, Any]
    testing_result: Dict[str, Any]
    review_result: Dict[str, Any]
    deployment_result: Dict[str, Any]
    monitoring_result: Dict[str, Any]
    
    # 아티팩트
    artifacts: List[Dict[str, Any]]
    
    # 메타데이터
    created_at: datetime
    updated_at: datetime
    execution_time: int  # milliseconds
    token_usage: Dict[str, int]
    
    # 에러 처리
    errors: List[Dict[str, Any]]
    retry_count: int
    
    # 현재 실행 중인 노드
    current_node: Optional[str]
    
    # 다음 실행할 노드들
    next_nodes: List[str]


class StateManager:
    """상태 관리 유틸리티"""
    
    @staticmethod
    def create_initial_state(
        pipeline_id: str,
        requirements: str,
        task_type: TaskType = TaskType.FEATURE,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """초기 상태 생성"""
        now = datetime.utcnow()
        
        return WorkflowState(
            pipeline_id=pipeline_id,
            thread_id=f"{pipeline_id}-{now.timestamp()}",
            task_type=task_type,
            status=PipelineStatus.PENDING,
            requirements=requirements,
            context=context or {},
            constraints=[],
            messages=[],
            analysis_result={},
            planning_result={},
            development_result={},
            testing_result={},
            review_result={},
            deployment_result={},
            monitoring_result={},
            artifacts=[],
            created_at=now,
            updated_at=now,
            execution_time=0,
            token_usage={"input": 0, "output": 0},
            errors=[],
            retry_count=0,
            current_node=None,
            next_nodes=[]
        )
    
    @staticmethod
    def update_status(
        state: WorkflowState,
        status: PipelineStatus
    ) -> WorkflowState:
        """상태 업데이트"""
        state["status"] = status
        state["updated_at"] = datetime.utcnow()
        return state
    
    @staticmethod
    def add_message(
        state: WorkflowState,
        message: BaseMessage
    ) -> WorkflowState:
        """메시지 추가"""
        state["messages"].append(message)
        state["updated_at"] = datetime.utcnow()
        return state
    
    @staticmethod
    def add_artifact(
        state: WorkflowState,
        name: str,
        type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
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
    
    @staticmethod
    def add_error(
        state: WorkflowState,
        node: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """에러 추가"""
        error_entry = {
            "node": node,
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow()
        }
        
        state["errors"].append(error_entry)
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    @staticmethod
    def set_current_node(
        state: WorkflowState,
        node_name: str
    ) -> WorkflowState:
        """현재 노드 설정"""
        state["current_node"] = node_name
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    @staticmethod
    def update_node_result(
        state: WorkflowState,
        node_name: str,
        result: Dict[str, Any]
    ) -> WorkflowState:
        """노드 결과 업데이트"""
        result_field_map = {
            "analyze_task": "analysis_result",
            "planning": "planning_result",
            "development": "development_result",
            "testing": "testing_result",
            "review": "review_result",
            "deployment": "deployment_result",
            "monitoring": "monitoring_result"
        }
        
        if node_name in result_field_map:
            field_name = result_field_map[node_name]
            state[field_name] = result
        
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    @staticmethod
    def calculate_execution_time(
        state: WorkflowState
    ) -> int:
        """실행 시간 계산"""
        if state["created_at"]:
            delta = datetime.utcnow() - state["created_at"]
            return int(delta.total_seconds() * 1000)
        return 0
    
    @staticmethod
    def is_terminal_state(state: WorkflowState) -> bool:
        """종료 상태인지 확인"""
        return state["status"] in [
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED
        ]
    
    @staticmethod
    def should_retry(state: WorkflowState, max_retries: int = 3) -> bool:
        """재시도 여부 확인"""
        return (
            state["status"] == PipelineStatus.FAILED and
            state["retry_count"] < max_retries
        )
    
    @staticmethod
    def get_progress_percentage(state: WorkflowState) -> float:
        """진행률 계산"""
        total_steps = 7  # 전체 노드 수
        completed_steps = 0
        
        if state["analysis_result"]:
            completed_steps += 1
        if state["planning_result"]:
            completed_steps += 1
        if state["development_result"]:
            completed_steps += 1
        if state["testing_result"]:
            completed_steps += 1
        if state["review_result"]:
            completed_steps += 1
        if state["deployment_result"]:
            completed_steps += 1
        if state["monitoring_result"]:
            completed_steps += 1
        
        return (completed_steps / total_steps) * 100