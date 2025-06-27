from typing import Dict, List, Optional
from pydantic import Field, BaseSettings
from enum import Enum
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class QuestionType(str, Enum):
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"

# 질문 유형 설정
QUESTION_TYPES = {
    QuestionType.ANALYSIS: [
        '비교 분석',
        '원인 분석',
        '영향 분석',
        '패턴 분석',
        '관계 분석'
    ],
    QuestionType.SYNTHESIS: [
        '새로운 해결책 제시',
        '대안적 접근법 개발',
        '통합적 관점 제시',
        '실용적 적용 방안',
        '혁신적 아이디어 제시'
    ]
}

class QuestionConfig(BaseSettings):
    MIN_QUESTIONS: int = Field(default=5, ge=1, le=10)
    MAX_QUESTIONS: int = Field(default=15, ge=10, le=30)
    DEFAULT_QUESTIONS: int = Field(default=10, ge=5, le=15)
    
    class Config:
        env_prefix = 'QUESTION_'

class OpenAIConfig(BaseSettings):
    API_KEY: str = Field(default="")
    MODEL: str = Field(default="gpt-4")
    MAX_TOKENS: int = Field(default=2000)
    TEMPERATURE: float = Field(default=0.7)
    
    class Config:
        env_prefix = 'OPENAI_'

class GeminiConfig(BaseSettings):
    API_KEY: str = Field(default="")
    MODEL: str = Field(default="gemini-pro")
    
    class Config:
        env_prefix = 'GEMINI_'

class YouTubeConfig(BaseSettings):
    API_KEY: str = Field(default="")
    
    class Config:
        env_prefix = 'YOUTUBE_'

class LogConfig(BaseSettings):
    LEVEL: str = Field(default="INFO")
    FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    FILE: str = Field(default="app.log")
    
    class Config:
        env_prefix = 'LOG_'

class Config(BaseSettings):
    # 기본 Flask 설정
    ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    TESTING: bool = Field(default=False)
    SECRET_KEY: str = Field(default="dev-key-123")
    FLASK_DEBUG: str = Field(default=None)
    
    # 질문 타입 설정
    QUESTION_TYPES: dict = Field(default=QUESTION_TYPES)
    
    # 컴포넌트별 설정
    QUESTION: QuestionConfig = QuestionConfig()
    OPENAI: OpenAIConfig = OpenAIConfig()
    GEMINI: GeminiConfig = GeminiConfig()
    YOUTUBE: YouTubeConfig = YouTubeConfig()
    LOG: LogConfig = LogConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = ""
        extra = 'allow'  # 추가 환경 변수 허용

# 환경별 설정
class DevelopmentConfig(Config):
    ENV: str = "development"
    DEBUG: bool = True

class ProductionConfig(Config):
    ENV: str = "production"
    DEBUG: bool = False
    
class TestingConfig(Config):
    ENV: str = "testing"
    TESTING: bool = True
    DEBUG: bool = True

# 환경별 설정 매핑
config_by_name = {
    "development": DevelopmentConfig(),
    "production": ProductionConfig(),
    "testing": TestingConfig()
}

# 현재 환경 설정 가져오기
def get_config() -> Config:
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name[env] 