"""Runtime settings, read from environment variables and the repository .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    contact_email: str = ""
    data_dir: Path = REPO_ROOT / "data"
    valhalla_url: str = "http://localhost:8002"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def user_agent(self) -> str:
        contact = self.contact_email or "datathon prototype"
        return f"PrijePotpisa/0.1 (+{contact})"


@lru_cache
def get_settings() -> Settings:
    return Settings()
