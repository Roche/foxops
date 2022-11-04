from functools import cache

from pydantic import BaseSettings, SecretStr


class GitLabSettings(BaseSettings):
    """Gitlab specific settings.
    client_id & client_secret are generated when registering foxops as OAuth application
    """

    address: str
    client_id: str
    client_secret: SecretStr
    client_scope: str = "api openid profile email"

    class Config:
        env_prefix: str = "foxops_gitlab_"
        secrets_dir: str = "/var/run/secrets/foxops"


@cache
def get_gitlab_settings() -> GitLabSettings:
    return GitLabSettings()  # type: ignore
