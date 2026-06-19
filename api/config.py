from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        extra="ignore",
    )

    database_url: str
    # LLM provider: "anthropic" | "nim" | "openai" | "gemini"
    llm_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    nim_api_key: Optional[str] = None
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    razorpay_key_id: str
    razorpay_key_secret: str
    jwt_secret: str
    frontend_url: str = "http://localhost:3000"  # comma-separated for multiple origins
    demo_secret: str = "demo-dev-secret"  # override in prod
    admin_secret: str = "admin-dev-secret"  # override in prod via ADMIN_SECRET env var

settings = Settings()
