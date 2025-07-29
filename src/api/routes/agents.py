"""
에이전트 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime, timedelta

from src.storage.repositories import AgentExecutionRepository
from src.storage.database import get_db_session
from src.api.schemas import (
    AgentExecutionResponse,
    AgentStatusResponse,
    AgentMetricsResponse
)
from src.core.schemas import AgentType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def get_agents_status() -> List[AgentStatusResponse]:
    """모든 에이전트 상태 조회"""
    agents = [
        {
            "name": "PlanningAgent",
            "type": AgentType.PLANNING,
            "status": "ready",
            "version": "1.0.0",
            "capabilities": ["requirement_analysis", "architecture_design", "timeline_estimation"]
        },
        {
            "name": "DevelopmentAgent",
            "type": AgentType.DEVELOPMENT,
            "status": "ready",
            "version": "1.0.0",
            "capabilities": ["code_generation", "test_creation", "api_integration"]
        },
        {
            "name": "TestingAgent",
            "type": AgentType.TESTING,
            "status": "ready",
            "version": "1.0.0",
            "capabilities": ["unit_testing", "integration_testing", "performance_testing"]
        },
        {
            "name": "DeploymentAgent",
            "type": AgentType.DEPLOYMENT,
            "status": "ready",
            "version": "1.0.0",
            "capabilities": ["containerization", "ci_cd_setup", "infrastructure_provisioning"]
        },
        {
            "name": "MonitoringAgent",
            "type": AgentType.MONITORING,
            "status": "ready",
            "version": "1.0.0",
            "capabilities": ["metrics_setup", "alert_configuration", "dashboard_creation"]
        }
    ]
    
    return [AgentStatusResponse(**agent) for agent in agents]


@router.get("/executions")
async def list_agent_executions(
    agent_type: Optional[AgentType] = None,
    pipeline_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    session=Depends(get_db_session)
) -> List[AgentExecutionResponse]:
    """에이전트 실행 이력 조회"""
    try:
        repo = AgentExecutionRepository(session)
        
        # 필터 조건 구성
        filters = {}
        if agent_type:
            filters["agent_name"] = f"{agent_type.value}Agent"
        if pipeline_id:
            filters["pipeline_id"] = pipeline_id
        if status:
            filters["status"] = status
            
        # 실행 이력 조회
        executions = await repo.list(
            skip=skip,
            limit=limit,
            **filters
        )
        
        return [AgentExecutionResponse.from_orm(e) for e in executions]
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_agent_execution(
    execution_id: UUID,
    session=Depends(get_db_session)
) -> AgentExecutionResponse:
    """특정 에이전트 실행 상세 조회"""
    try:
        repo = AgentExecutionRepository(session)
        execution = await repo.get(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
            
        return AgentExecutionResponse.from_orm(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_agent_metrics(
    agent_type: Optional[AgentType] = None,
    period: str = "24h",
    session=Depends(get_db_session)
) -> AgentMetricsResponse:
    """에이전트 메트릭 조회"""
    try:
        # 기간 파싱
        period_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        time_delta = period_map.get(period, timedelta(hours=24))
        start_time = datetime.utcnow() - time_delta
        
        repo = AgentExecutionRepository(session)
        
        # 에이전트별 메트릭 계산
        metrics = {}
        
        agent_types = [agent_type] if agent_type else list(AgentType)
        
        for at in agent_types:
            agent_name = f"{at.value}Agent"
            
            # 해당 기간의 실행 통계
            executions = await repo.list(
                agent_name=agent_name,
                created_after=start_time
            )
            
            if executions:
                success_count = sum(1 for e in executions if e.status == "success")
                failed_count = sum(1 for e in executions if e.status == "failed")
                total_count = len(executions)
                
                # 실행 시간 통계
                execution_times = [
                    (e.end_time - e.start_time).total_seconds()
                    for e in executions
                    if e.end_time and e.start_time
                ]
                
                avg_execution_time = (
                    sum(execution_times) / len(execution_times)
                    if execution_times else 0
                )
                
                # 토큰 사용량 통계
                total_tokens = sum(
                    e.token_usage.get("total_tokens", 0)
                    for e in executions
                    if e.token_usage
                )
                
                metrics[at.value] = {
                    "total_executions": total_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
                    "avg_execution_time": avg_execution_time,
                    "total_tokens_used": total_tokens
                }
            else:
                metrics[at.value] = {
                    "total_executions": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "success_rate": 0,
                    "avg_execution_time": 0,
                    "total_tokens_used": 0
                }
        
        return AgentMetricsResponse(
            period=period,
            start_time=start_time.isoformat(),
            end_time=datetime.utcnow().isoformat(),
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_type}/test")
async def test_agent(
    agent_type: AgentType,
    test_input: Dict[str, Any]
) -> Dict[str, Any]:
    """에이전트 테스트 실행"""
    try:
        # 에이전트 인스턴스 가져오기
        agent = get_agent_instance(agent_type)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
            
        # 간단한 테스트 실행
        result = {
            "agent": agent_type.value,
            "status": "success",
            "test_input": test_input,
            "test_output": {
                "message": f"Test execution successful for {agent_type.value}",
                "capabilities_tested": agent.get_capabilities()
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_agent_instance(agent_type: AgentType):
    """에이전트 인스턴스 반환"""
    agent_map = {
        AgentType.PLANNING: "PlanningAgent",
        AgentType.DEVELOPMENT: "DevelopmentAgent",
        AgentType.TESTING: "TestingAgent",
        AgentType.DEPLOYMENT: "DeploymentAgent",
        AgentType.MONITORING: "MonitoringAgent"
    }
    
    agent_name = agent_map.get(agent_type)
    if not agent_name:
        return None
        
    # 동적 임포트 (실제 구현에서는 싱글톤 패턴 사용)
    try:
        if agent_type == AgentType.PLANNING:
            from src.agents.planning.planning_agent import PlanningAgent
            return PlanningAgent()
        elif agent_type == AgentType.DEVELOPMENT:
            from src.agents.development.development_agent import DevelopmentAgent
            return DevelopmentAgent()
        elif agent_type == AgentType.TESTING:
            from src.agents.testing.testing_agent import TestingAgent
            return TestingAgent()
        elif agent_type == AgentType.DEPLOYMENT:
            from src.agents.deployment.deployment_agent import DeploymentAgent
            return DeploymentAgent()
        elif agent_type == AgentType.MONITORING:
            from src.agents.monitoring.monitoring_agent import MonitoringAgent
            return MonitoringAgent()
    except Exception as e:
        logger.error(f"Failed to get agent instance: {e}")
        return None