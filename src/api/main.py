"""
메인 FastAPI 애플리케이션
"""

from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from src.api.routes import pipelines, agents, health, metrics
from src.api.websocket import WebSocketManager
from src.api.middleware.logging import LoggingMiddleware, PerformanceLoggingMiddleware
from src.storage.database import init_db
from src.core.config import settings
from src.core.config_validator import validate_config_on_startup
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명주기 관리"""
    # Startup
    logger.info("Starting Agentic Dev Pipeline API...")
    
    # 설정 검증
    try:
        validate_config_on_startup()
        logger.info("Configuration validation passed")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # 데이터베이스 초기화
    await init_db()
    
    # WebSocket 매니저 초기화
    app.state.ws_manager = WebSocketManager()
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    

# FastAPI 인스턴스 생성
app = FastAPI(
    title="Agentic Development Pipeline",
    description="AI-powered development workflow automation platform",
    version="1.0.0",
    lifespan=lifespan
)

# 미들웨어 추가 (순서 중요 - 나중에 추가된 것이 먼저 실행됨)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 성능 로깅 미들웨어
app.add_middleware(PerformanceLoggingMiddleware)

# 요청/응답 로깅 미들웨어
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(metrics.router, tags=["metrics"])  # Prometheus 메트릭
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "Agentic Development Pipeline",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 엔드포인트 - 실시간 업데이트용"""
    ws_manager = app.state.ws_manager
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            
            # 파이프라인 상태 구독
            if data.get("action") == "subscribe":
                pipeline_id = data.get("pipeline_id")
                if pipeline_id:
                    await ws_manager.subscribe_to_pipeline(client_id, pipeline_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "pipeline_id": pipeline_id
                    })
            
            # Ping-Pong 처리
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        ws_manager.disconnect(client_id)


# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": {
            "code": 500,
            "message": "Internal server error"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )