"""Test de integración Fase 2 — pipeline completo con agente Strands real."""
import src  # fix AWS_CONFIG_FILE antes de boto3
import uuid
import asyncio
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from src.db import repository as repo
from src.core.enricher.enrichment_agent import build_enrichment_agent
from src.core.analyzers.pipeline import run

ACTIVO_ID = str(uuid.uuid4())
MICROSERVICE = "test-fase2"
# Usamos un proyecto minimo de 1 archivo para que el agente no tarde demasiado


@pytest.fixture(scope="module")
def sample_project(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("fase2")
    (tmp / "comision.py").write_text(
        "class Comision:\n"
        "    def calcular(self, monto, tipo):\n"
        "        if monto <= 0:\n"
        "            raise ValueError('monto invalido')\n"
        "        return monto * 0.035 if tipo == 'credito' else monto * 0.015\n\n"
        "    def validar(self, monto):\n"
        "        return monto >= 1.0\n"
    )
    return tmp


class _Base(DeclarativeBase):
    pass


class ArchivoFuenteF2(_Base):
    __tablename__ = "archivos_fuente_f2"
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


class UnidadLogicaF2(_Base):
    __tablename__ = "unidades_logicas_f2"
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


class EscaneoF2(_Base):
    __tablename__ = "escaneos_f2"
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


@pytest.fixture(scope="module")
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _Base.metadata.create_all(engine)
    orig_a, orig_u, orig_e = repo.ArchivoFuenteORM, repo.UnidadLogicaORM, repo.EscaneoORM
    repo.ArchivoFuenteORM = ArchivoFuenteF2
    repo.UnidadLogicaORM = UnidadLogicaF2
    repo.EscaneoORM = EscaneoF2
    s = sessionmaker(bind=engine)()
    yield s
    s.close()
    repo.ArchivoFuenteORM, repo.UnidadLogicaORM, repo.EscaneoORM = orig_a, orig_u, orig_e


@pytest.fixture(scope="module")
def agent():
    a = build_enrichment_agent()
    if a is None:
        pytest.skip("Credenciales SSO no disponibles")
    return a


def test_pipeline_sin_agent_completa_sin_error(session, sample_project):
    result = asyncio.run(run(
        project_path=sample_project,
        activo_id=ACTIVO_ID,
        microservice_name=MICROSERVICE,
        session=session,
    ))
    assert result["archivos_total"] > 0
    assert result["funciones_total"] > 0
    assert result["enriquecido"] is False


def test_pipeline_con_agent_real_enriquece(session, agent, sample_project):
    result = asyncio.run(run(
        project_path=sample_project,
        activo_id=ACTIVO_ID,
        microservice_name=MICROSERVICE,
        session=session,
        enrichment_agent=agent,
    ))
    assert result["enriquecido"] is True
    assert result["archivos_total"] > 0


def test_escaneo_negocio_tiene_datos(session):
    escaneos = session.query(EscaneoF2).filter_by(activo_id=ACTIVO_ID).all()
    assert len(escaneos) > 0
    con_negocio = [e for e in escaneos if e.negocio]
    assert len(con_negocio) > 0
