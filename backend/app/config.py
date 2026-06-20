from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "MealMate"
    DATABASE_URL: str = "sqlite:///./data/mealmate.db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_DAYS: int = 7
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Dell AIA Gateway LLM Provider
    LLM_CLIENT_ID: str = ""
    LLM_CLIENT_SECRET: str = ""
    LLM_BASE_URL: str = "https://aia.gateway.dell.com/genai/dev/v1"
    LLM_MODEL: str = "gpt-oss-120b"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")


settings = Settings()
