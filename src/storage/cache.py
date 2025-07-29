"""
Redis 캐시 관리
"""

import json
import logging
import pickle
from typing import Optional, Any, Union, List, Dict, Callable
from datetime import timedelta
import asyncio
from functools import wraps

import redis
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from src.core.config import get_settings
from src.core.exceptions import CacheError

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheManager:
    """Redis 캐시 매니저"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self._lock = asyncio.Lock()
        
    def initialize(self):
        """캐시 초기화"""
        try:
            # 연결 풀 생성
            self.pool = ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=False,  # 바이너리 데이터 지원
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Redis 클라이언트 생성
            self.redis_client = Redis(connection_pool=self.pool)
            
            # 연결 테스트
            self.redis_client.ping()
            logger.info(f"Redis connected successfully at {settings.redis_host}:{settings.redis_port}")
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Redis 연결 실패해도 애플리케이션은 계속 실행
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {e}")
            self.redis_client = None
    
    def _serialize(self, value: Any) -> bytes:
        """값 직렬화"""
        try:
            # JSON 직렬화 시도
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # 실패하면 pickle 사용
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """값 역직렬화"""
        if not data:
            return None
        
        try:
            # JSON 역직렬화 시도
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 실패하면 pickle 사용
            return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"Cache hit for key: {key}")
                return self._deserialize(data)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except RedisError as e:
            logger.warning(f"Redis get error for key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """캐시에 값 저장"""
        if not self.redis_client:
            return False
        
        try:
            serialized = self._serialize(value)
            
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            logger.debug(f"Cached key: {key}, ttl: {ttl}")
            return True
        except RedisError as e:
            logger.warning(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Deleted key: {key}, result: {result}")
            return bool(result)
        except RedisError as e:
            logger.warning(f"Redis delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.warning(f"Redis exists error for key {key}: {e}")
            return False
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """여러 키 동시 조회"""
        if not self.redis_client:
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = self._deserialize(value)
            return result
        except RedisError as e:
            logger.warning(f"Redis mget error: {e}")
            return {}
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """여러 키 동시 저장"""
        if not self.redis_client:
            return False
        
        try:
            # 값 직렬화
            serialized_mapping = {
                key: self._serialize(value)
                for key, value in mapping.items()
            }
            
            if ttl:
                # TTL이 있으면 개별 저장
                pipe = self.redis_client.pipeline()
                for key, value in serialized_mapping.items():
                    pipe.setex(key, ttl, value)
                pipe.execute()
            else:
                self.redis_client.mset(serialized_mapping)
            
            return True
        except RedisError as e:
            logger.warning(f"Redis mset error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """카운터 증가"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except RedisError as e:
            logger.warning(f"Redis increment error for key {key}: {e}")
            return None
    
    def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """TTL 설정"""
        if not self.redis_client:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return bool(self.redis_client.expire(key, ttl))
        except RedisError as e:
            logger.warning(f"Redis expire error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """패턴에 맞는 키 삭제"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Redis clear pattern error for {pattern}: {e}")
            return 0
    
    def get_ttl(self, key: str) -> Optional[int]:
        """TTL 조회"""
        if not self.redis_client:
            return None
        
        try:
            ttl = self.redis_client.ttl(key)
            return ttl if ttl >= 0 else None
        except RedisError as e:
            logger.warning(f"Redis TTL error for key {key}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Redis 상태 확인"""
        if not self.redis_client:
            return {
                "status": "disconnected",
                "error": "Redis client not initialized"
            }
        
        try:
            # Ping
            self.redis_client.ping()
            
            # 정보 조회
            info = self.redis_client.info()
            
            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_days": info.get("uptime_in_days")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 캐시 데코레이터
def cached(
    key_prefix: str,
    ttl: Optional[Union[int, timedelta]] = 3600,
    key_func: Optional[Callable] = None
):
    """캐시 데코레이터
    
    Args:
        key_prefix: 캐시 키 접두사
        ttl: Time To Live (초 또는 timedelta)
        key_func: 캐시 키 생성 함수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # 기본 키 생성 (함수 인자 기반)
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"
            
            # 캐시 조회
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시 저장
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # 비동기 함수 지원
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 캐시 키 생성
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"
            
            # 캐시 조회
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 캐시 저장
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # 함수가 코루틴인지 확인
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

# 캐시 무효화 데코레이터
def invalidate_cache(pattern: str):
    """캐시 무효화 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache_manager.clear_pattern(pattern)
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            cache_manager.clear_pattern(pattern)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

# 싱글톤 인스턴스
cache_manager = CacheManager()

# 캐시 키 생성 헬퍼
class CacheKeys:
    """캐시 키 네임스페이스"""
    
    @staticmethod
    def pipeline(pipeline_id: str) -> str:
        return f"pipeline:{pipeline_id}"
    
    @staticmethod
    def agent_execution(execution_id: str) -> str:
        return f"agent_execution:{execution_id}"
    
    @staticmethod
    def workflow_state(thread_id: str) -> str:
        return f"workflow_state:{thread_id}"
    
    @staticmethod
    def artifact(artifact_id: str) -> str:
        return f"artifact:{artifact_id}"
    
    @staticmethod
    def user_session(session_id: str) -> str:
        return f"session:{session_id}"
    
    @staticmethod
    def api_rate_limit(api_key: str) -> str:
        return f"rate_limit:{api_key}"
    
    @staticmethod
    def metric(name: str, timestamp: str) -> str:
        return f"metric:{name}:{timestamp}"