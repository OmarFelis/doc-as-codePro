"""Paso 5 — Tests de los repositorios nuevos (SQLite en memoria)."""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base
from src.db import repository as repo
from src.models.domain import ArchivoFuente, UnidadLogica, Escaneo, TipoUnidad, RiskLevel

ACTIVO_ID = str(uuid.uuid4())


# ── SQLite-compatible ORM overrides ───────────────────────────────────────────
# SQLite no soporta UUID ni JSONB ni ARRAY — redefinimos las tablas para tests

from sqlalchemy.orm import DeclarativeBase

class _Base(DeclarativeBase):
    pass


class ArchivoFuenteTest(_Base):
    __tablename__ = "archivos_fuente"
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
    __tablename__ = "unidades_logicas"
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
    __tablename__ = "escaneos"
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

    # Monkey-patch los ORM del repo para usar las versiones SQLite
    import src.db.repository as r
    orig_a, orig_u, orig_e = r.ArchivoFuenteORM, r.UnidadLogicaORM, r.EscaneoORM
    r.ArchivoFuenteORM = ArchivoFuenteTest
    r.UnidadLogicaORM = UnidadLogicaTest
    r.EscaneoORM = EscaneoTest

    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    r.ArchivoFuenteORM, r.UnidadLogicaORM, r.EscaneoORM = orig_a, orig_u, orig_e


def _archivo() -> ArchivoFuente:
    return ArchivoFuente(
        activo_id=ACTIVO_ID,
        nombre="payments.py",
        ruta_archivo="src/payments.py",
        capa="dominio",
        lenguaje="python",
        total_funciones=2,
        total_clases=1,
        lineas_codigo=50,
    )


def _unidad(archivo_id: str, tipo=TipoUnidad.FUNCION, parent_id=None) -> UnidadLogica:
    return UnidadLogica(
        activo_id=ACTIVO_ID,
        archivo_id=archivo_id,
        nombre="calcular_comision",
        tipo=tipo,
        capa="dominio",
        risk_level=RiskLevel.LOW,
        overall_score=75.0,
        parent_id=parent_id,
    )


def _escaneo() -> Escaneo:
    return Escaneo(
        activo_id=ACTIVO_ID,
        score_general=66.4,
        nivel_riesgo=RiskLevel.HIGH,
        archivos_total=1,
        funciones_total=2,
        clases_total=1,
    )


# ── Tests ArchivoFuente ───────────────────────────────────────────────────────

def test_insert_archivo_retorna_con_id(session):
    saved = repo.insert_archivo(session, _archivo())
    assert saved.id is not None
    assert saved.nombre == "payments.py"


def test_insert_archivo_activo_id_correcto(session):
    saved = repo.insert_archivo(session, _archivo())
    assert saved.activo_id == ACTIVO_ID


# ── Tests UnidadLogica ────────────────────────────────────────────────────────

def test_insert_unidades_retorna_lista_con_ids(session):
    archivo = repo.insert_archivo(session, _archivo())
    unidades = [_unidad(archivo.id), _unidad(archivo.id)]
    saved = repo.insert_unidades(session, unidades)
    assert len(saved) == 2
    assert all(u.id is not None for u in saved)


def test_insert_unidades_preserva_parent_id(session):
    archivo = repo.insert_archivo(session, _archivo())
    clase_id = str(uuid.uuid4())
    unidad = _unidad(archivo.id, tipo=TipoUnidad.FUNCION, parent_id=clase_id)
    saved = repo.insert_unidades(session, [unidad])
    assert saved[0].parent_id == clase_id


def test_insert_unidades_preserva_archivo_id(session):
    archivo = repo.insert_archivo(session, _archivo())
    saved = repo.insert_unidades(session, [_unidad(archivo.id)])
    assert saved[0].archivo_id == archivo.id


# ── Tests Escaneo ─────────────────────────────────────────────────────────────

def test_insert_escaneo_retorna_con_id(session):
    saved = repo.insert_escaneo(session, _escaneo())
    assert saved.id is not None
    assert saved.score_general == 66.4


def test_insert_escaneo_es_insert_only(session):
    repo.insert_escaneo(session, _escaneo())
    repo.insert_escaneo(session, _escaneo())
    session.commit()
    rows = session.query(EscaneoTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) == 2  # INSERT-only, no upsert


def test_get_escaneos_by_activo(session):
    repo.insert_escaneo(session, _escaneo())
    repo.insert_escaneo(session, _escaneo())
    session.commit()
    results = repo.get_escaneos_by_activo(session, ACTIVO_ID)
    assert len(results) == 2


# ── Test delete ───────────────────────────────────────────────────────────────

def test_delete_archivos_by_activo(session):
    repo.insert_archivo(session, _archivo())
    repo.insert_archivo(session, _archivo())
    session.commit()
    repo.delete_archivos_by_activo(session, ACTIVO_ID)
    session.commit()
    rows = session.query(ArchivoFuenteTest).filter_by(activo_id=ACTIVO_ID).all()
    assert len(rows) == 0
