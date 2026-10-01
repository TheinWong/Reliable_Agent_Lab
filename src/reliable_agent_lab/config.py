from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAL_", env_file=".env", extra="ignore")

    order_service_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8081")
    tool_timeout_seconds: float = 5.0
    metrics_mcp_url: AnyHttpUrl = AnyHttpUrl("http://localhost:18081/mcp")
    logs_mcp_url: AnyHttpUrl = AnyHttpUrl("http://localhost:18082/mcp")
    traces_mcp_url: AnyHttpUrl = AnyHttpUrl("http://localhost:18083/mcp")
    operations_mcp_url: AnyHttpUrl = AnyHttpUrl("http://localhost:18084/mcp")
    postgres_dsn: str | None = None
