"""
커스텀 예외 클래스 정의
"""

from typing import Optional, Dict, Any
from src.core.constants import ErrorCode

class BaseError(Exception):
    """기본 에러 클래스"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details
            }
        }

# 인증 관련 예외
class AuthenticationError(BaseError):
    """인증 에러"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.UNAUTHORIZED, 401, details)

class AuthorizationError(BaseError):
    """인가 에러"""
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.FORBIDDEN, 403, details)

class TokenExpiredError(BaseError):
    """토큰 만료 에러"""
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TOKEN_EXPIRED, 401, details)

# 검증 관련 예외
class ValidationError(BaseError):
    """검증 에러"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(message, ErrorCode.VALIDATION_ERROR, 400, details)

class InvalidInputError(BaseError):
    """잘못된 입력 에러"""
    def __init__(self, message: str = "Invalid input provided", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_INPUT, 400, details)

# 리소스 관련 예외
class NotFoundError(BaseError):
    """리소스 없음 에러"""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, ErrorCode.NOT_FOUND, 404)

class AlreadyExistsError(BaseError):
    """리소스 중복 에러"""
    def __init__(self, resource: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} already exists"
        super().__init__(message, ErrorCode.ALREADY_EXISTS, 409, details)

class ConflictError(BaseError):
    """충돌 에러"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.CONFLICT, 409, details)

# 시스템 관련 예외
class InternalError(BaseError):
    """내부 서버 에러"""
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INTERNAL_ERROR, 500, details)

class ServiceUnavailableError(BaseError):
    """서비스 사용 불가 에러"""
    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        message = f"{service} is currently unavailable"
        super().__init__(message, ErrorCode.SERVICE_UNAVAILABLE, 503, details)

class TimeoutError(BaseError):
    """타임아웃 에러"""
    def __init__(self, operation: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        message = f"{operation} timed out after {timeout} seconds"
        super().__init__(message, ErrorCode.TIMEOUT, 504, details)

class RateLimitError(BaseError):
    """Rate Limit 에러"""
    def __init__(self, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        super().__init__(message, ErrorCode.RATE_LIMITED, 429, details)

# AI 관련 예외
class AIServiceError(BaseError):
    """AI 서비스 에러"""
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"AI service '{service}' error: {message}"
        super().__init__(full_message, ErrorCode.AI_SERVICE_ERROR, 502, details)

class TokenLimitExceededError(BaseError):
    """토큰 제한 초과 에러"""
    def __init__(self, used_tokens: int, max_tokens: int):
        message = f"Token limit exceeded: {used_tokens}/{max_tokens}"
        details = {
            "used_tokens": used_tokens,
            "max_tokens": max_tokens
        }
        super().__init__(message, ErrorCode.TOKEN_LIMIT_EXCEEDED, 400, details)

class InvalidAIResponseError(BaseError):
    """잘못된 AI 응답 에러"""
    def __init__(self, message: str = "Invalid response from AI service", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_RESPONSE, 502, details)

# 파이프라인 관련 예외
class PipelineError(BaseError):
    """파이프라인 에러"""
    def __init__(self, message: str, pipeline_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if pipeline_id:
            details = details or {}
            details["pipeline_id"] = pipeline_id
        super().__init__(message, ErrorCode.INTERNAL_ERROR, 500, details)

class PipelineExecutionError(PipelineError):
    """파이프라인 실행 에러"""
    pass

class PipelineStateError(PipelineError):
    """파이프라인 상태 에러"""
    pass

# 에이전트 관련 예외
class AgentError(BaseError):
    """에이전트 에러"""
    def __init__(self, agent_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"Agent '{agent_name}' error: {message}"
        details = details or {}
        details["agent"] = agent_name
        super().__init__(full_message, ErrorCode.INTERNAL_ERROR, 500, details)

class AgentExecutionError(AgentError):
    """에이전트 실행 에러"""
    pass

class AgentTimeoutError(AgentError):
    """에이전트 타임아웃 에러"""
    def __init__(self, agent_name: str, timeout: int):
        super().__init__(agent_name, f"Execution timed out after {timeout} seconds", {"timeout": timeout})

# 노드 관련 예외
class NodeError(BaseError):
    """노드 에러"""
    def __init__(self, node_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"Node '{node_name}' error: {message}"
        details = details or {}
        details["node"] = node_name
        super().__init__(full_message, ErrorCode.INTERNAL_ERROR, 500, details)

class NodeExecutionError(NodeError):
    """노드 실행 에러"""
    pass

# MCP 관련 예외
class MCPError(BaseError):
    """MCP 에러"""
    def __init__(self, server_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"MCP server '{server_name}' error: {message}"
        details = details or {}
        details["server"] = server_name
        super().__init__(full_message, ErrorCode.SERVICE_UNAVAILABLE, 503, details)

class MCPConnectionError(MCPError):
    """MCP 연결 에러"""
    pass

class MCPToolError(MCPError):
    """MCP 도구 에러"""
    def __init__(self, server_name: str, tool_name: str, message: str):
        details = {"tool": tool_name}
        super().__init__(server_name, f"Tool '{tool_name}' error: {message}", details)