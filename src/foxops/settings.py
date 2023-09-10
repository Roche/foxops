from enum import Enum
from pathlib import Path

from pydantic import BaseSettings, DirectoryPath, SecretStr


# extracted database-related settings into a separate class, as they are also needed by alembic
# for generating migrations
class DatabaseSettings(BaseSettings):
    url: SecretStr = SecretStr("sqlite+aiosqlite:///./test.db")

    class Config:
        env_prefix = "foxops_database_"
        secrets_dir = "/var/run/secrets/foxops"


class HosterType(Enum):
    GITLAB = "gitlab"
    LOCAL = "local"


class GitlabHosterSettings(BaseSettings):
    address: str
    token: SecretStr

    class Config:
        env_prefix: str = "foxops_hoster_gitlab_"
        secrets_dir: str = "/var/run/secrets/foxops"


class LocalHosterSettings(BaseSettings):
    directory: DirectoryPath

    class Config:
        env_prefix: str = "foxops_hoster_local_"
        secrets_dir: str = "/var/run/secrets/foxops"


class Settings(BaseSettings):
    static_token: SecretStr
    frontend_dist_dir: Path = Path("ui/dist")
    log_level: str = "INFO"

    hoster_type: HosterType = HosterType.LOCAL

    class Config:
        env_prefix = "foxops_"
        secrets_dir = "/var/run/secrets/foxops"
