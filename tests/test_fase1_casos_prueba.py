"""
Casos de prueba end-to-end — Fase 1
Validan el pipeline completo con microservicios de ejemplo realistas.

Casos cubiertos:
  CT-01: Microservicio de dominio puro → capa DOMINIO, scores altos
  CT-02: Acoplamiento multicapa → has_multi_layer_coupling = True
  CT-03: Infraestructura pura → capa INFRAESTRUCTURA, no procesa reglas
  CT-04: Alta complejidad → risk_level HIGH, overall_score bajo
  CT-05: Doble análisis del mismo microservicio → no duplica registros
  CT-06: Pipeline retorna quality_summary con todos los campos requeridos
"""
import pytest
import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base
from src.db import repository as repo
from src.core.analyzers import logical_unit_extractor
from src.models.domain import FileAnalysis, LanguageType

FIXTURES = Path(__file__).parent / "fixtures" / "microservicios"


# --- ORM SQLite para tests ---

class QualityAuditORMTest(Base):
    __tablename__ = "qa_e2e"
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
    Base.metadata.create_all(engine, tables=[QualityAuditORMTest.__table__])
    Session = sessionmaker(bind=engine)
    s = Session()
    original = repo.QualityAuditORM
    repo.QualityAuditORM = QualityAuditORMTest
    yield s
    s.close()
    repo.QualityAuditORM = original


def _analyze_fixture(filename: str) -> FileAnalysis:
    """Analiza un fixture usando el PythonAnalyzer real."""
    from src.core.analyzers.python_analyzer import PythonAnalyzer
    return PythonAnalyzer().analyze_file(FIXTURES / filename)


# ─────────────────────────────────────────────
# CT-01: Dominio puro
# ─────────────────────────────────────────────

def test_ct01_dominio_puro_clasifica_capa_correcta():
    """CT-01: Funciones sin imports de infra → capa DOMINIO."""
    fa = _analyze_fixture("dominio_puro.py")
    audits = logical_unit_extractor.extract(fa)

    layers = {a.metrics["architecture_layer"] for a in audits}
    assert layers == {"dominio"}, f"Se esperaba solo 'dominio', se obtuvo: {layers}"


def test_ct01_dominio_puro_scores_altos():
    """CT-01: Funciones simples de dominio → overall_score > 60."""
    fa = _analyze_fixture("dominio_puro.py")
    audits = logical_unit_extractor.extract(fa)

    for audit in audits:
        assert audit.overall_score is not None
        assert audit.overall_score > 60, (
            f"{audit.entity_name}: overall_score={audit.overall_score} esperado > 60"
        )


def test_ct01_dominio_puro_risk_low():
    """CT-01: Funciones simples → risk_level LOW."""
    fa = _analyze_fixture("dominio_puro.py")
    audits = logical_unit_extractor.extract(fa)
    assert all(a.risk_level == "LOW" for a in audits)


def test_ct01_dominio_puro_sin_multi_layer():
    """CT-01: Sin imports mixtos → has_multi_layer_coupling = False."""
    fa = _analyze_fixture("dominio_puro.py")
    audits = logical_unit_extractor.extract(fa)
    assert all(a.compliance["has_multi_layer_coupling"] is False for a in audits)


# ─────────────────────────────────────────────
# CT-02: Acoplamiento multicapa
# ─────────────────────────────────────────────

def test_ct02_multicapa_detecta_coupling():
    """CT-02: Imports de fastapi + boto3 → has_multi_layer_coupling = True."""
    fa = _analyze_fixture("acoplamiento_multicapa.py")
    audits = logical_unit_extractor.extract(fa)

    assert len(audits) > 0
    assert any(a.compliance["has_multi_layer_coupling"] is True for a in audits), (
        "Se esperaba al menos una unidad con has_multi_layer_coupling=True"
    )


def test_ct02_multicapa_capa_infraestructura():
    """CT-02: Archivo con boto3 + fastapi → capa INFRAESTRUCTURA (infra tiene precedencia)."""
    fa = _analyze_fixture("acoplamiento_multicapa.py")
    audits = logical_unit_extractor.extract(fa)
    layers = {a.metrics["architecture_layer"] for a in audits}
    assert "infraestructura" in layers


# ─────────────────────────────────────────────
# CT-03: Infraestructura pura
# ─────────────────────────────────────────────

def test_ct03_infraestructura_clasifica_correcta():
    """CT-03: Imports de boto3/psycopg2 → capa INFRAESTRUCTURA."""
    fa = _analyze_fixture("infraestructura_pura.py")
    audits = logical_unit_extractor.extract(fa)

    layers = {a.metrics["architecture_layer"] for a in audits}
    assert layers == {"infraestructura"}, f"Se esperaba solo 'infraestructura', se obtuvo: {layers}"


