"""
pytest 설정 및 공통 fixture
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os

from src.storage.models import Base
from src.config import TestSettings
from src.storage.cache import redis_client

# 테스트 설정 사용
test_settings = TestSettings()

# 테스트용 데이터베이스 엔진
test_engine = create_async_engine(
    test_settings.postgres_url,
    echo=False,
    poolclass=NullPool
)

# 테스트용 세션 팩토리
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """데이터베이스 초기화"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 fixture"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def redis_cleanup():
    """Redis 정리 fixture"""
    yield
    await redis_client.flushdb()


@pytest.fixture
def mock_claude_response():
    """Claude API 응답 모킹"""
    return {
        "id": "test-message-id",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Test response from Claude"
            }
        ],
        "model": "claude-3-opus-20240229",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50
        }
    }


@pytest.fixture
def sample_requirements():
    """샘플 요구사항"""
    return """
    Create a REST API for a todo application with the following features:
    - User authentication (JWT)
    - CRUD operations for todos
    - PostgreSQL database
    - Redis caching
    - Unit tests
    """


@pytest.fixture
def sample_context():
    """샘플 컨텍스트"""
    return {
        "project_type": "web_api",
        "tech_stack": "FastAPI, PostgreSQL, Redis",
        "team_size": 3,
        "timeline": "2 weeks"
    }


@pytest.fixture
async def mock_mcp_server(monkeypatch):
    """MCP 서버 모킹"""
    class MockMCPServer:
        async def start(self):
            pass
            
        async def stop(self):
            pass
            
        async def call_tool(self, tool: str, params: dict):
            return {
                "success": True,
                "result": f"Mock result for {tool}"
            }
    
    def mock_create_server(*args, **kwargs):
        return MockMCPServer()
    
    monkeypatch.setattr(
        "src.integrations.mcp.client.MCPServer",
        mock_create_server
    )
    
    yield MockMCPServer()


# 환경 변수 설정
os.environ["AGENTIC_ENV"] = "test"
os.environ["AGENTIC_ANTHROPIC_API_KEY"] = "test-key"
os.environ["AGENTIC_SECRET_KEY"] = "test-secret-key"