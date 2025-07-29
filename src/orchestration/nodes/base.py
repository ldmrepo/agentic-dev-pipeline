"""
베이스 노드
모든 워크플로우 노드의 베이스 클래스
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import time
from functools import wraps

from langchain_core.messages import AIMessage, HumanMessage

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
            
            # 현재 노드 설정
            StateManager.set_current_node(state, node_name)
            
            # 노드 실행
            result = await func(state, *args, **kwargs)
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Node {node_name} completed in {execution_time}ms")
            
            # 실행 시간 업데이트
            state["execution_time"] += execution_time
            
            # 결과를 상태에 저장
            StateManager.update_node_result(state, node_name, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Node {node_name} failed: {str(e)}")
            
            # 에러 기록
            StateManager.add_error(
                state,
                node_name,
                str(e),
                {"traceback": str(e.__traceback__)}
            )
            
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
    
    def add_message(
        self,
        state: WorkflowState,
        content: str,
        message_type: str = "ai"
    ):
        """상태에 메시지 추가"""
        if message_type == "ai":
            message = AIMessage(content=content)
        else:
            message = HumanMessage(content=content)
        
        StateManager.add_message(state, message)
    
    def add_artifact(
        self,
        state: WorkflowState,
        name: str,
        type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """상태에 아티팩트 추가"""
        StateManager.add_artifact(state, name, type, content, metadata)
    
    def update_token_usage(
        self,
        state: WorkflowState,
        input_tokens: int,
        output_tokens: int
    ):
        """토큰 사용량 업데이트"""
        StateManager.update_token_usage(state, input_tokens, output_tokens)
    
    def log_progress(self, message: str, level: str = "info"):
        """진행 상황 로깅"""
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.name}] {message}")
    
    def should_continue(self, state: WorkflowState) -> bool:
        """계속 진행할지 여부 확인"""
        # 취소 상태 확인
        if state["status"] == "cancelled":
            self.log_progress("Workflow cancelled", "warning")
            return False
        
        # 최대 재시도 횟수 확인
        if state["retry_count"] >= 3:
            self.log_progress("Maximum retry attempts reached", "error")
            return False
        
        return True
    
    def get_previous_result(
        self,
        state: WorkflowState,
        node_name: str
    ) -> Optional[Dict[str, Any]]:
        """이전 노드 결과 가져오기"""
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
            return state.get(field_name)
        
        return None