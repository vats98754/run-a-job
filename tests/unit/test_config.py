"""Basic configuration tests."""

import pytest
from run_a_job.config.settings import Settings


@pytest.mark.unit
def test_settings_creation():
    """Test that settings can be created."""
    settings = Settings()
    assert settings.browser_headless is True
    assert settings.browser_timeout == 30000
    assert settings.max_concurrent_jobs == 10


@pytest.mark.unit
def test_database_url_default():
    """Test database URL default value."""
    settings = Settings()
    assert "sqlite+aiosqlite" in settings.database_url


@pytest.mark.unit
def test_api_settings():
    """Test API settings."""
    settings = Settings()
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.api_workers == 1