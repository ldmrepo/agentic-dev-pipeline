"""
워크플로우 엔진
LangGraph 기반 워크플로우 엔진
"""

from typing import Dict, Any, Optional, List, AsyncGenerator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import logging
from contextlib import asynccontextmanager

from src.core.config import get_settings
from src.orchestration.state import WorkflowState, StateManager, PipelineStatus
from src.storage.database import get_async_session
from src.core.exceptions import WorkflowExecutionError

logger = logging.getLogger(__name__)
settings = get_settings()


class WorkflowEngine:
    """LangGraph 기반 워크플로우 엔진"""
    
    def __init__(self):
        self.graphs: Dict[str, StateGraph] = {}
        self.compiled_graphs: Dict[str, Any] = {}
        self.checkpointer = None
        self._initialize_checkpointer()
    
    def _initialize_checkpointer(self):
        """체크포인터 초기화"""
        if settings.environment == "development":
            # 개발 환경에서는 메모리 체크포인터 사용
            self.checkpointer = MemorySaver()
        else:
            # 프로덕션 환경에서는 PostgreSQL 체크포인터 사용
            # AsyncPostgresSaver는 비동기 초기화가 필요하므로 나중에 설정
            self.checkpointer = None
    
    async def initialize_postgres_checkpointer(self):
        """PostgreSQL 체크포인터 비동기 초기화"""
        if settings.environment != "development" and self.checkpointer is None:
            try:
                self.checkpointer = await AsyncPostgresSaver.from_conn_string(
                    settings.database_url
                )
                await self.checkpointer.setup()
                logger.info("PostgreSQL checkpointer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL checkpointer: {e}")
                # 폴백으로 메모리 체크포인터 사용
                self.checkpointer = MemorySaver()
                logger.warning("Falling back to memory checkpointer")
    
    def register_graph(self, name: str, graph: StateGraph):
        """그래프 등록"""
        self.graphs[name] = graph
        
        # 그래프 컴파일
        if self.checkpointer:
            compiled = graph.compile(checkpointer=self.checkpointer)
        else:
            compiled = graph.compile()
        
        self.compiled_graphs[name] = compiled
        logger.info(f"Graph '{name}' registered and compiled successfully")
    
    async def execute(
        self,
        graph_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """워크플로우 실행"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.compiled_graphs[graph_name]
        
        # 기본 설정
        if config is None:
            config = {}
        
        # thread_id 생성
        if "configurable" not in config:
            config["configurable"] = {}
        if "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = f"{graph_name}-{asyncio.get_event_loop().time()}"
        
        try:
            # 상태 초기화
            state = input_data
            StateManager.update_status(state, PipelineStatus.RUNNING)
            
            # 비동기 실행
            result = await graph.ainvoke(state, config)
            
            # 실행 완료
            StateManager.update_status(result, PipelineStatus.COMPLETED)
            result["execution_time"] = StateManager.calculate_execution_time(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            
            # 상태 업데이트
            if "state" in locals():
                StateManager.update_status(state, PipelineStatus.FAILED)
                StateManager.add_error(
                    state,
                    state.get("current_node", "unknown"),
                    str(e)
                )
            
            raise WorkflowExecutionError(f"Workflow execution failed: {str(e)}")
    
    async def stream(
        self,
        graph_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """워크플로우 스트리밍 실행"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        graph = self.compiled_graphs[graph_name]
        
        # 기본 설정
        if config is None:
            config = {}
        
        # thread_id 생성
        if "configurable" not in config:
            config["configurable"] = {}
        if "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = f"{graph_name}-{asyncio.get_event_loop().time()}"
        
        try:
            # 상태 초기화
            state = input_data
            StateManager.update_status(state, PipelineStatus.RUNNING)
            
            # 스트리밍 실행
            async for chunk in graph.astream(state, config):
                # 각 노드 실행 결과를 스트리밍
                if "__end__" not in chunk:
                    node_name = list(chunk.keys())[0]
                    node_result = chunk[node_name]
                    
                    # 현재 노드 설정
                    StateManager.set_current_node(state, node_name)
                    
                    # 진행률 계산
                    progress = StateManager.get_progress_percentage(node_result)
                    
                    yield {
                        "node": node_name,
                        "result": node_result,
                        "progress": progress,
                        "timestamp": asyncio.get_event_loop().time()
                    }
            
            # 실행 완료
            StateManager.update_status(state, PipelineStatus.COMPLETED)
            
        except Exception as e:
            logger.error(f"Workflow streaming failed: {str(e)}")
            StateManager.update_status(state, PipelineStatus.FAILED)
            StateManager.add_error(
                state,
                state.get("current_node", "unknown"),
                str(e)
            )
            raise
    
    async def get_state(
        self,
        graph_name: str,
        thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """워크플로우 상태 조회"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        if not self.checkpointer:
            logger.warning("No checkpointer available, cannot retrieve state")
            return None
        
        graph = self.compiled_graphs[graph_name]
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            state = await graph.aget_state(config)
            return state.values if state else None
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None
    
    async def update_state(
        self,
        graph_name: str,
        thread_id: str,
        updates: Dict[str, Any],
        as_node: Optional[str] = None
    ):
        """워크플로우 상태 업데이트"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        if not self.checkpointer:
            raise ValueError("No checkpointer available, cannot update state")
        
        graph = self.compiled_graphs[graph_name]
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            await graph.aupdate_state(config, updates, as_node=as_node)
            logger.info(f"State updated for thread {thread_id}")
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            raise
    
    async def get_state_history(
        self,
        graph_name: str,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """워크플로우 상태 히스토리 조회"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        if not self.checkpointer:
            logger.warning("No checkpointer available, cannot retrieve history")
            return []
        
        graph = self.compiled_graphs[graph_name]
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            history = []
            async for state in graph.aget_state_history(config):
                history.append(state.values)
                if limit and len(history) >= limit:
                    break
            
            return history
        except Exception as e:
            logger.error(f"Failed to get state history: {e}")
            return []
    
    async def cancel_workflow(
        self,
        graph_name: str,
        thread_id: str
    ):
        """워크플로우 취소"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        # 현재 상태 조회
        state = await self.get_state(graph_name, thread_id)
        if not state:
            raise ValueError(f"No state found for thread {thread_id}")
        
        # 상태를 CANCELLED로 업데이트
        state["status"] = PipelineStatus.CANCELLED
        state["updated_at"] = asyncio.get_event_loop().time()
        
        await self.update_state(graph_name, thread_id, state)
        logger.info(f"Workflow cancelled for thread {thread_id}")
    
    async def retry_workflow(
        self,
        graph_name: str,
        thread_id: str,
        from_node: Optional[str] = None
    ) -> Dict[str, Any]:
        """워크플로우 재시도"""
        if graph_name not in self.compiled_graphs:
            raise ValueError(f"Unknown graph: {graph_name}")
        
        # 현재 상태 조회
        state = await self.get_state(graph_name, thread_id)
        if not state:
            raise ValueError(f"No state found for thread {thread_id}")
        
        # 재시도 가능 여부 확인
        if not StateManager.should_retry(state):
            raise ValueError("Maximum retry attempts reached")
        
        # 재시도 카운트 증가
        state["retry_count"] += 1
        state["status"] = PipelineStatus.RUNNING
        state["errors"] = []  # 에러 초기화
        
        # 특정 노드부터 재시작
        if from_node:
            state["current_node"] = from_node
        
        # 재실행
        config = {"configurable": {"thread_id": thread_id}}
        return await self.execute(graph_name, state, config)
    
    async def cleanup(self):
        """리소스 정리"""
        if hasattr(self.checkpointer, 'aclose'):
            await self.checkpointer.aclose()
        
        self.graphs.clear()
        self.compiled_graphs.clear()
        
        logger.info("Workflow engine cleaned up")


# 싱글톤 인스턴스
workflow_engine = WorkflowEngine()


@asynccontextmanager
async def get_workflow_engine():
    """워크플로우 엔진 컨텍스트 매니저"""
    # PostgreSQL 체크포인터 초기화
    await workflow_engine.initialize_postgres_checkpointer()
    
    try:
        yield workflow_engine
    finally:
        # 정리 작업은 애플리케이션 종료 시에만 수행
        pass