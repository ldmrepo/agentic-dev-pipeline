"""
계획 수립 에이전트
요구사항 분석과 프로젝트 계획 수립
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentContext, AgentResult
from src.integrations.mcp.tools import MCPTools
from src.core.schemas import (
    TaskAnalysis, ProjectPlan, WorkBreakdownItem,
    TaskComplexity, TaskType
)
from src.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

class RequirementsAnalysisInput(BaseModel):
    """요구사항 분석 입력"""
    requirements: str = Field(description="프로젝트 요구사항")
    constraints: List[str] = Field(default_factory=list, description="제약사항")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class PlanningAgent(BaseAgent):
    """계획 수립 AI 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            description="요구사항을 분석하고 프로젝트 계획을 수립하는 에이전트"
        )
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        return """You are an expert software architect and project planner.
Your role is to analyze requirements and create comprehensive project plans.

Key responsibilities:
1. Analyze and decompose complex requirements
2. Identify technical requirements and constraints
3. Create detailed work breakdown structures (WBS)
4. Estimate effort and timelines
5. Identify risks and dependencies
6. Define success criteria
7. Suggest appropriate architecture and technology stack

When analyzing requirements:
- Be thorough and consider all aspects
- Break down complex tasks into manageable pieces
- Consider both functional and non-functional requirements
- Think about scalability, security, and maintainability
- Provide realistic time estimates
- Identify potential challenges early

Output Format:
- Task Analysis: complexity, technical requirements, risks
- Architecture: system design, components, integrations
- WBS: detailed task breakdown with dependencies
- Timeline: realistic schedule with milestones
- Resources: required skills and tools
- Success Criteria: measurable goals"""
    
    def _get_specialized_tools(self) -> List[Tool]:
        """계획 수립 전문 도구"""
        tools = []
        
        # 요구사항 분석 도구
        def analyze_requirements(requirements: str) -> str:
            """요구사항을 분석하여 기술 요구사항 도출"""
            return f"Analyzed requirements: {requirements[:100]}..."
        
        tools.append(Tool(
            name="analyze_requirements",
            description="Analyze project requirements to extract technical requirements",
            func=analyze_requirements
        ))
        
        # 작업 분해 도구
        def create_wbs(requirements: str) -> str:
            """작업 분해 구조(WBS) 생성"""
            return "Created work breakdown structure"
        
        tools.append(Tool(
            name="create_wbs",
            description="Create work breakdown structure from requirements",
            func=create_wbs
        ))
        
        # 리스크 분석 도구
        def identify_risks(plan: str) -> str:
            """프로젝트 리스크 식별"""
            return "Identified project risks"
        
        tools.append(Tool(
            name="identify_risks",
            description="Identify potential risks in the project",
            func=identify_risks
        ))
        
        # 파일 시스템 도구 추가
        tools.extend([
            MCPTools.filesystem_read(),
            MCPTools.filesystem_write(),
            MCPTools.search_code()
        ])
        
        return tools
    
    async def analyze_task(self, context: AgentContext) -> TaskAnalysis:
        """태스크 분석
        
        Args:
            context: 에이전트 컨텍스트
            
        Returns:
            태스크 분석 결과
        """
        # 복잡도 판단
        requirements_length = len(context.requirements)
        has_integration = "api" in context.requirements.lower() or "integrate" in context.requirements.lower()
        has_ui = "ui" in context.requirements.lower() or "frontend" in context.requirements.lower()
        has_data = "database" in context.requirements.lower() or "data" in context.requirements.lower()
        
        # 복잡도 계산
        complexity_score = 0
        if requirements_length > 500:
            complexity_score += 1
        if has_integration:
            complexity_score += 1
        if has_ui:
            complexity_score += 1
        if has_data:
            complexity_score += 1
        
        if complexity_score <= 1:
            complexity = TaskComplexity.SIMPLE
        elif complexity_score <= 2:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.COMPLEX
        
        # 기술 요구사항 추출
        technical_requirements = []
        if has_ui:
            technical_requirements.append("Frontend development")
        if has_data:
            technical_requirements.append("Database design")
        if has_integration:
            technical_requirements.append("API integration")
        
        # 리스크 식별
        risks = []
        if complexity == TaskComplexity.COMPLEX:
            risks.append("High complexity may lead to delays")
        if has_integration:
            risks.append("External API dependencies")
        
        # 예상 시간 계산 (복잡도 기반)
        base_hours = {
            TaskComplexity.SIMPLE: 8,
            TaskComplexity.MEDIUM: 24,
            TaskComplexity.COMPLEX: 40
        }
        estimated_hours = base_hours[complexity]
        
        return TaskAnalysis(
            task_type=TaskType.FEATURE,  # 기본값, 실제로는 분석 필요
            complexity=complexity,
            technical_requirements=technical_requirements,
            risks=risks,
            challenges=["Clear requirement definition", "Testing strategy"],
            estimated_hours=estimated_hours,
            required_expertise=["Python", "Software Architecture"],
            dependencies=[]
        )
    
    async def create_project_plan(self, analysis: TaskAnalysis, requirements: str) -> ProjectPlan:
        """프로젝트 계획 수립
        
        Args:
            analysis: 태스크 분석 결과
            requirements: 요구사항
            
        Returns:
            프로젝트 계획
        """
        # 아키텍처 설계
        architecture = {
            "overview": "Modular architecture with clear separation of concerns",
            "components": [
                {"name": "API Layer", "description": "RESTful API endpoints"},
                {"name": "Business Logic", "description": "Core application logic"},
                {"name": "Data Layer", "description": "Database interactions"}
            ],
            "technologies": ["Python", "FastAPI", "PostgreSQL"]
        }
        
        # WBS 생성
        wbs = []
        task_id = 1
        
        # 주요 단계별 작업 생성
        phases = [
            ("Requirements Analysis", "Detailed analysis of requirements", 4),
            ("System Design", "Architecture and design documentation", 8),
            ("Implementation", "Core functionality development", analysis.estimated_hours * 0.6),
            ("Testing", "Unit and integration testing", analysis.estimated_hours * 0.2),
            ("Documentation", "API and user documentation", analysis.estimated_hours * 0.1),
            ("Deployment", "Deployment and monitoring setup", 4)
        ]
        
        for phase_name, description, hours in phases:
            wbs.append(WorkBreakdownItem(
                task_id=f"T{task_id:03d}",
                task_name=phase_name,
                description=description,
                estimated_hours=int(hours),
                dependencies=[f"T{task_id-1:03d}"] if task_id > 1 else [],
                assignee_type="AI_Agent"
            ))
            task_id += 1
        
        # 타임라인 생성
        start_date = datetime.utcnow()
        timeline = {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(hours=analysis.estimated_hours)).isoformat(),
            "milestones": [
                {
                    "name": "Design Complete",
                    "date": (start_date + timedelta(hours=12)).isoformat()
                },
                {
                    "name": "MVP Ready",
                    "date": (start_date + timedelta(hours=analysis.estimated_hours * 0.7)).isoformat()
                },
                {
                    "name": "Production Ready",
                    "date": (start_date + timedelta(hours=analysis.estimated_hours)).isoformat()
                }
            ]
        }
        
        # 리소스 계획
        resources = {
            "human": ["1 Senior Developer", "1 DevOps Engineer"],
            "tools": ["GitHub", "Docker", "Kubernetes"],
            "infrastructure": ["Cloud hosting", "CI/CD pipeline"]
        }
        
        # 성공 기준
        success_criteria = [
            "All functional requirements implemented",
            "95% test coverage achieved",
            "Performance benchmarks met",
            "Zero critical security vulnerabilities",
            "Documentation complete"
        ]
        
        # 리스크와 완화 전략
        risks = []
        for risk in analysis.risks:
            risks.append({
                "risk": risk,
                "impact": "Medium",
                "probability": "Low",
                "mitigation": "Regular monitoring and early detection"
            })
        
        return ProjectPlan(
            architecture=architecture,
            wbs=wbs,
            timeline=timeline,
            risks=risks,
            resources=resources,
            success_criteria=success_criteria
        )
    
    async def _process_result(self, raw_result: Dict[str, Any], context: AgentContext) -> AgentResult:
        """결과 처리"""
        try:
            # 에이전트 출력에서 계획 추출
            output = raw_result.get("output", "")
            
            # 태스크 분석
            analysis = await self.analyze_task(context)
            
            # 프로젝트 계획 수립
            plan = await self.create_project_plan(analysis, context.requirements)
            
            # 아티팩트 생성
            artifacts = []
            
            # 1. 프로젝트 계획 문서
            plan_doc = {
                "name": "project_plan.md",
                "type": "documentation",
                "content": self._format_plan_document(plan, analysis),
                "metadata": {
                    "format": "markdown",
                    "version": "1.0"
                }
            }
            artifacts.append(plan_doc)
            
            # 2. WBS 파일
            wbs_data = {
                "name": "work_breakdown_structure.json",
                "type": "data",
                "content": json.dumps([item.model_dump() for item in plan.wbs], indent=2),
                "metadata": {
                    "format": "json",
                    "total_tasks": len(plan.wbs),
                    "total_hours": sum(item.estimated_hours for item in plan.wbs)
                }
            }
            artifacts.append(wbs_data)
            
            # 3. 아키텍처 다이어그램 (PlantUML)
            architecture_diagram = {
                "name": "architecture.puml",
                "type": "diagram",
                "content": self._generate_architecture_diagram(plan.architecture),
                "metadata": {
                    "format": "plantuml",
                    "type": "component_diagram"
                }
            }
            artifacts.append(architecture_diagram)
            
            # 결과 구성
            result_data = {
                "task_analysis": analysis.model_dump(),
                "project_plan": plan.model_dump(),
                "summary": {
                    "total_tasks": len(plan.wbs),
                    "estimated_hours": analysis.estimated_hours,
                    "complexity": analysis.complexity.value,
                    "risk_count": len(plan.risks)
                }
            }
            
            return AgentResult(
                success=True,
                output=result_data,
                artifacts=artifacts,
                messages=[
                    f"Successfully analyzed requirements and created project plan",
                    f"Identified {len(plan.wbs)} tasks with total effort of {analysis.estimated_hours} hours",
                    f"Project complexity: {analysis.complexity.value}"
                ],
                metrics={
                    "wbs_tasks": len(plan.wbs),
                    "estimated_hours": analysis.estimated_hours,
                    "artifacts_created": len(artifacts)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process planning result: {e}")
            return AgentResult(
                success=False,
                output=None,
                errors=[str(e)],
                metrics={"error_type": type(e).__name__}
            )
    
    def _format_plan_document(self, plan: ProjectPlan, analysis: TaskAnalysis) -> str:
        """프로젝트 계획을 마크다운 문서로 포맷"""
        doc = f"""# Project Plan

## Executive Summary
- **Complexity**: {analysis.complexity.value}
- **Estimated Effort**: {analysis.estimated_hours} hours
- **Key Risks**: {len(analysis.risks)}
- **Total Tasks**: {len(plan.wbs)}

## Technical Requirements
{chr(10).join(f"- {req}" for req in analysis.technical_requirements)}

## Architecture Overview
{plan.architecture.get('overview', 'N/A')}

### Components
{chr(10).join(f"- **{comp['name']}**: {comp['description']}" for comp in plan.architecture.get('components', []))}

### Technology Stack
{chr(10).join(f"- {tech}" for tech in plan.architecture.get('technologies', []))}

## Work Breakdown Structure
| Task ID | Task Name | Hours | Dependencies |
|---------|-----------|-------|--------------|
{chr(10).join(f"| {task.task_id} | {task.task_name} | {task.estimated_hours} | {', '.join(task.dependencies) or 'None'} |" for task in plan.wbs)}

## Timeline
- **Start Date**: {plan.timeline['start_date']}
- **End Date**: {plan.timeline['end_date']}

### Milestones
{chr(10).join(f"- {m['name']}: {m['date']}" for m in plan.timeline.get('milestones', []))}

## Risk Management
{chr(10).join(f"- **{r['risk']}**: {r['mitigation']}" for r in plan.risks)}

## Success Criteria
{chr(10).join(f"- {criterion}" for criterion in plan.success_criteria)}

## Resources Required
### Human Resources
{chr(10).join(f"- {resource}" for resource in plan.resources.get('human', []))}

### Tools & Infrastructure
{chr(10).join(f"- {tool}" for tool in plan.resources.get('tools', []))}
"""
        return doc
    
    def _generate_architecture_diagram(self, architecture: Dict[str, Any]) -> str:
        """아키텍처 다이어그램 생성 (PlantUML)"""
        components = architecture.get('components', [])
        
        diagram = """@startuml
!theme plain
title System Architecture

package "Application" {
"""
        
        for comp in components:
            diagram += f"  component [{comp['name']}] as {comp['name'].replace(' ', '')}\n"
        
        diagram += "}\n\n"
        
        # 기본 관계 추가
        if len(components) > 1:
            diagram += "note right: Components communicate via defined interfaces\n"
            for i in range(len(components) - 1):
                comp1 = components[i]['name'].replace(' ', '')
                comp2 = components[i + 1]['name'].replace(' ', '')
                diagram += f"{comp1} --> {comp2}\n"
        
        diagram += "\n@enduml"
        
        return diagram
    
    async def _validate_specific_input(self, context: AgentContext) -> Optional[str]:
        """계획 수립 특화 입력 검증"""
        if len(context.requirements) < 10:
            return "Requirements too short - please provide detailed requirements"
        
        if len(context.requirements) > 10000:
            return "Requirements too long - please summarize to under 10000 characters"
        
        return None
    
    async def _validate_specific_output(self, result: AgentResult) -> Optional[str]:
        """계획 수립 특화 출력 검증"""
        if not result.output:
            return "No plan generated"
        
        output = result.output
        if not isinstance(output, dict):
            return "Invalid output format"
        
        # 필수 필드 확인
        required_fields = ["task_analysis", "project_plan"]
        for field in required_fields:
            if field not in output:
                return f"Missing required field: {field}"
        
        # WBS 검증
        plan = output.get("project_plan", {})
        wbs = plan.get("wbs", [])
        if not wbs:
            return "No work breakdown structure created"
        
        # 아티팩트 검증
        if len(result.artifacts) < 2:
            return "Insufficient artifacts generated"
        
        return None