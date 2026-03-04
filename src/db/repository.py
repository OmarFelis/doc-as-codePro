"""Repositorios para infra_detalle.archivos_fuente, unidades_logicas, escaneos."""
import json
import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models import ArchivoFuenteORM, UnidadLogicaORM, EscaneoORM
from src.models.domain import ArchivoFuente, UnidadLogica, Escaneo

_now = lambda: datetime.now(timezone.utc)
_uuid = lambda v: str(uuid.UUID(v)) if v else None
_json = lambda v: json.dumps(v, ensure_ascii=False) if v else None


# ── ArchivoFuente ──────────────────────────────────────────────────────────────

def _archivo_to_orm(a: ArchivoFuente) -> dict:
    return {
        "id": _uuid(a.id) or str(uuid.uuid4()),
        "activo_id": _uuid(a.activo_id),
        "aplicacion_id": _uuid(a.aplicacion_id),
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
        "metadata_": _json(a.metadata) if a.metadata else None,
        "build_number": a.build_number,
        "commit_hash": a.commit_hash,
        "escaneado_en": a.escaneado_en or _now(),
        "created_at": _now(),
        "updated_at": _now(),
    }


def _archivo_to_domain(row: ArchivoFuenteORM) -> ArchivoFuente:
    return ArchivoFuente(
        id=str(row.id),
        activo_id=str(row.activo_id),
        aplicacion_id=str(row.aplicacion_id) if row.aplicacion_id else None,
        nombre=row.nombre,
        ruta_archivo=row.ruta_archivo,
        proposito=row.proposito,
        capa=row.capa,
        lenguaje=row.lenguaje,
        total_funciones=row.total_funciones or 0,
        total_clases=row.total_clases or 0,
        endpoints=row.endpoints or 0,
        operaciones_bd=row.operaciones_bd or 0,
        llamadas_externas=row.llamadas_externas or 0,
        complejidad_ciclomatica=row.complejidad_ciclomatica or 0,
        lineas_codigo=row.lineas_codigo or 0,
        resumen=row.resumen,
        metadata=json.loads(row.metadata_) if row.metadata_ else {},
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
        select(ArchivoFuenteORM).where(ArchivoFuenteORM.activo_id == _uuid(activo_id))
    ).scalars().all()
    for row in rows:
        session.delete(row)
    session.flush()


# ── UnidadLogica ───────────────────────────────────────────────────────────────

