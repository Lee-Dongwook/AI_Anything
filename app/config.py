"""Type-safe configuration via Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="E2E_HEALER_", env_file=".env", extra="ignore")

    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-2024-08-06", description="Structured-Outputs-capable model")
    max_loops: int = Field(default=3, description="repair loop cap (Router termination)")
    playwright_cmd: str = Field(default="npx playwright test", description="Playwright invocation")
    log_level: str = Field(default="INFO")


settings = Settings()
