"""
Casos de prueba end-to-end — Fase 1
CT-01: Dominio puro → capa DOMINIO, scores altos
CT-02: Acoplamiento multicapa → has_multi_layer_coupling = True
CT-03: Infraestructura pura → capa INFRAESTRUCTURA
CT-04: Alta complejidad → risk_level HIGH, score bajo
CT-05: Doble análisis → escaneos INSERT-only, archivos re-insertados
CT-06: Pipeline retorna summary con campos requeridos
"""
import uuid
import shutil
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from src.db import repository as repo
from src.core.analyzers import logical_unit_extractor
from src.models.domain import FileAnalysis, LanguageType

FIXTURES = Path(__file__).parent / "fixtures" / "microservicios"
ACTIVO_ID = str(uuid.uuid4())


class _Base(DeclarativeBase):
    pass


class ArchivoFuenteTest(_Base):
    __tablename__ = "archivos_fuente_e2e"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activo_id = Column(String(36), nullable=False)
    aplicacion_id = Column(String(255), nullable=True)
    nombre = Column(String(255), nullable=False)
    ruta_archivo = Column(Text, nullable=False)
    proposito = Column(Text, nullable=True)
    capa = Column(String(50), nullable=True)
    lenguaje = Column(String(50), nullable=True)
    total_funciones = Column(Integer, default=0)
    total_clases = Column(Integer, default=0)
    endpoints = Column(JSON, default=list)
    operaciones_bd = Column(JSON, default=list)
    llamadas_externas = Column(JSON, default=list)
    complejidad_ciclomatica = Column(Integer, default=0)
    lineas_codigo = Column(Integer, default=0)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    build_number = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)


class UnidadLogicaTest(_Base):
    __tablename__ = "unidades_logicas_e2e"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    archivo_id = Column(String(36), nullable=True)
    parent_id = Column(String(36), nullable=True)
    activo_id = Column(String(36), nullable=False)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)
    capa = Column(String(50), nullable=True)
    proposito = Column(Text, nullable=True)
    complejidad = Column(Integer, default=0)
    lineas_codigo = Column(Integer, default=0)
    accede_bd = Column(Boolean, default=False)
    llamadas_externas = Column(JSON, default=list)
    docstring = Column(Boolean, default=False)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    risk_level = Column(String(10), default="MEDIUM")
    overall_score = Column(Float, nullable=True)
    compliance = Column(JSON, default=dict)
    activo = Column(Boolean, default=True)


class EscaneoTest(_Base):
    __tablename__ = "escaneos_e2e"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activo_id = Column(String(36), nullable=False)
    aplicacion_id = Column(String(255), nullable=True)
    build_number = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    generado_por = Column(String(100), default="code-agent-v1")
    score_general = Column(Float, nullable=True)
    nivel_riesgo = Column(String(10), nullable=True)
    archivos_total = Column(Integer, default=0)
    funciones_total = Column(Integer, default=0)
    clases_total = Column(Integer, default=0)
    dominios_negocio = Column(JSON, default=list)
    metricas = Column(JSON, default=dict)
    arquitectura = Column(JSON, default=dict)
    seguridad = Column(JSON, default=dict)
    rendimiento = Column(JSON, default=dict)
    negocio = Column(JSON, default=dict)
    cumplimiento = Column(JSON, default=dict)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _Base.metadata.create_all(engine)
    orig_a, orig_u, orig_e = repo.ArchivoFuenteORM, repo.UnidadLogicaORM, repo.EscaneoORM
    repo.ArchivoFuenteORM = ArchivoFuenteTest
    repo.UnidadLogicaORM = UnidadLogicaTest
    repo.EscaneoORM = EscaneoTest
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    repo.ArchivoFuenteORM, repo.UnidadLogicaORM, repo.EscaneoORM = orig_a, orig_u, orig_e


def _analyze_fixture(filename: str) -> FileAnalysis:
    from src.core.analyzers.python_analyzer import PythonAnalyzer
    return PythonAnalyzer().analyze_file(FIXTURES / filename)


# ── CT-01: Dominio puro ───────────────────────────────────────────────────────

