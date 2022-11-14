import pytest
from _pytest.monkeypatch import MonkeyPatch

from foxops.hosters.gitlab import GitLabSettings
from foxops.settings import Settings


@pytest.mark.filterwarnings('ignore:directory "/var/run/secrets/foxops" does not exist')
def test_settings_can_load_config_from_env(monkeypatch: MonkeyPatch):
    # GIVEN
    monkeypatch.setenv("FOXOPS_GITLAB_ADDRESS", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_TOKEN", "dummy")
    monkeypatch.setenv("FOXOPS_STATIC_TOKEN", "dummy")

    # WHEN
    gsettings: GitLabSettings = GitLabSettings()  # type: ignore
    settings = Settings()  # type: ignore

    # THEN
    assert gsettings.address == "dummy"
    assert gsettings.token.get_secret_value() == "dummy"
    assert settings.static_token.get_secret_value() == "dummy"
