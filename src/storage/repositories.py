"""
구체적인 리포지토리 구현
각 모델에 특화된 쿼리 메서드 제공
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from src.storage.base import BaseRepository
from src.storage.models import (
    Pipeline, AgentExecution, Artifact, WorkflowState,
    Tag, APIKey, AuditLog, Metric, DeploymentHistory
)
from src.core.schemas import (
    PipelineCreate, PipelineUpdate,
    AgentExecutionCreate, AgentExecutionResponse,
    ArtifactCreate, ArtifactResponse
)
from src.core.constants import PipelineStatus, AgentType, ArtifactType
from src.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class PipelineRepository(BaseRepository[Pipeline, PipelineCreate, PipelineUpdate]):
    """파이프라인 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(Pipeline, db)
    
    def get_with_executions(self, pipeline_id: UUID) -> Optional[Pipeline]:
        """실행 정보와 함께 파이프라인 조회"""
        return self.db.query(Pipeline)\
            .options(joinedload(Pipeline.executions))\
            .filter(Pipeline.id == pipeline_id)\
            .first()
    
    def get_active_pipelines(self) -> List[Pipeline]:
        """활성 파이프라인 목록 조회"""
        return self.db.query(Pipeline)\
            .filter(Pipeline.status.in_([
                PipelineStatus.RUNNING,
                PipelineStatus.PENDING,
                PipelineStatus.ANALYZING,
                PipelineStatus.PLANNING,
                PipelineStatus.DEVELOPING,
                PipelineStatus.TESTING,
                PipelineStatus.DEPLOYING
            ]))\
            .all()
    
    def get_by_status(self, status: PipelineStatus, limit: int = 100) -> List[Pipeline]:
        """상태별 파이프라인 조회"""
        return self.db.query(Pipeline)\
            .filter(Pipeline.status == status)\
            .order_by(Pipeline.created_at.desc())\
            .limit(limit)\
            .all()
    
    def get_recent_pipelines(self, hours: int = 24, limit: int = 100) -> List[Pipeline]:
        """최근 파이프라인 조회"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Pipeline)\
            .filter(Pipeline.created_at >= since)\
            .order_by(Pipeline.created_at.desc())\
            .limit(limit)\
            .all()
    
    def update_status(self, pipeline_id: UUID, status: PipelineStatus, error_message: Optional[str] = None) -> Pipeline:
        """파이프라인 상태 업데이트"""
        pipeline = self.get_or_404(pipeline_id)
        pipeline.status = status
        
        if error_message:
            pipeline.error_message = error_message
        
        # 시작/완료 시간 업데이트
        if status == PipelineStatus.RUNNING and not pipeline.started_at:
            pipeline.started_at = datetime.utcnow()
        elif status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
            pipeline.completed_at = datetime.utcnow()
            if pipeline.started_at:
                pipeline.execution_time = int((pipeline.completed_at - pipeline.started_at).total_seconds() * 1000)
        
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """파이프라인 통계 조회"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # 상태별 개수
        status_counts = self.db.query(
            Pipeline.status,
            func.count(Pipeline.id).label('count')
        ).filter(
            Pipeline.created_at >= since
        ).group_by(Pipeline.status).all()
        
        # 평균 실행 시간
        avg_execution_time = self.db.query(
            func.avg(Pipeline.execution_time)
        ).filter(
            and_(
                Pipeline.created_at >= since,
                Pipeline.execution_time.isnot(None)
            )
        ).scalar()
        
        # 성공률
        total = self.db.query(func.count(Pipeline.id)).filter(
            and_(
                Pipeline.created_at >= since,
                Pipeline.status.in_([PipelineStatus.COMPLETED, PipelineStatus.FAILED])
            )
        ).scalar()
        
        success = self.db.query(func.count(Pipeline.id)).filter(
            and_(
                Pipeline.created_at >= since,
                Pipeline.status == PipelineStatus.COMPLETED
            )
        ).scalar()
        
        return {
            "status_distribution": {str(status): count for status, count in status_counts},
            "average_execution_time_ms": avg_execution_time or 0,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "total_pipelines": total or 0
        }

