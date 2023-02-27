"""add template repository to incarnation

Revision ID: b5550893860c
Revises: 0c83b17b732d
Create Date: 2023-02-27 13:41:45.635667+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b5550893860c"
down_revision = "0c83b17b732d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.add_column(sa.Column("template_repository", sa.String(), nullable=False))
        batch_op.alter_column("incarnation_repository", nullable=False)
        batch_op.alter_column("target_directory", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.drop_column("template_repository")
        batch_op.alter_column("incarnation_repository", nullable=True)
        batch_op.alter_column("target_directory", nullable=True)
