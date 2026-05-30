"""Production settings validation tests."""

import pytest

from backend.settings import Settings


def test_production_rejects_debug_mode() -> None:
    with pytest.raises(ValueError, match="APP_DEBUG"):
        Settings(
            _env_file=(),
            app_env="production",
            app_debug=True,
            jwt_secret_key="production-jwt-secret-key-with-sufficient-length",
            admin_api_key="admin-secret",
            openrouter_api_key="sk-test",
        )


def test_production_requires_admin_key() -> None:
    with pytest.raises(ValueError, match="ADMIN_API_KEY"):
        Settings(
            _env_file=(),
            app_env="production",
            jwt_secret_key="production-jwt-secret-key-with-sufficient-length",
            openrouter_api_key="sk-test",
            admin_api_key="",
        )
