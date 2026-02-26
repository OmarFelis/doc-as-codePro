"""CRUD para quality_audits."""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select
from src.db.models import QualityAuditORM
from src.models.domain import QualityAudit


def _to_orm(audit: QualityAudit) -> dict:
    return {
        "id": str(uuid.UUID(audit.id)) if audit.id else str(uuid.uuid4()),
        "parent_id": str(uuid.UUID(audit.parent_id)) if audit.parent_id else None,
        "entity_name": audit.entity_name,
        "entity_type": audit.entity_type if isinstance(audit.entity_type, str) else audit.entity_type.value,
        "runtime_env": audit.runtime_env,
        "language": audit.language if isinstance(audit.language, str) else (audit.language.value if audit.language else None),
        "risk_level": audit.risk_level if isinstance(audit.risk_level, str) else audit.risk_level.value,
        "overall_score": audit.overall_score,
        "description": audit.description,
        "external_relations": audit.external_relations,
        "metrics": audit.metrics,
        "compliance": audit.compliance,
    }


def _to_domain(row: QualityAuditORM) -> QualityAudit:
    return QualityAudit(
        id=str(row.id),
        parent_id=str(row.parent_id) if row.parent_id else None,
        entity_name=row.entity_name,
        entity_type=row.entity_type,
        runtime_env=row.runtime_env,
        language=row.language,
        risk_level=row.risk_level,
        overall_score=row.overall_score,
        description=row.description or {},
        external_relations=row.external_relations or {},
        metrics=row.metrics or {},
        compliance=row.compliance or {},
        created_at=row.created_at,
    )


def upsert(session: Session, audit: QualityAudit) -> QualityAudit:
    """Inserta o actualiza por entity_name + entity_type."""
    existing = session.execute(
        select(QualityAuditORM).where(
            QualityAuditORM.entity_name == audit.entity_name,
            QualityAuditORM.entity_type == (audit.entity_type if isinstance(audit.entity_type, str) else audit.entity_type.value),
        )
    ).scalar_one_or_none()

    data = _to_orm(audit)

    if existing:
        for k, v in data.items():
            if k != "id":
                setattr(existing, k, v)
        session.flush()
        return _to_domain(existing)

    row = QualityAuditORM(**data)
    session.add(row)
    session.flush()
    return _to_domain(row)


def upsert_all(session: Session, audits: List[QualityAudit]) -> List[QualityAudit]:
    return [upsert(session, a) for a in audits]


def get_by_name(session: Session, entity_name: str) -> Optional[QualityAudit]:
    row = session.execute(
        select(QualityAuditORM).where(QualityAuditORM.entity_name == entity_name)
    ).scalar_one_or_none()
    return _to_domain(row) if row else None


def get_by_parent(session: Session, parent_id: str) -> List[QualityAudit]:
    rows = session.execute(
        select(QualityAuditORM).where(QualityAuditORM.parent_id == parent_id)
    ).scalars().all()
    return [_to_domain(r) for r in rows]
