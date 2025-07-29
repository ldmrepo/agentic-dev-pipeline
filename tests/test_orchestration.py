"""
오케스트레이션 레이어 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.orchestration.state import WorkflowState, StateManager, TaskType
from src.orchestration.engine import WorkflowEngine
from src.orchestration.nodes.base import BaseNode
from src.orchestration.nodes.analyze import AnalyzeTaskNode
from src.core.schemas import PipelineStatus


class TestWorkflowState:
    """워크플로우 상태 테스트"""
    
    def test_state_initialization(self):
        """상태 초기화 테스트"""
        state = WorkflowState(
            pipeline_id="test-123",
            thread_id="thread-456",
            task_type=TaskType.FEATURE,
            status=PipelineStatus.PENDING,
            requirements="Create API"
        )
        
        assert state["pipeline_id"] == "test-123"
        assert state["task_type"] == TaskType.FEATURE
        assert state["status"] == PipelineStatus.PENDING
        assert state["messages"] == []
        
    def test_state_manager_operations(self):
        """상태 관리자 작업 테스트"""
        state = WorkflowState(
            pipeline_id="test-123",
            thread_id="thread-456"
        )
        
        # 메시지 추가
        from langchain_core.messages import AIMessage
        message = AIMessage(content="Test message")
        StateManager.add_message(state, message)
        
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "Test message"
        
        # 아티팩트 추가
        StateManager.add_artifact(
            state,
            name="test.py",
            type="code",
            content="print('hello')"
        )
        
        assert len(state["artifacts"]) == 1
        assert state["artifacts"][0]["name"] == "test.py"
        
        # 토큰 사용량 업데이트
        StateManager.update_token_usage(state, 100, 50)
        
        assert state["total_tokens"] == 150
        assert state["input_tokens"] == 100
        assert state["output_tokens"] == 50


class TestAnalyzeTaskNode:
    """태스크 분석 노드 테스트"""
    
    @pytest.mark.asyncio
    async def test_analyze_task_execution(self, sample_requirements):
        """태스크 분석 실행 테스트"""
        node = AnalyzeTaskNode()
        
        state = WorkflowState(
            pipeline_id="test-123",
            requirements=sample_requirements,
            context={"project_type": "api"}
        )
        
        # Claude 클라이언트 모킹
        with patch('src.orchestration.nodes.analyze.claude_client') as mock_client:
            mock_client.analyze = AsyncMock(return_value={
                "content": '''
                {
                    "task_type": "feature",
                    "complexity": "medium",
                    "technical_requirements": ["FastAPI", "PostgreSQL"],
                    "risks": [],
                    "estimated_hours": 40,
                    "required_expertise": ["Python", "API"],
                    "success_criteria": ["All endpoints working"]
                }
                '''
            })
            
            result = await node.execute(state)
            
            assert result["task_type"] == "feature"
            assert result["complexity"] == "medium"
            assert result["estimated_hours"] == 40
            assert len(result["technical_requirements"]) == 2


class TestWorkflowEngine:
    """워크플로우 엔진 테스트"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """엔진 초기화 테스트"""
        engine = WorkflowEngine()
        
        assert engine.graphs == {}
        assert engine.checkpointer is not None
        
    @pytest.mark.asyncio
    async def test_register_graph(self):
        """그래프 등록 테스트"""
        engine = WorkflowEngine()
        
        # 모의 그래프 생성
        from langgraph.graph import StateGraph
        graph = StateGraph(WorkflowState)
        graph.add_node("test", lambda x: x)
        graph.set_entry_point("test")
        
        # 등록
        engine.register_graph("test_graph", graph)
        
        assert "test_graph" in engine.graphs
        
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """워크플로우 실행 테스트"""
        engine = WorkflowEngine()
        
        # 간단한 워크플로우 생성
        from langgraph.graph import StateGraph, END
        
        async def simple_node(state):
            state["result"] = "executed"
            return state
            
        graph = StateGraph(dict)
        graph.add_node("simple", simple_node)
        graph.set_entry_point("simple")
        graph.add_edge("simple", END)
        
        compiled = await graph.acompile()
        engine.graphs["simple_workflow"] = compiled
        
        # 실행
        result = await engine.execute(
            "simple_workflow",
            {"initial": "data"}
        )
        
        assert result["result"] == "executed"


class TestBaseNode:
    """베이스 노드 테스트"""
    
    @pytest.mark.asyncio
    async def test_node_error_handling(self):
        """노드 에러 처리 테스트"""
        
        class TestNode(BaseNode):
            async def execute(self, state: WorkflowState) -> Dict[str, Any]:
                raise ValueError("Test error")
                
        node = TestNode("TestNode")
        state = WorkflowState(pipeline_id="test-123")
        
        with pytest.raises(Exception):
            await node.execute(state)
            
    @pytest.mark.asyncio
    async def test_node_helpers(self):
        """노드 헬퍼 메서드 테스트"""
        
        class TestNode(BaseNode):
            async def execute(self, state: WorkflowState) -> Dict[str, Any]:
                # 메시지 추가
                self.add_message(state, "Test message")
                
                # 아티팩트 추가
                self.add_artifact(
                    state,
                    name="result.txt",
                    type="text",
                    content="Test result"
                )
                
                # 토큰 사용량 업데이트
                self.update_token_usage(state, 50, 25)
                
                return {"status": "success"}
                
        node = TestNode("TestNode")
        state = WorkflowState(
            pipeline_id="test-123",
            messages=[],
            artifacts=[],
            total_tokens=0
        )
        
        result = await node.execute(state)
        
        assert result["status"] == "success"
        assert len(state["messages"]) == 1
        assert len(state["artifacts"]) == 1
        assert state["total_tokens"] == 75


class TestMainWorkflow:
    """메인 워크플로우 테스트"""
    
    @pytest.mark.asyncio
    async def test_route_after_analysis(self):
        """분석 후 라우팅 테스트"""
        from src.orchestration.graphs.main_workflow import route_after_analysis
        
        # Feature 태스크
        state = WorkflowState(
            task_type=TaskType.FEATURE,
            analysis_result={"complexity": "high"}
        )
        
        route = route_after_analysis(state)
        assert route == "planning"
        
        # Hotfix 태스크
        state["task_type"] = TaskType.HOTFIX
        route = route_after_analysis(state)
        assert route == "hotfix"
        
        # Documentation 태스크
        state["task_type"] = TaskType.DOCUMENTATION
        route = route_after_analysis(state)
        assert route == "review"
        
    @pytest.mark.asyncio
    async def test_route_after_review(self):
        """리뷰 후 라우팅 테스트"""
        from src.orchestration.graphs.main_workflow import route_after_review
        
        # 승인된 경우
        state = WorkflowState(
            task_type=TaskType.FEATURE,
            review_result={"approved": True}
        )
        
        route = route_after_review(state)
        assert route == "deployment"
        
        # 재작업 필요
        state["review_result"] = {
            "approved": False,
            "needs_rework": True
        }
        state["retry_count"] = 0
        
        route = route_after_review(state)
        assert route == "rework"
        
        # 최대 재시도 초과
        state["retry_count"] = 3
        route = route_after_review(state)
        assert route == "end"