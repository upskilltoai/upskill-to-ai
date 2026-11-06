"""Settings refuse to start in production without an explicit DATABASE_URL."""

import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    # Start every test from nothing: no real environment variables leaking in,
    # and run from an empty temporary folder, so the developer's .env (looked
    # up in the current folder) isn't found either.
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)


def test_development_uses_the_local_default(monkeypatch):
    settings = Settings()
    assert settings.environment == "development"
    assert "localhost:5432" in settings.database_url


def test_production_without_database_url_refuses_to_start(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValidationError, match="DATABASE_URL must be set explicitly"):
        Settings()


def test_production_with_database_url_starts(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://app:secret@db.example:5432/app"
    )
    settings = Settings()
    assert settings.database_url.endswith("db.example:5432/app")


def test_explicitly_setting_the_local_default_also_counts(monkeypatch):
    # The check is "was it provided", not "is it different from the default".
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://upskill:upskill@localhost:5432/upskill"
    )
    assert Settings().database_url.startswith("postgresql+psycopg://")
