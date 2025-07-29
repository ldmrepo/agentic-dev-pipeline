"""
개발 에이전트 (리팩토링 버전)
코드 생성, API 구현, 데이터베이스 설계 등 개발 작업 수행
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from langchain.tools import Tool

from src.agents.base import BaseAgent, AgentContext, AgentResult
from src.integrations.mcp.tools import MCPTools
from src.core.schemas import DevelopmentResult, CodeFile, ArtifactType
from src.core.exceptions import AgentExecutionError
from src.utils.logger import get_logger, log_execution_time, log_agent_execution

# 분리된 모듈들 임포트
from .code_generator import CodeGenerator
from .api_designer import APIDesigner
from .database_designer import DatabaseDesigner

logger = get_logger(__name__)


class DevelopmentAgent(BaseAgent):
    """개발 AI 에이전트 (리팩토링 버전)"""
    
    def __init__(self):
        super().__init__(
            name="DevelopmentAgent",
            description="코드 생성, API 설계, 데이터베이스 설계 등 개발 작업 수행",
            version="2.0"
        )
        self.mcp_tools = MCPTools()
        
    def _get_tools(self) -> List[Tool]:
        """에이전트가 사용할 도구 목록"""
        tools = []
        
        # 코드 생성 도구
        tools.extend(CodeGenerator.get_tools(self.llm, self.mcp_tools))
        
        # API 설계 도구
        tools.extend(APIDesigner.get_tools(self.llm, self.mcp_tools))
        
        # 데이터베이스 설계 도구
        tools.extend(DatabaseDesigner.get_tools(self.llm, self.mcp_tools))
        
        # 기타 개발 도구
        tools.extend([
            Tool(
                name="setup_development_environment",
                description="개발 환경 설정 (의존성, 도구, 설정 파일)",
                func=self._setup_development_environment
            ),
            Tool(
                name="integrate_external_services",
                description="외부 서비스 통합 (API, 라이브러리, SDK)",
                func=self._integrate_external_services
            ),
            Tool(
                name="review_code_quality",
                description="코드 품질 검토 및 개선 제안",
                func=self._review_code_quality
            ),
        ])
        
        return tools
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """You are an expert software development agent specializing in:
        
        1. **Code Generation**:
           - Backend development (Python, Node.js, Go, Java)
           - Frontend development (React, Vue, Angular)
           - Mobile development (React Native, Flutter)
           - Infrastructure as Code (Terraform, CloudFormation)
        
        2. **API Design**:
           - RESTful API design and implementation
           - GraphQL schema design
           - API documentation and testing
           - Authentication and authorization
        
        3. **Database Design**:
           - Relational database design (PostgreSQL, MySQL)
           - NoSQL database design (MongoDB, Redis)
           - Query optimization
           - Data migration strategies
        
        4. **Best Practices**:
           - Clean code principles
           - Design patterns
           - SOLID principles
           - Security best practices
           - Performance optimization
        
        When developing code:
        - Always follow the language/framework conventions
        - Include comprehensive error handling
        - Add appropriate logging and monitoring
        - Write testable code
        - Consider scalability and maintainability
        - Document complex logic
        
        Output Format:
        - Provide clear, well-structured code
        - Include comments for complex sections
        - Add usage examples where appropriate
        - Suggest testing strategies
        """
    
    @log_execution_time
    async def execute(self, context: AgentContext) -> AgentResult:
        """개발 작업 실행"""
        import time
        start_time = time.time()
        
        try:
            # 개발 계획 분석
            plan = context.get("development_plan", {})
            task_type = context.get("task_type", "general")
            
            logger.info(
                f"Starting development task",
                extra={
                    "task_type": task_type,
                    "plan_components": list(plan.keys()) if isinstance(plan, dict) else None
                }
            )
            
            # 작업 유형에 따른 실행
            if task_type == "backend":
                result = await self._develop_backend(plan)
            elif task_type == "frontend":
                result = await self._develop_frontend(plan)
            elif task_type == "api":
                result = await self._develop_api(plan)
            elif task_type == "database":
                result = await self._develop_database(plan)
            elif task_type == "fullstack":
                result = await self._develop_fullstack(plan)
            else:
                result = await self._develop_general(plan)
            
            # 결과 정리
            artifacts = self._collect_artifacts(result)
            
            # 실행 시간 계산
            duration = time.time() - start_time
            
            # 에이전트 실행 로깅
            log_agent_execution(
                agent_name="DevelopmentAgent",
                status="success",
                duration=duration,
                task_type=task_type,
                files_created=len(artifacts)
            )
            
            return AgentResult(
                success=True,
                data={
                    "development_result": result,
                    "artifacts": artifacts,
                    "files_created": len(artifacts),
                    "summary": self._generate_summary(result)
                },
                artifacts=artifacts
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Development execution failed",
                extra={
                    "task_type": task_type,
                    "error": str(e),
                    "duration": duration
                },
                exc_info=True
            )
            
            # 에이전트 실행 실패 로깅
            log_agent_execution(
                agent_name="DevelopmentAgent",
                status="error",
                duration=duration,
                task_type=task_type,
                error=str(e)
            )
            
            return AgentResult(
                success=False,
                error=str(e),
                data={"error_details": str(e)}
            )
    
    async def _develop_backend(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """백엔드 개발"""
        logger.info("Developing backend components", extra={"components": plan.get("components", [])})
        
        # 백엔드 코드 생성
        backend_specs = {
            "language": plan.get("language", "python"),
            "framework": plan.get("framework", "fastapi"),
            "components": plan.get("components", []),
            "files": plan.get("files", [])
        }
        
        response = await self.agent.ainvoke({
            "input": f"Develop backend with specifications: {json.dumps(backend_specs)}",
            "tools": ["generate_backend_code", "design_database_schema", "design_rest_api"]
        })
        
        return {
            "type": "backend",
            "components": response.get("components", []),
            "apis": response.get("apis", []),
            "database": response.get("database", {})
        }
    
    async def _develop_frontend(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """프론트엔드 개발"""
        logger.info("Developing frontend components")
        
        frontend_specs = {
            "framework": plan.get("framework", "react"),
            "ui_library": plan.get("ui_library", "material-ui"),
            "components": plan.get("components", []),
            "pages": plan.get("pages", [])
        }
        
        response = await self.agent.ainvoke({
            "input": f"Develop frontend with specifications: {json.dumps(frontend_specs)}",
            "tools": ["generate_frontend_code"]
        })
        
        return {
            "type": "frontend",
            "components": response.get("components", []),
            "pages": response.get("pages", []),
            "styles": response.get("styles", [])
        }
    
    async def _develop_api(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """API 개발"""
        logger.info("Developing API")
        
        api_specs = {
            "type": plan.get("api_type", "rest"),
            "endpoints": plan.get("endpoints", []),
            "authentication": plan.get("authentication", "jwt"),
            "documentation": plan.get("documentation", True)
        }
        
        response = await self.agent.ainvoke({
            "input": f"Design and implement API: {json.dumps(api_specs)}",
            "tools": ["design_rest_api", "generate_api_documentation", "create_api_tests"]
        })
        
        return {
            "type": "api",
            "endpoints": response.get("endpoints", []),
            "documentation": response.get("documentation", {}),
            "tests": response.get("tests", [])
        }
    
    async def _develop_database(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 개발"""
        logger.info("Developing database")
        
        db_specs = {
            "type": plan.get("database_type", "postgresql"),
            "entities": plan.get("entities", []),
            "relationships": plan.get("relationships", []),
            "indexes": plan.get("indexes", [])
        }
        
        response = await self.agent.ainvoke({
            "input": f"Design database schema: {json.dumps(db_specs)}",
            "tools": ["design_database_schema", "generate_migrations", "optimize_database_queries"]
        })
        
        return {
            "type": "database",
            "schema": response.get("schema", {}),
            "migrations": response.get("migrations", []),
            "optimizations": response.get("optimizations", [])
        }
    
    async def _develop_fullstack(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """풀스택 개발"""
        logger.info("Developing fullstack application")
        
        # 백엔드, 프론트엔드, API, 데이터베이스 모두 개발
        results = {}
        
        if "backend" in plan:
            results["backend"] = await self._develop_backend(plan["backend"])
        
        if "frontend" in plan:
            results["frontend"] = await self._develop_frontend(plan["frontend"])
        
        if "api" in plan:
            results["api"] = await self._develop_api(plan["api"])
        
        if "database" in plan:
            results["database"] = await self._develop_database(plan["database"])
        
        return {
            "type": "fullstack",
            **results
        }
    
    async def _develop_general(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """일반 개발 작업"""
        logger.info("Executing general development task")
        
        response = await self.agent.ainvoke({
            "input": f"Execute development task: {json.dumps(plan)}",
            "tools": self.tool_names
        })
        
        return {
            "type": "general",
            "result": response
        }
    
    def _setup_development_environment(self, input_str: str) -> str:
        """개발 환경 설정"""
        try:
            specs = json.loads(input_str)
            
            # 패키지 매니저 파일 생성
            if specs.get("language") == "python":
                requirements = specs.get("dependencies", [])
                self.mcp_tools.call_tool(
                    server="filesystem",
                    tool="write_file",
                    arguments={
                        "path": "requirements.txt",
                        "content": "\n".join(requirements)
                    }
                )
            elif specs.get("language") == "javascript":
                package_json = {
                    "name": specs.get("project_name", "project"),
                    "version": "1.0.0",
                    "dependencies": specs.get("dependencies", {})
                }
                self.mcp_tools.call_tool(
                    server="filesystem",
                    tool="write_file",
                    arguments={
                        "path": "package.json",
                        "content": json.dumps(package_json, indent=2)
                    }
                )
            
            # 설정 파일 생성
            config_files = {
                ".gitignore": self._generate_gitignore(specs.get("language")),
                ".env.example": self._generate_env_example(specs),
                "README.md": self._generate_readme(specs)
            }
            
            for filename, content in config_files.items():
                self.mcp_tools.call_tool(
                    server="filesystem",
                    tool="write_file",
                    arguments={
                        "path": filename,
                        "content": content
                    }
                )
            
            return "Successfully set up development environment"
            
        except Exception as e:
            logger.error(
                "Error setting up development environment",
                extra={"error": str(e), "language": specs.get("language")},
                exc_info=True
            )
            return f"Failed to set up environment: {str(e)}"
    
    def _integrate_external_services(self, input_str: str) -> str:
        """외부 서비스 통합"""
        try:
            specs = json.loads(input_str)
            service_type = specs.get("service_type")
            
            integration_code = f"""
# {service_type} Integration
import os
from typing import Optional

class {service_type.title()}Client:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('{service_type.upper()}_API_KEY')
        
    def connect(self):
        # Implementation here
        pass
"""
            
            self.mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": f"src/integrations/{service_type}_client.py",
                    "content": integration_code
                }
            )
            
            return f"Successfully integrated {service_type} service"
            
        except Exception as e:
            logger.error(f"Error integrating external service: {e}")
            return f"Failed to integrate service: {str(e)}"
    
    def _review_code_quality(self, input_str: str) -> str:
        """코드 품질 검토"""
        try:
            specs = json.loads(input_str)
            file_path = specs.get("file_path")
            
            # 코드 읽기
            code_content = self.mcp_tools.call_tool(
                server="filesystem",
                tool="read_file",
                arguments={"path": file_path}
            )
            
            # 코드 품질 분석
            review_prompt = f"""
            Review the following code for quality:
            {code_content}
            
            Check for:
            1. Code style and formatting
            2. Potential bugs
            3. Performance issues
            4. Security vulnerabilities
            5. Best practices
            """
            
            review = self.llm.invoke(review_prompt)
            
            return f"Code review completed: {review.content}"
            
        except Exception as e:
            logger.error(f"Error reviewing code quality: {e}")
            return f"Failed to review code: {str(e)}"
    
    def _collect_artifacts(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """아티팩트 수집"""
        artifacts = []
        
        # 재귀적으로 결과에서 파일 정보 추출
        def extract_files(data: Any, prefix: str = ""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in ["files", "components", "endpoints", "schema"]:
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and "path" in item:
                                    artifacts.append({
                                        "name": item.get("name", Path(item["path"]).name),
                                        "type": ArtifactType.CODE,
                                        "path": item["path"],
                                        "description": item.get("description", "")
                                    })
                    else:
                        extract_files(value, f"{prefix}{key}.")
            elif isinstance(data, list):
                for item in data:
                    extract_files(item, prefix)
        
        extract_files(result)
        return artifacts
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """개발 결과 요약 생성"""
        summary_parts = []
        
        if "backend" in result:
            backend = result["backend"]
            summary_parts.append(f"Backend: {len(backend.get('components', []))} components")
        
        if "frontend" in result:
            frontend = result["frontend"]
            summary_parts.append(f"Frontend: {len(frontend.get('components', []))} components")
        
        if "api" in result:
            api = result["api"]
            summary_parts.append(f"API: {len(api.get('endpoints', []))} endpoints")
        
        if "database" in result:
            database = result["database"]
            summary_parts.append(f"Database: {len(database.get('schema', {}).get('tables', []))} tables")
        
        return " | ".join(summary_parts) if summary_parts else "Development completed"
    
    def _generate_gitignore(self, language: str) -> str:
        """언어별 .gitignore 생성"""
        common = """
# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment
.env
.env.local
"""
        
        language_specific = {
            "python": """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
.coverage
.pytest_cache/
htmlcov/
*.egg-info/
dist/
build/
""",
            "javascript": """
# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity
dist/
build/
.next/
out/
"""
        }
        
        return common + language_specific.get(language, "")
    
    def _generate_env_example(self, specs: Dict[str, Any]) -> str:
        """환경 변수 예제 생성"""
        env_vars = []
        
        # 기본 환경 변수
        env_vars.extend([
            "# Application",
            "APP_ENV=development",
            "APP_PORT=3000",
            ""
        ])
        
        # 데이터베이스
        if specs.get("database"):
            env_vars.extend([
                "# Database",
                "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
                ""
            ])
        
        # API 키
        if specs.get("external_services"):
            env_vars.extend([
                "# External Services",
                "API_KEY=your-api-key-here",
                ""
            ])
        
        return "\n".join(env_vars)
    
    def _generate_readme(self, specs: Dict[str, Any]) -> str:
        """README.md 생성"""
        return f"""# {specs.get('project_name', 'Project')}

{specs.get('description', 'Project description')}

## Installation

```bash
# Install dependencies
{self._get_install_command(specs.get('language'))}
```

## Usage

```bash
# Run the application
{self._get_run_command(specs.get('language'))}
```

## Development

```bash
# Run tests
{self._get_test_command(specs.get('language'))}
```

## License

MIT
"""
    
    def _get_install_command(self, language: str) -> str:
        """언어별 설치 명령"""
        commands = {
            "python": "pip install -r requirements.txt",
            "javascript": "npm install",
            "go": "go mod download",
            "java": "mvn install"
        }
        return commands.get(language, "# Install dependencies")
    
    def _get_run_command(self, language: str) -> str:
        """언어별 실행 명령"""
        commands = {
            "python": "python main.py",
            "javascript": "npm start",
            "go": "go run main.go",
            "java": "mvn spring-boot:run"
        }
        return commands.get(language, "# Run application")
    
    def _get_test_command(self, language: str) -> str:
        """언어별 테스트 명령"""
        commands = {
            "python": "pytest",
            "javascript": "npm test",
            "go": "go test ./...",
            "java": "mvn test"
        }
        return commands.get(language, "# Run tests")