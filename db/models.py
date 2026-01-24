from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.sql import func
from geoalchemy2 import Geography

from db.session import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(pg.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    start_geom = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)
    end_geom = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)
    distance_km = Column(Float, nullable=True)
    risk_level = Column(String(length=32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RouteSegment(Base):
    __tablename__ = "route_segments"

    id = Column(pg.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    route_id = Column(pg.UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    path = Column(Geography(geometry_type="LINESTRING", srid=4326, spatial_index=False), nullable=False)
    score = Column(Float, nullable=True)
    metadata = Column(pg.JSONB, server_default=text("'{}'::jsonb"), nullable=False)


class AuthorityDecision(Base):
    __tablename__ = "authority_decisions"

    id = Column(pg.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    route_id = Column(pg.UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    actor_role = Column(Enum("DISTRICT", "NDRF", name="actor_role_enum"), nullable=False)
    decision = Column(Enum("APPROVED", "REJECTED", name="decision_enum"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(pg.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    actor = Column(String(length=255), nullable=False)
    action = Column(String(length=255), nullable=False)
    payload = Column(pg.JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
