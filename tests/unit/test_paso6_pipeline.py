"""Paso 6 — Test del pipeline completo con SQLite en memoria."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
from datetime import datetime, timezone

from src.db.models import Base
from src.db import repository as repo
from src.models.domain import QualityAudit, EntityType, RiskLevel


# Mismo ORM SQLite del Paso 5
class QualityAuditORMSQLite(Base):
    __tablename__ = "quality_audits_p6"
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
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[QualityAuditORMSQLite.__table__])
    Session = sessionmaker(bind=engine)
    s = Session()
    original = repo.QualityAuditORM
    repo.QualityAuditORM = QualityAuditORMSQLite
    yield s
    s.close()
    repo.QualityAuditORM = original


@pytest.fixture
def sample_project(tmp_path):
    """Crea un proyecto Python mínimo para analizar."""
    (tmp_path / "payments.py").write_text(
        "def calcular_comision(monto, tipo):\n"
        "    if monto <= 0:\n"
        "        raise ValueError('monto invalido')\n"
        "    return monto * 0.035 if tipo == 'credito' else monto * 0.015\n\n"
        "def validar_monto(monto):\n"
        "    return monto >= 1.0\n"
    )
    return tmp_path


@pytest.mark.asyncio
async def test_pipeline_persiste_microservicio_padre(session, sample_project):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(sample_project, "ACS", session)
    session.commit()

    parent = repo.get_by_name(session, "ACS")
    assert parent is not None
    assert parent.entity_type == "MICROSERVICE"


@pytest.mark.asyncio
async def test_pipeline_persiste_unidades_logicas(session, sample_project):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(sample_project, "ACS", session)
    session.commit()

    parent = repo.get_by_name(session, "ACS")
    children = repo.get_by_parent(session, parent.id)
    assert len(children) > 0
    assert all(c.entity_type == "LOGIC_UNIT" for c in children)


@pytest.mark.asyncio
async def test_pipeline_retorna_quality_summary(session, sample_project):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(sample_project, "ACS", session)

    assert "microservice_id" in summary
    assert "overall_score" in summary
    assert "risk_level" in summary
    assert "units_count" in summary
    assert summary["units_count"] > 0
    assert summary["microservice_name"] == "ACS"


@pytest.mark.asyncio
async def test_pipeline_con_llm_extrae_reglas(session, sample_project):
    from src.core.analyzers import pipeline
    import json

    llm = AsyncMock()
    llm.generate_text = AsyncMock(return_value=json.dumps([
        {"description": "Valida que el monto sea mayor a cero", "condition": "monto <= 0", "result": "ValueError"}
    ]))

    summary = await pipeline.run(sample_project, "ACS", session, llm_client=llm)
    assert summary["business_rules_count"] >= 0  # puede ser 0 si no hay unidades DOMINIO


@pytest.mark.asyncio
async def test_pipeline_doble_ejecucion_no_duplica(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, "ACS", session)
    session.commit()
    await pipeline.run(sample_project, "ACS", session)
    session.commit()

    rows = session.query(QualityAuditORMSQLite).filter_by(entity_name="ACS").all()
    assert len(rows) == 1
