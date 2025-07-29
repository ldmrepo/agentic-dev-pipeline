"""
표준화된 로깅 설정 및 유틸리티
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback
from contextvars import ContextVar

from src.core.config import settings


# 컨텍스트 변수 (요청 ID, 사용자 ID 등 추적)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
pipeline_id_var: ContextVar[Optional[str]] = ContextVar('pipeline_id', default=None)


class StructuredFormatter(logging.Formatter):
    """구조화된 로그 포맷터 (JSON)"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 기본 로그 데이터
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 컨텍스트 정보 추가
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        pipeline_id = pipeline_id_var.get()
        if pipeline_id:
            log_data["pipeline_id"] = pipeline_id
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 추가 필드 (record.extra)
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName", 
                          "levelname", "levelno", "lineno", "module", "msecs", "message",
                          "pathname", "process", "processName", "relativeCreated", "thread",
                          "threadName", "exc_info", "exc_text", "stack_info"]:
                log_data[key] = value
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터 (개발 환경용)"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # 로그 레벨 색상
        levelname = record.levelname
        if levelname in self.COLORS:
            levelname_color = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.levelname = levelname_color
        
        # 타임스탬프
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 컨텍스트 정보
        context_parts = []
        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        
        pipeline_id = pipeline_id_var.get()
        if pipeline_id:
            context_parts.append(f"pipe={pipeline_id[:8]}")
        
        context = f"[{' '.join(context_parts)}] " if context_parts else ""
        
        # 로거 이름 단축
        logger_name = record.name
        if logger_name.startswith('src.'):
            logger_name = logger_name[4:]
        
        # 포맷 적용
        if record.exc_info:
            exc_text = '\n' + ''.join(traceback.format_exception(*record.exc_info))
        else:
            exc_text = ''
        
        return f"{timestamp} {record.levelname} [{logger_name}] {context}{record.getMessage()}{exc_text}"


class LoggerManager:
    """로거 관리자"""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._setup_root_logger()
        self._setup_log_directory()
    
    def _setup_root_logger(self):
        """루트 로거 설정"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.log_level))
        
        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        
        if settings.log_format == "json":
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredFormatter())
        
        root_logger.addHandler(console_handler)
        
        # 파일 핸들러 (프로덕션)
        if settings.is_production():
            log_file = Path("logs") / f"agentic-pipeline-{datetime.now().strftime('%Y%m%d')}.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(file_handler)
    
    def _setup_log_directory(self):
        """로그 디렉토리 생성"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    def get_logger(self, name: str) -> logging.Logger:
        """로거 인스턴스 반환"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def set_context(self, **kwargs):
        """로깅 컨텍스트 설정"""
        if "request_id" in kwargs:
            request_id_var.set(kwargs["request_id"])
        
        if "user_id" in kwargs:
            user_id_var.set(kwargs["user_id"])
        
        if "pipeline_id" in kwargs:
            pipeline_id_var.set(kwargs["pipeline_id"])
    
    def clear_context(self):
        """로깅 컨텍스트 초기화"""
        request_id_var.set(None)
        user_id_var.set(None)
        pipeline_id_var.set(None)


# 싱글톤 인스턴스
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logger_manager.get_logger(name)


def set_logging_context(**kwargs):
    """로깅 컨텍스트 설정"""
    logger_manager.set_context(**kwargs)


def clear_logging_context():
    """로깅 컨텍스트 초기화"""
    logger_manager.clear_context()


class LoggingContextManager:
    """로깅 컨텍스트 매니저"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.previous_values = {}
    
    def __enter__(self):
        # 현재 값 저장
        self.previous_values = {
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "pipeline_id": pipeline_id_var.get()
        }
        
        # 새 값 설정
        set_logging_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 이전 값 복원
        if self.previous_values["request_id"] is not None:
            request_id_var.set(self.previous_values["request_id"])
        if self.previous_values["user_id"] is not None:
            user_id_var.set(self.previous_values["user_id"])
        if self.previous_values["pipeline_id"] is not None:
            pipeline_id_var.set(self.previous_values["pipeline_id"])


def log_execution_time(func):
    """실행 시간 로깅 데코레이터"""
    import time
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"{func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "success"
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"{func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "error",
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"{func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "success"
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"{func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "error",
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise
    
    # 비동기 함수 체크
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """API 요청 로깅"""
    logger = get_logger("api.access")
    
    logger.info(
        f"{method} {path} {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            **kwargs
        }
    )


def log_agent_execution(agent_name: str, status: str, duration: float, **kwargs):
    """에이전트 실행 로깅"""
    logger = get_logger(f"agents.{agent_name}")
    
    logger.info(
        f"Agent execution: {agent_name}",
        extra={
            "agent_name": agent_name,
            "status": status,
            "duration": duration,
            **kwargs
        }
    )


def log_pipeline_event(event_type: str, pipeline_id: str, **kwargs):
    """파이프라인 이벤트 로깅"""
    logger = get_logger("pipeline.events")
    
    with LoggingContextManager(pipeline_id=pipeline_id):
        logger.info(
            f"Pipeline event: {event_type}",
            extra={
                "event_type": event_type,
                **kwargs
            }
        )


# 로깅 레벨 별 함수
def debug(message: str, **kwargs):
    """디버그 로그"""
    logger = get_logger("app")
    logger.debug(message, extra=kwargs)


def info(message: str, **kwargs):
    """정보 로그"""
    logger = get_logger("app")
    logger.info(message, extra=kwargs)


def warning(message: str, **kwargs):
    """경고 로그"""
    logger = get_logger("app")
    logger.warning(message, extra=kwargs)


def error(message: str, exc_info: bool = False, **kwargs):
    """에러 로그"""
    logger = get_logger("app")
    logger.error(message, exc_info=exc_info, extra=kwargs)


def critical(message: str, exc_info: bool = False, **kwargs):
    """치명적 에러 로그"""
    logger = get_logger("app")
    logger.critical(message, exc_info=exc_info, extra=kwargs)