def _unidad_to_orm(u: UnidadLogica) -> dict:
    return {
        "id": _uuid(u.id) or str(uuid.uuid4()),
        "archivo_id": _uuid(u.archivo_id),
        "parent_id": _uuid(u.parent_id),
        "activo_id": _uuid(u.activo_id),
        "aplicacion_id": _uuid(u.aplicacion_id),
        "nombre": u.nombre,
        "tipo": u.tipo if isinstance(u.tipo, str) else u.tipo.value,
        "linea_inicio": u.linea_inicio,
        "linea_fin": u.linea_fin,
        "complejidad": u.complejidad,
        "lineas_codigo": u.lineas_codigo,
        "accede_bd": u.accede_bd,
        "llamadas_externas": u.llamadas_externas,
        "docstring": u.docstring,
        "resumen": u.resumen,
        "metadata_": _json(u.metadata) if u.metadata else None,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _unidad_to_domain(row: UnidadLogicaORM) -> UnidadLogica:
    return UnidadLogica(
        id=str(row.id),
        archivo_id=str(row.archivo_id) if row.archivo_id else None,
        parent_id=str(row.parent_id) if row.parent_id else None,
        activo_id=str(row.activo_id),
        aplicacion_id=str(row.aplicacion_id) if row.aplicacion_id else None,
        nombre=row.nombre,
        tipo=row.tipo,
        linea_inicio=row.linea_inicio,
        linea_fin=row.linea_fin,
        complejidad=row.complejidad or 0,
        lineas_codigo=row.lineas_codigo or 0,
        accede_bd=row.accede_bd or False,
        llamadas_externas=row.llamadas_externas or 0,
        docstring=row.docstring or False,
        resumen=row.resumen,
        metadata=json.loads(row.metadata_) if row.metadata_ else {},
    )


def insert_unidades(session: Session, unidades: List[UnidadLogica]) -> List[UnidadLogica]:
    rows = [UnidadLogicaORM(**_unidad_to_orm(u)) for u in unidades]
    session.add_all(rows)
    session.flush()
    return [_unidad_to_domain(r) for r in rows]


def update_resumen_unidad(session: Session, unidad_id: str, resumen: str) -> None:
    row = session.get(UnidadLogicaORM, _uuid(unidad_id))
    if row:
        row.resumen = resumen
        row.updated_at = _now()
        session.flush()


# ── Escaneo ────────────────────────────────────────────────────────────────────

def _escaneo_to_orm(e: Escaneo) -> dict:
    nivel = e.nivel_riesgo if isinstance(e.nivel_riesgo, str) else (e.nivel_riesgo.value if e.nivel_riesgo else "LOW")
    return {
        "id": _uuid(e.id) or str(uuid.uuid4()),
        "activo_id": _uuid(e.activo_id),
        "aplicacion_id": _uuid(e.aplicacion_id),
        "build_number": e.build_number,
        "commit_hash": e.commit_hash,
        "escaneado_en": e.escaneado_en or _now(),
        "generado_por": e.generado_por,
        "score_general": e.score_general,
        "nivel_riesgo": nivel,
        "archivos_total": e.archivos_total,
        "funciones_total": e.funciones_total,
        "clases_total": e.clases_total,
        "dominios_negocio": _json(e.dominios_negocio) if e.dominios_negocio else None,
        "metricas": _json(e.metricas) if e.metricas else None,
        "arquitectura": _json(e.arquitectura) if e.arquitectura else None,
        "seguridad": _json(e.seguridad) if e.seguridad else None,
        "rendimiento": _json(e.rendimiento) if e.rendimiento else None,
        "negocio": _json(e.negocio) if e.negocio else None,
        "cumplimiento": _json(e.cumplimiento) if e.cumplimiento else None,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _escaneo_to_domain(row: EscaneoORM) -> Escaneo:
    return Escaneo(
        id=str(row.id),
        activo_id=str(row.activo_id),
        aplicacion_id=str(row.aplicacion_id) if row.aplicacion_id else None,
        build_number=row.build_number,
        commit_hash=row.commit_hash,
        escaneado_en=row.escaneado_en,
        generado_por=row.generado_por,
        score_general=row.score_general,
        nivel_riesgo=row.nivel_riesgo,
        archivos_total=row.archivos_total or 0,
        funciones_total=row.funciones_total or 0,
        clases_total=row.clases_total or 0,
        dominios_negocio=json.loads(row.dominios_negocio) if row.dominios_negocio else [],
        metricas=json.loads(row.metricas) if row.metricas else {},
        arquitectura=json.loads(row.arquitectura) if row.arquitectura else {},
        seguridad=json.loads(row.seguridad) if row.seguridad else {},
        rendimiento=json.loads(row.rendimiento) if row.rendimiento else {},
        negocio=json.loads(row.negocio) if row.negocio else {},
        cumplimiento=json.loads(row.cumplimiento) if row.cumplimiento else {},
    )


def insert_escaneo(session: Session, escaneo: Escaneo) -> Escaneo:
    row = EscaneoORM(**_escaneo_to_orm(escaneo))
    session.add(row)
    session.flush()
    return _escaneo_to_domain(row)


def get_escaneos_by_activo(session: Session, activo_id: str) -> List[Escaneo]:
    rows = session.execute(
        select(EscaneoORM).where(EscaneoORM.activo_id == _uuid(activo_id))
        .order_by(EscaneoORM.escaneado_en.desc())
    ).scalars().all()
    return [_escaneo_to_domain(r) for r in rows]
