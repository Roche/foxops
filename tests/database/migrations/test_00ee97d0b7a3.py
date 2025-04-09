import json

from sqlalchemy import text

from alembic.command import upgrade
from alembic.script import ScriptDirectory

INSERT_INCARNAION = text(
    """
    INSERT INTO incarnation (
        id,
        incarnation_repository,
        target_directory,
        template_repository
    ) VALUES (
        1,
        'test/incarnation',
        '.',
        'https://example.com/template.git'
    )
    """
)
INSERT_LEGACY_CHANGE = text(
    """
    INSERT INTO change (
        incarnation_id,
        revision,
        type,
        created_at,
        requested_version_hash,
        requested_version,
        requested_data,
        commit_sha,
        commit_pushed
    ) VALUES (
        1,
        :revision,
        'direct',
        '2021-01-01 00:00:00',
        '1234567890abcdef',
        '1.0.0',
        :requested_data,
        '1234567890abcdef',
        1
    )
    """
)


async def test_database_upgrade(alembic_config, database_engine, async_database_engine):
    # GIVEN
    # ... the migration script
    TARGET_REVISION = "00ee97d0b7a3"
    sd = ScriptDirectory.from_config(alembic_config)
    previous_revision = sd.get_revision(TARGET_REVISION).down_revision

    # ... a database with the previous schema version and some data in the change table
    upgrade(alembic_config, previous_revision)

    with database_engine.connect() as connection:
        connection.execute(INSERT_INCARNAION)
        connection.execute(
            INSERT_LEGACY_CHANGE, parameters={"revision": 1, "requested_data": json.dumps({"dummydata": "yes"})}
        )
        connection.execute(
            INSERT_LEGACY_CHANGE, parameters={"revision": 2, "requested_data": json.dumps({"dummydata": "no"})}
        )
        connection.commit()

    # WHEN
    # ... running the migration to the target version
    upgrade(alembic_config, TARGET_REVISION)
