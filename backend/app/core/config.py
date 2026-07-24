from pydantic_settings import BaseSettings
from typing import List
import json, os


class Settings(BaseSettings):
    APP_NAME: str = "云南自然灾害应急协同决策平台"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/disaster"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/disaster"
    REDIS_URL: str = "redis://localhost:6379/0"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    DEEPSEEK_API_KEY: str = "sk-placeholder"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DIFY_API_URL: str = "http://localhost:5001/v1"
    DIFY_API_KEY: str = "app-placeholder"
    OPENWEATHER_API_KEY: str = ""
    QWEATHER_API_KEY: str = ""
    JWT_SECRET: str = "yunnan-disaster-jwt-secret-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = '["http://localhost:3000","http://127.0.0.1:3000","http://localhost:80","http://localhost"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
# Force reload from .env (workaround for Chinese path)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k == "DEEPSEEK_API_KEY" and settings.DEEPSEEK_API_KEY == "sk-placeholder":
                    settings.DEEPSEEK_API_KEY = v
                    try:
                        from app.services.deepseek import deepseek_client
                        deepseek_client._refresh_config()
                    except Exception:
                        pass
                elif k == "DIFY_API_KEY" and settings.DIFY_API_KEY == "app-placeholder":
                    settings.DIFY_API_KEY = v
                elif k == "DIFY_API_URL":
                    settings.DIFY_API_URL = v
                elif k == "OPENWEATHER_API_KEY" and not settings.OPENWEATHER_API_KEY:
                    settings.OPENWEATHER_API_KEY = v
                elif k == "QWEATHER_API_KEY" and not settings.QWEATHER_API_KEY:
                    settings.QWEATHER_API_KEY = v
