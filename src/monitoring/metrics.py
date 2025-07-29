"""
Prometheus 메트릭 정의 및 수집
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Any

# 시스템 정보
system_info = Info('agentic_pipeline_info', 'Agentic Development Pipeline system information')
system_info.info({
    'version': '1.0.0',
    'environment': 'production'
})

# 파이프라인 메트릭
pipeline_executions_total = Counter(
    'pipeline_executions_total',
    'Total number of pipeline executions',
    ['pipeline_type', 'status']
)

pipeline_duration_seconds = Histogram(
    'pipeline_duration_seconds',
    'Pipeline execution duration in seconds',
    ['pipeline_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

pipeline_tasks_total = Counter(
    'pipeline_tasks_total',
    'Total number of tasks in pipeline',
    ['pipeline_type', 'task_type', 'status']
)

active_pipelines = Gauge(
    'active_pipelines',
    'Number of currently active pipelines',
    ['pipeline_type']
)

# 에이전트 메트릭
agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_type', 'status']
)

agent_duration_seconds = Histogram(
    'agent_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60)
)

active_agents = Gauge(
    'active_agents',
    'Number of currently active agents',
    ['agent_type']
)

agent_errors_total = Counter(
    'agent_errors_total',
    'Total number of agent errors',
    ['agent_type', 'error_type']
)

# Claude API 메트릭
claude_api_calls_total = Counter(
    'claude_api_calls_total',
    'Total number of Claude API calls',
    ['model', 'status']
)

claude_api_tokens_total = Counter(
    'claude_api_tokens_total',
    'Total number of tokens used in Claude API',
    ['model', 'token_type']  # token_type: prompt, completion
)

claude_api_latency_seconds = Histogram(
    'claude_api_latency_seconds',
    'Claude API call latency in seconds',
    ['model'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
)

# MCP 메트릭
mcp_tool_calls_total = Counter(
    'mcp_tool_calls_total',
    'Total number of MCP tool calls',
    ['server', 'tool', 'status']
)

mcp_tool_latency_seconds = Histogram(
    'mcp_tool_latency_seconds',
    'MCP tool call latency in seconds',
    ['server', 'tool'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5)
)

mcp_server_errors_total = Counter(
    'mcp_server_errors_total',
    'Total number of MCP server errors',
    ['server', 'error_type']
)

# 스토리지 메트릭
database_queries_total = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1)
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# API 메트릭
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10)
)

websocket_connections = Gauge(
    'websocket_connections',
    'Number of active WebSocket connections'
)

# 시스템 리소스 메트릭
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)


def track_time(metric: Histogram, labels: dict = None):
    """시간 측정 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def increment_counter(counter: Counter, labels: dict = None):
    """카운터 증가 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(*args, **kwargs)
                if labels:
                    counter.labels(**labels).inc()
                else:
                    counter.inc()
                return result
            except Exception as e:
                # 에러 발생 시에도 카운터 증가 (status=error 레이블 사용 권장)
                raise
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                if labels:
                    counter.labels(**labels).inc()
                else:
                    counter.inc()
                return result
            except Exception as e:
                # 에러 발생 시에도 카운터 증가 (status=error 레이블 사용 권장)
                raise
        
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def update_system_metrics():
    """시스템 리소스 메트릭 업데이트"""
    import psutil
    
    # 메모리 사용량
    memory = psutil.virtual_memory()
    memory_usage_bytes.set(memory.used)
    
    # CPU 사용률
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage_percent.set(cpu_percent)