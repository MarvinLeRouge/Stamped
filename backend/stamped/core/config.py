from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STAMPED_", env_file=".env", extra="ignore")

    port: int = 8421
    data_dir: Path = Path("data")
    quest_gap_hours: int = 6
    thumb_size: int = 400


settings = Settings()
