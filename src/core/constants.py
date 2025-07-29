"""
애플리케이션 상수 정의
"""

from enum import Enum

# API 버전
API_VERSION = "v1"

# 파이프라인 상태
class PipelineStatus(str, Enum):
    """파이프라인 상태"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

# 에이전트 타입
class AgentType(str, Enum):
    """에이전트 타입"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

# 태스크 타입
class TaskType(str, Enum):
    """태스크 타입"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"

# 태스크 복잡도
class TaskComplexity(str, Enum):
    """태스크 복잡도"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"

# 아티팩트 타입
class ArtifactType(str, Enum):
    """아티팩트 타입"""
    CODE = "code"
    DOCUMENT = "document"
    TEST = "test"
    CONFIG = "config"
    DIAGRAM = "diagram"
    SCRIPT = "script"
    DATA = "data"

# 프로그래밍 언어
class ProgrammingLanguage(str, Enum):
    """지원하는 프로그래밍 언어"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"
    SQL = "sql"
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"

# 프레임워크
class Framework(str, Enum):
    """지원하는 프레임워크"""
    FASTAPI = "fastapi"
    EXPRESS = "express"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    DJANGO = "django"
    FLASK = "flask"
    SPRING = "spring"
    GIN = "gin"

# 배포 환경
class DeploymentEnvironment(str, Enum):
    """배포 환경"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

# 배포 전략
class DeploymentStrategy(str, Enum):
    """배포 전략"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"

# HTTP 메서드
class HTTPMethod(str, Enum):
    """HTTP 메서드"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

# 로그 레벨
class LogLevel(str, Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# 메트릭 타입
class MetricType(str, Enum):
    """메트릭 타입"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

# 캐시 키 프리픽스
class CacheKeyPrefix:
    """캐시 키 프리픽스"""
    PIPELINE = "pipeline:"
    AGENT = "agent:"
    WORKFLOW = "workflow:"
    USER = "user:"
    TOKEN = "token:"
    RESULT = "result:"

# 시간 관련 상수
class TimeConstants:
    """시간 관련 상수"""
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    THIRTY_MINUTES = 1800
    ONE_HOUR = 3600
    ONE_DAY = 86400
    ONE_WEEK = 604800

# 크기 제한
class SizeLimits:
    """크기 제한 상수"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_CODE_LENGTH = 100000  # 100K characters
    MAX_LOG_LENGTH = 10000  # 10K characters
    MAX_ARTIFACTS = 100  # 파이프라인당 최대 아티팩트 수

# 재시도 설정
class RetryConfig:
    """재시도 설정"""
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier

# 에러 코드
class ErrorCode(str, Enum):
    """에러 코드"""
    # 인증 관련
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # 검증 관련
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    
    # 리소스 관련
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    
    # 시스템 관련
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    
    # AI 관련
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"
    INVALID_RESPONSE = "INVALID_RESPONSE"

# 성공 메시지
class SuccessMessage:
    """성공 메시지"""
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    COMPLETED = "Operation completed successfully"
    STARTED = "Operation started successfully"

# 정규식 패턴
class RegexPatterns:
    """정규식 패턴"""
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    SEMVER = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    GITHUB_REPO = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"