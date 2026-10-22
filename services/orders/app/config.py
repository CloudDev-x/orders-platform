from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration from ORDERS_* environment variables (12-factor).

    database_url has no default on purpose: the service must not start
    without an explicit database, and the password must never be hardcoded.
    """

    model_config = SettingsConfigDict(env_prefix="ORDERS_", extra="ignore")

    service_name: str = "orders"
    log_level: str = "INFO"

    database_url: SecretStr

    # Per-pod connection pool. Fail fast when the pool is exhausted instead of queueing.
    db_pool_size: int = 5
    db_max_overflow: int = 0
    db_pool_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
