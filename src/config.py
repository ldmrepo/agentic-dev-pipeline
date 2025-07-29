"""
애플리케이션 설정
환경 변수 및 구성 관리
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os
from functools import lru_cache


class Settings(BaseSettings):
    """전역 설정"""
    
    # 애플리케이션 기본 설정
    app_name: str = "Agentic Development Pipeline"
    debug: bool = False
    api_port: int = 8000
    
    # 보안
    secret_key: str = "your-secret-key-here"
    cors_origins: List[str] = ["*"]
    
    # 데이터베이스
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "agentic_dev_pipeline"
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        """Redis 연결 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-opus-20240229"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.1
    
    # LangGraph
    langgraph_api_key: Optional[str] = None
    langgraph_platform_url: Optional[str] = None
    
    # MCP 설정
    mcp_server_configs: Dict[str, Dict[str, Any]] = {
        "filesystem": {
            "command": "python",
            "args": ["-m", "mcp_servers.filesystem"],
            "env": {}
        },
        "github": {
            "command": "python",
            "args": ["-m", "mcp_servers.github"],
            "env": {}
        },
        "docker": {
            "command": "python",
            "args": ["-m", "mcp_servers.docker"],
            "env": {}
        }
    }
    
    # 벡터 데이터베이스
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "agentic_dev_pipeline"
    
    # 로깅
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 모니터링
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # 캐싱
    cache_ttl: int = 3600  # 1시간
    cache_max_size: int = 1000
    
    # 워크플로우 설정
    workflow_timeout: int = 3600  # 1시간
    max_retry_attempts: int = 3
    concurrent_agents: int = 5
    
    # 파일 저장소
    upload_dir: str = "./uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".cpp", ".c",
        ".html", ".css", ".json", ".yaml", ".yml",
        ".md", ".txt", ".dockerfile", ".sh"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 환경 변수 접두사
        env_prefix = "AGENTIC_"


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()


# 환경별 설정
class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    debug: bool = True
    log_level: str = "DEBUG"
    

class ProductionSettings(Settings):
    """프로덕션 환경 설정"""
    debug: bool = False
    log_level: str = "WARNING"
    cors_origins: List[str] = ["https://app.example.com"]


class TestSettings(Settings):
    """테스트 환경 설정"""
    postgres_db: str = "agentic_test"
    redis_db: int = 15
    

# 환경별 설정 매핑
env_settings_map = {
    "development": DevelopmentSettings,
    "production": ProductionSettings,
    "test": TestSettings
}


def get_env_settings() -> Settings:
    """환경에 따른 설정 반환"""
    env = os.getenv("AGENTIC_ENV", "development").lower()
    settings_class = env_settings_map.get(env, Settings)
    return settings_class()


# 설정 검증
def validate_settings(settings: Settings) -> None:
    """필수 설정 검증"""
    if not settings.anthropic_api_key:
        raise ValueError("AGENTIC_ANTHROPIC_API_KEY is required")
    
    if not settings.secret_key or settings.secret_key == "your-secret-key-here":
        raise ValueError("AGENTIC_SECRET_KEY must be set to a secure value")
    
    # 디렉토리 생성
    os.makedirs(settings.upload_dir, exist_ok=True)