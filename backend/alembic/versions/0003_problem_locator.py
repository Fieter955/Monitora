"""Add physical locator and network role metadata.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("locations") as batch:
        batch.add_column(
            sa.Column("address", sa.String(length=255), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))

    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("asset_tag", sa.String(length=80), nullable=True))
        batch.add_column(
            sa.Column(
                "physical_group", sa.String(length=160), nullable=False, server_default=""
            )
        )
        batch.add_column(
            sa.Column(
                "physical_position", sa.String(length=160), nullable=False, server_default=""
            )
        )
        batch.add_column(
            sa.Column(
                "network_role", sa.String(length=24), nullable=False, server_default="endpoint"
            )
        )
        batch.create_unique_constraint("uq_devices_asset_tag", ["asset_tag"])


def downgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.drop_constraint("uq_devices_asset_tag", type_="unique")
        batch.drop_column("network_role")
        batch.drop_column("physical_position")
        batch.drop_column("physical_group")
        batch.drop_column("asset_tag")

    with op.batch_alter_table("locations") as batch:
        batch.drop_column("longitude")
        batch.drop_column("latitude")
        batch.drop_column("address")
