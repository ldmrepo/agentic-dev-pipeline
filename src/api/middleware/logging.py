"""
로깅 미들웨어
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import (
    set_logging_context, 
    clear_logging_context,
    log_api_request,
    get_logger
)


logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 로깅 컨텍스트 설정
        set_logging_context(request_id=request_id)
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 정보 로깅
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 시간 계산
            duration = time.time() - start_time
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            
            # 응답 로깅
            log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                request_id=request_id,
                content_length=response.headers.get("content-length", 0)
            )
            
            return response
            
        except Exception as e:
            # 예외 발생 시간 계산
            duration = time.time() - start_time
            
            # 에러 로깅
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # 에러 응답
            return Response(
                content=f"Internal Server Error (Request ID: {request_id})",
                status_code=500,
                headers={"X-Request-ID": request_id}
            )
            
        finally:
            # 로깅 컨텍스트 정리
            clear_logging_context()


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """성능 로깅 미들웨어"""
    
    # 느린 요청 임계값 (초)
    SLOW_REQUEST_THRESHOLD = 1.0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 메모리 사용량 (시작)
        import psutil
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간
        duration = time.time() - start_time
        
        # 메모리 사용량 (종료)
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = end_memory - start_memory
        
        # 느린 요청 로깅
        if duration > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "memory_delta_mb": memory_delta,
                    "threshold": self.SLOW_REQUEST_THRESHOLD
                }
            )
        
        # 성능 메트릭을 응답 헤더에 추가 (개발 환경에서만)
        from src.core.config import settings
        if settings.is_development():
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Memory-Delta"] = f"{memory_delta:.2f}MB"
        
        return response