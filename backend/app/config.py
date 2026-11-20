from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    latitude: float = 51.5074
    longitude: float = -0.1278

    carbon_provider: str = "uk_carbon"
    electricity_maps_api_key: str = ""
    electricity_maps_zone: str = "GB"

    openai_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""

    database_url: str = "sqlite+aiosqlite:///./gridpulse.db"
    sim_tick_seconds: float = 3.0

    @property
    def active_llm_key(self) -> str:
        return self.openai_api_key or self.groq_api_key or self.gemini_api_key

    @property
    def ai_mode(self) -> str:
        return "Live LLM" if self.active_llm_key else "Deterministic Fallback"


settings = Settings()
