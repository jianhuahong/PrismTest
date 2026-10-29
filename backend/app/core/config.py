from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Prism"
    secret_key: str = "dev-only-change-me"
    access_token_expire_seconds: int = 1800
    refresh_token_expire_seconds: int = 604800
    database_url: str = "mysql+aiomysql://root:prism_root@127.0.0.1:3307/prism"
    redis_url: str = "redis://127.0.0.1:6380/0"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
