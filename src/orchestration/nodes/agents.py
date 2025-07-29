"""
에이전트 실행 노드들
각 에이전트를 실행하는 워크플로우 노드
"""

from typing import Dict, Any, Optional

from src.orchestration.nodes.base import BaseNode, node_error_handler
from src.orchestration.state import WorkflowState
from src.agents.planning.planning_agent import PlanningAgent
from src.agents.development.development_agent import DevelopmentAgent
from src.agents.testing.testing_agent import TestingAgent
from src.agents.deployment.deployment_agent import DeploymentAgent
from src.agents.monitoring.monitoring_agent import MonitoringAgent
from src.core.schemas import AgentContext


class PlanningNode(BaseNode):
    """계획 수립 노드"""
    
    def __init__(self):
        super().__init__("Planning")
        self.agent = PlanningAgent()
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """Planning Agent 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting planning phase...")
        
        # 분석 결과 가져오기
        analysis_result = self.get_previous_result(state, "analyze_task")
        if not analysis_result:
            raise ValueError("No analysis result found")
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=state["requirements"],
            task_type=state["task_type"],
            previous_results={"analysis": analysis_result},
            constraints=state.get("constraints", []),
            metadata={
                "pipeline_id": state["pipeline_id"],
                "complexity": analysis_result.get("complexity", "medium")
            }
        )
        
        try:
            # Planning Agent 실행
            result = await self.agent.execute(context)
            
            if result.success:
                self.add_message(
                    state,
                    f"Planning completed successfully. Created {len(result.artifacts)} artifacts."
                )
                
                # 아티팩트 추가
                for artifact in result.artifacts:
                    self.add_artifact(
                        state,
                        artifact["name"],
                        artifact["type"],
                        artifact["content"],
                        artifact.get("metadata")
                    )
                
                self.log_progress("Planning phase completed")
                return result.output
            else:
                raise Exception(f"Planning failed: {', '.join(result.errors)}")
                
        except Exception as e:
            self.log_progress(f"Planning failed: {str(e)}", "error")
            raise


class DevelopmentNode(BaseNode):
    """개발 노드"""
    
    def __init__(self):
        super().__init__("Development")
        self.agent = DevelopmentAgent()
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """Development Agent 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting development phase...")
        
        # 이전 결과들 가져오기
        analysis_result = self.get_previous_result(state, "analyze_task")
        planning_result = self.get_previous_result(state, "planning")
        
        if not planning_result:
            raise ValueError("No planning result found")
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=state["requirements"],
            task_type=state["task_type"],
            previous_results={
                "analysis": analysis_result,
                "planning": planning_result
            },
            constraints=state.get("constraints", []),
            metadata={
                "pipeline_id": state["pipeline_id"],
                "architecture": planning_result.get("architecture", {})
            }
        )
        
        try:
            # Development Agent 실행
            result = await self.agent.execute(context)
            
            if result.success:
                self.add_message(
                    state,
                    f"Development completed. Generated {len(result.artifacts)} code files."
                )
                
                # 아티팩트 추가
                for artifact in result.artifacts:
                    self.add_artifact(
                        state,
                        artifact["name"],
                        artifact["type"],
                        artifact["content"],
                        artifact.get("metadata")
                    )
                
                self.log_progress("Development phase completed")
                return result.output
            else:
                raise Exception(f"Development failed: {', '.join(result.errors)}")
                
        except Exception as e:
            self.log_progress(f"Development failed: {str(e)}", "error")
            raise


class TestingNode(BaseNode):
    """테스팅 노드"""
    
    def __init__(self):
        super().__init__("Testing")
        self.agent = TestingAgent()
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """Testing Agent 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting testing phase...")
        
        # 이전 결과들 가져오기
        development_result = self.get_previous_result(state, "development")
        
        if not development_result:
            raise ValueError("No development result found")
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=state["requirements"],
            task_type=state["task_type"],
            previous_results={
                "development_result": development_result
            },
            constraints=state.get("constraints", []),
            metadata={
                "pipeline_id": state["pipeline_id"],
                "generated_files": development_result.get("generated_files", [])
            }
        )
        
        try:
            # Testing Agent 실행
            result = await self.agent.execute(context)
            
            if result.success:
                test_summary = result.output.get("summary", {})
                self.add_message(
                    state,
                    f"Testing completed. Generated {test_summary.get('total_tests', 0)} tests. "
                    f"Coverage: {test_summary.get('coverage', 0):.1f}%"
                )
                
                # 아티팩트 추가
                for artifact in result.artifacts:
                    self.add_artifact(
                        state,
                        artifact["name"],
                        artifact["type"],
                        artifact["content"],
                        artifact.get("metadata")
                    )
                
                self.log_progress("Testing phase completed")
                return result.output
            else:
                raise Exception(f"Testing failed: {', '.join(result.errors)}")
                
        except Exception as e:
            self.log_progress(f"Testing failed: {str(e)}", "error")
            raise


class DeploymentNode(BaseNode):
    """배포 노드"""
    
    def __init__(self):
        super().__init__("Deployment")
        self.agent = DeploymentAgent()
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """Deployment Agent 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting deployment phase...")
        
        # 이전 결과들 가져오기
        development_result = self.get_previous_result(state, "development")
        testing_result = self.get_previous_result(state, "testing")
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=state["requirements"],
            task_type=state["task_type"],
            previous_results={
                "development_result": development_result,
                "testing_result": testing_result
            },
            constraints=state.get("constraints", []),
            metadata={
                "pipeline_id": state["pipeline_id"],
                "environment": "production"
            }
        )
        
        try:
            # Deployment Agent 실행
            result = await self.agent.execute(context)
            
            if result.success:
                self.add_message(
                    state,
                    f"Deployment configuration completed. Created deployment artifacts."
                )
                
                # 아티팩트 추가
                for artifact in result.artifacts:
                    self.add_artifact(
                        state,
                        artifact["name"],
                        artifact["type"],
                        artifact["content"],
                        artifact.get("metadata")
                    )
                
                self.log_progress("Deployment phase completed")
                return result.output
            else:
                raise Exception(f"Deployment failed: {', '.join(result.errors)}")
                
        except Exception as e:
            self.log_progress(f"Deployment failed: {str(e)}", "error")
            raise


