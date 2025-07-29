"""
강화된 설정 검증 로직
"""

import os
import re
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urlparse
import ipaddress
import logging

from pydantic import ValidationError
from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigValidator:
    """설정 검증기"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """모든 설정 검증"""
        validation_methods = [
            self._validate_environment,
            self._validate_api_keys,
            self._validate_database,
            self._validate_redis,
            self._validate_security,
            self._validate_networking,
            self._validate_mcp_servers,
            self._validate_rate_limits,
            self._validate_logging,
            self._validate_monitoring
        ]
        
        for method in validation_methods:
            try:
                method()
            except Exception as e:
                self.errors.append(f"Validation error in {method.__name__}: {str(e)}")
        
        # 결과 반환
        result = {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self._generate_summary()
        }
        
        # 에러가 있으면 예외 발생
        if self.errors:
            error_msg = f"Configuration validation failed:\n" + "\n".join(f"  ❌ {e}" for e in self.errors)
            if self.warnings:
                error_msg += "\n\nWarnings:\n" + "\n".join(f"  ⚠️  {w}" for w in self.warnings)
            raise ConfigurationError(error_msg)
        
        # 경고만 있으면 로그
        if self.warnings:
            logger.warning("Configuration warnings:\n" + "\n".join(f"  ⚠️  {w}" for w in self.warnings))
        
        return result
    
    def _validate_environment(self):
        """환경 설정 검증"""
        valid_envs = {"development", "staging", "production", "test"}
        
        if self.settings.environment not in valid_envs:
            self.errors.append(f"Invalid environment: {self.settings.environment}. Must be one of {valid_envs}")
        
        # 프로덕션 환경 특별 검증
        if self.settings.is_production():
            if self.settings.debug:
                self.errors.append("Debug mode must be disabled in production")
            
            if self.settings.log_level == "DEBUG":
                self.warnings.append("DEBUG log level in production may expose sensitive information")
    
    def _validate_api_keys(self):
        """API 키 검증"""
        # Anthropic API 키
        if not self.settings.anthropic_api_key:
            self.errors.append("ANTHROPIC_API_KEY is required")
        elif not self._is_valid_api_key(self.settings.anthropic_api_key, "sk-ant-"):
            self.errors.append("Invalid Anthropic API key format")
        
        # GitHub 토큰 (MCP에서 사용)
        github_token = self.settings.mcp_servers.get("github", {}).get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
        if github_token and not self._is_valid_github_token(github_token):
            self.warnings.append("Invalid GitHub token format")
    
    def _validate_database(self):
        """데이터베이스 설정 검증"""
        # PostgreSQL 연결 정보
        if not self.settings.postgres_password:
            self.errors.append("Database password is required")
        
        if self.settings.postgres_password == "agentic123":
            if self.settings.is_production():
                self.errors.append("Default database password must be changed in production")
            else:
                self.warnings.append("Using default database password - change before production")
        
        # 데이터베이스 이름 검증
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.settings.postgres_db):
            self.errors.append(f"Invalid database name: {self.settings.postgres_db}")
        
        # URL 유효성 검증
        try:
            db_url = urlparse(self.settings.database_url)
            if db_url.scheme not in ["postgresql+asyncpg", "postgresql"]:
                self.errors.append(f"Invalid database URL scheme: {db_url.scheme}")
        except Exception as e:
            self.errors.append(f"Invalid database URL: {str(e)}")
    
    def _validate_redis(self):
        """Redis 설정 검증"""
        try:
            redis_url = urlparse(self.settings.redis_url)
            if redis_url.scheme not in ["redis", "rediss"]:
                self.errors.append(f"Invalid Redis URL scheme: {redis_url.scheme}")
            
            # Redis TTL 검증
            if self.settings.redis_ttl <= 0:
                self.errors.append(f"Redis TTL must be positive: {self.settings.redis_ttl}")
            elif self.settings.redis_ttl > 86400 * 30:  # 30 days
                self.warnings.append(f"Redis TTL is very long ({self.settings.redis_ttl}s), may cause memory issues")
        except Exception as e:
            self.errors.append(f"Invalid Redis URL: {str(e)}")
    
    def _validate_security(self):
        """보안 설정 검증"""
        # Secret Key
        if self.settings.secret_key == "your-secret-key-here-change-in-production":
            if self.settings.is_production():
                self.errors.append("Default secret key must be changed in production")
            else:
                self.warnings.append("Using default secret key - change before production")
        
        # Secret Key 강도 검증
        if len(self.settings.secret_key) < 32:
            self.errors.append("Secret key must be at least 32 characters long")
        
        if not self._has_good_entropy(self.settings.secret_key):
            self.warnings.append("Secret key has low entropy - consider using a stronger key")
        
        # Token 만료 시간
        if self.settings.access_token_expire_minutes < 5:
            self.warnings.append("Access token expiration time is very short")
        
        if self.settings.refresh_token_expire_days > 90:
            self.warnings.append("Refresh token expiration time is very long (>90 days)")
        
        # CORS 설정
        if "*" in self.settings.allowed_hosts and self.settings.is_production():
            self.errors.append("Wildcard allowed hosts (*) should not be used in production")
    
    def _validate_networking(self):
        """네트워킹 설정 검증"""
        # 포트 검증
        ports = {
            "server_port": self.settings.server_port,
            "chroma_port": self.settings.chroma_port,
            "prometheus_port": self.settings.prometheus_port
        }
        
        used_ports: Set[int] = set()
        for name, port in ports.items():
            if not (1 <= port <= 65535):
                self.errors.append(f"Invalid {name}: {port} (must be 1-65535)")
            
            if port < 1024 and os.geteuid() != 0:
                self.warnings.append(f"{name} {port} requires root privileges")
            
            if port in used_ports:
                self.errors.append(f"Port {port} is used by multiple services")
            used_ports.add(port)
        
        # Host 검증
        try:
            ipaddress.ip_address(self.settings.server_host)
        except ValueError:
            # 호스트명일 수 있음
            if not re.match(r'^[a-zA-Z0-9.-]+$', self.settings.server_host):
                self.errors.append(f"Invalid server host: {self.settings.server_host}")
    
    def _validate_mcp_servers(self):
        """MCP 서버 설정 검증"""
        for server_name, config in self.settings.mcp_servers.items():
            # 필수 필드 확인
            if "command" not in config:
                self.errors.append(f"MCP server '{server_name}' missing required field: command")
            
            # 명령어 실행 가능 여부 확인
            command = config.get("command", "")
            if command and not self._is_command_available(command):
                self.warnings.append(f"MCP server '{server_name}' command not found: {command}")
            
            # 파일시스템 서버 보안 검증
            if server_name == "filesystem":
                allowed_dirs = []
                for arg in config.get("args", []):
                    if arg.startswith("--allowed-directory"):
                        allowed_dirs.append(arg.split("=")[1] if "=" in arg else "")
                
                if "." in allowed_dirs or "/" in allowed_dirs:
                    self.warnings.append("MCP filesystem server has root access - consider restricting")
    
    def _validate_rate_limits(self):
        """Rate Limit 설정 검증"""
        if self.settings.rate_limit_requests <= 0:
            self.errors.append(f"Rate limit requests must be positive: {self.settings.rate_limit_requests}")
        
        if self.settings.rate_limit_period <= 0:
            self.errors.append(f"Rate limit period must be positive: {self.settings.rate_limit_period}")
        
        # 너무 제한적인 설정 경고
        requests_per_second = self.settings.rate_limit_requests / self.settings.rate_limit_period
        if requests_per_second < 0.1:
            self.warnings.append(f"Rate limit is very restrictive ({requests_per_second:.2f} req/s)")
    
    def _validate_logging(self):
        """로깅 설정 검증"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.settings.log_level not in valid_levels:
            self.errors.append(f"Invalid log level: {self.settings.log_level}. Must be one of {valid_levels}")
        
        valid_formats = {"json", "plain"}
        if self.settings.log_format not in valid_formats:
            self.errors.append(f"Invalid log format: {self.settings.log_format}. Must be one of {valid_formats}")
    
    def _validate_monitoring(self):
        """모니터링 설정 검증"""
        if self.settings.enable_metrics and self.settings.prometheus_port == self.settings.server_port:
            self.errors.append("Prometheus port conflicts with server port")
        
        if self.settings.sentry_dsn:
            if not self._is_valid_sentry_dsn(self.settings.sentry_dsn):
                self.errors.append("Invalid Sentry DSN format")
    
    def _is_valid_api_key(self, key: str, prefix: str) -> bool:
        """API 키 형식 검증"""
        return key.startswith(prefix) and len(key) > len(prefix) + 20
    
    def _is_valid_github_token(self, token: str) -> bool:
        """GitHub 토큰 형식 검증"""
        # GitHub personal access token patterns
        patterns = [
            r'^ghp_[a-zA-Z0-9]{36}$',  # Personal access tokens (classic)
            r'^github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}$',  # Fine-grained personal access tokens
        ]
        return any(re.match(pattern, token) for pattern in patterns)
    
    def _is_valid_sentry_dsn(self, dsn: str) -> bool:
        """Sentry DSN 형식 검증"""
        try:
            parsed = urlparse(dsn)
            return parsed.scheme in ["http", "https"] and parsed.hostname and "@" in parsed.netloc
        except:
            return False
    
    def _has_good_entropy(self, s: str) -> bool:
        """문자열 엔트로피 검증 (간단한 버전)"""
        # 최소한 대소문자, 숫자, 특수문자 포함
        has_lower = any(c.islower() for c in s)
        has_upper = any(c.isupper() for c in s)
        has_digit = any(c.isdigit() for c in s)
        has_special = any(not c.isalnum() for c in s)
        
        return sum([has_lower, has_upper, has_digit, has_special]) >= 3
    
    def _is_command_available(self, command: str) -> bool:
        """명령어 사용 가능 여부 확인"""
        import shutil
        return shutil.which(command) is not None
    
    def _generate_summary(self) -> str:
        """검증 결과 요약"""
        if not self.errors and not self.warnings:
            return "✅ All configuration validations passed"
        
        summary_parts = []
        if self.errors:
            summary_parts.append(f"❌ {len(self.errors)} errors")
        if self.warnings:
            summary_parts.append(f"⚠️  {len(self.warnings)} warnings")
        
        return " | ".join(summary_parts)


