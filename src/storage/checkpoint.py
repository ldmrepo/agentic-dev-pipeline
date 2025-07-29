"""
LangGraph 체크포인트 저장소
PostgreSQL 기반 체크포인트 영속성
"""

import logging
import json
from typing import Optional, Sequence, Tuple, Dict, Any
from datetime import datetime
import uuid

from langgraph.checkpoint import BaseCheckpointSaver, Checkpoint
from langgraph.checkpoint.base import CheckpointTuple, CheckpointMetadata, ChannelValues
from sqlalchemy.orm import Session

from src.storage.models import WorkflowState
from src.storage.repositories import WorkflowStateRepository
from src.storage.database import get_db_session
from src.core.exceptions import CheckpointError

logger = logging.getLogger(__name__)

class PostgreSQLCheckpointSaver(BaseCheckpointSaver):
    """PostgreSQL 기반 체크포인트 저장소"""
    
    def __init__(self, db_session_factory=None):
        """
        Args:
            db_session_factory: 데이터베이스 세션 팩토리 함수
        """
        super().__init__()
        self.db_session_factory = db_session_factory or get_db_session
        self.logger = logging.getLogger(f"{__name__}.PostgreSQLCheckpointSaver")
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelValues,
    ) -> Dict[str, Any]:
        """체크포인트 저장
        
        Args:
            config: 설정 정보 (thread_id 포함)
            checkpoint: 체크포인트 데이터
            metadata: 체크포인트 메타데이터
            new_versions: 채널 버전 정보
            
        Returns:
            업데이트된 설정
        """
        try:
            with self.db_session_factory() as db:
                repo = WorkflowStateRepository(db)
                
                # thread_id 추출
                thread_id = config.get("configurable", {}).get("thread_id")
                if not thread_id:
                    raise CheckpointError("thread_id is required in config")
                
                # checkpoint_id 생성
                checkpoint_id = checkpoint.get("id", str(uuid.uuid4()))
                parent_id = checkpoint.get("parent_checkpoint_id")
                
                # 상태 데이터 준비
                state_data = {
                    "checkpoint": checkpoint,
                    "metadata": metadata,
                    "channel_versions": new_versions,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 체크포인트 저장
                workflow_state = repo.save_checkpoint(
                    thread_id=thread_id,
                    checkpoint_id=checkpoint_id,
                    state=state_data,
                    parent_id=parent_id
                )
                
                self.logger.debug(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")
                
                # 업데이트된 설정 반환
                return {
                    **config,
                    "configurable": {
                        **config.get("configurable", {}),
                        "checkpoint_id": checkpoint_id
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointError(f"Failed to save checkpoint: {e}")
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """체크포인트 튜플 조회
        
        Args:
            config: 설정 정보
            
        Returns:
            체크포인트 튜플 또는 None
        """
        try:
            with self.db_session_factory() as db:
                repo = WorkflowStateRepository(db)
                
                thread_id = config.get("configurable", {}).get("thread_id")
                if not thread_id:
                    return None
                
                checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
                
                if checkpoint_id:
                    # 특정 체크포인트 조회
                    state = repo.find_one_by(
                        thread_id=thread_id,
                        checkpoint_id=checkpoint_id
                    )
                else:
                    # 최신 체크포인트 조회
                    state = repo.get_latest_checkpoint(thread_id)
                
                if not state:
                    return None
                
                # 체크포인트 튜플 생성
                return self._state_to_tuple(state, config)
                
        except Exception as e:
            self.logger.error(f"Failed to get checkpoint: {e}")
            return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Sequence[CheckpointTuple]:
        """체크포인트 목록 조회
        
        Args:
            config: 설정 정보
            filter: 필터 조건
            before: 이전 체크포인트
            limit: 최대 개수
            
        Returns:
            체크포인트 튜플 목록
        """
        try:
            with self.db_session_factory() as db:
                repo = WorkflowStateRepository(db)
                
                thread_id = config.get("configurable", {}).get("thread_id") if config else None
                if not thread_id:
                    return []
                
                # 체크포인트 목록 조회
                states = repo.get_checkpoints(
                    thread_id=thread_id,
                    limit=limit or 10
                )
                
                # 튜플로 변환
                tuples = []
                for state in states:
                    tuple_config = {
                        **config,
                        "configurable": {
                            **config.get("configurable", {}),
                            "checkpoint_id": state.checkpoint_id
                        }
                    }
                    checkpoint_tuple = self._state_to_tuple(state, tuple_config)
                    if checkpoint_tuple:
                        tuples.append(checkpoint_tuple)
                
                return tuples
                
        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def _state_to_tuple(self, state: WorkflowState, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """WorkflowState를 CheckpointTuple로 변환
        
        Args:
            state: 워크플로우 상태
            config: 설정 정보
            
        Returns:
            체크포인트 튜플
        """
        try:
            state_data = state.state
            
            # 체크포인트 데이터 추출
            checkpoint = state_data.get("checkpoint", {})
            metadata = state_data.get("metadata", {})
            channel_versions = state_data.get("channel_versions", {})
            
            # 부모 설정 생성
            parent_config = None
            if state.parent_id:
                parent_config = {
                    **config,
                    "configurable": {
                        **config.get("configurable", {}),
                        "checkpoint_id": state.parent_id
                    }
                }
            
            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
                pending_writes=[]  # 대기 중인 쓰기 작업 (현재 미사용)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to convert state to tuple: {e}")
            return None
    
    def get_checkpoint(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """체크포인트 조회 (간편 메서드)
        
        Args:
            config: 설정 정보
            
        Returns:
            체크포인트 또는 None
        """
        checkpoint_tuple = self.get_tuple(config)
        return checkpoint_tuple.checkpoint if checkpoint_tuple else None
    
    def cleanup_old_checkpoints(self, days: int = 30) -> int:
        """오래된 체크포인트 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            삭제된 체크포인트 개수
        """
        try:
            with self.db_session_factory() as db:
                repo = WorkflowStateRepository(db)
                deleted = repo.cleanup_old_checkpoints(days)
                self.logger.info(f"Cleaned up {deleted} old checkpoints")
                return deleted
        except Exception as e:
            self.logger.error(f"Failed to cleanup old checkpoints: {e}")
            return 0

# Redis 기반 체크포인트 세이버 (선택적)
class RedisCheckpointSaver(BaseCheckpointSaver):
    """Redis 기반 체크포인트 저장소 (임시 저장용)"""
    
    def __init__(self, redis_client, ttl: int = 86400):
        """
        Args:
            redis_client: Redis 클라이언트
            ttl: 체크포인트 TTL (초, 기본 24시간)
        """
        super().__init__()
        self.redis = redis_client
        self.ttl = ttl
        self.logger = logging.getLogger(f"{__name__}.RedisCheckpointSaver")
    
    def _get_key(self, thread_id: str, checkpoint_id: Optional[str] = None) -> str:
        """Redis 키 생성"""
        if checkpoint_id:
            return f"checkpoint:{thread_id}:{checkpoint_id}"
        return f"checkpoint:{thread_id}:latest"
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelValues,
    ) -> Dict[str, Any]:
        """체크포인트 저장"""
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                raise CheckpointError("thread_id is required")
            
            checkpoint_id = checkpoint.get("id", str(uuid.uuid4()))
            
            # 데이터 직렬화
            data = {
                "checkpoint": checkpoint,
                "metadata": metadata,
                "channel_versions": new_versions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Redis에 저장
            key = self._get_key(thread_id, checkpoint_id)
            self.redis.setex(key, self.ttl, json.dumps(data))
            
            # 최신 체크포인트 업데이트
            latest_key = self._get_key(thread_id)
            self.redis.setex(latest_key, self.ttl, checkpoint_id)
            
            return {
                **config,
                "configurable": {
                    **config.get("configurable", {}),
                    "checkpoint_id": checkpoint_id
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint to Redis: {e}")
            raise CheckpointError(f"Failed to save checkpoint: {e}")
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """체크포인트 조회"""
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return None
            
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            
            # checkpoint_id가 없으면 최신 조회
            if not checkpoint_id:
                latest_key = self._get_key(thread_id)
                checkpoint_id = self.redis.get(latest_key)
                if checkpoint_id:
                    checkpoint_id = checkpoint_id.decode('utf-8')
            
            if not checkpoint_id:
                return None
            
            # 체크포인트 데이터 조회
            key = self._get_key(thread_id, checkpoint_id)
            data = self.redis.get(key)
            if not data:
                return None
            
            # 역직렬화
            state_data = json.loads(data.decode('utf-8'))
            
            return CheckpointTuple(
                config=config,
                checkpoint=state_data.get("checkpoint", {}),
                metadata=state_data.get("metadata", {}),
                parent_config=None,  # Redis는 부모 관계 미지원
                pending_writes=[]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get checkpoint from Redis: {e}")
            return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Sequence[CheckpointTuple]:
        """체크포인트 목록 조회 (Redis는 제한적 지원)"""
        # Redis는 목록 조회가 제한적이므로 최신 체크포인트만 반환
        if config:
            latest = self.get_tuple(config)
            return [latest] if latest else []
        return []