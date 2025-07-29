"""
헬스체크 엔드포인트
시스템 상태 확인
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import psutil
import asyncio
from datetime import datetime

from src.storage.database import get_db_session
from src.storage.cache import redis_client
from src.config import settings

router = APIRouter()


@router.get("")
async def health_check() -> Dict[str, Any]:
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "agentic-dev-pipeline"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """상세 헬스체크"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
        "system": {}
    }
    
    # 데이터베이스 체크
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Redis 체크
    try:
        await redis_client.ping()
        health_status["components"]["cache"] = {
            "status": "healthy",
            "type": "redis"
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # 시스템 리소스
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "available_mb": psutil.virtual_memory().available / (1024 * 1024)
        },
        "disk": {
            "percent": psutil.disk_usage('/').percent,
            "free_gb": psutil.disk_usage('/').free / (1024 * 1024 * 1024)
        }
    }
    
    return health_status


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """레디니스 체크 - 요청 처리 준비 상태"""
    try:
        # 필수 서비스 연결 확인
        checks = await asyncio.gather(
            check_database(),
            check_redis(),
            return_exceptions=True
        )
        
        all_ready = all(not isinstance(check, Exception) and check for check in checks)
        
        return {
            "ready": all_ready,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """라이브니스 체크 - 프로세스 생존 상태"""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": get_uptime()
    }


async def check_database() -> bool:
    """데이터베이스 연결 확인"""
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        return True
    except:
        return False


async def check_redis() -> bool:
    """Redis 연결 확인"""
    try:
        await redis_client.ping()
        return True
    except:
        return False


def get_uptime() -> float:
    """프로세스 업타임 계산"""
    process = psutil.Process()
    create_time = process.create_time()
    current_time = datetime.now().timestamp()
    return current_time - create_time