def test_ct01_dominio_puro_clasifica_capa_correcta():
    fa = _analyze_fixture("dominio_puro.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    layers = {u.capa for u in unidades}
    assert layers == {"dominio"}, f"Esperado solo 'dominio', obtenido: {layers}"


def test_ct01_dominio_puro_scores_altos():
    fa = _analyze_fixture("dominio_puro.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    for u in unidades:
        assert u.overall_score is not None
        assert u.overall_score > 60, f"{u.nombre}: score={u.overall_score} esperado > 60"


def test_ct01_dominio_puro_risk_low():
    fa = _analyze_fixture("dominio_puro.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert all(u.risk_level == "LOW" for u in unidades)


def test_ct01_dominio_puro_sin_multi_layer():
    fa = _analyze_fixture("dominio_puro.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert all(u.compliance.get("has_multi_layer_coupling") is False for u in unidades if u.compliance)


# ── CT-02: Acoplamiento multicapa ─────────────────────────────────────────────

def test_ct02_multicapa_detecta_coupling():
    fa = _analyze_fixture("acoplamiento_multicapa.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert any(u.compliance.get("has_multi_layer_coupling") is True for u in unidades)


def test_ct02_multicapa_capa_infraestructura():
    fa = _analyze_fixture("acoplamiento_multicapa.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert any(u.capa == "infraestructura" for u in unidades)


# ── CT-03: Infraestructura pura ───────────────────────────────────────────────

def test_ct03_infraestructura_clasifica_correcta():
    fa = _analyze_fixture("infraestructura_pura.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    layers = {u.capa for u in unidades}
    assert layers == {"infraestructura"}, f"Esperado solo 'infraestructura', obtenido: {layers}"


def test_ct03_infraestructura_detecta_aws_services():
    fa = _analyze_fixture("infraestructura_pura.py")
    archivo, _ = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert len(archivo.llamadas_externas) > 0, "Se esperaban AWS services detectados"


def test_ct03_infraestructura_no_es_dominio():
    fa = _analyze_fixture("infraestructura_pura.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert all(u.capa != "dominio" for u in unidades)


# ── CT-04: Alta complejidad ───────────────────────────────────────────────────

def test_ct04_alta_complejidad_risk_high():
    fa = _analyze_fixture("alta_complejidad.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    assert any(u.risk_level == "HIGH" for u in unidades)


def test_ct04_alta_complejidad_score_bajo():
    fa = _analyze_fixture("alta_complejidad.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    high_risk = [u for u in unidades if u.risk_level == "HIGH"]
    assert all(u.overall_score < 60 for u in high_risk)


def test_ct04_alta_complejidad_compliance_flag():
    fa = _analyze_fixture("alta_complejidad.py")
    _, unidades = logical_unit_extractor.extract(fa, ACTIVO_ID)
    high_risk = [u for u in unidades if u.risk_level == "HIGH" and u.compliance]
    assert all(u.compliance.get("complexity_ok") is False for u in high_risk)


# ── CT-05: Persistencia ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ct05_doble_analisis_escaneos_insert_only(session):
    from src.core.analyzers import pipeline
    await pipeline.run(FIXTURES, ACTIVO_ID, "ACS-TEST", session)
    session.commit()
    await pipeline.run(FIXTURES, ACTIVO_ID, "ACS-TEST", session)
    session.commit()
    rows = session.query(EscaneoTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) == 2  # INSERT-only, historial inmutable


@pytest.mark.asyncio
async def test_ct05_unidades_logicas_tienen_archivo_id(session):
    from src.core.analyzers import pipeline
    await pipeline.run(FIXTURES, ACTIVO_ID, "ACS-TEST", session)
    session.commit()
    unidades = session.query(UnidadLogicaTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(unidades) > 0
    assert all(u.archivo_id is not None for u in unidades)


# ── CT-06: Quality summary ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ct06_quality_summary_campos_requeridos(session):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(FIXTURES, ACTIVO_ID, "ACS-TEST", session)
    for field in ["escaneo_id", "activo_id", "score_general", "nivel_riesgo",
                  "archivos_total", "clases_total", "funciones_total"]:
        assert field in summary, f"Campo requerido ausente: {field}"


@pytest.mark.asyncio
async def test_ct06_quality_summary_risk_level_valido(session):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(FIXTURES, ACTIVO_ID, "ACS-TEST", session)
    assert summary["nivel_riesgo"] in {"LOW", "MEDIUM", "HIGH"}


@pytest.mark.asyncio
async def test_ct06_quality_summary_detecta_high_risk(session):
    from src.core.analyzers import pipeline
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(FIXTURES / "alta_complejidad.py", tmp / "alta_complejidad.py")
    try:
        summary = await pipeline.run(tmp, ACTIVO_ID, "COMPLEJO", session)
        assert summary["nivel_riesgo"] == "HIGH"
    finally:
        shutil.rmtree(tmp)
