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
    Column("incarnation_repository", String, nullable=False),
    Column("target_directory", String, nullable=False),
    Column("template_repository", String, nullable=False),
    UniqueConstraint("incarnation_repository", "target_directory", name="incarnation_identity"),
)

change = Table(
    "change",
    meta,
    Column("id", Integer, primary_key=True),
    Column("incarnation_id", Integer, ForeignKey("incarnation.id", ondelete="CASCADE"), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("type", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("requested_version_hash", String, nullable=False),
    Column("requested_version", String, nullable=False),
    Column("requested_data", String, nullable=False),
    Column("commit_sha", String, nullable=False),
    Column("commit_pushed", Boolean, nullable=False),
    # fields for merge request changes
    Column("merge_request_id", String),
    Column("merge_request_branch_name", String),
    UniqueConstraint("incarnation_id", "revision", name="change_incarnation_revision"),
)
