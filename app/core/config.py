from functools import lru_cache

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    finnhub_api_key: str = Field(..., validation_alias="FINNHUB_API_KEY")
    openai_model: str = Field("gpt-4o-mini", validation_alias="OPENAI_MODEL")


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        # Provide a clear error message when keys are missing.
        missing = [e["loc"][0] for e in exc.errors()]
        missing_str = ", ".join(str(m).upper() for m in missing)
        raise RuntimeError(
            f"Missing required environment variables: {missing_str}. "
            "Please set them in your environment or .env file."
        ) from exc


