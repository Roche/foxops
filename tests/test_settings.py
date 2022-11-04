import pytest
from _pytest.monkeypatch import MonkeyPatch

from foxops.hosters.gitlab import GitLabSettings
from foxops.jwt import JWTSettings
from foxops.settings import DatabaseSettings, Settings


@pytest.mark.filterwarnings('ignore:directory "/var/run/secrets/foxops" does not exist')
def test_settings_can_load_config_from_env(monkeypatch: MonkeyPatch):
    # GIVEN
    monkeypatch.setenv("FOXOPS_LOG_LEVEL", "dummy")
    monkeypatch.setenv("FOXOPS_DATABASE_URL", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_ADDRESS", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_CLIENT_ID", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_CLIENT_SECRET", "dummy")
    monkeypatch.setenv("FOXOPS_JWT_SECRET_KEY", "dummy")
    monkeypatch.setenv("FOXOPS_JWT_ALGORITHM", "dummy")
    monkeypatch.setenv("FOXOPS_JWT_TOKEN_EXPIRE", "42")

    # WHEN
    settings = Settings()
    db_settings: DatabaseSettings = DatabaseSettings()
    gitlab_settings: GitLabSettings = GitLabSettings()  # type: ignore
    jwt_settings: JWTSettings = JWTSettings()

    # THEN
    assert settings.log_level == "dummy"
    assert db_settings.url.get_secret_value() == "dummy"
    assert gitlab_settings.address == "dummy"
    assert gitlab_settings.client_id == "dummy"
    assert gitlab_settings.client_secret.get_secret_value() == "dummy"
    assert jwt_settings.secret_key.get_secret_value() == "dummy"
    assert jwt_settings.algorithm == "dummy"
    assert jwt_settings.token_expire == 42
