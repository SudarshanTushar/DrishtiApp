"""Initial minimal schema for routing with PostGIS"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from geoalchemy2 import Geography

revision = "20260124_000001"
down_revision = None
branch_labels = None
depends_on = None

actor_role_enum = sa.Enum("DISTRICT", "NDRF", name="actor_role_enum")
decision_enum = sa.Enum("APPROVED", "REJECTED", name="decision_enum")


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    actor_role_enum.create(op.get_bind(), checkfirst=True)
    decision_enum.create(op.get_bind(), checkfirst=True)

    # Check if table exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "routes" not in existing_tables:
        op.create_table(
            "routes",
            sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("start_geom", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
            sa.Column("end_geom", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
            sa.Column("distance_km", sa.Float(), nullable=True),
            sa.Column("risk_level", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "route_segments" not in existing_tables:
        op.create_table(
            "route_segments",
            sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("path", Geography(geometry_type="LINESTRING", srid=4326, spatial_index=False), nullable=False),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("segment_data", pg.JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        )

    if "authority_decisions" not in existing_tables:
        op.create_table(
            "authority_decisions",
            sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("actor_role", actor_role_enum, nullable=False),
            sa.Column("decision", decision_enum, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "audit_log" not in existing_tables:
        op.create_table(
            "audit_log",
            sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("actor", sa.String(length=255), nullable=False),
            sa.Column("action", sa.String(length=255), nullable=False),
            sa.Column("payload", pg.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )


def downgrade():
    op.drop_table("audit_log")
    op.drop_table("authority_decisions")
    op.drop_table("route_segments")
    op.drop_table("routes")
    decision_enum.drop(op.get_bind(), checkfirst=True)
    actor_role_enum.drop(op.get_bind(), checkfirst=True)
