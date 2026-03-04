"""Modelos ORM para schemas code.* y quality.*"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Integer, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ArchivoFuenteORM(Base):
    __tablename__ = "archivos_fuente"
    __table_args__ = {"schema": "code"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aplicacion_id = Column(String(255), nullable=True)
    nombre = Column(String(255), nullable=False)
    ruta_archivo = Column(Text, nullable=False)
    proposito = Column(Text, nullable=True)
    capa = Column(String(50), nullable=True)
    lenguaje = Column(String(50), nullable=True)
    total_funciones = Column(Integer, default=0)
    total_clases = Column(Integer, default=0)
    endpoints = Column(JSONB, default=list)
    operaciones_bd = Column(JSONB, default=list)
    llamadas_externas = Column(JSONB, default=list)
    complejidad_ciclomatica = Column(Integer, default=0)
    lineas_codigo = Column(Integer, default=0)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)
    build_number = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)


class UnidadLogicaORM(Base):
    __tablename__ = "unidades_logicas"
    __table_args__ = {"schema": "code"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archivo_id = Column(UUID(as_uuid=True), ForeignKey("code.archivos_fuente.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("code.unidades_logicas.id", ondelete="CASCADE"), nullable=True)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)  # CLASE|FUNCION|INTERFAZ|ENUM
    capa = Column(String(50), nullable=True)
    proposito = Column(Text, nullable=True)
    complejidad = Column(Integer, default=0)
    lineas_codigo = Column(Integer, default=0)
    accede_bd = Column(Boolean, default=False)
    llamadas_externas = Column(JSONB, default=list)
    docstring = Column(Boolean, default=False)
    resumen = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)
    risk_level = Column(String(10), default="MEDIUM")
    overall_score = Column(Float, nullable=True)
    compliance = Column(JSONB, default=dict)
    activo = Column(Boolean, default=True)


class EscaneoORM(Base):
    __tablename__ = "escaneos"
    __table_args__ = {"schema": "quality"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aplicacion_id = Column(String(255), nullable=True)
    build_number = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    escaneado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    generado_por = Column(String(100), default="code-agent-v1")
    score_general = Column(Float, nullable=True)
    nivel_riesgo = Column(String(10), nullable=True)  # LOW|MEDIUM|HIGH
    archivos_total = Column(Integer, default=0)
    funciones_total = Column(Integer, default=0)
    clases_total = Column(Integer, default=0)
    dominios_negocio = Column(ARRAY(Text), default=list)
    metricas = Column(JSONB, default=dict)
    arquitectura = Column(JSONB, default=dict)
    seguridad = Column(JSONB, default=dict)
    rendimiento = Column(JSONB, default=dict)
    negocio = Column(JSONB, default=dict)
    cumplimiento = Column(JSONB, default=dict)
