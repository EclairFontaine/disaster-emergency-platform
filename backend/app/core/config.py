from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    APP_NAME: str = "云南自然灾害应急协同决策平台"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/disaster"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/disaster"
    REDIS_URL: str = "redis://localhost:6379/0"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    DEEPSEEK_API_KEY: str = "sk-placeholder"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    JWT_SECRET: str = "yunnan-disaster-jwt-secret-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = '["http://localhost:3000","http://127.0.0.1:3000","http://localhost:80","http://localhost"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
