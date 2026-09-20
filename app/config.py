from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    # Optional override for which compiled curriculum file to load. Unset by
    # default, meaning content/curriculum.json.
    curriculum_json_path: str | None = None


settings = Settings()
