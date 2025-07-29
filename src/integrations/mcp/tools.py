"""
MCP 도구 래퍼
LangChain Tool 형식으로 MCP 도구를 래핑
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import json

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.integrations.mcp.manager import get_mcp_manager

logger = logging.getLogger(__name__)

class MCPToolInput(BaseModel):
    """MCP 도구 입력 스키마"""
    params: Dict[str, Any] = Field(description="Tool parameters")

def create_mcp_tool(
    server_name: str,
    tool_name: str,
    description: str,
    params_schema: Optional[Dict[str, Any]] = None
) -> Tool:
    """
    MCP 도구를 LangChain Tool로 변환
    
    Args:
        server_name: MCP 서버 이름
        tool_name: 도구 이름
        description: 도구 설명
        params_schema: 파라미터 스키마 (OpenAPI 형식)
    
    Returns:
        LangChain Tool 인스턴스
    """
    async def tool_func(params: Dict[str, Any]) -> str:
        """도구 실행 함수"""
        manager = await get_mcp_manager()
        result = await manager.call_tool(server_name, tool_name, params)
        
        # 결과를 문자열로 변환
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return str(result)
    
    # 동기 래퍼 (LangChain 호환성)
    def sync_wrapper(params: Dict[str, Any]) -> str:
        import asyncio
        return asyncio.run(tool_func(params))
    
    return Tool(
        name=f"{server_name}_{tool_name}",
        description=description,
        func=sync_wrapper,
        args_schema=MCPToolInput
    )

# 사전 정의된 도구들
class MCPTools:
    """자주 사용하는 MCP 도구 모음"""
    
    @staticmethod
    def filesystem_read() -> Tool:
        """파일 읽기 도구"""
        return create_mcp_tool(
            server_name="filesystem",
            tool_name="read_file",
            description="Read contents of a file",
            params_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            }
        )
    
    @staticmethod
    def filesystem_write() -> Tool:
        """파일 쓰기 도구"""
        return create_mcp_tool(
            server_name="filesystem",
            tool_name="write_file",
            description="Write content to a file",
            params_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        )
    
    @staticmethod
    def filesystem_list() -> Tool:
        """디렉토리 목록 도구"""
        return create_mcp_tool(
            server_name="filesystem",
            tool_name="list_directory",
            description="List files in a directory",
            params_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                },
                "required": ["path"]
            }
        )
    
    @staticmethod
    def github_create_issue() -> Tool:
        """GitHub 이슈 생성 도구"""
        return create_mcp_tool(
            server_name="github",
            tool_name="create_issue",
            description="Create a GitHub issue",
            params_schema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "Repository name (owner/repo)"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body"},
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Issue labels"
                    }
                },
                "required": ["repository", "title", "body"]
            }
        )
    
    @staticmethod
    def github_create_pr() -> Tool:
        """GitHub PR 생성 도구"""
        return create_mcp_tool(
            server_name="github",
            tool_name="create_pull_request",
            description="Create a GitHub pull request",
            params_schema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "Repository name"},
                    "title": {"type": "string", "description": "PR title"},
                    "body": {"type": "string", "description": "PR body"},
                    "base": {"type": "string", "description": "Base branch", "default": "main"},
                    "head": {"type": "string", "description": "Head branch"}
                },
                "required": ["repository", "title", "body", "head"]
            }
        )
    
    @staticmethod
    def docker_build() -> Tool:
        """Docker 이미지 빌드 도구"""
        return create_mcp_tool(
            server_name="docker",
            tool_name="build_image",
            description="Build a Docker image",
            params_schema={
                "type": "object",
                "properties": {
                    "context": {"type": "string", "description": "Build context path"},
                    "tag": {"type": "string", "description": "Image tag"},
                    "dockerfile": {"type": "string", "description": "Dockerfile path", "default": "Dockerfile"}
                },
                "required": ["context", "tag"]
            }
        )
    
    @staticmethod
    def shell_execute() -> Tool:
        """쉘 명령 실행 도구"""
        return create_mcp_tool(
            server_name="shell",
            tool_name="execute",
            description="Execute a shell command",
            params_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "cwd": {"type": "string", "description": "Working directory"}
                },
                "required": ["command"]
            }
        )
    
    @staticmethod
    def search_code() -> Tool:
        """코드 검색 도구"""
        return create_mcp_tool(
            server_name="search",
            tool_name="grep",
            description="Search for patterns in code",
            params_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex)"},
                    "path": {"type": "string", "description": "Search path", "default": "."},
                    "file_type": {"type": "string", "description": "File extension filter"}
                },
                "required": ["pattern"]
            }
        )
    
    @staticmethod
    def postgres_query() -> Tool:
        """PostgreSQL 쿼리 실행 도구"""
        return create_mcp_tool(
            server_name="postgres",
            tool_name="execute_query",
            description="Execute a PostgreSQL query",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "database": {"type": "string", "description": "Database name"}
                },
                "required": ["query"]
            }
        )
    
    @staticmethod
    def get_common_tools() -> List[Tool]:
        """자주 사용하는 도구 세트 반환"""
        return [
            MCPTools.filesystem_read(),
            MCPTools.filesystem_write(),
            MCPTools.filesystem_list(),
            MCPTools.shell_execute(),
            MCPTools.search_code()
        ]
    
    @staticmethod
    def get_development_tools() -> List[Tool]:
        """개발 관련 도구 세트"""
        return [
            MCPTools.filesystem_read(),
            MCPTools.filesystem_write(),
            MCPTools.filesystem_list(),
            MCPTools.github_create_issue(),
            MCPTools.github_create_pr(),
            MCPTools.docker_build(),
            MCPTools.shell_execute(),
            MCPTools.search_code()
        ]
    
    @staticmethod
    def get_database_tools() -> List[Tool]:
        """데이터베이스 관련 도구 세트"""
        return [
            MCPTools.postgres_query(),
            MCPTools.shell_execute()  # 마이그레이션 등을 위해
        ]

# 도구 팩토리 함수
def create_tool_from_mcp_spec(server_name: str, tool_spec: Dict[str, Any]) -> Tool:
    """
    MCP 도구 스펙에서 LangChain Tool 생성
    
    Args:
        server_name: MCP 서버 이름
        tool_spec: MCP 도구 스펙 (name, description, inputSchema)
    
    Returns:
        LangChain Tool
    """
    return create_mcp_tool(
        server_name=server_name,
        tool_name=tool_spec["name"],
        description=tool_spec.get("description", ""),
        params_schema=tool_spec.get("inputSchema", {})
    )

async def discover_all_tools() -> List[Tool]:
    """
    모든 MCP 서버에서 사용 가능한 도구 자동 발견
    
    Returns:
        발견된 모든 도구 리스트
    """
    tools = []
    manager = await get_mcp_manager()
    
    # 각 서버에서 도구 목록 조회
    for server_name, server in manager.client.servers.items():
        try:
            tool_list = await server.list_tools()
            
            for tool_spec in tool_list:
                tool = create_tool_from_mcp_spec(server_name, tool_spec)
                tools.append(tool)
                
        except Exception as e:
            logger.warning(f"Failed to discover tools from {server_name}: {e}")
    
    logger.info(f"Discovered {len(tools)} tools from MCP servers")
    return tools