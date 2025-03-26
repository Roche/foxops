import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)


class Permission(enum.Enum):
    READ = "read"
    WRITE = "write"


meta = MetaData()

# Database schemas
incarnations = Table(
    "incarnation",
    meta,
    Column("id", Integer, primary_key=True),
    Column("incarnation_repository", String, nullable=False),
    Column("target_directory", String, nullable=False),
    Column("template_repository", String, nullable=False),
    Column("owner", Integer, ForeignKey("foxops_user.id", ondelete="noaction"), nullable=False),
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
    Column("template_data_full", String, nullable=False),
    Column("commit_sha", String, nullable=False),
    Column("commit_pushed", Boolean, nullable=False),
    Column("initialized_by", Integer, ForeignKey("foxops_user.id", ondelete="setnull"), nullable=True),
    # fields for merge request changes
    Column("merge_request_id", String),
    Column("merge_request_branch_name", String),
    UniqueConstraint("incarnation_id", "revision", name="change_incarnation_revision"),
)


group = Table(
    "foxops_group",
    meta,
    Column("id", Integer, primary_key=True),
    Column("system_name", String, nullable=False, unique=True),
    Column("display_name", String, nullable=False),
)

user = Table(
    "foxops_user",
    meta,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False, unique=True),
    Column("is_admin", Boolean, nullable=False, default=False),
)

group_user = Table(
    "group_user",
    meta,
    Column("group_id", Integer, ForeignKey("foxops_group.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("foxops_user.id", ondelete="CASCADE"), primary_key=True),
)

user_incarnation_permission = Table(
    "user_incarnation_permission",
    meta,
    Column("user_id", Integer, ForeignKey("foxops_user.id", ondelete="CASCADE"), primary_key=True),
    Column("incarnation_id", Integer, ForeignKey("incarnation.id", ondelete="CASCADE"), primary_key=True),
    Column("type", Enum(Permission), nullable=False),
)


group_incarnation_permission = Table(
    "group_incarnation_permission",
    meta,
    Column("group_id", Integer, ForeignKey("foxops_group.id", ondelete="CASCADE"), primary_key=True),
    Column("incarnation_id", Integer, ForeignKey("incarnation.id", ondelete="CASCADE"), primary_key=True),
    Column("type", Enum(Permission), nullable=False),
)
