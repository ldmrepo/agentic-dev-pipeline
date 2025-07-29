"""
API 설계 관련 기능
"""

import logging
from typing import Dict, Any, List, Optional
import json

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)


class APIEndpointSpec(BaseModel):
    """API 엔드포인트 명세"""
    method: str = Field(description="HTTP 메서드")
    path: str = Field(description="엔드포인트 경로")
    description: str = Field(description="엔드포인트 설명")
    request_schema: Optional[Dict[str, Any]] = Field(default=None)
    response_schema: Optional[Dict[str, Any]] = Field(default=None)


class APIDesigner:
    """API 설계 도구"""
    
    @staticmethod
    def get_tools(llm, mcp_tools) -> List[Tool]:
        """API 설계 관련 도구 반환"""
        return [
            Tool(
                name="design_rest_api",
                description="RESTful API 설계 및 OpenAPI 스펙 생성",
                func=lambda input: APIDesigner._design_rest_api(llm, mcp_tools, input)
            ),
            Tool(
                name="generate_api_documentation",
                description="API 문서 자동 생성",
                func=lambda input: APIDesigner._generate_api_documentation(llm, mcp_tools, input)
            ),
            Tool(
                name="create_api_tests",
                description="API 테스트 코드 생성",
                func=lambda input: APIDesigner._create_api_tests(llm, mcp_tools, input)
            ),
        ]
    
    @staticmethod
    def _design_rest_api(llm, mcp_tools, input_str: str) -> str:
        """RESTful API 설계"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Design a RESTful API based on the following requirements:
            {json.dumps(specs, indent=2)}
            
            Generate:
            1. Complete OpenAPI 3.0 specification
            2. Endpoint definitions with request/response schemas
            3. Authentication and authorization strategy
            4. Error handling conventions
            5. Versioning strategy
            
            Follow REST best practices and include HATEOAS where appropriate.
            """
            
            response = llm.invoke(prompt)
            
            # OpenAPI 스펙 저장
            openapi_spec = response.content
            mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": "api/openapi.yaml",
                    "content": openapi_spec
                }
            )
            
            # API 라우트 파일 생성
            if "endpoints" in specs:
                for endpoint in specs["endpoints"]:
                    route_file = f"src/api/routes/{endpoint['resource']}.py"
                    mcp_tools.call_tool(
                        server="filesystem",
                        tool="write_file",
                        arguments={
                            "path": route_file,
                            "content": APIDesigner._generate_route_code(endpoint)
                        }
                    )
            
            return f"Successfully designed REST API with {len(specs.get('endpoints', []))} endpoints"
            
        except Exception as e:
            logger.error(f"Error designing REST API: {e}")
            raise AgentExecutionError(f"Failed to design REST API: {str(e)}")
    
    @staticmethod
    def _generate_api_documentation(llm, mcp_tools, input_str: str) -> str:
        """API 문서 생성"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Generate comprehensive API documentation for:
            {json.dumps(specs, indent=2)}
            
            Include:
            1. Getting started guide
            2. Authentication documentation
            3. Endpoint reference with examples
            4. Error codes and troubleshooting
            5. Rate limiting and best practices
            6. SDK usage examples
            """
            
            response = llm.invoke(prompt)
            
            # 문서 파일 생성
            doc_files = {
                "README.md": "api/docs/README.md",
                "AUTHENTICATION.md": "api/docs/AUTHENTICATION.md",
                "ENDPOINTS.md": "api/docs/ENDPOINTS.md",
                "ERRORS.md": "api/docs/ERRORS.md"
            }
            
            for doc_type, file_path in doc_files.items():
                mcp_tools.call_tool(
                    server="filesystem",
                    tool="write_file",
                    arguments={
                        "path": file_path,
                        "content": response.content
                    }
                )
            
            return "Successfully generated API documentation"
            
        except Exception as e:
            logger.error(f"Error generating API documentation: {e}")
            raise AgentExecutionError(f"Failed to generate API documentation: {str(e)}")
    
    @staticmethod
    def _create_api_tests(llm, mcp_tools, input_str: str) -> str:
        """API 테스트 생성"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Create comprehensive API tests for:
            {json.dumps(specs, indent=2)}
            
            Generate:
            1. Unit tests for each endpoint
            2. Integration tests for workflows
            3. Load testing scripts
            4. Security testing scenarios
            5. Mock data generators
            """
            
            response = llm.invoke(prompt)
            
            # 테스트 파일 생성
            test_file = "tests/api/test_endpoints.py"
            mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": test_file,
                    "content": response.content
                }
            )
            
            return "Successfully created API tests"
            
        except Exception as e:
            logger.error(f"Error creating API tests: {e}")
            raise AgentExecutionError(f"Failed to create API tests: {str(e)}")
    
    @staticmethod
    def _generate_route_code(endpoint: Dict[str, Any]) -> str:
        """라우트 코드 생성"""
        return f"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

@router.{endpoint['method'].lower()}("{endpoint['path']}")
async def {endpoint['operation_id']}():
    \"\"\"
    {endpoint['description']}
    \"\"\"
    # Implementation here
    pass
"""