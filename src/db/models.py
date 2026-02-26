"""Modelo SQLAlchemy para la tabla quality_audits."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class QualityAuditORM(Base):
    __tablename__ = "quality_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("quality_audits.id", ondelete="CASCADE"), nullable=True)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    runtime_env = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    risk_level = Column(String(10), nullable=False, default="MEDIUM")
    overall_score = Column(Float, nullable=True)
    description = Column(JSONB, nullable=False, default=dict)
    external_relations = Column(JSONB, nullable=False, default=dict)
    metrics = Column(JSONB, nullable=False, default=dict)
    compliance = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
