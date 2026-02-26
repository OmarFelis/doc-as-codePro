"""Paso 5 — Tests del QualityAuditRepository usando SQLite en memoria."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base, QualityAuditORM
from src.db import repository as repo
from src.models.domain import QualityAudit, EntityType, RiskLevel


# SQLite no soporta JSONB ni UUID nativos — usamos JSON y String como fallback
# Redefinimos las columnas para el test sin tocar el modelo de producción
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
import uuid
from datetime import datetime, timezone


class QualityAuditORMSQLite(Base):
    __tablename__ = "quality_audits_test"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), nullable=True)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    runtime_env = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    risk_level = Column(String(10), nullable=False, default="MEDIUM")
    overall_score = Column(Float, nullable=True)
    description = Column(JSON, nullable=False, default=dict)
    external_relations = Column(JSON, nullable=False, default=dict)
    metrics = Column(JSON, nullable=False, default=dict)
    compliance = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[QualityAuditORMSQLite.__table__])
    Session = sessionmaker(bind=engine)
    s = Session()
    # Monkey-patch el ORM que usa el repo para apuntar a la tabla SQLite
    original = repo.QualityAuditORM
    repo.QualityAuditORM = QualityAuditORMSQLite
    yield s
    s.close()
    repo.QualityAuditORM = original


def _audit(name: str, entity_type=EntityType.MICROSERVICE, parent_id=None, overall_score=75.0) -> QualityAudit:
    return QualityAudit(
        entity_name=name,
        entity_type=entity_type,
        parent_id=parent_id,
        language="python",
        risk_level=RiskLevel.LOW,
        overall_score=overall_score,
        metrics={"lines_of_code": 20},
        compliance={"loc_ok": True},
    )


def test_upsert_inserta_y_retorna_con_id(session):
    result = repo.upsert(session, _audit("ACS"))
    session.commit()
    assert result.id is not None
    assert result.entity_name == "ACS"


def test_upsert_actualiza_sin_duplicar(session):
    repo.upsert(session, _audit("ACS", overall_score=50.0))
    session.commit()
    repo.upsert(session, _audit("ACS", overall_score=80.0))
    session.commit()
    rows = session.query(QualityAuditORMSQLite).filter_by(entity_name="ACS").all()
    assert len(rows) == 1
    assert rows[0].overall_score == 80.0


def test_get_by_name_retorna_registro(session):
    repo.upsert(session, _audit("ACS"))
    session.commit()
    result = repo.get_by_name(session, "ACS")
    assert result is not None
    assert result.entity_name == "ACS"


def test_get_by_name_retorna_none_si_no_existe(session):
    result = repo.get_by_name(session, "NO_EXISTE")
    assert result is None


def test_get_by_parent_retorna_hijos(session):
    parent = repo.upsert(session, _audit("ACS", EntityType.MICROSERVICE))
    session.commit()

    repo.upsert(session, _audit("calcular_comision", EntityType.LOGIC_UNIT, parent_id=parent.id))
    repo.upsert(session, _audit("validar_monto", EntityType.LOGIC_UNIT, parent_id=parent.id))
    session.commit()

    children = repo.get_by_parent(session, parent.id)
    names = {c.entity_name for c in children}
    assert "calcular_comision" in names
    assert "validar_monto" in names


def test_upsert_all_persiste_lista(session):
    audits = [_audit(f"func_{i}", EntityType.LOGIC_UNIT) for i in range(3)]
    results = repo.upsert_all(session, audits)
    session.commit()
    assert len(results) == 3
    assert all(r.id is not None for r in results)
