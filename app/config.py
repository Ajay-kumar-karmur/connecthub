from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    worker_enabled: bool = True
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
