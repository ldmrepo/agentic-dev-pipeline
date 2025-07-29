"""
태스크 분석 노드
요구사항을 분석하고 태스크 타입을 결정
"""

from typing import Dict, Any
import json

from src.orchestration.nodes.base import BaseNode, node_error_handler
from src.orchestration.state import WorkflowState, TaskType
from src.integrations.claude import claude_client
from src.core.schemas import ComplexityLevel

class AnalyzeTaskNode(BaseNode):
    """태스크 분석 노드"""
    
    def __init__(self):
        super().__init__("AnalyzeTask")
    
    @node_error_handler
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """태스크 분석 실행"""
        if not self.should_continue(state):
            return {"status": "cancelled"}
        
        requirements = state["requirements"]
        context = state.get("context", {})
        
        self.log_progress(f"Analyzing requirements: {requirements[:100]}...")
        
        # Claude API를 사용한 요구사항 분석
        prompt = self._create_analysis_prompt(requirements, context)
        
        try:
            response = await claude_client.analyze(prompt)
            analysis = self._parse_analysis_response(response)
            
            # 상태 업데이트
            state["task_type"] = TaskType(analysis["task_type"])
            
            # 메시지 추가
            self.add_message(
                state,
                f"Task analyzed: {analysis['task_type']} - Complexity: {analysis['complexity']}\n"
                f"Estimated effort: {analysis['estimated_hours']} hours"
            )
            
            # 토큰 사용량 업데이트
            if hasattr(response, 'usage'):
                self.update_token_usage(
                    state,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
            
            self.log_progress(f"Analysis complete: {analysis['task_type']}")
            
            return {
                "task_type": analysis["task_type"],
                "complexity": analysis["complexity"],
                "technical_requirements": analysis["technical_requirements"],
                "risks": analysis["risks"],
                "estimated_hours": analysis["estimated_hours"],
                "required_expertise": analysis["required_expertise"],
                "success_criteria": analysis["success_criteria"]
            }
            
        except Exception as e:
            self.log_progress(f"Analysis failed: {str(e)}", "error")
            raise
    
    def _create_analysis_prompt(self, requirements: str, context: Dict[str, Any]) -> str:
        """분석 프롬프트 생성"""
        prompt = f"""
Analyze the following software development requirements and provide a structured analysis.

Requirements:
{requirements}

Context:
- Project Type: {context.get('project_type', 'Not specified')}
- Technology Stack: {context.get('tech_stack', 'Not specified')}
- Team Size: {context.get('team_size', 'Not specified')}
- Timeline: {context.get('timeline', 'Not specified')}

Please analyze and provide the following information in JSON format:

1. Task Type Classification:
   - feature: New functionality
   - bugfix: Fix existing issues
   - hotfix: Urgent production fix
   - refactor: Code improvement without functional changes
   - documentation: Documentation updates

2. Complexity Assessment:
   - simple: < 1 day effort
   - medium: 1-5 days effort
   - complex: > 5 days effort

3. Technical Requirements:
   - List key technical components needed
   - Required APIs/services
   - Database changes
   - Infrastructure requirements

4. Risks and Challenges:
   - Technical risks
   - Dependencies
   - Potential blockers

5. Estimated Effort:
   - Hours required for completion
   - Breakdown by phase (planning, development, testing)

6. Required Expertise:
   - Technical skills needed
   - Domain knowledge required

7. Success Criteria:
   - Clear, measurable criteria for completion

Format your response as a valid JSON object with the following structure:
{{
    "task_type": "feature|bugfix|hotfix|refactor|documentation",
    "complexity": "simple|medium|complex",
    "technical_requirements": ["req1", "req2", ...],
    "risks": [
        {{"risk": "description", "impact": "high|medium|low", "mitigation": "strategy"}}
    ],
    "estimated_hours": number,
    "effort_breakdown": {{
        "planning": number,
        "development": number,
        "testing": number,
        "deployment": number
    }},
    "required_expertise": ["skill1", "skill2", ...],
    "success_criteria": ["criterion1", "criterion2", ...]
}}
"""
        return prompt
    
    def _parse_analysis_response(self, response: Any) -> Dict[str, Any]:
        """분석 응답 파싱"""
        try:
            # Claude 응답에서 내용 추출
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # JSON 파싱 시도
            # JSON 블록 찾기
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
            else:
                # 기본값 반환
                self.log_progress("Failed to parse JSON, using defaults", "warning")
                analysis = self._get_default_analysis()
            
            # 필수 필드 검증 및 기본값 설정
            return self._validate_analysis(analysis)
            
        except Exception as e:
            self.log_progress(f"Error parsing analysis response: {e}", "error")
            return self._get_default_analysis()
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 검증 및 기본값 설정"""
        # 필수 필드 기본값
        defaults = {
            "task_type": "feature",
            "complexity": "medium",
            "technical_requirements": [],
            "risks": [],
            "estimated_hours": 8,
            "effort_breakdown": {
                "planning": 2,
                "development": 4,
                "testing": 1,
                "deployment": 1
            },
            "required_expertise": ["general"],
            "success_criteria": ["Requirements implemented and tested"]
        }
        
        # 기본값으로 누락된 필드 채우기
        for key, default_value in defaults.items():
            if key not in analysis:
                analysis[key] = default_value
        
        # 타입 검증
        if analysis["task_type"] not in ["feature", "bugfix", "hotfix", "refactor", "documentation"]:
            analysis["task_type"] = "feature"
        
        if analysis["complexity"] not in ["simple", "medium", "complex"]:
            analysis["complexity"] = "medium"
        
        # 숫자 필드 검증
        try:
            analysis["estimated_hours"] = int(analysis["estimated_hours"])
        except:
            analysis["estimated_hours"] = 8
        
        return analysis
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과"""
        return {
            "task_type": "feature",
            "complexity": "medium",
            "technical_requirements": ["Requirements analysis needed"],
            "risks": [{
                "risk": "Incomplete requirements",
                "impact": "medium",
                "mitigation": "Iterative development with feedback"
            }],
            "estimated_hours": 8,
            "effort_breakdown": {
                "planning": 2,
                "development": 4,
                "testing": 1,
                "deployment": 1
            },
            "required_expertise": ["general development"],
            "success_criteria": ["Requirements implemented and tested"]
        }


# 노드 인스턴스
analyze_task_node = AnalyzeTaskNode()