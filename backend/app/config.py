from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.4"
    OPENAI_BASE_URL: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.5-flash"
    GOOGLE_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    ZAI_API_KEY: str = ""
    ZAI_MODEL: str = "glm-4.7-flash"
    ZAI_BASE_URL: str = "https://api.z.ai/api/paas/v4/"
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,testserver,*.azurecontainerapps.io,*.azurefd.net"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    RATE_LIMIT_RPM: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
