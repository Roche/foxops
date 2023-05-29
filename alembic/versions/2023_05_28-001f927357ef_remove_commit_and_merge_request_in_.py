"""remove commit and merge request in incarnation

Revision ID: 001f927357ef
Revises: b5550893860c
Create Date: 2023-05-28 22:54:06.724594+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001f927357ef"
down_revision = "b5550893860c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.alter_column("template_repository", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_column("commit_sha")
        batch_op.drop_column("merge_request_id")


def downgrade() -> None:
    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.add_column(sa.Column("merge_request_id", sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column("commit_sha", sa.VARCHAR(), nullable=True))
        batch_op.alter_column("template_repository", existing_type=sa.VARCHAR(), nullable=True)
