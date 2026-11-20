from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "production"] = "development"
    frontend_origin: str = "http://localhost:5173"
    api_access_token: str = Field(default="", validation_alias="GRIDPULSE_API_TOKEN")

    latitude: float = Field(default=51.5074, ge=-90, le=90)
    longitude: float = Field(default=-0.1278, ge=-180, le=180)

    carbon_provider: Literal["uk_carbon", "electricity_maps"] = "uk_carbon"
    electricity_maps_api_key: str = ""
    electricity_maps_zone: str = "GB"

    openai_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""

    database_url: str = "sqlite+aiosqlite:///./gridpulse.db"
    sim_tick_seconds: float = Field(default=3.0, ge=0.5, le=10.0)

    @property
    def active_llm_key(self) -> str:
        return self.openai_api_key or self.groq_api_key or self.gemini_api_key

    @property
    def ai_mode(self) -> str:
        return "Live LLM" if self.active_llm_key else "Deterministic Fallback"


settings = Settings()