class MonitoringNode(BaseNode):
    """모니터링 노드"""
    
    def __init__(self):
        super().__init__("Monitoring")
        self.agent = MonitoringAgent()
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """Monitoring Agent 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting monitoring setup phase...")
        
        # 이전 결과들 가져오기
        deployment_result = self.get_previous_result(state, "deployment")
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=state["requirements"],
            task_type=state["task_type"],
            previous_results={
                "deployment_result": deployment_result
            },
            constraints=state.get("constraints", []),
            metadata={
                "pipeline_id": state["pipeline_id"],
                "monitoring_targets": ["api", "database", "cache"]
            }
        )
        
        try:
            # Monitoring Agent 실행
            result = await self.agent.execute(context)
            
            if result.success:
                self.add_message(
                    state,
                    f"Monitoring setup completed. Configured alerts and dashboards."
                )
                
                # 아티팩트 추가
                for artifact in result.artifacts:
                    self.add_artifact(
                        state,
                        artifact["name"],
                        artifact["type"],
                        artifact["content"],
                        artifact.get("metadata")
                    )
                
                self.log_progress("Monitoring setup completed")
                return result.output
            else:
                raise Exception(f"Monitoring setup failed: {', '.join(result.errors)}")
                
        except Exception as e:
            self.log_progress(f"Monitoring setup failed: {str(e)}", "error")
            raise


class ReviewNode(BaseNode):
    """리뷰 노드"""
    
    def __init__(self):
        super().__init__("Review")
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """코드 리뷰 및 품질 검증"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        self.log_progress("Starting review phase...")
        
        # 이전 결과들 가져오기
        development_result = self.get_previous_result(state, "development")
        testing_result = self.get_previous_result(state, "testing")
        
        # 간단한 리뷰 로직 (실제로는 더 복잡한 검증 수행)
        review_passed = True
        issues = []
        
        # 테스트 결과 검증
        if testing_result:
            test_summary = testing_result.get("summary", {})
            coverage = test_summary.get("coverage", 0)
            
            if coverage < 80:
                issues.append(f"Test coverage ({coverage:.1f}%) is below 80% threshold")
                review_passed = False
            
            if test_summary.get("failed", 0) > 0:
                issues.append(f"{test_summary['failed']} tests failed")
                review_passed = False
        
        # 코드 품질 검증 (시뮬레이션)
        if development_result:
            # 실제로는 SonarQube 등의 도구 사용
            code_quality_score = 85  # 시뮬레이션
            if code_quality_score < 80:
                issues.append(f"Code quality score ({code_quality_score}) is below threshold")
                review_passed = False
        
        review_result = {
            "approved": review_passed,
            "needs_rework": not review_passed and len(issues) < 3,
            "issues": issues,
            "recommendations": [
                "Consider adding more unit tests" if testing_result.get("summary", {}).get("coverage", 0) < 90 else None,
                "Review error handling patterns" if "error handling" in str(issues) else None
            ]
        }
        
        # 메시지 추가
        if review_passed:
            self.add_message(state, "✅ Review passed. Code is ready for deployment.")
        else:
            self.add_message(
                state,
                f"❌ Review failed with {len(issues)} issues:\n" + "\n".join(f"- {issue}" for issue in issues)
            )
        
        self.log_progress(f"Review completed: {'Passed' if review_passed else 'Failed'}")
        
        return review_result


# 노드 인스턴스
planning_node = PlanningNode()
development_node = DevelopmentNode()
testing_node = TestingNode()
deployment_node = DeploymentNode()
monitoring_node = MonitoringNode()
review_node = ReviewNode()