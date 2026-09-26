from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Optional override for which compiled curriculum file to load. Unset by
    # default, meaning content/curriculum.json.
    curriculum_json_path: str | None = None

    # Defaults to the Postgres that docker-compose.yml runs, with the same
    # deliberately-trivial local credentials, so a fresh clone works with no
    # setup. Nothing secret is embedded here that compose doesn't already
    # publish. Any real deployment sets DATABASE_URL explicitly; if it
    # forgets, connecting to a localhost that isn't there fails loudly
    # rather than quietly doing the wrong thing.
    # `+psycopg` selects psycopg 3. Dropping it would silently fall back to
    # psycopg2, which has no async support at all.
    database_url: str = "postgresql+psycopg://upskill:upskill@localhost:5432/upskill"


settings = Settings()