class AgentExecutionRepository(BaseRepository[AgentExecution, AgentExecutionCreate, Dict[str, Any]]):
    """에이전트 실행 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(AgentExecution, db)
    
    def get_by_pipeline(self, pipeline_id: UUID) -> List[AgentExecution]:
        """파이프라인별 실행 목록 조회"""
        return self.db.query(AgentExecution)\
            .filter(AgentExecution.pipeline_id == pipeline_id)\
            .order_by(AgentExecution.created_at.asc())\
            .all()
    
    def get_latest_by_type(self, pipeline_id: UUID, agent_type: AgentType) -> Optional[AgentExecution]:
        """특정 타입의 최신 실행 조회"""
        return self.db.query(AgentExecution)\
            .filter(
                and_(
                    AgentExecution.pipeline_id == pipeline_id,
                    AgentExecution.agent_type == agent_type
                )
            )\
            .order_by(AgentExecution.created_at.desc())\
            .first()
    
    def update_status(
        self,
        execution_id: UUID,
        status: PipelineStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> AgentExecution:
        """실행 상태 업데이트"""
        execution = self.get_or_404(execution_id)
        execution.status = status
        
        if output_data:
            execution.output_data = output_data
        if error_message:
            execution.error_message = error_message
        if token_usage:
            execution.input_tokens = token_usage.get('input_tokens', 0)
            execution.output_tokens = token_usage.get('output_tokens', 0)
        
        # 시작/완료 시간 업데이트
        if status == PipelineStatus.RUNNING and not execution.started_at:
            execution.started_at = datetime.utcnow()
        elif status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.execution_time = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def get_agent_statistics(self, agent_type: Optional[AgentType] = None, days: int = 7) -> Dict[str, Any]:
        """에이전트 실행 통계"""
        since = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(AgentExecution).filter(AgentExecution.created_at >= since)
        if agent_type:
            query = query.filter(AgentExecution.agent_type == agent_type)
        
        executions = query.all()
        
        # 통계 계산
        total = len(executions)
        success = sum(1 for e in executions if e.status == PipelineStatus.COMPLETED)
        failed = sum(1 for e in executions if e.status == PipelineStatus.FAILED)
        
        execution_times = [e.execution_time for e in executions if e.execution_time]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        total_tokens = sum(e.input_tokens + e.output_tokens for e in executions)
        
        return {
            "total_executions": total,
            "successful_executions": success,
            "failed_executions": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "average_execution_time_ms": avg_execution_time,
            "total_tokens_used": total_tokens
        }

class ArtifactRepository(BaseRepository[Artifact, ArtifactCreate, Dict[str, Any]]):
    """아티팩트 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(Artifact, db)
    
    def get_by_pipeline(self, pipeline_id: UUID, artifact_type: Optional[ArtifactType] = None) -> List[Artifact]:
        """파이프라인별 아티팩트 조회"""
        query = self.db.query(Artifact).filter(Artifact.pipeline_id == pipeline_id)
        
        if artifact_type:
            query = query.filter(Artifact.type == artifact_type)
        
        return query.order_by(Artifact.created_at.desc()).all()
    
    def get_by_execution(self, execution_id: UUID) -> List[Artifact]:
        """실행별 아티팩트 조회"""
        return self.db.query(Artifact)\
            .filter(Artifact.execution_id == execution_id)\
            .order_by(Artifact.created_at.desc())\
            .all()
    
    def get_by_name_and_type(self, pipeline_id: UUID, name: str, artifact_type: ArtifactType) -> Optional[Artifact]:
        """이름과 타입으로 아티팩트 조회"""
        return self.db.query(Artifact)\
            .filter(
                and_(
                    Artifact.pipeline_id == pipeline_id,
                    Artifact.name == name,
                    Artifact.type == artifact_type
                )
            )\
            .first()
    
    def get_latest_by_type(self, pipeline_id: UUID, artifact_type: ArtifactType) -> Optional[Artifact]:
        """특정 타입의 최신 아티팩트 조회"""
        return self.db.query(Artifact)\
            .filter(
                and_(
                    Artifact.pipeline_id == pipeline_id,
                    Artifact.type == artifact_type
                )
            )\
            .order_by(Artifact.created_at.desc())\
            .first()
    
    def get_total_size(self, pipeline_id: Optional[UUID] = None) -> int:
        """전체 아티팩트 크기 조회"""
        query = self.db.query(func.sum(Artifact.size))
        
        if pipeline_id:
            query = query.filter(Artifact.pipeline_id == pipeline_id)
        
        return query.scalar() or 0