def validate_config_on_startup():
    """애플리케이션 시작 시 설정 검증"""
    try:
        validator = ConfigValidator()
        result = validator.validate_all()
        
        if result["valid"]:
            logger.info("Configuration validation passed")
        
        return result
        
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during configuration validation: {e}")
        raise ConfigurationError(f"Configuration validation error: {str(e)}")


def get_config_report() -> str:
    """설정 검증 보고서 생성"""
    validator = ConfigValidator()
    
    # 검증 실행 (에러 발생하지 않도록)
    validator.errors = []
    validator.warnings = []
    
    validation_methods = [
        validator._validate_environment,
        validator._validate_api_keys,
        validator._validate_database,
        validator._validate_redis,
        validator._validate_security,
        validator._validate_networking,
        validator._validate_mcp_servers,
        validator._validate_rate_limits,
        validator._validate_logging,
        validator._validate_monitoring
    ]
    
    for method in validation_methods:
        try:
            method()
        except Exception:
            pass
    
    # 보고서 생성
    report = ["# Configuration Validation Report", ""]
    
    settings = validator.settings
    report.append(f"**Environment**: {settings.environment}")
    report.append(f"**Debug Mode**: {settings.debug}")
    report.append(f"**App Version**: {settings.app_version}")
    report.append("")
    
    if validator.errors:
        report.append("## ❌ Errors")
        for error in validator.errors:
            report.append(f"- {error}")
        report.append("")
    
    if validator.warnings:
        report.append("## ⚠️  Warnings")
        for warning in validator.warnings:
            report.append(f"- {warning}")
        report.append("")
    
    if not validator.errors and not validator.warnings:
        report.append("## ✅ All Checks Passed")
        report.append("No configuration issues detected.")
    
    return "\n".join(report)