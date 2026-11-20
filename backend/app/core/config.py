from functools import lru_cache
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AI Research Paper Intelligence System"
    database_url: str = "sqlite:///./research_intel.db"
    jwt_secret: str = "development-only-change-this-secret"
    jwt_expire_minutes: int = 1440
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    max_upload_mb: int = 20
    cors_origins: str = "http://localhost:5173"
    embedding_model: str = "all-MiniLM-L6-v2"
    uploads_dir: str = "uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def upload_path(self) -> Path:
        uploads_dir = self.uploads_dir
        if os.getenv("VERCEL") and not os.getenv("UPLOADS_DIR"):
            uploads_dir = "/tmp/research-intel-uploads"
        path = Path(uploads_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()

