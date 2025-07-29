"""
계획 수립 노드
분석된 요구사항을 기반으로 개발 계획 수립
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import TaskComplexity, ArtifactType

class PlanningNode(BaseNode):
    """계획 수립 노드"""
    
    def __init__(self):
        super().__init__(
            name="Planning",
            description="Create development plan based on analysis"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("analysis_result"):
            return "Analysis result is missing"
        
        analysis = state["analysis_result"]
        required_fields = ["task_type", "complexity", "estimated_hours", "technical_requirements"]
        
        for field in required_fields:
            if field not in analysis:
                return f"Analysis result missing required field: {field}"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """개발 계획 수립"""
        analysis = state["analysis_result"]
        requirements = state["requirements"]
        
        self.log_progress("Creating development plan...")
        
        # 계획 생성
        plan = await self._create_development_plan(analysis, requirements)
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Development plan created: {len(plan['tasks'])} tasks, "
            f"estimated {plan['total_hours']} hours",
            metadata={"plan_summary": {
                "total_tasks": len(plan["tasks"]),
                "total_hours": plan["total_hours"],
                "phases": len(plan["phases"])
            }}
        )
        
        # 계획 문서 아티팩트
        plan_artifact = self.add_artifact(
            state,
            name="development_plan",
            artifact_type=ArtifactType.DOCUMENT,
            content=json.dumps(plan, indent=2),
            metadata={"format": "json", "version": "1.0"}
        )
        
        # 아키텍처 다이어그램 (텍스트 기반)
        architecture_artifact = self.add_artifact(
            state,
            name="architecture_diagram",
            artifact_type=ArtifactType.DIAGRAM,
            content=self._create_architecture_diagram(plan),
            metadata={"format": "mermaid"}
        )
        
        # 결과 업데이트
        result_update = self.update_result(state, "planning_result", plan)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(plan_artifact)
        updates.update(architecture_artifact)
        updates.update(result_update)
        
        self.log_progress("Planning completed successfully")
        
        return updates
    
    async def _create_development_plan(self, analysis: Dict[str, Any], requirements: str) -> Dict[str, Any]:
        """개발 계획 생성"""
        complexity = analysis["complexity"]
        estimated_hours = analysis["estimated_hours"]
        tech_requirements = analysis["technical_requirements"]
        
        # 단계별 계획 생성
        phases = self._define_phases(complexity)
        tasks = self._create_tasks(tech_requirements, complexity, requirements)
        timeline = self._create_timeline(tasks, estimated_hours)
        resources = self._define_resources(analysis)
        
        plan = {
            "overview": {
                "total_hours": estimated_hours,
                "complexity": complexity,
                "start_date": datetime.utcnow().isoformat(),
                "estimated_end_date": (datetime.utcnow() + timedelta(hours=estimated_hours)).isoformat()
            },
            "phases": phases,
            "tasks": tasks,
            "timeline": timeline,
            "resources": resources,
            "architecture": self._define_architecture(tech_requirements),
            "risks": analysis.get("risks", []),
            "success_criteria": analysis.get("success_criteria", []),
            "milestones": self._define_milestones(phases, timeline)
        }
        
        return plan
    
    def _define_phases(self, complexity: str) -> List[Dict[str, Any]]:
        """개발 단계 정의"""
        base_phases = [
            {
                "id": "phase-1",
                "name": "Setup & Architecture",
                "description": "Project setup and architecture design",
                "deliverables": ["Project structure", "Architecture documentation"]
            },
            {
                "id": "phase-2",
                "name": "Core Implementation",
                "description": "Implement core functionality",
                "deliverables": ["Core features", "API endpoints", "Database schema"]
            },
            {
                "id": "phase-3",
                "name": "Testing & Refinement",
                "description": "Comprehensive testing and refinement",
                "deliverables": ["Test suite", "Bug fixes", "Performance optimization"]
            }
        ]
        
        # 복잡도에 따라 추가 단계
        if complexity in [TaskComplexity.COMPLEX.value, TaskComplexity.VERY_COMPLEX.value]:
            base_phases.insert(2, {
                "id": "phase-2b",
                "name": "Advanced Features",
                "description": "Implement advanced functionality",
                "deliverables": ["Advanced features", "Integration points"]
            })
        
        # 항상 배포 단계 포함
        base_phases.append({
            "id": "phase-4",
            "name": "Deployment & Documentation",
            "description": "Deploy and document the solution",
            "deliverables": ["Deployment configuration", "User documentation"]
        })
        
        return base_phases
    
    def _create_tasks(self, tech_requirements: List[str], complexity: str, requirements: str) -> List[Dict[str, Any]]:
        """작업 항목 생성"""
        tasks = []
        task_id = 1
        
        # 설정 태스크
        tasks.append({
            "id": f"task-{task_id}",
            "name": "Project Setup",
            "description": "Initialize project structure and dependencies",
            "category": "setup",
            "estimated_hours": 2,
            "dependencies": [],
            "assignee_type": "fullstack"
        })
        task_id += 1
        
        # 기술 요구사항별 태스크
        for req in tech_requirements:
            category = self._categorize_requirement(req)
            hours = self._estimate_task_hours(req, complexity)
            
            tasks.append({
                "id": f"task-{task_id}",
                "name": f"Implement {req}",
                "description": f"Develop and integrate {req}",
                "category": category,
                "estimated_hours": hours,
                "dependencies": [f"task-{task_id-1}"] if task_id > 1 else [],
                "assignee_type": self._determine_assignee(category)
            })
            task_id += 1
        
        # 테스트 태스크
        test_hours = max(4, int(sum(t["estimated_hours"] for t in tasks) * 0.3))
        tasks.append({
            "id": f"task-{task_id}",
            "name": "Write Tests",
            "description": "Create comprehensive test suite",
            "category": "testing",
            "estimated_hours": test_hours,
            "dependencies": [f"task-{i}" for i in range(2, task_id)],
            "assignee_type": "qa"
        })
        task_id += 1
        
        # 문서화 태스크
        tasks.append({
            "id": f"task-{task_id}",
            "name": "Documentation",
            "description": "Create user and technical documentation",
            "category": "documentation",
            "estimated_hours": 4,
            "dependencies": [f"task-{task_id-1}"],
            "assignee_type": "fullstack"
        })
        
        return tasks
    
    def _categorize_requirement(self, requirement: str) -> str:
        """요구사항 카테고리 분류"""
        req_lower = requirement.lower()
        
        if any(word in req_lower for word in ["ui", "frontend", "react", "vue"]):
            return "frontend"
        elif any(word in req_lower for word in ["api", "backend", "database", "server"]):
            return "backend"
        elif any(word in req_lower for word in ["deploy", "docker", "kubernetes", "ci/cd"]):
            return "infrastructure"
        else:
            return "general"
    
    def _estimate_task_hours(self, requirement: str, complexity: str) -> int:
        """태스크 시간 추정"""
        base_hours = 4
        
        # 복잡도에 따른 조정
        complexity_multiplier = {
            TaskComplexity.SIMPLE.value: 0.5,
            TaskComplexity.MEDIUM.value: 1.0,
            TaskComplexity.COMPLEX.value: 2.0,
            TaskComplexity.VERY_COMPLEX.value: 3.0
        }
        
        return int(base_hours * complexity_multiplier.get(complexity, 1.0))
    
    def _determine_assignee(self, category: str) -> str:
        """담당자 타입 결정"""
        assignee_map = {
            "frontend": "frontend",
            "backend": "backend",
            "infrastructure": "devops",
            "testing": "qa",
            "documentation": "technical_writer"
        }
        
        return assignee_map.get(category, "fullstack")
    
    def _create_timeline(self, tasks: List[Dict[str, Any]], total_hours: int) -> Dict[str, Any]:
        """타임라인 생성"""
        # 일일 작업 시간 (8시간)
        hours_per_day = 8
        total_days = total_hours / hours_per_day
        
        start_date = datetime.utcnow()
        
        timeline = {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=total_days)).isoformat(),
            "total_days": round(total_days, 1),
            "working_days": int(total_days),
            "buffer_days": max(1, int(total_days * 0.2)),  # 20% 버퍼
            "critical_path": self._calculate_critical_path(tasks)
        }
        
        return timeline
    
    def _calculate_critical_path(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """크리티컬 패스 계산 (단순화된 버전)"""
        # 실제로는 복잡한 알고리즘이 필요하지만, 여기서는 단순화
        critical_tasks = []
        
        for task in tasks:
            if task["estimated_hours"] >= 8 or not task["dependencies"]:
                critical_tasks.append(task["id"])
        
        return critical_tasks
    
    def _define_resources(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """필요 리소스 정의"""
        return {
            "team": {
                "required_expertise": analysis.get("required_expertise", []),
                "team_size": self._calculate_team_size(analysis["complexity"]),
                "roles": ["Developer", "QA Engineer", "DevOps Engineer"]
            },
            "tools": {
                "development": ["IDE", "Version Control", "API Testing Tools"],
                "deployment": ["Docker", "CI/CD Pipeline"],
                "monitoring": ["Logging", "Metrics", "Alerting"]
            },
            "infrastructure": {
                "development": "Local development environment",
                "staging": "Staging server",
                "production": "Production environment"
            }
        }
    
    def _calculate_team_size(self, complexity: str) -> int:
        """팀 규모 계산"""
        team_size_map = {
            TaskComplexity.SIMPLE.value: 1,
            TaskComplexity.MEDIUM.value: 2,
            TaskComplexity.COMPLEX.value: 3,
            TaskComplexity.VERY_COMPLEX.value: 4
        }
        
        return team_size_map.get(complexity, 2)
    
    def _define_architecture(self, tech_requirements: List[str]) -> Dict[str, Any]:
        """아키텍처 정의"""
        # 기본 아키텍처
        architecture = {
            "type": "microservices" if len(tech_requirements) > 5 else "monolithic",
            "layers": ["Presentation", "Business Logic", "Data Access"],
            "components": []
        }
        
        # 기술 요구사항에 따른 컴포넌트 추가
        for req in tech_requirements:
            if "api" in req.lower():
                architecture["components"].append({
                    "name": "REST API",
                    "type": "backend",
                    "technology": "FastAPI"
                })
            elif "frontend" in req.lower():
                architecture["components"].append({
                    "name": "Web UI",
                    "type": "frontend",
                    "technology": "React"
                })
            elif "database" in req.lower():
                architecture["components"].append({
                    "name": "Database",
                    "type": "data",
                    "technology": "PostgreSQL"
                })
        
        return architecture
    
    def _define_milestones(self, phases: List[Dict[str, Any]], timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """마일스톤 정의"""
        milestones = []
        
        phase_duration = float(timeline["total_days"]) / len(phases)
        current_date = datetime.utcnow()
        
        for i, phase in enumerate(phases):
            milestone_date = current_date + timedelta(days=phase_duration * (i + 1))
            
            milestones.append({
                "id": f"milestone-{i+1}",
                "name": f"{phase['name']} Complete",
                "date": milestone_date.isoformat(),
                "phase_id": phase["id"],
                "deliverables": phase["deliverables"]
            })
        
        return milestones
    
    def _create_architecture_diagram(self, plan: Dict[str, Any]) -> str:
        """아키텍처 다이어그램 생성 (Mermaid 형식)"""
        architecture = plan.get("architecture", {})
        components = architecture.get("components", [])
        
        diagram = """graph TD
    A[Client] --> B[Load Balancer]
    B --> C[Web Server]
"""
        
        # 컴포넌트별 추가
        for i, comp in enumerate(components):
            comp_id = chr(68 + i)  # D, E, F...
            diagram += f"    C --> {comp_id}[{comp['name']}]\n"
        
        # 데이터베이스가 있으면 추가
        if any("database" in c["name"].lower() for c in components):
            diagram += "    D --> DB[(Database)]\n"
        
        return diagram

# 노드 인스턴스 생성
planning_node = PlanningNode()