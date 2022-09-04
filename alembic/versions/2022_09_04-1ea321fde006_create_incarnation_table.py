"""create incarnation table

Revision ID: 1ea321fde006
Revises:
Create Date: 2022-09-04 19:17:53.794855+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "1ea321fde006"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incarnation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incarnation_repository", sa.String(), nullable=True),
        sa.Column("target_directory", sa.String(), nullable=True),
        sa.Column("commit_sha", sa.String(), nullable=True),
        sa.Column("merge_request_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incarnation_repository", "target_directory", name="incarnation_identity"),
    )


def downgrade() -> None:
    op.drop_table("incarnation")
