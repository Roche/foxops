import pytest
from _pytest.monkeypatch import MonkeyPatch

from foxops.settings import Settings


@pytest.mark.filterwarnings('ignore:directory "/var/run/secrets/foxops" does not exist')
def test_settings_can_load_config_from_env(monkeypatch: MonkeyPatch):
    # GIVEN
    monkeypatch.setenv("FOXOPS_GITLAB_ADDRESS", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_TOKEN", "dummy")

    # WHEN
    settings = Settings()

    # THEN
    assert settings.gitlab_token.get_secret_value() == "dummy"