class WorkflowStateRepository(BaseRepository[WorkflowState, Dict[str, Any], Dict[str, Any]]):
    """워크플로우 상태 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(WorkflowState, db)
    
    def get_latest_checkpoint(self, thread_id: str) -> Optional[WorkflowState]:
        """최신 체크포인트 조회"""
        return self.db.query(WorkflowState)\
            .filter(WorkflowState.thread_id == thread_id)\
            .order_by(WorkflowState.created_at.desc())\
            .first()
    
    def get_checkpoints(self, thread_id: str, limit: int = 10) -> List[WorkflowState]:
        """체크포인트 목록 조회"""
        return self.db.query(WorkflowState)\
            .filter(WorkflowState.thread_id == thread_id)\
            .order_by(WorkflowState.created_at.desc())\
            .limit(limit)\
            .all()
    
    def save_checkpoint(self, thread_id: str, checkpoint_id: str, state: Dict[str, Any], parent_id: Optional[str] = None) -> WorkflowState:
        """체크포인트 저장"""
        checkpoint = WorkflowState(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            parent_id=parent_id,
            state=state,
            metadata={}
        )
        
        self.db.add(checkpoint)
        self.db.commit()
        self.db.refresh(checkpoint)
        
        return checkpoint
    
    def cleanup_old_checkpoints(self, days: int = 30) -> int:
        """오래된 체크포인트 정리"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.db.query(WorkflowState)\
            .filter(WorkflowState.created_at < cutoff)\
            .delete()
        
        self.db.commit()
        return deleted

class TagRepository(BaseRepository[Tag, Dict[str, Any], Dict[str, Any]]):
    """태그 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(Tag, db)
    
    def get_by_name(self, name: str) -> Optional[Tag]:
        """이름으로 태그 조회"""
        return self.db.query(Tag).filter(Tag.name == name).first()
    
    def get_or_create(self, name: str, color: Optional[str] = None) -> Tag:
        """태그 조회 또는 생성"""
        tag = self.get_by_name(name)
        if not tag:
            tag = Tag(name=name, color=color)
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
        return tag
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 태그 조회"""
        results = self.db.query(
            Tag.name,
            Tag.color,
            func.count(Pipeline.id).label('usage_count')
        ).join(
            Pipeline.tags
        ).group_by(
            Tag.name, Tag.color
        ).order_by(
            func.count(Pipeline.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "name": name,
                "color": color,
                "usage_count": count
            }
            for name, color, count in results
        ]

class MetricRepository(BaseRepository[Metric, Dict[str, Any], Dict[str, Any]]):
    """메트릭 리포지토리"""
    
    def __init__(self, db: Session):
        super().__init__(Metric, db)
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """메트릭 기록"""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            labels=labels or {}
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        
        return metric
    
    def get_metrics(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Metric]:
        """메트릭 조회"""
        query = self.db.query(Metric).filter(Metric.name == name)
        
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        # 레이블 필터링 (JSON 필드)
        if labels:
            for key, value in labels.items():
                query = query.filter(Metric.labels[key].astext == value)
        
        return query.order_by(Metric.timestamp.desc()).all()
    
    def aggregate_metrics(
        self,
        name: str,
        aggregation: str = "avg",  # avg, sum, min, max
        interval: str = "hour",     # minute, hour, day
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """메트릭 집계"""
        # 시간 간격 설정
        if interval == "minute":
            date_trunc = func.date_trunc('minute', Metric.timestamp)
        elif interval == "hour":
            date_trunc = func.date_trunc('hour', Metric.timestamp)
        else:
            date_trunc = func.date_trunc('day', Metric.timestamp)
        
        # 집계 함수 설정
        if aggregation == "sum":
            agg_func = func.sum(Metric.value)
        elif aggregation == "min":
            agg_func = func.min(Metric.value)
        elif aggregation == "max":
            agg_func = func.max(Metric.value)
        else:
            agg_func = func.avg(Metric.value)
        
        query = self.db.query(
            date_trunc.label('timestamp'),
            agg_func.label('value'),
            func.count(Metric.id).label('count')
        ).filter(Metric.name == name)
        
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        results = query.group_by(date_trunc).order_by(date_trunc).all()
        
        return [
            {
                "timestamp": timestamp,
                "value": value,
                "count": count
            }
            for timestamp, value, count in results
        ]