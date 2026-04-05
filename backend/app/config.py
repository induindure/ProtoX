from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    supabase_url: str
    supabase_key: str
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
