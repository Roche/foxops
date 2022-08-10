from sqlalchemy import Column, Integer, MetaData, String, Table, UniqueConstraint

meta = MetaData()

# Database schemas
incarnations = Table(
    "incarnation",
    meta,
    Column("id", Integer, primary_key=True),
    Column("incarnation_repository", String),
    Column("target_directory", String),
    Column("commit_sha", String),
    Column("merge_request_id", String, nullable=True),
    UniqueConstraint("incarnation_repository", "target_directory", name="incarnation_identity"),
)
