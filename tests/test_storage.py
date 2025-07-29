"""
저장소 레이어 테스트
"""

import pytest
from uuid import uuid4
from datetime import datetime

from src.storage.models import Pipeline, AgentExecution, Artifact
from src.storage.repositories import PipelineRepository, AgentExecutionRepository
from src.core.schemas import PipelineStatus, TaskType


class TestPipelineRepository:
    """파이프라인 리포지토리 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_pipeline(self, db_session):
        """파이프라인 생성 테스트"""
        repo = PipelineRepository(db_session)
        
        pipeline = await repo.create(
            name="Test Pipeline",
            description="Test description",
            task_type=TaskType.FEATURE,
            metadata={"test": True}
        )
        
        assert pipeline.id is not None
        assert pipeline.name == "Test Pipeline"
        assert pipeline.status == PipelineStatus.PENDING
        assert pipeline.task_type == TaskType.FEATURE
        
    @pytest.mark.asyncio
    async def test_get_pipeline(self, db_session):
        """파이프라인 조회 테스트"""
        repo = PipelineRepository(db_session)
        
        # 파이프라인 생성
        created = await repo.create(
            name="Test Pipeline",
            task_type=TaskType.BUGFIX
        )
        
        # 조회
        pipeline = await repo.get(created.id)
        
        assert pipeline is not None
        assert pipeline.id == created.id
        assert pipeline.name == "Test Pipeline"
        
    @pytest.mark.asyncio
    async def test_update_pipeline(self, db_session):
        """파이프라인 업데이트 테스트"""
        repo = PipelineRepository(db_session)
        
        # 파이프라인 생성
        pipeline = await repo.create(
            name="Original Name",
            task_type=TaskType.FEATURE
        )
        
        # 업데이트
        updated = await repo.update(
            pipeline.id,
            name="Updated Name",
            status=PipelineStatus.IN_PROGRESS
        )
        
        assert updated.name == "Updated Name"
        assert updated.status == PipelineStatus.IN_PROGRESS
        
    @pytest.mark.asyncio
    async def test_list_pipelines(self, db_session):
        """파이프라인 목록 조회 테스트"""
        repo = PipelineRepository(db_session)
        
        # 여러 파이프라인 생성
        for i in range(5):
            await repo.create(
                name=f"Pipeline {i}",
                task_type=TaskType.FEATURE if i % 2 == 0 else TaskType.BUGFIX
            )
        
        # 전체 조회
        all_pipelines = await repo.list()
        assert len(all_pipelines) >= 5
        
        # 필터링 조회
        feature_pipelines = await repo.list(task_type=TaskType.FEATURE)
        assert all(p.task_type == TaskType.FEATURE for p in feature_pipelines)
        
        # 페이지네이션
        page1 = await repo.list(skip=0, limit=2)
        page2 = await repo.list(skip=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestAgentExecutionRepository:
    """에이전트 실행 리포지토리 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_execution(self, db_session):
        """에이전트 실행 생성 테스트"""
        # 먼저 파이프라인 생성
        pipeline_repo = PipelineRepository(db_session)
        pipeline = await pipeline_repo.create(
            name="Test Pipeline",
            task_type=TaskType.FEATURE
        )
        
        # 에이전트 실행 생성
        exec_repo = AgentExecutionRepository(db_session)
        execution = await exec_repo.create(
            pipeline_id=pipeline.id,
            agent_name="PlanningAgent",
            input_data={"requirements": "test"},
            status="running"
        )
        
        assert execution.id is not None
        assert execution.pipeline_id == pipeline.id
        assert execution.agent_name == "PlanningAgent"
        assert execution.status == "running"
        
    @pytest.mark.asyncio
    async def test_update_execution(self, db_session):
        """에이전트 실행 업데이트 테스트"""
        # 파이프라인 생성
        pipeline_repo = PipelineRepository(db_session)
        pipeline = await pipeline_repo.create(
            name="Test Pipeline",
            task_type=TaskType.FEATURE
        )
        
        # 실행 생성
        exec_repo = AgentExecutionRepository(db_session)
        execution = await exec_repo.create(
            pipeline_id=pipeline.id,
            agent_name="DevelopmentAgent",
            input_data={},
            status="running"
        )
        
        # 업데이트
        output_data = {"generated_files": ["main.py", "test.py"]}
        token_usage = {"input_tokens": 1000, "output_tokens": 500}
        
        updated = await exec_repo.update(
            execution.id,
            status="success",
            output_data=output_data,
            token_usage=token_usage,
            end_time=datetime.utcnow()
        )
        
        assert updated.status == "success"
        assert updated.output_data == output_data
        assert updated.token_usage == token_usage
        assert updated.end_time is not None


class TestCacheOperations:
    """캐시 작업 테스트"""
    
    @pytest.mark.asyncio
    async def test_redis_cache(self, redis_cleanup):
        """Redis 캐시 테스트"""
        from src.storage.cache import redis_client
        
        # 값 설정
        await redis_client.set("test_key", "test_value", ex=60)
        
        # 값 조회
        value = await redis_client.get("test_key")
        assert value == "test_value"
        
        # 삭제
        await redis_client.delete("test_key")
        value = await redis_client.get("test_key")
        assert value is None
        
    @pytest.mark.asyncio
    async def test_cache_json(self, redis_cleanup):
        """JSON 캐시 테스트"""
        from src.storage.cache import redis_client
        import json
        
        # JSON 데이터
        data = {
            "id": str(uuid4()),
            "name": "Test",
            "metadata": {"key": "value"}
        }
        
        # 저장
        await redis_client.set(
            "json_test",
            json.dumps(data),
            ex=60
        )
        
        # 조회
        cached = await redis_client.get("json_test")
        loaded = json.loads(cached)
        
        assert loaded["id"] == data["id"]
        assert loaded["name"] == data["name"]
        assert loaded["metadata"] == data["metadata"]