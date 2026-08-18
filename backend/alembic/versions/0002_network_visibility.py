"""Add locations, floorplans, network discovery, and encrypted credential references.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["locations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("parent_id", "name", name="uq_location_parent_name"),
    )
    op.create_index("ix_locations_name", "locations", ["name"])
    op.create_index("ix_locations_parent_id", "locations", ["parent_id"])

    op.create_table(
        "floorplans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("location_id"),
    )
    op.create_index("ix_floorplans_location_id", "floorplans", ["location_id"], unique=True)

    op.create_table(
        "credential_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_credential_profiles_name", "credential_profiles", ["name"], unique=True)

    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("room_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("credential_profile_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("librenms_device_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("capabilities", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(
            sa.Column(
                "monitoring_level", sa.String(length=20), nullable=False, server_default="basic"
            )
        )
        batch.add_column(sa.Column("stream_url", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("floorplan_x", sa.Float(), nullable=True))
        batch.add_column(sa.Column("floorplan_y", sa.Float(), nullable=True))
        batch.add_column(sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key(
            "fk_devices_room_id", "locations", ["room_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_foreign_key(
            "fk_devices_credential_profile_id",
            "credential_profiles",
            ["credential_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_unique_constraint("uq_devices_librenms_device_id", ["librenms_device_id"])
        batch.create_index("ix_devices_room_id", ["room_id"])

    op.create_table(
        "network_ports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("source_port_id", sa.Integer(), nullable=False),
        sa.Column("if_index", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("alias", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("admin_status", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("oper_status", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("speed_bps", sa.BigInteger(), nullable=True),
        sa.Column("rx_bps", sa.Float(), nullable=True),
        sa.Column("tx_bps", sa.Float(), nullable=True),
        sa.Column("errors_in", sa.Float(), nullable=True),
        sa.Column("errors_out", sa.Float(), nullable=True),
        sa.Column("discards_in", sa.Float(), nullable=True),
        sa.Column("discards_out", sa.Float(), nullable=True),
        sa.Column("mac_address", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("device_id", "source_port_id", name="uq_network_port_source"),
    )
    op.create_index("ix_network_ports_device_id", "network_ports", ["device_id"])

    op.create_table(
        "port_expectations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("port_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="spare"),
        sa.Column("expected_device_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("consecutive_mismatches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["port_id"], ["network_ports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expected_device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("port_id"),
    )
    op.create_index("ix_port_expectations_port_id", "port_expectations", ["port_id"], unique=True)

    op.create_table(
        "network_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=120), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("local_device_id", sa.Integer(), nullable=False),
        sa.Column("local_port_id", sa.Integer(), nullable=True),
        sa.Column("remote_device_id", sa.Integer(), nullable=True),
        sa.Column("remote_port_id", sa.Integer(), nullable=True),
        sa.Column("remote_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("remote_port_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["local_device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["local_port_id"], ["network_ports.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["remote_device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["remote_port_id"], ["network_ports.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_index("ix_network_links_source_key", "network_links", ["source_key"], unique=True)
    op.create_index("ix_network_links_local_device_id", "network_links", ["local_device_id"])
    op.create_index("ix_network_links_remote_device_id", "network_links", ["remote_device_id"])

    op.create_table(
        "device_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("reason", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("stream_status", sa.String(length=24), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index(
        "ix_device_observations_device_id", "device_observations", ["device_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("device_observations")
    op.drop_table("network_links")
    op.drop_table("port_expectations")
    op.drop_table("network_ports")
    with op.batch_alter_table("devices") as batch:
        batch.drop_index("ix_devices_room_id")
        batch.drop_constraint("uq_devices_librenms_device_id", type_="unique")
        batch.drop_constraint("fk_devices_credential_profile_id", type_="foreignkey")
        batch.drop_constraint("fk_devices_room_id", type_="foreignkey")
        for column in (
            "archived_at",
            "last_seen_at",
            "floorplan_y",
            "floorplan_x",
            "stream_url",
            "monitoring_level",
            "capabilities",
            "librenms_device_id",
            "credential_profile_id",
            "room_id",
        ):
            batch.drop_column(column)
    op.drop_table("credential_profiles")
    op.drop_table("floorplans")
    op.drop_table("locations")
