from pydantic import model_validator
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
    # publish. Outside development the default is refused (see below).
    # `+psycopg` selects psycopg 3. Dropping it would silently fall back to
    # psycopg2, which has no async support at all.
    database_url: str = "postgresql+psycopg://upskill:upskill@localhost:5432/upskill"

    @model_validator(mode="after")
    def _database_url_is_explicit_outside_development(self) -> Settings:
        # The engine connects lazily, so a deployment that forgot DATABASE_URL
        # would start fine on the local default and fail only at the first
        # query (sign-in). Refuse to start instead. `model_fields_set` holds
        # the fields actually provided (environment variables, .env) rather
        # than left at their default.
        if (
            self.environment != "development"
            and "database_url" not in self.model_fields_set
        ):
            raise ValueError(
                f"DATABASE_URL must be set explicitly when ENVIRONMENT={self.environment!r}. "
                "Refusing to start on the local development default."
            )
        return self


settings = Settings()
