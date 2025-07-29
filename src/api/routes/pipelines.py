"""
파이프라인 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from src.api.schemas import (
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
    PipelineExecuteRequest,
    PipelineListResponse
)
from src.storage.repositories import PipelineRepository
from src.storage.database import get_db_session
from src.orchestration.engine import WorkflowEngine
from src.core.schemas import TaskType, PipelineStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# 워크플로우 엔진 인스턴스
workflow_engine = WorkflowEngine()


@router.post("", response_model=PipelineResponse)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    background_tasks: BackgroundTasks,
    session=Depends(get_db_session)
) -> PipelineResponse:
    """새 파이프라인 생성 및 실행"""
    try:
        # 파이프라인 레포지토리
        repo = PipelineRepository(session)
        
        # 파이프라인 생성
        pipeline = await repo.create(
            name=pipeline_data.name,
            description=pipeline_data.description,
            task_type=pipeline_data.task_type,
            metadata=pipeline_data.metadata
        )
        
        # 백그라운드에서 워크플로우 실행
        if pipeline_data.auto_execute:
            background_tasks.add_task(
                execute_pipeline_workflow,
                pipeline.id,
                pipeline_data.requirements,
                pipeline_data.context
            )
            
        return PipelineResponse.from_orm(pipeline)
        
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PipelineListResponse)
async def list_pipelines(
    skip: int = 0,
    limit: int = 20,
    status: Optional[PipelineStatus] = None,
    task_type: Optional[TaskType] = None,
    session=Depends(get_db_session)
) -> PipelineListResponse:
    """파이프라인 목록 조회"""
    try:
        repo = PipelineRepository(session)
        
        # 필터 조건 구성
        filters = {}
        if status:
            filters["status"] = status
        if task_type:
            filters["task_type"] = task_type
            
        # 파이프라인 조회
        pipelines = await repo.list(
            skip=skip,
            limit=limit,
            **filters
        )
        
        # 전체 개수 조회
        total = await repo.count(**filters)
        
        return PipelineListResponse(
            pipelines=[PipelineResponse.from_orm(p) for p in pipelines],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: UUID,
    session=Depends(get_db_session)
) -> PipelineResponse:
    """특정 파이프라인 조회"""
    try:
        repo = PipelineRepository(session)
        pipeline = await repo.get(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        return PipelineResponse.from_orm(pipeline)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    update_data: PipelineUpdate,
    session=Depends(get_db_session)
) -> PipelineResponse:
    """파이프라인 업데이트"""
    try:
        repo = PipelineRepository(session)
        
        # 업데이트 데이터 준비
        update_dict = update_data.dict(exclude_unset=True)
        
        # 파이프라인 업데이트
        pipeline = await repo.update(pipeline_id, **update_dict)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        return PipelineResponse.from_orm(pipeline)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: UUID,
    request: PipelineExecuteRequest,
    background_tasks: BackgroundTasks,
    session=Depends(get_db_session)
) -> Dict[str, Any]:
    """파이프라인 실행"""
    try:
        repo = PipelineRepository(session)
        pipeline = await repo.get(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        # 이미 실행 중인지 확인
        if pipeline.status in [PipelineStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=400,
                detail="Pipeline is already running"
            )
            
        # 백그라운드에서 실행
        background_tasks.add_task(
            execute_pipeline_workflow,
            pipeline_id,
            request.requirements or pipeline.requirements,
            request.context or {}
        )
        
        return {
            "status": "started",
            "pipeline_id": str(pipeline_id),
            "message": "Pipeline execution started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/cancel")
async def cancel_pipeline(
    pipeline_id: UUID,
    session=Depends(get_db_session)
) -> Dict[str, Any]:
    """파이프라인 취소"""
    try:
        repo = PipelineRepository(session)
        pipeline = await repo.get(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        # 실행 중이 아니면 취소 불가
        if pipeline.status not in [PipelineStatus.IN_PROGRESS, PipelineStatus.PENDING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel pipeline in {pipeline.status} status"
            )
            
        # 상태 업데이트
        await repo.update(
            pipeline_id,
            status=PipelineStatus.CANCELLED
        )
        
        # 워크플로우 엔진에서 취소
        await workflow_engine.cancel(str(pipeline_id))
        
        return {
            "status": "cancelled",
            "pipeline_id": str(pipeline_id),
            "message": "Pipeline execution cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}/artifacts")
async def get_pipeline_artifacts(
    pipeline_id: UUID,
    artifact_type: Optional[str] = None,
    session=Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """파이프라인 아티팩트 조회"""
    try:
        repo = PipelineRepository(session)
        pipeline = await repo.get(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        # 아티팩트 필터링
        artifacts = pipeline.artifacts
        if artifact_type:
            artifacts = [a for a in artifacts if a.type == artifact_type]
            
        return [
            {
                "id": str(a.id),
                "name": a.name,
                "type": a.type,
                "path": a.path,
                "size": a.metadata.get("size", 0),
                "created_at": a.created_at.isoformat()
            }
            for a in artifacts
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}/logs")
async def get_pipeline_logs(
    pipeline_id: UUID,
    agent: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    session=Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """파이프라인 로그 조회"""
    try:
        repo = PipelineRepository(session)
        pipeline = await repo.get(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
            
        # 로그 필터링 (실제로는 로그 저장소에서 조회)
        logs = []
        for execution in pipeline.executions:
            if agent and execution.agent_name != agent:
                continue
                
            log_entries = execution.logs or []
            if level:
                log_entries = [l for l in log_entries if l.get("level") == level]
                
            logs.extend(log_entries[:limit])
            
        return logs[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_pipeline_workflow(
    pipeline_id: UUID,
    requirements: str,
    context: Dict[str, Any]
):
    """백그라운드에서 파이프라인 워크플로우 실행"""
    try:
        logger.info(f"Starting workflow execution for pipeline {pipeline_id}")
        
        # 워크플로우 입력 데이터 구성
        input_data = {
            "pipeline_id": str(pipeline_id),
            "requirements": requirements,
            "context": context,
            "task_type": context.get("task_type", TaskType.FEATURE)
        }
        
        # 워크플로우 실행
        result = await workflow_engine.execute(
            graph_name="main_workflow",
            input_data=input_data
        )
        
        logger.info(f"Workflow execution completed for pipeline {pipeline_id}")
        
    except Exception as e:
        logger.error(f"Workflow execution failed for pipeline {pipeline_id}: {e}")
        
        # 파이프라인 상태를 실패로 업데이트
        async with get_db_session() as session:
            repo = PipelineRepository(session)
            await repo.update(
                pipeline_id,
                status=PipelineStatus.FAILED,
                error_message=str(e)
            )