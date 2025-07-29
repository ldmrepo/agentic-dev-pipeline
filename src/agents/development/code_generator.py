"""
코드 생성 관련 기능
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.core.schemas import CodeFile, ArtifactType
from src.core.exceptions import AgentExecutionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeGenerationInput(BaseModel):
    """코드 생성 입력"""
    language: str = Field(description="프로그래밍 언어")
    framework: Optional[str] = Field(default=None, description="프레임워크")
    specifications: Dict[str, Any] = Field(description="코드 명세")


class CodeGenerator:
    """코드 생성 도구"""
    
    @staticmethod
    def get_tools(llm, mcp_tools) -> List[Tool]:
        """코드 생성 관련 도구 반환"""
        return [
            Tool(
                name="generate_backend_code",
                description="백엔드 코드 생성 (API, 비즈니스 로직, 데이터 모델)",
                func=lambda input: CodeGenerator._generate_backend_code(llm, mcp_tools, input)
            ),
            Tool(
                name="generate_frontend_code",
                description="프론트엔드 코드 생성 (UI 컴포넌트, 상태 관리, 라우팅)",
                func=lambda input: CodeGenerator._generate_frontend_code(llm, mcp_tools, input)
            ),
            Tool(
                name="generate_infrastructure_code",
                description="인프라 코드 생성 (Docker, Kubernetes, Terraform)",
                func=lambda input: CodeGenerator._generate_infrastructure_code(llm, mcp_tools, input)
            ),
        ]
    
    @staticmethod
    def _generate_backend_code(llm, mcp_tools, input_str: str) -> str:
        """백엔드 코드 생성"""
        try:
            # 입력 파싱
            import json
            specs = json.loads(input_str)
            
            # 코드 생성 프롬프트
            prompt = f"""
            Generate backend code based on the following specifications:
            {json.dumps(specs, indent=2)}
            
            Requirements:
            1. Follow best practices for the chosen language/framework
            2. Include proper error handling
            3. Add comprehensive logging
            4. Implement input validation
            5. Include unit tests
            """
            
            response = llm.invoke(prompt)
            
            # 생성된 코드를 파일로 저장
            if "files" in specs:
                for file_spec in specs["files"]:
                    file_path = Path(file_spec["path"])
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # MCP 도구를 사용하여 파일 작성
                    mcp_tools.call_tool(
                        server="filesystem",
                        tool="write_file",
                        arguments={
                            "path": str(file_path),
                            "content": response.content
                        }
                    )
            
            return f"Successfully generated backend code: {response.content[:200]}..."
            
        except Exception as e:
            logger.error(f"Error generating backend code: {e}")
            raise AgentExecutionError(f"Failed to generate backend code: {str(e)}")
    
    @staticmethod
    def _generate_frontend_code(llm, mcp_tools, input_str: str) -> str:
        """프론트엔드 코드 생성"""
        try:
            import json
            specs = json.loads(input_str)
            
            prompt = f"""
            Generate frontend code based on the following specifications:
            {json.dumps(specs, indent=2)}
            
            Requirements:
            1. Create responsive UI components
            2. Implement proper state management
            3. Add accessibility features
            4. Include error boundaries
            5. Write component tests
            """
            
            response = llm.invoke(prompt)
            
            # 컴포넌트 파일 생성
            if "components" in specs:
                for component in specs["components"]:
                    file_path = Path(f"src/components/{component['name']}.tsx")
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    mcp_tools.call_tool(
                        server="filesystem",
                        tool="write_file",
                        arguments={
                            "path": str(file_path),
                            "content": response.content
                        }
                    )
            
            return f"Successfully generated frontend code: {response.content[:200]}..."
            
        except Exception as e:
            logger.error(f"Error generating frontend code: {e}")
            raise AgentExecutionError(f"Failed to generate frontend code: {str(e)}")
    
    @staticmethod
    def _generate_infrastructure_code(llm, mcp_tools, input_str: str) -> str:
        """인프라 코드 생성"""
        try:
            import json
            specs = json.loads(input_str)
            
            prompt = f"""
            Generate infrastructure as code based on the following specifications:
            {json.dumps(specs, indent=2)}
            
            Requirements:
            1. Create Docker configuration
            2. Generate Kubernetes manifests
            3. Include CI/CD pipeline
            4. Add monitoring configuration
            5. Implement security best practices
            """
            
            response = llm.invoke(prompt)
            
            # 인프라 파일 생성
            infra_files = {
                "Dockerfile": "docker/Dockerfile",
                "docker-compose.yml": "docker-compose.yml",
                "deployment.yaml": "k8s/deployment.yaml",
                "service.yaml": "k8s/service.yaml"
            }
            
            for file_type, file_path in infra_files.items():
                if file_type in specs.get("files", []):
                    path = Path(file_path)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    
                    mcp_tools.call_tool(
                        server="filesystem",
                        tool="write_file",
                        arguments={
                            "path": str(path),
                            "content": response.content
                        }
                    )
            
            return f"Successfully generated infrastructure code: {response.content[:200]}..."
            
        except Exception as e:
            logger.error(f"Error generating infrastructure code: {e}")
            raise AgentExecutionError(f"Failed to generate infrastructure code: {str(e)}")