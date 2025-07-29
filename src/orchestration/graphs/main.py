"""
메인 개발 워크플로우 그래프
전체 개발 파이프라인의 플로우를 정의
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
import logging

from src.orchestration.state import WorkflowState, StateManager
from src.orchestration.nodes.analyze import analyze_task_node
from src.orchestration.nodes.planning import planning_node
from src.orchestration.nodes.development import development_node
from src.orchestration.nodes.testing import testing_node
from src.orchestration.nodes.review import review_node
from src.orchestration.nodes.deployment import deployment_node
from src.orchestration.nodes.monitoring import monitoring_node
from src.core.constants import TaskType, PipelineStatus

logger = logging.getLogger(__name__)

def create_main_workflow() -> StateGraph:
    """
    메인 개발 워크플로우 생성
    
    플로우:
    1. analyze_task: 요구사항 분석
    2. planning: 개발 계획 수립
    3. development: 코드 구현
    4. testing: 테스트 실행
    5. review: 코드 리뷰
    6. deployment: 배포 (선택적)
    7. monitoring: 모니터링 설정
    """
    
    # 그래프 초기화
    graph = StateGraph(WorkflowState)
    
    # 노드 추가
    graph.add_node("analyze_task", analyze_task_node)
    graph.add_node("planning", planning_node)
    graph.add_node("development", development_node)
    graph.add_node("testing", testing_node)
    graph.add_node("review", review_node)
    graph.add_node("deployment", deployment_node)
    graph.add_node("monitoring", monitoring_node)
    
    # 시작점 설정
    graph.set_entry_point("analyze_task")
    
    # 엣지 정의: analyze_task 후 라우팅
    graph.add_conditional_edges(
        "analyze_task",
        route_after_analysis,
        {
            "planning": "planning",
            "hotfix": "development",  # 핫픽스는 계획 단계 건너뛰기
            "end": END
        }
    )
    
    # 순차 실행 엣지
    graph.add_edge("planning", "development")
    graph.add_edge("development", "testing")
    graph.add_edge("testing", "review")
    
    # 리뷰 후 조건부 라우팅
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "deployment": "deployment",
            "rework": "development",  # 수정 필요시 개발로 되돌아감
            "end": END
        }
    )
    
    # 배포 후 라우팅
    graph.add_conditional_edges(
        "deployment",
        route_after_deployment,
        {
            "monitoring": "monitoring",
            "end": END
        }
    )
    
    # 모니터링은 항상 종료
    graph.add_edge("monitoring", END)
    
    return graph

def route_after_analysis(state: WorkflowState) -> str:
    """태스크 분석 후 라우팅 결정"""
    # 계속 진행 여부 확인
    if not state.get("should_continue", True):
        logger.info("Pipeline stopped after analysis")
        return "end"
    
    # 태스크 타입에 따른 라우팅
    task_type = state.get("task_type", TaskType.FEATURE)
    
    if task_type == TaskType.HOTFIX:
        logger.info("Routing to hotfix flow - skipping planning")
        return "hotfix"
    
    logger.info("Routing to standard planning flow")
    return "planning"

def route_after_review(state: WorkflowState) -> str:
    """코드 리뷰 후 라우팅 결정"""
    review_result = state.get("review_result", {})
    
    # 리뷰 승인 여부 확인
    if review_result.get("approved", False):
        # 배포 건너뛰기 플래그 확인
        if state.get("skip_deployment", False):
            logger.info("Review approved but deployment skipped")
            return "end"
        
        logger.info("Review approved, proceeding to deployment")
        return "deployment"
    
    # 수정 필요 여부 확인
    if review_result.get("needs_rework", False):
        # 재시도 횟수 확인
        if state.get("retry_count", 0) >= 3:
            logger.warning("Maximum rework attempts reached")
            return "end"
        
        logger.info("Review requires rework")
        return "rework"
    
    # 기타 경우 종료
    logger.info("Review completed without deployment")
    return "end"

def route_after_deployment(state: WorkflowState) -> str:
    """배포 후 라우팅 결정"""
    deployment_result = state.get("deployment_result", {})
    
    # 배포 성공 여부 확인
    if deployment_result.get("success", False):
        logger.info("Deployment successful, setting up monitoring")
        return "monitoring"
    
    logger.info("Deployment failed or skipped monitoring")
    return "end"

def create_hotfix_workflow() -> StateGraph:
    """
    핫픽스 전용 워크플로우
    더 빠른 처리를 위해 일부 단계 생략
    """
    graph = StateGraph(WorkflowState)
    
    # 노드 추가 (계획 단계 제외)
    graph.add_node("analyze_task", analyze_task_node)
    graph.add_node("development", development_node)
    graph.add_node("testing", testing_node)
    graph.add_node("deployment", deployment_node)
    
    # 플로우 정의
    graph.set_entry_point("analyze_task")
    graph.add_edge("analyze_task", "development")
    graph.add_edge("development", "testing")
    
    # 테스트 후 즉시 배포
    graph.add_conditional_edges(
        "testing",
        lambda state: "deployment" if state.get("testing_result", {}).get("passed", False) else END,
        {
            "deployment": "deployment",
            END: END
        }
    )
    
    graph.add_edge("deployment", END)
    
    return graph

def create_parallel_development_workflow() -> StateGraph:
    """
    병렬 개발 워크플로우
    프론트엔드, 백엔드, 인프라를 동시에 개발
    """
    from langgraph.graph import Send
    
    graph = StateGraph(WorkflowState)
    
    # 노드 정의
    def split_development_tasks(state: WorkflowState) -> list:
        """개발 태스크를 프론트엔드, 백엔드, 인프라로 분할"""
        planning_result = state.get("planning_result", {})
        tasks = planning_result.get("tasks", [])
        
        # 태스크를 카테고리별로 분류
        frontend_tasks = [t for t in tasks if t.get("category") == "frontend"]
        backend_tasks = [t for t in tasks if t.get("category") == "backend"]
        infra_tasks = [t for t in tasks if t.get("category") == "infrastructure"]
        
        # 병렬 실행을 위한 Send 객체 생성
        sends = []
        
        if frontend_tasks:
            sends.append(Send("frontend_development", {"tasks": frontend_tasks}))
        if backend_tasks:
            sends.append(Send("backend_development", {"tasks": backend_tasks}))
        if infra_tasks:
            sends.append(Send("infrastructure_development", {"tasks": infra_tasks}))
        
        return sends
    
    def merge_development_results(state: WorkflowState) -> Dict[str, Any]:
        """병렬 개발 결과 병합"""
        # 각 개발 결과 수집
        frontend_result = state.get("frontend_result", {})
        backend_result = state.get("backend_result", {})
        infra_result = state.get("infrastructure_result", {})
        
        # 통합 결과 생성
        merged_result = {
            "frontend": frontend_result,
            "backend": backend_result,
            "infrastructure": infra_result,
            "generated_files": (
                frontend_result.get("files", []) +
                backend_result.get("files", []) +
                infra_result.get("files", [])
            ),
            "total_artifacts": (
                len(frontend_result.get("files", [])) +
                len(backend_result.get("files", [])) +
                len(infra_result.get("files", []))
            )
        }
        
        return {"development_result": merged_result}
    
    # 노드 추가
    graph.add_node("split_tasks", split_development_tasks)
    graph.add_node("frontend_development", development_node)
    graph.add_node("backend_development", development_node)
    graph.add_node("infrastructure_development", development_node)
    graph.add_node("merge_results", merge_development_results)
    
    # 플로우 정의
    graph.set_entry_point("split_tasks")
    
    # 결과 병합
    graph.add_edge("frontend_development", "merge_results")
    graph.add_edge("backend_development", "merge_results")
    graph.add_edge("infrastructure_development", "merge_results")
    
    graph.add_edge("merge_results", END)
    
    return graph