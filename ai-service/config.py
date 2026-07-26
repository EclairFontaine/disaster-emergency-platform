import os
from pydantic_settings import BaseSettings

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = "sk-placeholder"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DIFY_API_URL: str = "http://localhost:5001/v1"
    DIFY_API_KEY: str = "app-placeholder"
    SERVICE_HOST: str = "127.0.0.1"
    SERVICE_PORT: int = 8001

    @property
    def database_url(self) -> str:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return f"sqlite+aiosqlite:///{_DATA_DIR}/ai_service.db"

    class Config:
        env_file = os.path.join(_BASE_DIR, ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
