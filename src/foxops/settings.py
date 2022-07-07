from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    gitlab_address: str
    gitlab_token: SecretStr
    git_commit_author_name: str = "foxops"
    git_commit_author_email: str = "noreply@foxops.io"

    class Config:
        env_prefix = "foxops_"
        secrets_dir = "/var/run/secrets/foxops"
