"""Add User and Groups Model

Revision ID: 5ae180bb248c
Revises: 00ee97d0b7a3
Create Date: 2025-03-26 07:30:50.314010+00:00

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5ae180bb248c"
down_revision = "00ee97d0b7a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foxops_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_name"),
    )
    op.create_table(
        "foxops_user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "group_user",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["foxops_group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["foxops_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )
    op.create_table(
        "group_incarnation_permission",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("incarnation_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Enum("READ", "WRITE", name="permission"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["foxops_group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incarnation_id"], ["incarnation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "incarnation_id"),
    )
    op.create_table(
        "user_incarnation_permission",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("incarnation_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Enum("READ", "WRITE", name="permission"), nullable=False),
        sa.ForeignKeyConstraint(["incarnation_id"], ["incarnation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["foxops_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "incarnation_id"),
    )
    with op.batch_alter_table("change") as batch_op:
        batch_op.add_column(sa.Column("initialized_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("change_user_fk", "foxops_user", ["initialized_by"], ["id"], ondelete="SET NULL")

    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.add_column(sa.Column("owner", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("incarnation_owner_fk", "foxops_user", ["owner"], ["id"], ondelete="NO ACTION")

    op.execute("INSERT INTO foxops_user (id, username, is_admin) VALUES (1, 'root', TRUE)")
    op.execute("UPDATE incarnation SET owner = 1")

    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.alter_column("owner", nullable=False)


def downgrade() -> None:
    op.drop_constraint("change_user_fk", "incarnation", type_="foreignkey")
    op.drop_column("incarnation", "owner")
    op.drop_constraint("incarnation_owner_fk", "change", type_="foreignkey")
    op.drop_column("change", "initialized_by")
    op.drop_table("user_incarnation_permission")
    op.drop_table("group_incarnation_permission")
    op.drop_table("group_user")
    op.drop_table("foxops_user")
    op.drop_table("foxops_group")
