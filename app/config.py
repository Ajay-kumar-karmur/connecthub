from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    worker_enabled: bool = True
    max_attempts: int = 8
    failure_threshold: int = 5
    pause_seconds: int = 30
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
