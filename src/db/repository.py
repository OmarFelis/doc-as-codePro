"""Repositorios para code.archivos_fuente, code.unidades_logicas, quality.escaneos."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models import ArchivoFuenteORM, UnidadLogicaORM, EscaneoORM
from src.models.domain import ArchivoFuente, UnidadLogica, Escaneo


# ── ArchivoFuente ──────────────────────────────────────────────────────────────

def _archivo_to_orm(a: ArchivoFuente) -> dict:
    return {
        "id": str(uuid.UUID(a.id)) if a.id else str(uuid.uuid4()),
        "activo_id": str(uuid.UUID(a.activo_id)),
        "aplicacion_id": a.aplicacion_id,
        "nombre": a.nombre,
        "ruta_archivo": a.ruta_archivo,
        "proposito": a.proposito,
        "capa": a.capa,
        "lenguaje": a.lenguaje,
        "total_funciones": a.total_funciones,
        "total_clases": a.total_clases,
        "endpoints": a.endpoints,
        "operaciones_bd": a.operaciones_bd,
        "llamadas_externas": a.llamadas_externas,
        "complejidad_ciclomatica": a.complejidad_ciclomatica,
        "lineas_codigo": a.lineas_codigo,
        "resumen": a.resumen,
        "metadata_": a.metadata,
        "build_number": a.build_number,
        "commit_hash": a.commit_hash,
        "escaneado_en": a.escaneado_en or datetime.now(timezone.utc),
    }


def _archivo_to_domain(row: ArchivoFuenteORM) -> ArchivoFuente:
    return ArchivoFuente(
        id=str(row.id),
        activo_id=str(row.activo_id),
        aplicacion_id=row.aplicacion_id,
        nombre=row.nombre,
        ruta_archivo=row.ruta_archivo,
        proposito=row.proposito,
        capa=row.capa,
        lenguaje=row.lenguaje,
        total_funciones=row.total_funciones or 0,
        total_clases=row.total_clases or 0,
        endpoints=row.endpoints or [],
        operaciones_bd=row.operaciones_bd or [],
        llamadas_externas=row.llamadas_externas or [],
        complejidad_ciclomatica=row.complejidad_ciclomatica or 0,
        lineas_codigo=row.lineas_codigo or 0,
        resumen=row.resumen,
        metadata=row.metadata_ or {},
        build_number=row.build_number,
        commit_hash=row.commit_hash,
        escaneado_en=row.escaneado_en,
    )


def insert_archivo(session: Session, archivo: ArchivoFuente) -> ArchivoFuente:
    row = ArchivoFuenteORM(**_archivo_to_orm(archivo))
    session.add(row)
    session.flush()
    return _archivo_to_domain(row)


def delete_archivos_by_activo(session: Session, activo_id: str) -> None:
    rows = session.execute(
        select(ArchivoFuenteORM).where(ArchivoFuenteORM.activo_id == str(uuid.UUID(activo_id)))
    ).scalars().all()
    for row in rows:
        session.delete(row)
    session.flush()


# ── UnidadLogica ───────────────────────────────────────────────────────────────

def _unidad_to_orm(u: UnidadLogica) -> dict:
    return {
        "id": str(uuid.UUID(u.id)) if u.id else str(uuid.uuid4()),
        "archivo_id": str(uuid.UUID(u.archivo_id)) if u.archivo_id else None,
        "parent_id": str(uuid.UUID(u.parent_id)) if u.parent_id else None,
        "activo_id": str(uuid.UUID(u.activo_id)),
        "nombre": u.nombre,
        "tipo": u.tipo if isinstance(u.tipo, str) else u.tipo.value,
        "capa": u.capa,
        "proposito": u.proposito,
        "complejidad": u.complejidad,
        "lineas_codigo": u.lineas_codigo,
        "accede_bd": u.accede_bd,
        "llamadas_externas": u.llamadas_externas,
        "docstring": u.docstring,
        "resumen": u.resumen,
        "metadata_": u.metadata,
        "risk_level": u.risk_level if isinstance(u.risk_level, str) else u.risk_level.value,
        "overall_score": u.overall_score,
        "compliance": u.compliance,
    }


def _unidad_to_domain(row: UnidadLogicaORM) -> UnidadLogica:
    return UnidadLogica(
        id=str(row.id),
        archivo_id=str(row.archivo_id) if row.archivo_id else None,
        parent_id=str(row.parent_id) if row.parent_id else None,
        activo_id=str(row.activo_id),
        nombre=row.nombre,
        tipo=row.tipo,
        capa=row.capa,
        proposito=row.proposito,
        complejidad=row.complejidad or 0,
        lineas_codigo=row.lineas_codigo or 0,
        accede_bd=row.accede_bd or False,
        llamadas_externas=row.llamadas_externas or [],
        docstring=row.docstring or False,
        resumen=row.resumen,
        metadata=row.metadata_ or {},
        risk_level=row.risk_level,
        overall_score=row.overall_score,
        compliance=row.compliance or {},
    )


def insert_unidades(session: Session, unidades: List[UnidadLogica]) -> List[UnidadLogica]:
    rows = [UnidadLogicaORM(**_unidad_to_orm(u)) for u in unidades]
    session.add_all(rows)
    session.flush()
    return [_unidad_to_domain(r) for r in rows]


# ── Escaneo ────────────────────────────────────────────────────────────────────

def _escaneo_to_orm(e: Escaneo) -> dict:
    return {
        "id": str(uuid.UUID(e.id)) if e.id else str(uuid.uuid4()),
        "activo_id": str(uuid.UUID(e.activo_id)),
        "aplicacion_id": e.aplicacion_id,
        "build_number": e.build_number,
        "commit_hash": e.commit_hash,
        "escaneado_en": e.escaneado_en or datetime.now(timezone.utc),
        "generado_por": e.generado_por,
        "score_general": e.score_general,
        "nivel_riesgo": e.nivel_riesgo if isinstance(e.nivel_riesgo, str) else (e.nivel_riesgo.value if e.nivel_riesgo else None),
        "archivos_total": e.archivos_total,
        "funciones_total": e.funciones_total,
        "clases_total": e.clases_total,
        "dominios_negocio": e.dominios_negocio,
        "metricas": e.metricas,
        "arquitectura": e.arquitectura,
        "seguridad": e.seguridad,
        "rendimiento": e.rendimiento,
        "negocio": e.negocio,
        "cumplimiento": e.cumplimiento,
    }


def _escaneo_to_domain(row: EscaneoORM) -> Escaneo:
    return Escaneo(
        id=str(row.id),
        activo_id=str(row.activo_id),
        aplicacion_id=row.aplicacion_id,
        build_number=row.build_number,
        commit_hash=row.commit_hash,
        escaneado_en=row.escaneado_en,
        generado_por=row.generado_por,
        score_general=row.score_general,
        nivel_riesgo=row.nivel_riesgo,
        archivos_total=row.archivos_total or 0,
        funciones_total=row.funciones_total or 0,
        clases_total=row.clases_total or 0,
        dominios_negocio=row.dominios_negocio or [],
        metricas=row.metricas or {},
        arquitectura=row.arquitectura or {},
        seguridad=row.seguridad or {},
        rendimiento=row.rendimiento or {},
        negocio=row.negocio or {},
        cumplimiento=row.cumplimiento or {},
    )


def insert_escaneo(session: Session, escaneo: Escaneo) -> Escaneo:
    row = EscaneoORM(**_escaneo_to_orm(escaneo))
    session.add(row)
    session.flush()
    return _escaneo_to_domain(row)


def get_escaneos_by_activo(session: Session, activo_id: str) -> List[Escaneo]:
    rows = session.execute(
        select(EscaneoORM).where(EscaneoORM.activo_id == str(uuid.UUID(activo_id)))
        .order_by(EscaneoORM.escaneado_en.desc())
    ).scalars().all()
    return [_escaneo_to_domain(r) for r in rows]
