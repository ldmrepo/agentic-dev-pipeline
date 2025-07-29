"""
API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
import json

from src.api.main import app
from src.api.schemas import PipelineCreate, PipelineResponse
from src.core.schemas import TaskType, PipelineStatus


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


class TestHealthEndpoints:
    """헬스체크 엔드포인트 테스트"""
    
    def test_basic_health_check(self, client):
        """기본 헬스체크 테스트"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        
    def test_detailed_health_check(self, client):
        """상세 헬스체크 테스트"""
        # 데이터베이스와 Redis 모킹
        with patch('src.api.routes.health.get_db_session') as mock_db:
            with patch('src.api.routes.health.redis_client') as mock_redis:
                mock_db.return_value.__aenter__.return_value.execute = AsyncMock()
                mock_redis.ping = AsyncMock()
                
                response = client.get("/health/detailed")
                
                assert response.status_code == 200
                data = response.json()
                assert "components" in data
                assert "system" in data


class TestPipelineEndpoints:
    """파이프라인 엔드포인트 테스트"""
    
    def test_create_pipeline(self, client):
        """파이프라인 생성 테스트"""
        # Repository 모킹
        with patch('src.api.routes.pipelines.PipelineRepository') as mock_repo:
            mock_pipeline = MagicMock()
            mock_pipeline.id = uuid4()
            mock_pipeline.name = "Test Pipeline"
            mock_pipeline.status = PipelineStatus.PENDING
            mock_pipeline.task_type = TaskType.FEATURE
            mock_pipeline.created_at = "2025-01-01T00:00:00"
            mock_pipeline.updated_at = "2025-01-01T00:00:00"
            
            mock_repo.return_value.create = AsyncMock(return_value=mock_pipeline)
            
            # WorkflowEngine 모킹
            with patch('src.api.routes.pipelines.execute_pipeline_workflow'):
                payload = {
                    "name": "Test Pipeline",
                    "description": "Test description",
                    "task_type": "feature",
                    "requirements": "Create API",
                    "auto_execute": True
                }
                
                response = client.post("/api/v1/pipelines", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Test Pipeline"
                assert data["status"] == "pending"
                
    def test_list_pipelines(self, client):
        """파이프라인 목록 조회 테스트"""
        with patch('src.api.routes.pipelines.PipelineRepository') as mock_repo:
            mock_pipelines = []
            for i in range(3):
                pipeline = MagicMock()
                pipeline.id = uuid4()
                pipeline.name = f"Pipeline {i}"
                pipeline.status = PipelineStatus.COMPLETED
                pipeline.task_type = TaskType.FEATURE
                pipeline.created_at = "2025-01-01T00:00:00"
                pipeline.updated_at = "2025-01-01T00:00:00"
                mock_pipelines.append(pipeline)
                
            mock_repo.return_value.list = AsyncMock(return_value=mock_pipelines)
            mock_repo.return_value.count = AsyncMock(return_value=3)
            
            response = client.get("/api/v1/pipelines")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert len(data["pipelines"]) == 3
            
    def test_get_pipeline(self, client):
        """특정 파이프라인 조회 테스트"""
        pipeline_id = uuid4()
        
        with patch('src.api.routes.pipelines.PipelineRepository') as mock_repo:
            mock_pipeline = MagicMock()
            mock_pipeline.id = pipeline_id
            mock_pipeline.name = "Test Pipeline"
            mock_pipeline.status = PipelineStatus.IN_PROGRESS
            mock_pipeline.task_type = TaskType.BUGFIX
            mock_pipeline.created_at = "2025-01-01T00:00:00"
            mock_pipeline.updated_at = "2025-01-01T00:00:00"
            
            mock_repo.return_value.get = AsyncMock(return_value=mock_pipeline)
            
            response = client.get(f"/api/v1/pipelines/{pipeline_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(pipeline_id)
            assert data["status"] == "in_progress"
            
    def test_execute_pipeline(self, client):
        """파이프라인 실행 테스트"""
        pipeline_id = uuid4()
        
        with patch('src.api.routes.pipelines.PipelineRepository') as mock_repo:
            mock_pipeline = MagicMock()
            mock_pipeline.id = pipeline_id
            mock_pipeline.status = PipelineStatus.COMPLETED
            
            mock_repo.return_value.get = AsyncMock(return_value=mock_pipeline)
            
            with patch('src.api.routes.pipelines.execute_pipeline_workflow'):
                payload = {
                    "requirements": "Updated requirements",
                    "context": {"priority": "high"}
                }
                
                response = client.post(
                    f"/api/v1/pipelines/{pipeline_id}/execute",
                    json=payload
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "started"
                assert data["pipeline_id"] == str(pipeline_id)


class TestAgentEndpoints:
    """에이전트 엔드포인트 테스트"""
    
    def test_get_agents_status(self, client):
        """에이전트 상태 조회 테스트"""
        response = client.get("/api/v1/agents/status")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # 5개 에이전트
        
        agent_names = [agent["name"] for agent in data]
        assert "PlanningAgent" in agent_names
        assert "DevelopmentAgent" in agent_names
        
    def test_get_agent_metrics(self, client):
        """에이전트 메트릭 조회 테스트"""
        with patch('src.api.routes.agents.AgentExecutionRepository') as mock_repo:
            mock_executions = []
            for i in range(5):
                execution = MagicMock()
                execution.status = "success" if i < 4 else "failed"
                execution.start_time = "2025-01-01T00:00:00"
                execution.end_time = "2025-01-01T01:00:00"
                execution.token_usage = {"total_tokens": 1000}
                mock_executions.append(execution)
                
            mock_repo.return_value.list = AsyncMock(return_value=mock_executions)
            
            response = client.get("/api/v1/agents/metrics?period=24h")
            
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "24h"
            assert "metrics" in data


class TestWebSocketEndpoint:
    """WebSocket 엔드포인트 테스트"""
    
    def test_websocket_connection(self, client):
        """WebSocket 연결 테스트"""
        with patch('src.api.main.WebSocketManager') as mock_ws_manager:
            mock_manager = MagicMock()
            mock_ws_manager.return_value = mock_manager
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = MagicMock()
            
            with client.websocket_connect("/ws/test-client") as websocket:
                # 연결 확인
                websocket.send_json({"action": "ping"})
                
                # Mock 응답 설정
                mock_manager.subscribe_to_pipeline = AsyncMock()
                
                # 구독 테스트
                websocket.send_json({
                    "action": "subscribe",
                    "pipeline_id": str(uuid4())
                })


class TestErrorHandling:
    """에러 처리 테스트"""
    
    def test_404_error(self, client):
        """404 에러 테스트"""
        response = client.get("/api/v1/pipelines/invalid-uuid")
        assert response.status_code == 422  # UUID 형식 오류
        
    def test_validation_error(self, client):
        """유효성 검증 에러 테스트"""
        # 잘못된 task_type
        payload = {
            "name": "Test",
            "task_type": "invalid_type"
        }
        
        response = client.post("/api/v1/pipelines", json=payload)
        assert response.status_code == 422