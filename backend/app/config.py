import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Search and load .env from root and backend directory
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
if os.path.exists(root_env):
    load_dotenv(dotenv_path=root_env, override=True)
load_dotenv(override=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Campus Ops AI Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Notion Configuration (supports aliases)
    NOTION_API_KEY: str = (
        os.getenv("NOTION_API_KEY") 
        or os.getenv("NOTION_TOKEN") 
        or ""
    ).strip()

    NOTION_REQUESTS_DATABASE_ID: str = (
        os.getenv("NOTION_REQUESTS_DATABASE_ID") 
        or os.getenv("NOTION_REQUESTS_DB_ID") 
        or ""
    ).strip().replace("-", "")

    NOTION_RUN_LOG_DATABASE_ID: str = (
        os.getenv("NOTION_RUN_LOG_DATABASE_ID") 
        or os.getenv("NOTION_RUNLOG_DB_ID") 
        or ""
    ).strip().replace("-", "")
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_notion_configured(self) -> bool:
        return bool(
            self.NOTION_API_KEY 
            and not self.NOTION_API_KEY.startswith("secret_placeholder")
            and len(self.NOTION_API_KEY) > 10
            and self.NOTION_REQUESTS_DATABASE_ID 
            and not self.NOTION_REQUESTS_DATABASE_ID.startswith("placeholder")
            and len(self.NOTION_REQUESTS_DATABASE_ID) >= 32
        )

settings = Settings()
