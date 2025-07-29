"""
Prometheus 메트릭 엔드포인트
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.monitoring.metrics import update_system_metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> Response:
    """Prometheus 메트릭 반환"""
    # 시스템 메트릭 업데이트
    update_system_metrics()
    
    # 메트릭 생성
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )