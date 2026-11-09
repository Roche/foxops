from enum import Enum
from pathlib import Path

from pydantic import DirectoryPath, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# extracted database-related settings into a separate class, as they are also needed by alembic
# for generating migrations
class DatabaseSettings(BaseSettings):
    url: SecretStr = SecretStr("sqlite+aiosqlite:///./test.db")

    model_config = SettingsConfigDict(env_prefix="foxops_database_", secrets_dir="/var/run/secrets/foxops")


class HosterType(Enum):
    GITLAB = "gitlab"
    LOCAL = "local"


class GitlabHosterSettings(BaseSettings):
    address: str
    token: SecretStr

    model_config = SettingsConfigDict(env_prefix="foxops_hoster_gitlab_", secrets_dir="/var/run/secrets/foxops")


class LocalHosterSettings(BaseSettings):
    directory: DirectoryPath

    model_config = SettingsConfigDict(env_prefix="foxops_hoster_local_", secrets_dir="/var/run/secrets/foxops")


class Settings(BaseSettings):
    static_token: SecretStr
    frontend_dist_dir: Path = Path("ui/dist")
    log_level: str = "INFO"

    hoster_type: HosterType = HosterType.LOCAL

    model_config = SettingsConfigDict(env_prefix="foxops_", secrets_dir="/var/run/secrets/foxops")
