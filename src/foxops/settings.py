from pathlib import Path

from pydantic import BaseSettings, SecretStr


# extracted database-related settings into a separate class, as they are also needed by alembic
# for generating migrations
class DatabaseSettings(BaseSettings):
    url: SecretStr = SecretStr("sqlite+aiosqlite:///./test.db")

    class Config:
        env_prefix = "foxops_database_"
        secrets_dir = "/var/run/secrets/foxops"


class Settings(BaseSettings):
    static_token: SecretStr
    frontend_dist_dir: Path = Path("ui/dist")
    log_level: str = "INFO"

    class Config:
        env_prefix = "foxops_"
        secrets_dir = "/var/run/secrets/foxops"
