from functools import cache

from pydantic import SecretStr

from foxops.hosters import HosterSettings


class GitLabSettings(HosterSettings):
    """Gitlab specific settings."""

    address: str
    token: SecretStr

    class Config:
        env_prefix: str = "foxops_gitlab_"
        secrets_dir: str = "/var/run/secrets/foxops"


@cache
def get_gitlab_settings() -> GitLabSettings:
    return GitLabSettings()  # type: ignore
