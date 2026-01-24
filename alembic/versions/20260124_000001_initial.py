"""Initial database schema with PostGIS types"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from geoalchemy2 import Geography

revision = "20260124_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "routes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_geom", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("end_geom", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("distance_km", sa.Numeric(10, 2)),
        sa.Column("risk_level", sa.String(length=32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "route_segments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", Geography(geometry_type="LINESTRING", srid=4326, spatial_index=False)),
        sa.Column("score", sa.Numeric(5, 2)),
        sa.Column("metadata", pg.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "telemetry",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("position", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("battery", sa.Integer()),
        sa.Column("signal", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("payload", pg.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_table("audit_log")
    op.drop_table("telemetry")
    op.drop_table("route_segments")
    op.drop_table("routes")
    op.drop_table("users")
