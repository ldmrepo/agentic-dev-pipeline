"""
메인 워크플로우 그래프
LangGraph를 사용한 개발 파이프라인 워크플로우
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
import logging

from src.orchestration.state import WorkflowState, TaskType
from src.orchestration.nodes.analyze import analyze_task_node
from src.orchestration.nodes.agents import (
    planning_node,
    development_node,
    testing_node,
    deployment_node,
    monitoring_node,
    review_node
)

logger = logging.getLogger(__name__)


def create_main_workflow() -> StateGraph:
    """메인 개발 워크플로우 생성"""
    
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
    
    # 조건부 라우팅
    graph.add_conditional_edges(
        "analyze_task",
        route_after_analysis,
        {
            "planning": "planning",
            "hotfix": "development",  # 핫픽스는 바로 개발로
            "review": "review",  # 문서화는 리뷰만
            "end": END
        }
    )
    
    # 순차적 엣지
    graph.add_edge("planning", "development")
    graph.add_edge("development", "testing")
    graph.add_edge("testing", "review")
    
    # 리뷰 후 조건부 라우팅
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "deployment": "deployment",
            "rework": "development",  # 재작업 필요
            "end": END
        }
    )
    
    graph.add_edge("deployment", "monitoring")
    graph.add_edge("monitoring", END)
    
    return graph


def route_after_analysis(state: WorkflowState) -> str:
    """태스크 분석 후 라우팅"""
    task_type = state.get("task_type", TaskType.FEATURE)
    analysis_result = state.get("analysis_result", {})
    
    # 분석 실패 시
    if not analysis_result:
        logger.error("No analysis result found")
        return "end"
    
    # 태스크 타입별 라우팅
    if task_type == TaskType.HOTFIX:
        logger.info("Routing to hotfix flow - skipping planning")
        state["next_nodes"] = ["development", "testing", "review", "deployment"]
        return "hotfix"
    
    elif task_type == TaskType.DOCUMENTATION:
        logger.info("Routing to documentation flow - review only")
        state["next_nodes"] = ["review"]
        return "review"
    
    else:
        logger.info(f"Routing to standard flow for {task_type}")
        state["next_nodes"] = ["planning", "development", "testing", "review", "deployment", "monitoring"]
        return "planning"


def route_after_review(state: WorkflowState) -> str:
    """리뷰 후 라우팅"""
    review_result = state.get("review_result", {})
    
    if not review_result:
        logger.error("No review result found")
        return "end"
    
    if review_result.get("approved", False):
        logger.info("Review approved, proceeding to deployment")
        
        # 배포가 필요한 태스크인지 확인
        task_type = state.get("task_type", TaskType.FEATURE)
        if task_type == TaskType.DOCUMENTATION:
            logger.info("Documentation task - skipping deployment")
            return "end"
        
        return "deployment"
    
    elif review_result.get("needs_rework", False):
        logger.info("Review requires rework")
        
        # 재시도 횟수 확인
        if state.get("retry_count", 0) < 2:
            state["retry_count"] = state.get("retry_count", 0) + 1
            return "rework"
        else:
            logger.warning("Maximum rework attempts reached")
            return "end"
    
    else:
        logger.info("Review failed, ending workflow")
        return "end"


def create_parallel_development_graph() -> StateGraph:
    """병렬 개발 워크플로우 (프론트엔드/백엔드/인프라)"""
    
    graph = StateGraph(WorkflowState)
    
    # 병렬 실행을 위한 노드
    graph.add_node("split_tasks", split_development_tasks)
    graph.add_node("frontend_dev", frontend_development_node)
    graph.add_node("backend_dev", backend_development_node)
    graph.add_node("infra_dev", infrastructure_development_node)
    graph.add_node("merge_results", merge_development_results)
    
    # 플로우 정의
    graph.set_entry_point("split_tasks")
    
    # 병렬 실행
    graph.add_edge("split_tasks", "frontend_dev")
    graph.add_edge("split_tasks", "backend_dev")
    graph.add_edge("split_tasks", "infra_dev")
    
    # 결과 병합
    graph.add_edge("frontend_dev", "merge_results")
    graph.add_edge("backend_dev", "merge_results")
    graph.add_edge("infra_dev", "merge_results")
    
    graph.add_edge("merge_results", END)
    
    return graph


async def split_development_tasks(state: WorkflowState) -> Dict[str, Any]:
    """개발 태스크 분할"""
    planning_result = state.get("planning_result", {})
    wbs = planning_result.get("wbs", {})
    
    # 태스크를 카테고리별로 분류
    frontend_tasks = []
    backend_tasks = []
    infra_tasks = []
    
    for task in wbs.get("tasks", []):
        assignee = task.get("assignee_type", "general")
        
        if assignee == "frontend":
            frontend_tasks.append(task)
        elif assignee == "backend":
            backend_tasks.append(task)
        elif assignee == "devops":
            infra_tasks.append(task)
    
    return {
        "frontend_tasks": frontend_tasks,
        "backend_tasks": backend_tasks,
        "infra_tasks": infra_tasks
    }


async def frontend_development_node(state: WorkflowState) -> Dict[str, Any]:
    """프론트엔드 개발 노드"""
    tasks = state.get("frontend_tasks", [])
    logger.info(f"Developing {len(tasks)} frontend tasks")
    
    # 실제로는 DevelopmentAgent를 사용하여 프론트엔드 코드 생성
    return {"frontend_result": f"Completed {len(tasks)} frontend tasks"}


async def backend_development_node(state: WorkflowState) -> Dict[str, Any]:
    """백엔드 개발 노드"""
    tasks = state.get("backend_tasks", [])
    logger.info(f"Developing {len(tasks)} backend tasks")
    
    # 실제로는 DevelopmentAgent를 사용하여 백엔드 코드 생성
    return {"backend_result": f"Completed {len(tasks)} backend tasks"}


async def infrastructure_development_node(state: WorkflowState) -> Dict[str, Any]:
    """인프라 개발 노드"""
    tasks = state.get("infra_tasks", [])
    logger.info(f"Setting up {len(tasks)} infrastructure tasks")
    
    # 실제로는 DeploymentAgent를 사용하여 인프라 설정
    return {"infra_result": f"Completed {len(tasks)} infrastructure tasks"}


async def merge_development_results(state: WorkflowState) -> Dict[str, Any]:
    """개발 결과 병합"""
    frontend = state.get("frontend_result", {})
    backend = state.get("backend_result", {})
    infra = state.get("infra_result", {})
    
    logger.info("Merging development results from all tracks")
    
    return {
        "merged_result": {
            "frontend": frontend,
            "backend": backend,
            "infrastructure": infra
        }
    }


def create_hotfix_workflow() -> StateGraph:
    """핫픽스 전용 빠른 워크플로우"""
    
    graph = StateGraph(WorkflowState)
    
    # 최소한의 노드만 포함
    graph.add_node("analyze", analyze_task_node)
    graph.add_node("develop", development_node)
    graph.add_node("test", testing_node)
    graph.add_node("deploy", deployment_node)
    
    # 선형 플로우
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "develop")
    graph.add_edge("develop", "test")
    
    # 테스트 후 조건부 배포
    graph.add_conditional_edges(
        "test",
        lambda state: "deploy" if state.get("testing_result", {}).get("passed", False) else END,
        {
            "deploy": "deploy",
            END: END
        }
    )
    
    graph.add_edge("deploy", END)
    
    return graph