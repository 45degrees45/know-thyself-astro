from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        extra="ignore",
    )

    database_url: str
    anthropic_api_key: str
    razorpay_key_id: str
    razorpay_key_secret: str
    jwt_secret: str
    frontend_url: str = "http://localhost:3000"

settings = Settings()
