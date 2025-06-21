import logging
import structlog
from typing import Any, Dict, Callable
from datetime import datetime
from functools import wraps
from config import get_config

config = get_config()

def setup_logger() -> structlog.BoundLogger:
    """
    구조화된 로깅을 설정합니다.
    """
    logging.basicConfig(
        format=config.LOG.FORMAT,
        level=config.LOG.LEVEL,
        filename=config.LOG.FILE
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()

logger = setup_logger()

def log_request(func: Callable) -> Callable:
    """
    요청 로깅을 위한 데코레이터
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            
            # 응답 시간 계산
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 성공 로그
            logger.info(
                "request_processed",
                function_name=func.__name__,
                response_time=response_time,
                status="success"
            )
            
            return result
            
        except Exception as e:
            # 응답 시간 계산
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 에러 로그
            logger.error(
                "request_failed",
                function_name=func.__name__,
                response_time=response_time,
                error=str(e),
                status="error"
            )
            
            raise
            
    return wrapper

def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    에러 로깅을 위한 유틸리티 함수
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context if context else {}
    ) 