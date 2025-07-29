"""
MCP 서버 매니저
MCP 서버들의 생명주기 관리 및 모니터링
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.integrations.mcp.client import MCPClient, MCPServer
from src.core.config import get_settings
from src.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)
settings = get_settings()

class MCPManager:
    """MCP 서버 통합 관리자"""
    
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.health_check_interval = 30  # 초
        self.server_status: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self, server_configs: Optional[Dict[str, Dict[str, Any]]] = None):
        """매니저 초기화"""
        async with self._lock:
            if self.client:
                logger.warning("MCP Manager already initialized")
                return
            
            # 설정에서 서버 구성 로드
            configs = server_configs or settings.mcp_servers
            
            # 클라이언트 생성
            self.client = MCPClient(configs)
            
            # 서버 상태 초기화
            for server_name in configs.keys():
                self.server_status[server_name] = {
                    "status": "initialized",
                    "last_check": None,
                    "consecutive_failures": 0,
                    "total_requests": 0,
                    "failed_requests": 0
                }
            
            logger.info(f"MCP Manager initialized with {len(configs)} servers")
    
    async def start_all_servers(self):
        """모든 MCP 서버 시작"""
        if not self.client:
            raise IntegrationError("MCP Manager not initialized")
        
        logger.info("Starting all MCP servers...")
        
        # 서버 시작
        await self.client.start_all()
        
        # 상태 업데이트
        for server_name in self.server_status.keys():
            self.server_status[server_name]["status"] = "running"
            self.server_status[server_name]["started_at"] = datetime.utcnow()
        
        # 헬스체크 시작
        await self.start_health_monitoring()
        
        logger.info("All MCP servers started successfully")
    
    async def stop_all_servers(self):
        """모든 MCP 서버 중지"""
        if not self.client:
            return
        
        logger.info("Stopping all MCP servers...")
        
        # 헬스체크 중지
        await self.stop_health_monitoring()
        
        # 서버 중지
        await self.client.stop_all()
        
        # 상태 업데이트
        for server_name in self.server_status.keys():
            self.server_status[server_name]["status"] = "stopped"
            self.server_status[server_name]["stopped_at"] = datetime.utcnow()
        
        logger.info("All MCP servers stopped")
    
    async def start_health_monitoring(self):
        """헬스 모니터링 시작"""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health monitoring started")
    
    async def stop_health_monitoring(self):
        """헬스 모니터링 중지"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
        logger.info("Health monitoring stopped")
    
    async def _health_check_loop(self):
        """헬스체크 루프"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.check_all_servers_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def check_all_servers_health(self):
        """모든 서버 헬스체크"""
        if not self.client:
            return
        
        health_results = await self.client.health_check_all()
        
        for server_name, is_healthy in health_results.items():
            status = self.server_status.get(server_name, {})
            status["last_check"] = datetime.utcnow()
            
            if is_healthy:
                status["status"] = "healthy"
                status["consecutive_failures"] = 0
            else:
                status["status"] = "unhealthy"
                status["consecutive_failures"] = status.get("consecutive_failures", 0) + 1
                
                # 자동 재시작 처리
                if status["consecutive_failures"] >= 3:
                    logger.warning(f"Server {server_name} has failed {status['consecutive_failures']} times, restarting...")
                    await self.restart_server(server_name)
    
    async def restart_server(self, server_name: str):
        """특정 서버 재시작"""
        if not self.client or server_name not in self.client.servers:
            raise ValueError(f"Unknown server: {server_name}")
        
        server = self.client.servers[server_name]
        await server.restart()
        
        # 상태 초기화
        self.server_status[server_name]["consecutive_failures"] = 0
        self.server_status[server_name]["restarted_at"] = datetime.utcnow()
    
    async def call_tool(self, server_name: str, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출 (통계 포함)"""
        if not self.client:
            raise IntegrationError("MCP Manager not initialized")
        
        # 요청 카운트 증가
        if server_name in self.server_status:
            self.server_status[server_name]["total_requests"] += 1
        
        try:
            result = await self.client.call_tool(server_name, tool, params)
            return result
        except Exception as e:
            # 실패 카운트 증가
            if server_name in self.server_status:
                self.server_status[server_name]["failed_requests"] += 1
            raise
    
    def get_server_status(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """서버 상태 조회"""
        if server_name:
            return self.server_status.get(server_name, {})
        return self.server_status.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계 조회"""
        total_requests = sum(s.get("total_requests", 0) for s in self.server_status.values())
        failed_requests = sum(s.get("failed_requests", 0) for s in self.server_status.values())
        healthy_servers = sum(1 for s in self.server_status.values() if s.get("status") == "healthy")
        
        return {
            "total_servers": len(self.server_status),
            "healthy_servers": healthy_servers,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "success_rate": (total_requests - failed_requests) / total_requests if total_requests > 0 else 0,
            "server_details": self.server_status
        }
    
    # 편의 메서드들 (클라이언트 메서드 프록시)
    async def read_file(self, path: str) -> str:
        """파일 읽기"""
        return await self.client.read_file(path)
    
    async def write_file(self, path: str, content: str):
        """파일 쓰기"""
        await self.client.write_file(path, content)
    
    async def list_directory(self, path: str) -> List[str]:
        """디렉토리 목록"""
        return await self.client.list_directory(path)
    
    async def create_github_issue(self, repo: str, title: str, body: str, labels: List[str] = None):
        """GitHub 이슈 생성"""
        return await self.client.create_github_issue(repo, title, body, labels)
    
    async def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """쉘 명령 실행"""
        params = {"command": command}
        if cwd:
            params["cwd"] = cwd
        
        return await self.call_tool("shell", "execute", params)
    
    async def search_code(self, pattern: str, path: str = ".", file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """코드 검색"""
        params = {
            "pattern": pattern,
            "path": path
        }
        if file_type:
            params["file_type"] = file_type
        
        result = await self.call_tool("search", "grep", params)
        return result.get("matches", [])

# 싱글톤 인스턴스
_mcp_manager: Optional[MCPManager] = None

async def get_mcp_manager() -> MCPManager:
    """MCP 매니저 싱글톤 인스턴스 반환"""
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
        await _mcp_manager.initialize()
    
    return _mcp_manager

# 전역 매니저 인스턴스 (FastAPI 시작 시 초기화)
mcp_manager = MCPManager()