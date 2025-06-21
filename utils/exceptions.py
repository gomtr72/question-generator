from typing import Any, Dict, Optional

class QuestionGeneratorError(Exception):
    """질문 생성기 기본 예외 클래스"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

class ValidationError(QuestionGeneratorError):
    """입력 데이터 검증 실패 예외"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class OpenAIError(QuestionGeneratorError):
    """OpenAI API 관련 예외"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="OPENAI_API_ERROR",
            status_code=503,
            details=details
        )

class ContentProcessingError(QuestionGeneratorError):
    """콘텐츠 처리 관련 예외"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="CONTENT_PROCESSING_ERROR",
            status_code=422,
            details=details
        )

class ConfigurationError(QuestionGeneratorError):
    """설정 관련 예외"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        ) 