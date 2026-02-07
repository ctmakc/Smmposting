"""Tests for configuration."""

from libs.core.config import Settings


class TestSettings:
    def test_defaults(self):
        settings = Settings(
            _env_file=None,
        )
        assert settings.app_name == "content-factory"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert "postgresql" in settings.database_url

    def test_override_via_init(self):
        settings = Settings(
            app_name="test-app",
            debug=True,
            log_level="DEBUG",
            _env_file=None,
        )
        assert settings.app_name == "test-app"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
