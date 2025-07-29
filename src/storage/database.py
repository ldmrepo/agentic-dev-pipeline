"""
데이터베이스 설정 및 세션 관리
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from src.storage.models import Base
from src.config import settings

logger = logging.getLogger(__name__)

# 비동기 엔진 생성
engine: AsyncEngine = create_async_engine(
    settings.postgres_url,
    echo=settings.debug,
    poolclass=NullPool,  # 비동기에서는 NullPool 권장
    future=True
)

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db() -> None:
    """데이터베이스 초기화"""
    try:
        async with engine.begin() as conn:
            # 테이블 생성
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """데이터베이스 연결 종료"""
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 컨텍스트 매니저"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# FastAPI 의존성을 위한 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성 주입용 세션 생성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()