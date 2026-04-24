from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,testserver,*.azurecontainerapps.io,*.azurefd.net"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    RATE_LIMIT_RPM: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
