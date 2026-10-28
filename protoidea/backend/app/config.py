from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Existing settings
    gemini_api_key: str
    supabase_url: str
    supabase_key: str
    database_url: str
    groq_api_key: str

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False          # set true in production (HTTPS only)
    auth_cookie_name: str = "protox_session"
    verify_token_hours: int = 24

    # Email (empty SMTP_HOST = print links to the terminal instead of sending)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()