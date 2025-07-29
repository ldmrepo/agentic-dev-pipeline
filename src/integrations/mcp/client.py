"""
MCP (Model Context Protocol) 클라이언트
외부 도구 및 서비스와의 통합을 위한 MCP 구현
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import subprocess
from pathlib import Path

from src.core.config import get_settings
from src.core.exceptions import IntegrationError, ToolExecutionError

logger = logging.getLogger(__name__)
settings = get_settings()

class MCPTransport(Enum):
    """MCP 전송 방식"""
    STDIO = "stdio"
    WEBSOCKET = "websocket"
    HTTP_SSE = "http_sse"

@dataclass
class MCPServerConfig:
    """MCP 서버 설정"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    transport: MCPTransport = MCPTransport.STDIO
    health_check_interval: int = 30
    restart_on_failure: bool = True
    max_retries: int = 3

class MCPServer:
    """개별 MCP 서버 관리"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_running = False
        self.retry_count = 0
        self._lock = asyncio.Lock()
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        
    async def start(self):
        """서버 프로세스 시작"""
        async with self._lock:
            if self.is_running:
                logger.warning(f"MCP server {self.config.name} is already running")
                return
            
            try:
                # 환경 변수 설정
                env = os.environ.copy()
                env.update(self.config.env)
                
                # 프로세스 시작
                if self.config.transport == MCPTransport.STDIO:
                    self.process = await asyncio.create_subprocess_exec(
                        self.config.command,
                        *self.config.args,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env
                    )
                    
                    self.reader = self.process.stdout
                    self.writer = self.process.stdin
                    
                    # 응답 처리 태스크 시작
                    asyncio.create_task(self._handle_responses())
                    
                self.is_running = True
                self.retry_count = 0
                logger.info(f"MCP server {self.config.name} started successfully")
                
            except Exception as e:
                logger.error(f"Failed to start MCP server {self.config.name}: {e}")
                raise IntegrationError(f"MCP server start failed: {e}")
    
    async def stop(self):
        """서버 프로세스 중지"""
        async with self._lock:
            if not self.is_running:
                return
            
            try:
                if self.process:
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    
            except asyncio.TimeoutError:
                logger.warning(f"MCP server {self.config.name} did not terminate, killing")
                if self.process:
                    self.process.kill()
                    await self.process.wait()
            
            self.is_running = False
            self.process = None
            self.reader = None
            self.writer = None
            
            # 대기 중인 요청 취소
            for future in self._pending_requests.values():
                if not future.done():
                    future.cancel()
            self._pending_requests.clear()
            
            logger.info(f"MCP server {self.config.name} stopped")
    
    async def restart(self):
        """서버 재시작"""
        logger.info(f"Restarting MCP server {self.config.name}")
        await self.stop()
        await asyncio.sleep(1)  # 잠시 대기
        await self.start()
    
    async def health_check(self) -> bool:
        """서버 상태 확인"""
        if not self.is_running or not self.process:
            return False
        
        # 프로세스 상태 확인
        if self.process.returncode is not None:
            return False
        
        # 간단한 ping 요청
        try:
            result = await self.call_tool("ping", {})
            return result.get("status") == "ok"
        except:
            return False
    
    async def call_tool(self, tool: str, params: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """
        MCP 도구 호출
        
        Args:
            tool: 도구 이름
            params: 도구 파라미터
            timeout: 요청 타임아웃
            
        Returns:
            도구 실행 결과
        """
        if not self.is_running:
            raise IntegrationError(f"MCP server {self.config.name} is not running")
        
        # 요청 ID 생성
        request_id = self._get_next_request_id()
        
        # 요청 메시지 구성
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": params
            }
        }
        
        # Future 생성
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # 요청 전송
            await self._send_request(request)
            
            # 응답 대기
            result = await asyncio.wait_for(future, timeout=timeout)
            
            # 에러 확인
            if "error" in result:
                raise ToolExecutionError(
                    f"Tool {tool} failed: {result['error'].get('message', 'Unknown error')}"
                )
            
            return result.get("result", {})
            
        except asyncio.TimeoutError:
            raise ToolExecutionError(f"Tool {tool} execution timeout")
        finally:
            # 요청 정리
            self._pending_requests.pop(request_id, None)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self._send_request_and_wait(request)
        return response.get("result", {}).get("tools", [])
    
    async def _send_request(self, request: Dict[str, Any]):
        """요청 전송"""
        if not self.writer:
            raise IntegrationError("No writer available")
        
        # JSON-RPC 메시지 전송
        message = json.dumps(request) + "\n"
        self.writer.write(message.encode())
        await self.writer.drain()
    
    async def _send_request_and_wait(self, request: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """요청 전송 후 응답 대기"""
        request_id = request["id"]
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            await self._send_request(request)
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._pending_requests.pop(request_id, None)
    
    async def _handle_responses(self):
        """응답 처리 루프"""
        while self.is_running and self.reader:
            try:
                line = await self.reader.readline()
                if not line:
                    break
                
                # JSON 파싱
                try:
                    response = json.loads(line.decode().strip())
                except json.JSONDecodeError:
                    continue
                
                # 요청 ID 확인
                request_id = response.get("id")
                if request_id in self._pending_requests:
                    future = self._pending_requests[request_id]
                    if not future.done():
                        future.set_result(response)
                
                # 알림 처리
                if response.get("method") == "notifications/message":
                    await self._handle_notification(response.get("params", {}))
                    
            except Exception as e:
                logger.error(f"Error handling response from {self.config.name}: {e}")
    
    async def _handle_notification(self, params: Dict[str, Any]):
        """서버 알림 처리"""
        logger.info(f"Notification from {self.config.name}: {params}")
    
    def _get_next_request_id(self) -> int:
        """다음 요청 ID 생성"""
        self._request_id += 1
        return self._request_id

class MCPClient:
    """MCP 클라이언트 - 여러 MCP 서버 관리"""
    
    def __init__(self, server_configs: Dict[str, Dict[str, Any]]):
        self.servers: Dict[str, MCPServer] = {}
        self._initialize_servers(server_configs)
    
    def _initialize_servers(self, configs: Dict[str, Dict[str, Any]]):
        """서버 초기화"""
        for name, config in configs.items():
            server_config = MCPServerConfig(
                name=name,
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {}),
                transport=MCPTransport(config.get("transport", "stdio"))
            )
            self.servers[name] = MCPServer(server_config)
    
    async def start_all(self):
        """모든 서버 시작"""
        tasks = [server.start() for server in self.servers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_all(self):
        """모든 서버 중지"""
        tasks = [server.stop() for server in self.servers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def call_tool(self, server_name: str, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """특정 서버의 도구 호출"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        return await server.call_tool(tool, params)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """모든 서버 상태 확인"""
        results = {}
        for name, server in self.servers.items():
            results[name] = await server.health_check()
        return results
    
    # 편의 메서드들
    async def read_file(self, path: str) -> str:
        """파일 읽기 (filesystem 서버)"""
        result = await self.call_tool(
            "filesystem",
            "read_file",
            {"path": path}
        )
        return result.get("content", "")
    
    async def write_file(self, path: str, content: str):
        """파일 쓰기 (filesystem 서버)"""
        await self.call_tool(
            "filesystem",
            "write_file",
            {"path": path, "content": content}
        )
    
    async def list_directory(self, path: str) -> List[str]:
        """디렉토리 목록 (filesystem 서버)"""
        result = await self.call_tool(
            "filesystem",
            "list_directory",
            {"path": path}
        )
        return result.get("files", [])
    
    async def create_github_issue(self, repo: str, title: str, body: str, labels: List[str] = None):
        """GitHub 이슈 생성 (github 서버)"""
        params = {
            "repository": repo,
            "title": title,
            "body": body
        }
        if labels:
            params["labels"] = labels
            
        return await self.call_tool("github", "create_issue", params)
    
    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        base: str = "main",
        head: str = None
    ):
        """GitHub PR 생성 (github 서버)"""
        return await self.call_tool(
            "github",
            "create_pull_request",
            {
                "repository": repo,
                "title": title,
                "body": body,
                "base": base,
                "head": head
            }
        )
    
    async def run_docker_command(self, command: List[str], **kwargs):
        """Docker 명령 실행 (docker 서버)"""
        return await self.call_tool(
            "docker",
            "run_command",
            {"command": command, **kwargs}
        )
    
    async def build_docker_image(self, context: str, tag: str, dockerfile: str = "Dockerfile"):
        """Docker 이미지 빌드 (docker 서버)"""
        return await self.call_tool(
            "docker",
            "build_image",
            {
                "context": context,
                "tag": tag,
                "dockerfile": dockerfile
            }
        )
    
    async def execute_sql(self, query: str, database: str = None):
        """SQL 쿼리 실행 (postgres 서버)"""
        params = {"query": query}
        if database:
            params["database"] = database
            
        return await self.call_tool("postgres", "execute_query", params)