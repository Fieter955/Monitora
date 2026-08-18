"""Initial application tables.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("prometheus_job", sa.String(length=80), nullable=False),
        sa.Column("prometheus_target", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_devices_name", "devices", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_devices_name", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
