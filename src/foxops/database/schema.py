from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

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

change = Table(
    "change",
    meta,
    Column("id", Integer, primary_key=True),
    Column("incarnation_id", Integer, ForeignKey("incarnation.id", ondelete="CASCADE"), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("type", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("requested_version", String),
    Column("requested_data", String),
    Column("commit_sha", String, nullable=False),
    Column("commit_pushed", Boolean),
    # fields for merge request changes
    Column("merge_request_id", String),
    Column("merge_request_status", String),
    Column("merge_request_branch_name", String),
    Column("main_branch_commit_sha", String),
    UniqueConstraint("incarnation_id", "revision", name="change_incarnation_revision"),
)
