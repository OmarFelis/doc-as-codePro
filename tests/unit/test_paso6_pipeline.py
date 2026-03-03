"""Paso 6 — Tests del pipeline completo con SQLite en memoria."""
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from src.db import repository as repo
from src.models.domain import ArchivoFuente, UnidadLogica, Escaneo

ACTIVO_ID = str(uuid.uuid4())


class _Base(DeclarativeBase):
    pass


class ArchivoFuenteTest(_Base):
    __tablename__ = "archivos_fuente_p6"
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
    __tablename__ = "unidades_logicas_p6"
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
    __tablename__ = "escaneos_p6"
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


@pytest.fixture
def sample_project(tmp_path):
    """Proyecto Python mínimo con una clase y dos métodos."""
    (tmp_path / "payments.py").write_text(
        "class Comision:\n"
        "    def calcular(self, monto, tipo):\n"
        "        if monto <= 0:\n"
        "            raise ValueError('monto invalido')\n"
        "        return monto * 0.035 if tipo == 'credito' else monto * 0.015\n\n"
        "    def validar(self, monto):\n"
        "        return monto >= 1.0\n"
    )
    return tmp_path


@pytest.mark.asyncio
async def test_pipeline_persiste_archivo_fuente(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    rows = session.query(ArchivoFuenteTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) >= 1
    assert rows[0].nombre == "payments.py"


@pytest.mark.asyncio
async def test_pipeline_persiste_unidades_logicas(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    rows = session.query(UnidadLogicaTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) > 0


@pytest.mark.asyncio
async def test_pipeline_produce_jerarquia_clase_funcion(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    clases = session.query(UnidadLogicaTest).filter_by(activo_id=ACTIVO_ID, tipo="CLASE").all()
    funciones = session.query(UnidadLogicaTest).filter_by(activo_id=ACTIVO_ID, tipo="FUNCION").all()
    assert len(clases) >= 1
    assert len(funciones) >= 1
    # Al menos una función tiene parent_id apuntando a una clase
    clase_ids = {c.id for c in clases}
    assert any(f.parent_id in clase_ids for f in funciones)


@pytest.mark.asyncio
async def test_pipeline_persiste_escaneo(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    rows = session.query(EscaneoTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) == 1
    assert rows[0].score_general is not None
    assert rows[0].nivel_riesgo in ("LOW", "MEDIUM", "HIGH")


@pytest.mark.asyncio
async def test_pipeline_retorna_summary_correcto(session, sample_project):
    from src.core.analyzers import pipeline
    summary = await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    assert summary["activo_id"] == ACTIVO_ID
    assert "escaneo_id" in summary
    assert "score_general" in summary
    assert summary["archivos_total"] >= 1
    assert summary["funciones_total"] >= 1


@pytest.mark.asyncio
async def test_pipeline_escaneo_insert_only_en_doble_ejecucion(session, sample_project):
    from src.core.analyzers import pipeline
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    await pipeline.run(sample_project, ACTIVO_ID, "ACS", session)
    session.commit()
    rows = session.query(EscaneoTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) == 2  # INSERT-only, historial inmutable
