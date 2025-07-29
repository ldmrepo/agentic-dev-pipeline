"""
애플리케이션 설정 관리
환경 변수 및 설정 값들을 중앙에서 관리
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache
import os

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Application
    app_name: str = "Agentic Development Pipeline"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API
    api_v1_str: str = "/api/v1"
    api_key: Optional[str] = None
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    
    # Database
    postgres_server: str = "localhost"
    postgres_user: str = "agentic"
    postgres_password: str = "agentic123"
    postgres_db: str = "agentic_pipeline"
    
    @property
    def database_url(self) -> str:
        """데이터베이스 URL 생성"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}/{self.postgres_db}"
    
    @property
    def sync_database_url(self) -> str:
        """동기 데이터베이스 URL (Alembic용)"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}/{self.postgres_db}"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour
    
    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    
    @property
    def chroma_url(self) -> str:
        """ChromaDB URL 생성"""
        return f"http://{self.chroma_host}:{self.chroma_port}"
    
    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-opus-20240229"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.1
    
    # LangGraph
    langgraph_recursion_limit: int = 50
    langgraph_checkpoint_ttl: int = 86400  # 24 hours
    
    # MCP
    mcp_servers: Dict[str, Dict[str, Any]] = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "--allowed-directory", "."],
            "env": {}
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN", "")}
        }
    }
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    allowed_hosts: list = ["*"]
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 8081
    enable_metrics: bool = True
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "plain"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment.lower() == "development"

@lru_cache()
def get_settings() -> Settings:
    """캐시된 설정 인스턴스 반환"""
    return Settings()

def validate_settings():
    """설정 값 검증 (기본 검증 - 강화된 검증은 config_validator 사용)"""
    settings = get_settings()
    
    # 필수 값 확인
    required_fields = {
        "anthropic_api_key": "ANTHROPIC_API_KEY environment variable is required",
        "postgres_password": "Database password is required",
        "secret_key": "Secret key must be changed in production"
    }
    
    errors = []
    
    for field, error_msg in required_fields.items():
        value = getattr(settings, field)
        if not value or (field == "secret_key" and settings.is_production() and value == "your-secret-key-here-change-in-production"):
            errors.append(error_msg)
    
    if errors:
        error_message = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_message)
    
    return True

# 설정 인스턴스 export
settings = get_settings()