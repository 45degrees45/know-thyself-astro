from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    razorpay_key_id: str
    razorpay_key_secret: str
    jwt_secret: str
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