def test_ct03_infraestructura_detecta_aws_services():
    """CT-03: Imports de boto3/s3/sqs → aws_services poblado."""
    fa = _analyze_fixture("infraestructura_pura.py")
    audits = logical_unit_extractor.extract(fa)

    aws_services = audits[0].metrics.get("aws_services", [])
    assert len(aws_services) > 0, "Se esperaban AWS services detectados"


def test_ct03_infraestructura_no_es_dominio():
    """CT-03: Ninguna unidad de infraestructura debe clasificar como dominio."""
    fa = _analyze_fixture("infraestructura_pura.py")
    audits = logical_unit_extractor.extract(fa)
    assert all(a.metrics["architecture_layer"] != "dominio" for a in audits)


# ─────────────────────────────────────────────
# CT-04: Alta complejidad
# ─────────────────────────────────────────────

def test_ct04_alta_complejidad_risk_high():
    """CT-04: Función con complejidad > 15 → risk_level HIGH."""
    fa = _analyze_fixture("alta_complejidad.py")
    audits = logical_unit_extractor.extract(fa)

    assert any(a.risk_level == "HIGH" for a in audits), (
        "Se esperaba al menos una unidad con risk_level=HIGH"
    )


def test_ct04_alta_complejidad_score_bajo():
    """CT-04: Alta complejidad → overall_score < 60."""
    fa = _analyze_fixture("alta_complejidad.py")
    audits = logical_unit_extractor.extract(fa)

    high_risk = [a for a in audits if a.risk_level == "HIGH"]
    assert all(a.overall_score < 60 for a in high_risk), (
        "Unidades HIGH risk deberían tener overall_score < 60"
    )


def test_ct04_alta_complejidad_compliance_flag():
    """CT-04: Complejidad > 10 → compliance.complexity_ok = False."""
    fa = _analyze_fixture("alta_complejidad.py")
    audits = logical_unit_extractor.extract(fa)

    high_risk = [a for a in audits if a.risk_level == "HIGH"]
    assert all(a.compliance["complexity_ok"] is False for a in high_risk)


# ─────────────────────────────────────────────
# CT-05: Persistencia — no duplica registros
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ct05_doble_analisis_no_duplica(session):
    """CT-05: Analizar el mismo microservicio dos veces no duplica en BD."""
    from src.core.analyzers import pipeline

    fixtures_path = FIXTURES
    await pipeline.run(fixtures_path, "ACS-TEST", session)
    session.commit()
    await pipeline.run(fixtures_path, "ACS-TEST", session)
    session.commit()

    rows = session.query(QualityAuditORMTest).filter_by(entity_name="ACS-TEST").all()
    assert len(rows) == 1, f"Se esperaba 1 registro padre, se encontraron {len(rows)}"


@pytest.mark.asyncio
async def test_ct05_unidades_logicas_persisten_con_parent_id(session):
    """CT-05: Las unidades lógicas tienen parent_id apuntando al microservicio."""
    from src.core.analyzers import pipeline

    summary = await pipeline.run(FIXTURES, "ACS-TEST", session)
    session.commit()

    parent = repo.get_by_name(session, "ACS-TEST")
    children = repo.get_by_parent(session, parent.id)

    assert len(children) > 0
    assert all(c.parent_id == parent.id for c in children)
    assert all(c.entity_type == "LOGIC_UNIT" for c in children)


# ─────────────────────────────────────────────
# CT-06: Quality summary completo
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ct06_quality_summary_campos_requeridos(session):
    """CT-06: El pipeline retorna todos los campos del quality_summary."""
    from src.core.analyzers import pipeline

    summary = await pipeline.run(FIXTURES, "ACS-TEST", session)

    required_fields = [
        "microservice_id", "microservice_name", "overall_score",
        "risk_level", "units_count", "business_rules_count", "high_risk_units"
    ]
    for field in required_fields:
        assert field in summary, f"Campo requerido ausente: {field}"


@pytest.mark.asyncio
async def test_ct06_quality_summary_risk_level_valido(session):
    """CT-06: risk_level del summary debe ser LOW, MEDIUM o HIGH."""
    from src.core.analyzers import pipeline

    summary = await pipeline.run(FIXTURES, "ACS-TEST", session)
    assert summary["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


@pytest.mark.asyncio
async def test_ct06_quality_summary_detecta_high_risk(session):
    """CT-06: Con fixture de alta complejidad → high_risk_units > 0."""
    from src.core.analyzers import pipeline

    # Solo el fixture de alta complejidad
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(FIXTURES / "alta_complejidad.py", tmp / "alta_complejidad.py")

    try:
        summary = await pipeline.run(tmp, "COMPLEJO", session)
        assert summary["high_risk_units"] > 0, "Se esperaban unidades HIGH risk"
        assert summary["risk_level"] == "HIGH"
    finally:
        shutil.rmtree(tmp)
