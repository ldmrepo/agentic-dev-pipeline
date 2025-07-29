"""
에이전트 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.planning.planning_agent import PlanningAgent
from src.agents.development.development_agent import DevelopmentAgent
from src.agents.testing.testing_agent import TestingAgent
from src.core.schemas import AgentContext, TaskType


class TestPlanningAgent:
    """계획 수립 에이전트 테스트"""
    
    @pytest.mark.asyncio
    async def test_planning_agent_initialization(self):
        """에이전트 초기화 테스트"""
        agent = PlanningAgent()
        
        assert agent.name == "PlanningAgent"
        assert agent.claude_client is not None
        assert agent.mcp_manager is not None
        
    @pytest.mark.asyncio
    async def test_analyze_requirements(self, mock_claude_response):
        """요구사항 분석 테스트"""
        agent = PlanningAgent()
        
        # Claude 클라이언트 모킹
        with patch.object(agent.claude_client, 'analyze', 
                         new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Todo API with authentication",
                "key_features": ["Authentication", "CRUD", "Database"],
                "technical_stack": ["FastAPI", "PostgreSQL", "Redis"]
            }
            
            result = await agent.analyze_requirements(
                "Create a REST API for todo app"
            )
            
            assert "summary" in result
            assert "key_features" in result
            assert len(result["key_features"]) == 3
            
    @pytest.mark.asyncio
    async def test_create_architecture(self):
        """아키텍처 설계 테스트"""
        agent = PlanningAgent()
        
        with patch.object(agent.claude_client, 'generate_code',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "layers": ["API", "Service", "Repository"],
                "components": {
                    "api": ["routes", "middleware"],
                    "service": ["business logic"],
                    "repository": ["database access"]
                }
            }
            
            requirements = {
                "summary": "Todo API",
                "key_features": ["CRUD", "Auth"]
            }
            
            result = await agent.create_architecture(requirements)
            
            assert "layers" in result
            assert "components" in result
            assert len(result["layers"]) == 3
            
    @pytest.mark.asyncio
    async def test_execute_planning(self, sample_requirements, sample_context):
        """계획 수립 실행 테스트"""
        agent = PlanningAgent()
        
        # 컨텍스트 생성
        context = AgentContext(
            requirements=sample_requirements,
            task_type=TaskType.FEATURE,
            constraints=[],
            metadata={"project": "test"}
        )
        
        # 모든 메서드 모킹
        with patch.multiple(
            agent,
            analyze_requirements=AsyncMock(return_value={
                "summary": "Todo API",
                "key_features": ["CRUD"]
            }),
            create_architecture=AsyncMock(return_value={
                "layers": ["API", "Service"]
            }),
            estimate_timeline=AsyncMock(return_value={
                "total_days": 10,
                "phases": {"development": 7, "testing": 3}
            }),
            identify_risks=AsyncMock(return_value=[
                {"risk": "Timeline", "mitigation": "Prioritize features"}
            ])
        ):
            result = await agent.execute(context)
            
            assert result.success
            assert "architecture" in result.output
            assert "timeline" in result.output
            assert len(result.artifacts) > 0


class TestDevelopmentAgent:
    """개발 에이전트 테스트"""
    
    @pytest.mark.asyncio
    async def test_generate_code(self):
        """코드 생성 테스트"""
        agent = DevelopmentAgent()
        
        with patch.object(agent.claude_client, 'generate_code',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
'''
            
            spec = {
                "component": "main",
                "type": "api",
                "requirements": "Basic FastAPI app"
            }
            
            result = await agent.generate_code(spec)
            
            assert "FastAPI" in result
            assert "@app.get" in result
            
    @pytest.mark.asyncio
    async def test_create_tests(self):
        """테스트 생성 테스트"""
        agent = DevelopmentAgent()
        
        with patch.object(agent.claude_client, 'generate_code',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''
import pytest
from fastapi.testclient import TestClient

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
'''
            
            code = "FastAPI application code"
            result = await agent.create_tests(code)
            
            assert "pytest" in result
            assert "test_read_root" in result
            
    @pytest.mark.asyncio
    async def test_execute_development(self, sample_context):
        """개발 실행 테스트"""
        agent = DevelopmentAgent()
        
        planning_result = {
            "architecture": {
                "components": ["api", "service", "repository"]
            },
            "technical_stack": ["FastAPI", "PostgreSQL"]
        }
        
        context = AgentContext(
            requirements="Create API",
            task_type=TaskType.FEATURE,
            previous_results={"planning": planning_result},
            metadata={}
        )
        
        # MCP 매니저 모킹
        with patch.object(agent.mcp_manager, 'call_tool',
                         new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = {"success": True}
            
            # Claude 클라이언트 모킹
            with patch.object(agent.claude_client, 'generate_code',
                             new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = "Generated code"
                
                result = await agent.execute(context)
                
                assert result.success
                assert len(result.artifacts) > 0
                assert any(a["type"] == "code" for a in result.artifacts)


class TestTestingAgent:
    """테스팅 에이전트 테스트"""
    
    @pytest.mark.asyncio
    async def test_generate_unit_tests(self):
        """단위 테스트 생성 테스트"""
        agent = TestingAgent()
        
        with patch.object(agent.claude_client, 'generate_code',
                         new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''
def test_add():
    assert add(2, 3) == 5
    
def test_subtract():
    assert subtract(5, 3) == 2
'''
            
            code_file = {
                "path": "math.py",
                "content": "def add(a, b): return a + b"
            }
            
            result = await agent.generate_unit_tests(code_file)
            
            assert "test_add" in result
            assert "assert" in result
            
    @pytest.mark.asyncio
    async def test_run_tests(self, mock_mcp_server):
        """테스트 실행 테스트"""
        agent = TestingAgent()
        
        test_files = ["test_main.py", "test_service.py"]
        
        with patch.object(agent.mcp_manager, 'call_tool',
                         new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = {
                "success": True,
                "output": "All tests passed",
                "coverage": 85.5
            }
            
            result = await agent.run_tests(test_files)
            
            assert result["success"]
            assert result["coverage"] == 85.5