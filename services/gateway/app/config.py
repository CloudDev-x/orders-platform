from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (12-factor).

    Set GATEWAY_LOG_LEVEL=DEBUG, for example, to override a default.
    """

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", extra="ignore")

    service_name: str = "gateway"
    log_level: str = "INFO"
    # In Kubernetes this becomes the orders Service DNS name, e.g. http://orders.prod.svc.cluster.local
    orders_base_url: str = "http://orders:8000"
    http_timeout_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
