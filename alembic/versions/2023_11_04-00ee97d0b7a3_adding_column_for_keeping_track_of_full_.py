"""adding column for keeping track of full template data

Revision ID: 00ee97d0b7a3
Revises: 001f927357ef
Create Date: 2023-11-04 16:14:57.823773+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "00ee97d0b7a3"
down_revision = "001f927357ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("change", sa.Column("template_data_full", sa.String(), nullable=True))
    op.execute("UPDATE change SET template_data_full = requested_data")

    with op.batch_alter_table("change") as batch_op:
        batch_op.alter_column("template_data_full", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("change", "template_data_full")
    # ### end Alembic commands ###