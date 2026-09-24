"""Add Windows host and ISP uplink metadata.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.add_column(
            sa.Column("isp_name", sa.String(length=160), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("wan_if_name", sa.String(length=160), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("wan_if_index", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.drop_column("wan_if_index")
        batch.drop_column("wan_if_name")
        batch.drop_column("isp_name")
