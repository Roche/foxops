"""add auto_update_interval_seconds to incarnation

Revision ID: a1b2c3d4e5f6
Revises: 00ee97d0b7a3
Create Date: 2026-05-06 00:00:00.000000+00:00

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "00ee97d0b7a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incarnation", sa.Column("auto_update_interval_seconds", sa.Integer(), nullable=True))
    op.execute("UPDATE incarnation SET auto_update_interval_seconds = 0")
    with op.batch_alter_table("incarnation") as batch_op:
        batch_op.alter_column("auto_update_interval_seconds", nullable=False)


def downgrade() -> None:
    op.drop_column("incarnation", "auto_update_interval_seconds")
