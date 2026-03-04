"""Modelos ORM alineados al schema infra_detalle (BD de Stefano)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ArchivoFuenteORM(Base):
    __tablename__ = "archivos_fuente"
    __table_args__ = {"schema": "infra_detalle"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aplicacion_id = Column(UUID(as_uuid=True), nullable=False)
    nombre = Column(String(255), nullable=False)
    ruta_archivo = Column(Text, nullable=True)
    proposito = Column(String(30), nullable=True)
    capa = Column(String(20), nullable=True)
    lenguaje = Column(String(20), nullable=True)
    total_funciones = Column(Integer, default=0)
    total_clases = Column(Integer, default=0)
    endpoints = Column(Integer, default=0)
    operaciones_bd = Column(Integer, default=0)
    llamadas_externas = Column(Integer, default=0)
    complejidad_ciclomatica = Column(Integer, nullable=True)
    lineas_codigo = Column(Integer, nullable=True)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)
    build_number = Column(String(20), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class UnidadLogicaORM(Base):
    __tablename__ = "unidades_logicas"
    __table_args__ = {"schema": "infra_detalle"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archivo_id = Column(UUID(as_uuid=True), ForeignKey("infra_detalle.archivos_fuente.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("infra_detalle.unidades_logicas.id", ondelete="CASCADE"), nullable=True)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aplicacion_id = Column(UUID(as_uuid=True), nullable=False)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)  # CLASE|FUNCION|INTERFAZ|ENUM
    linea_inicio = Column(Integer, nullable=True)
    linea_fin = Column(Integer, nullable=True)
    complejidad = Column(Integer, nullable=True)
    lineas_codigo = Column(Integer, nullable=True)
    accede_bd = Column(Boolean, default=False)
    llamadas_externas = Column(Integer, default=0)
    docstring = Column(Boolean, default=False)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class EscaneoORM(Base):
    __tablename__ = "escaneos"
    __table_args__ = {"schema": "infra_detalle"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aplicacion_id = Column(UUID(as_uuid=True), nullable=False)
    build_number = Column(String(20), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    generado_por = Column(String(100), nullable=True)
    score_general = Column(Float, nullable=True)
    nivel_riesgo = Column(String(10), nullable=False)  # LOW|MEDIUM|HIGH
    archivos_total = Column(Integer, default=0)
    funciones_total = Column(Integer, default=0)
    clases_total = Column(Integer, default=0)
    dominios_negocio = Column(Text, nullable=True)
    metricas = Column(Text, nullable=True)
    arquitectura = Column(Text, nullable=True)
    seguridad = Column(Text, nullable=True)
    rendimiento = Column(Text, nullable=True)
    negocio = Column(Text, nullable=True)
    cumplimiento = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
